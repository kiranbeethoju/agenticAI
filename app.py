"""
Flask Web Application for Agent System
Requires credentials before allowing any agent operations
"""

from flask import Flask, render_template, request, jsonify, session, Response, send_file
from flask_cors import CORS
import os
import yaml
import json
import time
from datetime import datetime, timedelta
import secrets
from cassandra_db import flows_table, logs_table, runs_table, telemetry_table
import csv
import io
import re
import urllib.parse
import urllib.request

# Create necessary directories
os.makedirs('workflows', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Import agent components
from llm_providers import LLMProviderFactory
from observability import Observer
from agent import SimplifiedAgent


# Simple query helpers for Cassandra
class Query:
    def __init__(self):
        pass
    
    @staticmethod
    def flow_id_equals(flow_id):
        return f"flow_id == '{flow_id}'"
    
    @staticmethod  
    def run_id_equals(run_id):
        return f"run_id == '{run_id}'"


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure session key
app.permanent_session_lifetime = timedelta(hours=1)  # 1 hour session
CORS(app)

# Global variables
active_agents = {}


def _insert_telemetry(event: dict):
    try:
        telemetry_table.insert({
            'timestamp': datetime.now().isoformat(),
            **(event or {})
        })
    except Exception:
        # Telemetry should never break core app flows
        pass


def _duckduckgo_search(query: str, max_results: int = 5):
    q = (query or '').strip()
    if not q:
        return [], 'empty_query', None

    # Preferred: duckduckgo_search library (more reliable results)
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=max(1, int(max_results or 5))):
                results.append({
                    'title': (r.get('title') or '').strip(),
                    'text': (r.get('body') or '').strip(),
                    'url': (r.get('href') or '').strip()
                })
        return results, 'ddgs', None
    except ImportError as e:
        # Library not installed
        ddgs_error = str(e)
    except Exception as e:
        # Library failed; we can still fallback
        ddgs_error = str(e)

    params = {
        'q': q,
        'format': 'json',
        'no_html': 1,
        'skip_disambig': 1
    }
    url = 'https://api.duckduckgo.com/?' + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
    except Exception as e:
        # If outbound internet is blocked (corporate network / firewall), return a structured error
        return [{
            'title': 'ToolError',
            'text': f'DuckDuckGo request failed: {str(e)}',
            'url': url
        }], 'ddg_instant_answer_error', ddgs_error if 'ddgs_error' in locals() else None

    try:
        data = json.loads(body.decode('utf-8'))
    except Exception:
        data = json.loads(body.decode('utf-8', errors='ignore'))

    results = []
    abstract = (data.get('AbstractText') or '').strip()
    if abstract:
        results.append({
            'title': (data.get('Heading') or 'Abstract').strip(),
            'text': abstract,
            'url': (data.get('AbstractURL') or '').strip()
        })

    def walk_topics(topics):
        for t in topics or []:
            if isinstance(t, dict) and t.get('Text') and t.get('FirstURL'):
                results.append({
                    'title': (t.get('Text') or '')[:80],
                    'text': (t.get('Text') or '').strip(),
                    'url': (t.get('FirstURL') or '').strip()
                })
            elif isinstance(t, dict) and t.get('Topics'):
                walk_topics(t.get('Topics'))

    walk_topics(data.get('RelatedTopics') or [])
    return results[:max(1, int(max_results or 5))], 'ddg_instant_answer', ddgs_error if 'ddgs_error' in locals() else None


def _render_with_context(template: str, *, context: dict, steps: list, step_index: int):
    out = (template or '').replace("{{input}}", context.get('input', '') or '')
    out = out.replace("{{tool_input}}", context.get('tool_input', '') or '')
    out = out.replace("{{tool input}}", context.get('tool_input', '') or '')

    for key, res in (context.get('history') or {}).items():
        if key.startswith('step'):
            out = out.replace(f"{{{{step{key[4:]}}}}}", res)

    name_map = {}
    for i, past_step in enumerate(steps):
        if i < step_index:
            step_key = f"step{i+1}"
            if step_key in (context.get('history') or {}):
                name_map[past_step.get('name', f"Step {i+1}")] = context['history'][step_key]

    for name, res in name_map.items():
        out = out.replace(f"{{{{{name}}}}}", res)
    return out


def _execute_step_tools(*, step: dict, context: dict, steps: list, step_index: int, session_id=None, workflow_id=None, run_id=None):
    enable_tool = bool(step.get('enable_tool'))
    if not enable_tool:
        return []

    tools = step.get('tools') or []
    outputs = []
    for tool in tools:
        tool_type = (tool.get('type') or '').strip()
        if tool_type != 'google_search':
            continue

        query_template = tool.get('query_template') or tool.get('query') or '{{input}}'
        rendered_query = _render_with_context(query_template, context=context, steps=steps, step_index=step_index)
        context['tool_input'] = rendered_query
        max_results = tool.get('max_results', 5)
        results, source, source_error = _duckduckgo_search(rendered_query, max_results=max_results)

        try:
            print(f"[TOOL] google_search | step={step.get('name', f'Step {step_index+1}')} | source={source} | results={len(results) if isinstance(results, list) else 0} | query={rendered_query}")
            if source_error:
                print(f"[TOOL] google_search source_error: {source_error}")
        except Exception:
            pass

        try:
            logs_table.insert({
                'timestamp': datetime.now().isoformat(),
                'message': f"Tool Call: google_search ({step.get('name', f'Step {step_index+1}')})",
                'response': {
                    'text': f"Query: {rendered_query} | Results: {len(results) if isinstance(results, list) else 0}",
                    'reasoning': 'Tool Execution'
                },
                'session_id': session_id,
                'type': 'tool',
                'full_context': {
                    'tool': 'google_search',
                    'query': rendered_query,
                    'max_results': max_results,
                    'source': source,
                    'source_error': source_error,
                    'results_preview': results[:3] if isinstance(results, list) else results
                }
            })
        except Exception:
            pass
        outputs.append({
            'tool': 'google_search',
            'query': rendered_query,
            'results': results
        })

    return outputs


def _execute_workflow_steps(*, steps, user_input, data_config, provider, observer, session_id=None, workflow_id=None, run_id=None):
    context = {"input": user_input, "history": {}}

    def run_step_logic(step_index, step):
        step_name = step.get('name', f'Step {step_index+1}')
        prompt_template = step.get('prompt', '')

        enable_llm = step.get('enable_llm')
        if enable_llm is None:
            enable_llm = True

        enable_tool = bool(step.get('enable_tool'))
        tool_outputs = _execute_step_tools(step=step, context=context, steps=steps, step_index=step_index, session_id=session_id, workflow_id=workflow_id, run_id=run_id)
        tool_block = json.dumps(tool_outputs, ensure_ascii=False, indent=2) if enable_tool else ''

        final_prompt = _render_with_context(prompt_template, context=context, steps=steps, step_index=step_index)
        if enable_tool:
            if "{{tool_results}}" in final_prompt:
                final_prompt = final_prompt.replace("{{tool_results}}", tool_block)
            else:
                final_prompt = final_prompt + "\n\nTool Results:\n" + tool_block

        flow_config = data_config or {}
        exec_model = flow_config.get('model') or provider.config.get("model")
        target_key = (flow_config.get('api_key') or "").strip()

        if not target_key or ("nvidia" in exec_model.lower() and target_key.startswith("AIza")):
            target_key = provider.config.get('api_key', "").strip()

        target_url = (provider.config.get('base_url', 'https://integrate.api.nvidia.com/v1')).strip()

        if not enable_llm:
            result_text = tool_block
            latency = 0.0
            _insert_telemetry({
                'type': 'workflow_step',
                'session_id': session_id,
                'workflow_id': workflow_id,
                'run_id': run_id,
                'step_index': step_index,
                'step_name': step_name,
                'model': None,
                'latency': latency,
                'input_preview': str(final_prompt)[:200],
                'output_preview': str(result_text)[:200]
            })
            return step_index, step_name, result_text

        step_start = time.time()
        observer.trace_call(f"WorkflowStep-{step_index+1}", final_prompt)

        from openai import OpenAI
        step_client = OpenAI(api_key=target_key, base_url=target_url)

        extra_body = None

        is_reasoning_model = "nemotron" in exec_model.lower() and "nano" not in exec_model.lower()
        if "gpt-oss" in exec_model.lower():
            is_reasoning_model = False
        if is_reasoning_model:
            extra_body = {
                "reasoning_budget": 16383,
                "chat_template_kwargs": {"enable_thinking": True}
            }
        if "llama-3.1-405b" in exec_model.lower():
            extra_body = {
                "reasoning_budget": 16383,
                "chat_template_kwargs": {"enable_thinking": True}
            }

        completion = step_client.chat.completions.create(
            model=exec_model,
            messages=[{"content": final_prompt, "role": "user"}],
            extra_body=extra_body,
            stream=False
        )

        result_text = completion.choices[0].message.content
        latency = time.time() - step_start
        provider._record_metrics(latency)
        observer.trace_response(f"WorkflowStep-{step_index+1}", {
            "latency": latency,
            "text": result_text,
            "model": exec_model
        })

        _insert_telemetry({
            'type': 'workflow_step',
            'session_id': session_id,
            'workflow_id': workflow_id,
            'run_id': run_id,
            'step_index': step_index,
            'step_name': step_name,
            'model': exec_model,
            'latency': latency,
            'input_preview': str(final_prompt)[:200],
            'output_preview': str(result_text)[:200]
        })

        return step_index, step_name, result_text

    from concurrent.futures import ThreadPoolExecutor

    groups = []
    for i, step in enumerate(steps):
        if not step.get('parallel') or not groups:
            groups.append([(i, step)])
        else:
            groups[-1].append((i, step))

    events = []
    for group in groups:
        if len(group) == 1:
            idx, step = group[0]
            res_idx, step_name, res_content = run_step_logic(idx, step)
            context["history"][f"step{res_idx+1}"] = res_content
            events.append({"type": "step", "step_index": res_idx, "name": step_name, "content": res_content})
        else:
            with ThreadPoolExecutor(max_workers=len(group)) as executor:
                futures = [executor.submit(run_step_logic, idx, s) for idx, s in group]
                for future in futures:
                    res_idx, step_name, res_content = future.result()
                    context["history"][f"step{res_idx+1}"] = res_content
                    events.append({"type": "step", "step_index": res_idx, "name": step_name, "content": res_content})

    return context, events


def validate_credentials(provider, api_key, base_url=None):
    """Validate credentials by attempting a light-weight API check"""
    try:
        if provider == "nvidia":
            target_url = base_url or "https://integrate.api.nvidia.com/v1"
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=target_url)
            # Just list models - doesn't require specific model knowledge or tokens
            client.models.list()
            
        elif provider == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            # List models for Gemini validation
            client.models.list()
        
        return True, "Credentials validated successfully"
    except Exception as e:
        # Provide a cleaner error if it's a known API issue
        err_str = str(e)
        if "401" in err_str:
            return False, "API Key is invalid or unauthorized. Please check your credentials."
        return False, f"Validation failed: {err_str}"


@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@app.route('/api/session-check', methods=['GET'])
def session_check():
    """Check if user has an active session"""
    session_id = session.get('session_id')
    has_session = session_id and session_id in active_agents
    
    return jsonify({
        'has_session': has_session,
        'provider': session.get('provider') if has_session else None,
        'session_id': session_id if has_session else None
    })


@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate credentials and create agent session"""
    data = request.json
    provider = data.get('provider', 'nvidia')
    api_key = data.get('api_key', '').strip()
    base_url = data.get('base_url', '').strip()
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key is required'
        }), 400
    
    # Validate credentials
    is_valid, message = validate_credentials(provider, api_key, base_url)
    
    if not is_valid:
        return jsonify({
            'success': False,
            'error': message
        }), 401
    
    # Create session ID
    session_id = secrets.token_urlsafe(16)
    session.permanent = True  # Make session permanent
    session['session_id'] = session_id
    session['provider'] = provider
    
    # Create config for this session
    config = {
        'llm_providers': {
            provider: {
                'enabled': True,
                'api_key': api_key,
                'default': True
            }
        },
        'agent': {
            'name': 'WebAgent',
            'max_iterations': 10,
            'temperature': 1.0,
            'top_p': 1.0,
            'max_tokens': 16384
        },
        'observability': {
            'logging': {
                'enabled': True,
                'level': 'INFO',
                'format': 'detailed',
                'file': f'logs/session_{session_id}.log'
            },
            'tracing': {
                'enabled': True,
                'trace_calls': True,
                'trace_responses': True
            },
            'metrics': {
                'enabled': True,
                'track_latency': True,
                'track_token_usage': True
            }
        }
    }
    
    if provider == 'nvidia':
        config['llm_providers'][provider]['base_url'] = base_url or 'https://integrate.api.nvidia.com/v1'
        # Using the exact name from the user's working test script
        config['llm_providers'][provider]['model'] = 'openai/gpt-oss-20b'
        config['llm_providers'][provider]['streaming'] = True
        config['llm_providers'][provider]['reasoning_budget'] = 16384
        config['llm_providers'][provider]['enable_thinking'] = True
    
    # Create observer
    observer = Observer(config['observability'])
    
    # Create provider
    provider_obj = LLMProviderFactory.create_provider(
        provider,
        config['llm_providers'][provider],
        observer
    )
    
    # Store in active agents
    active_agents[session_id] = {
        'provider': provider_obj,
        'observer': observer,
        'config': config,
        'history': [],
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'message': message,
        'session_id': session_id,
        'provider': provider,
        'model': config['llm_providers'][provider].get('model'),
        'api_key': api_key
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests with SSE streaming"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401
    
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400
    
    agent_data = active_agents[session_id]
    provider = agent_data['provider']
    observer = agent_data['observer']
    
    def generate_events():
        full_response = ""
        reasoning_content = ""
        start_time = time.time()
        
        try:
            # Plan the task first (Agentic behavior)
            client = provider.client
            model = provider.config.get("model")
            
            observer.trace_call("Chat", message)
            
            # Step 1: Generate a "Thinking" stream and "Content" stream
            completion = client.chat.completions.create(
                model=model,
                messages=[{"content": message, "role": "user"}],
                temperature=1,
                top_p=1,
                max_tokens=16384,
                extra_body={
                    "reasoning_budget": 16384,
                    "chat_template_kwargs": {"enable_thinking": True}
                } if "nemotron" in model.lower() and "nano" not in model.lower() else None,
                stream=True
            )
            
            for chunk in completion:
                if not chunk.choices: continue
                delta = chunk.choices[0].delta
                
                # Check for reasoning
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    reasoning_content += reasoning
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning})}\n\n"
                
                # Check for content
                if delta.content is not None:
                    full_response += delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': delta.content})}\n\n"
            
            latency = time.time() - start_time
            provider._record_metrics(latency)
            
            # Record in history at the end
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'response': {'text': full_response, 'reasoning': reasoning_content},
                'session_id': session_id,
                'type': 'chat',
                'model': model,
                'latency': latency
            }
            agent_data['history'].append(log_entry)
            observer.trace_response("Chat", log_entry)
            
            # Persist to DB
            logs_table.insert(log_entry)

            _insert_telemetry({
                'type': 'chat',
                'session_id': session_id,
                'model': model,
                'latency': latency,
                'input_preview': str(message)[:200],
                'output_preview': str(full_response)[:200]
            })
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            latency = time.time() - start_time
            provider.metrics["errors"] += 1
            observer.log("ERROR", f"Chat failed: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(generate_events(), mimetype='text/event-stream')


@app.route('/api/workflow/save', methods=['POST'])
def save_flow():
    """Save a workflow to the database"""
    data = request.json
    name = data.get('name', 'Untitled Flow')
    steps = data.get('steps', [])
    flow_id = data.get('flow_id') or secrets.token_hex(4)
    
    flows_table.upsert({
        'name': name,
        'steps': steps,
        'flow_id': flow_id,
        'config': data.get('config', {}),
        'updated_at': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'flow_id': flow_id})


@app.route('/api/workflow/delete', methods=['POST'])
def delete_flow():
    """Delete a workflow from the database"""
    data = request.json
    flow_id = data.get('flow_id')
    
    if flow_id:
        flows_table.remove(Query.flow_id_equals(flow_id))
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Flow ID required'}), 400

@app.route('/api/workflow/list', methods=['GET'])
def list_flows():
    """List all saved workflows"""
    return jsonify({'success': True, 'flows': flows_table.all()})


@app.route('/api/workflow/execute', methods=['POST'])
def execute_workflow():
    """Dynamically execute a workflow defined by the UI"""
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401
    
    data = request.json
    steps = data.get('steps', [])
    user_input = data.get('input', '')
    flow_id = data.get('flow_id') or secrets.token_hex(4)
    flow_name = data.get('name', 'Manual Workflow')
    
    agent_data = active_agents[session_id]
    provider = agent_data['provider']
    observer = agent_data['observer']
    
    # Generate run ID and insert initial run record
    run_id = secrets.token_hex(8)
    started_at = datetime.now().isoformat()
    
    try:
        runs_table.insert({
            'run_id': run_id,
            'workflow_id': flow_id,
            'flow_name': flow_name,
            'input_column': None,
            'status': 'running',
            'started_at': started_at,
            'completed_at': None,
            'results': [],
            'count': 0,
            'error': None
        })
    except Exception as e:
        print(f"[WORKFLOW] Failed to insert run record: {e}")
    
    # Execution Engine
    def run_dynamic_workflow():
        context = {"input": user_input, "history": {}}
        
        # Helper to execute a single step (used for both sequential and parallel)
        def run_step_logic(step_index, step):
            step_name = step.get('name', f'Step {step_index+1}')
            prompt_template = step.get('prompt', '')
            
            enable_llm = step.get('enable_llm')
            if enable_llm is None:
                enable_llm = True

            enable_tool = bool(step.get('enable_tool'))
            tool_outputs = _execute_step_tools(step=step, context=context, steps=steps, step_index=step_index, session_id=session_id, workflow_id=flow_id, run_id=run_id)
            tool_block = json.dumps(tool_outputs, ensure_ascii=False, indent=2) if enable_tool else ''

            # Construct final prompt from context
            final_prompt = prompt_template.replace("{{input}}", context["input"])
            
            # 1. Replace {{stepN}}
            for key, res in context["history"].items():
                final_prompt = final_prompt.replace(f"{{{{step{key[4:]}}}}}", res) if key.startswith('step') else final_prompt
                
            # 2. Replace {{Step Name}} by mapping names to previous results
            # Create a lookup map of Step Name -> Result
            name_map = {}
            for i, past_step in enumerate(steps):
                if i < step_index: # Only look at past steps
                   step_key = f"step{i+1}"
                   if step_key in context["history"]:
                       name_map[past_step['name']] = context["history"][step_key]
            
            for name, res in name_map.items():
                final_prompt = final_prompt.replace(f"{{{{{name}}}}}", res)

            if enable_tool:
                if "{{tool_results}}" in final_prompt:
                    final_prompt = final_prompt.replace("{{tool_results}}", tool_block)
                else:
                    final_prompt = final_prompt + "\n\nTool Results:\n" + tool_block
            
            # Determine configuration
            flow_config = data.get('config', {})
            exec_model = flow_config.get('model') or provider.config.get("model")
            
            # Use specific key or session key
            target_key = (flow_config.get('api_key') or "").strip()
            
            # CRITICAL SAFETY: If model is NVIDIA but key looks like Gemini (AIzaS...), 
            # or if target_key is empty, use the session's working key.
            if not target_key or ("nvidia" in exec_model.lower() and target_key.startswith("AIza")):
                target_key = provider.config.get('api_key', "").strip()
                source = "Session Key (Safety Fallback)" if flow_config.get('api_key') else "Session Key"
            else:
                source = "Manual Override"

            target_url = (provider.config.get('base_url', 'https://integrate.api.nvidia.com/v1')).strip()
            
            print(f"[WORKFLOW] Executing Step {step_index+1} ({step_name})")
            print(f"  - Model: {exec_model}")
            print(f"  - Key Source: {source}")
            if target_key:
                print(f"  - Key start: {target_key[:8]}...")
            
            if not enable_llm:
                latency = 0.0
                result_text = tool_block
                _insert_telemetry({
                    'type': 'workflow_step',
                    'session_id': session_id,
                    'workflow_id': flow_id,
                    'run_id': run_id,
                    'step_index': step_index,
                    'step_name': step_name,
                    'model': None,
                    'latency': latency,
                    'input_preview': str(final_prompt)[:200],
                    'output_preview': str(result_text)[:200]
                })
                return step_index, result_text

            step_start = time.time()
            observer.trace_call(f"WorkflowStep-{step_index+1}", final_prompt)

            # Create a fresh client for this thread to avoid any session/thread conflicts
            from openai import OpenAI
            step_client = OpenAI(api_key=target_key, base_url=target_url)

            # Only apply advanced reasoning params to models known to support them
            # Older 'nano' and standard 'instruct' models will return 401/400 if these are present
            extra_body = None
            
            # Explicitly exclude gpt-oss-20b/nano from reasoning
            is_reasoning_model = "nemotron" in exec_model.lower() and "nano" not in exec_model.lower()
            if "gpt-oss" in exec_model.lower():
                is_reasoning_model = False
            
            if is_reasoning_model:
                 extra_body = {
                    "reasoning_budget": 16383,
                    "chat_template_kwargs": {"enable_thinking": True}
                }
             # Also allow for Llama 3.1 405B which supports it
            if "llama-3.1-405b" in exec_model.lower():
                 extra_body = {
                    "reasoning_budget": 16383,
                    "chat_template_kwargs": {"enable_thinking": True}
                }

            completion = step_client.chat.completions.create(
                model=exec_model,
                messages=[{"content": final_prompt, "role": "user"}],
                extra_body=extra_body,
                stream=False
            )
            
            result_text = completion.choices[0].message.content
            latency = time.time() - step_start
            
            provider._record_metrics(latency)
            observer.trace_response(f"WorkflowStep-{step_index+1}", {
                "latency": latency,
                "text": result_text,
                "model": exec_model
            })

            _insert_telemetry({
                'type': 'workflow_step',
                'session_id': session_id,
                'workflow_id': flow_id,
                'run_id': run_id,
                'step_index': step_index,
                'step_name': step_name,
                'model': exec_model,
                'latency': latency,
                'input_preview': str(final_prompt)[:200],
                'output_preview': str(result_text)[:200]
            })
            
            return step_index, result_text

        try:
            from concurrent.futures import ThreadPoolExecutor
            
            # Group steps: a group is one or more steps that can run together
            # A step starts a new group unless it's marked 'parallel'
            groups = []
            for i, step in enumerate(steps):
                if not step.get('parallel') or not groups:
                    groups.append([(i, step)])
                else:
                    groups[-1].append((i, step))

            for group in groups:
                if len(group) == 1:
                    # Sequential path (keep original streaming feel if possible, but unified for now)
                    idx, step = group[0]
                    yield f"data: {json.dumps({'type': 'step_start', 'step_index': idx, 'name': step.get('name')})}\n\n"
                    
                    # For sequential, we can still stream
                    res_idx, res_content = run_step_logic(idx, step)
                    yield f"data: {json.dumps({'type': 'step_content', 'step_index': idx, 'content': res_content})}\n\n"
                    context["history"][f"step{idx+1}"] = res_content
                    yield f"data: {json.dumps({'type': 'step_done', 'step_index': idx})}\n\n"
                else:
                    # Parallel path
                    indices = [g[0] for g in group]
                    names = [g[1].get('name') for g in group]
                    
                    joined_names = ", ".join([n for n in names if n])
                    yield f"data: {json.dumps({'type': 'system', 'content': f'Starting Parallel Group: {joined_names}'})}\n\n"
                    
                    for idx, name in zip(indices, names):
                        yield f"data: {json.dumps({'type': 'step_start', 'step_index': idx, 'name': name})}\n\n"

                    with ThreadPoolExecutor(max_workers=len(group)) as executor:
                        futures = [executor.submit(run_step_logic, idx, s) for idx, s in group]
                        for future in futures:
                            res_idx, res_content = future.result()
                            context["history"][f"step{res_idx+1}"] = res_content
                            
                            # Find step name for the result
                            step_name = next((s['name'] for i, s in group if i == res_idx), f"Step {res_idx+1}")
                            
                            # Re-emit step_start to create a fresh bubble for the output in the UI
                            # This fixes the bug where parallel outputs were appended to the wrong bubble
                            yield f"data: {json.dumps({'type': 'step_start', 'step_index': res_idx, 'name': step_name})}\n\n"
                            yield f"data: {json.dumps({'type': 'step_content', 'step_index': res_idx, 'content': res_content})}\n\n"
                            yield f"data: {json.dumps({'type': 'step_done', 'step_index': res_idx})}\n\n"
            
            # Record successful workflow execution
            summary = "Workflow executed successfully.\n\nSteps Completed:\n"
            for k, v in context["history"].items():
                summary += f"- {k}: {v[:50]}...\n"
            
            # Update run record with completion
            try:
                runs_table.insert({
                    'run_id': run_id,
                    'workflow_id': flow_id,
                    'flow_name': flow_name,
                    'input_column': None,
                    'status': 'completed',
                    'started_at': started_at,
                    'completed_at': datetime.now().isoformat(),
                    'results': [{'step': k, 'output': v[:100]} for k, v in context["history"].items()],
                    'count': len(context["history"]),
                    'error': None
                })
            except Exception as e:
                print(f"[WORKFLOW] Failed to update run record: {e}")
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': f"Workflow Run: {user_input[:50]}...",
                'response': {'text': summary, 'reasoning': "Workflow Execution"},
                'session_id': session_id,
                'type': 'workflow',
                'full_context': context["history"], # Store full step details
                'workflow_id': flow_id,
                'run_id': run_id
            }
            agent_data['history'].append(log_entry)
            logs_table.insert(log_entry)

            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[WORKFLOW ERROR] {error_msg}")
            if "401" in error_msg:
                error_msg = f"LLM Authentication failed for model. Please verify your API Key and Model permissions. Detail: {error_msg[:100]}"
            
            # Update run record with error status
            try:
                runs_table.insert({
                    'run_id': run_id,
                    'workflow_id': flow_id,
                    'flow_name': flow_name,
                    'input_column': None,
                    'status': 'failed',
                    'started_at': started_at,
                    'completed_at': datetime.now().isoformat(),
                    'results': [],
                    'count': 0,
                    'error': error_msg
                })
            except Exception as ex:
                print(f"[WORKFLOW] Failed to update run record with error: {ex}")
            
            # Record failed execution
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': f"Workflow Run (Failed): {user_input[:50]}...",
                'response': {'text': f"Error: {error_msg}", 'reasoning': "Execution Failed"},
                'session_id': session_id,
                'type': 'workflow',
                'workflow_id': flow_id,
                'run_id': run_id
            }
            agent_data['history'].append(log_entry)
            logs_table.insert(log_entry)
            
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    return Response(run_dynamic_workflow(), mimetype='text/event-stream')

@app.route('/api/workflow/export', methods=['POST'])
def export_workflow_json():
    """Convert UI workflow to a downloadable JSON file"""
    data = request.json
    flow_id = data.get('flow_id', secrets.token_hex(4))
    name = data.get('name', 'MyWorkflow')
    
    # Create the JSON workflow data
    workflow_data = {
        "flow_id": flow_id,
        "name": name,
        "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "steps": data.get('steps', []),
        "config": data.get('config', {})
    }
    
    json_content = json.dumps(workflow_data, indent=2)
    
    return Response(
        json_content,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=workflow_{flow_id}.json"}
    )


@app.route('/api/workflow/csv/preview', methods=['POST'])
def workflow_csv_preview():
    """Upload a CSV and return columns + small preview for mapping"""
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'CSV file is required'}), 400

    f = request.files['file']
    raw = f.read()
    if not raw:
        return jsonify({'success': False, 'error': 'Empty CSV file'}), 400

    try:
        text = raw.decode('utf-8-sig')
    except Exception:
        text = raw.decode('utf-8', errors='ignore')

    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    preview = []
    for i, row in enumerate(reader):
        if i >= 10:
            break
        preview.append(row)

    upload_id = secrets.token_hex(8)
    safe_name = re.sub(r'[^a-zA-Z0-9._-]+', '_', f.filename or 'data.csv')
    file_path = os.path.join('uploads', f"{upload_id}_{safe_name}")
    with open(file_path, 'wb') as out:
        out.write(raw)

    return jsonify({
        'success': True,
        'upload_id': upload_id,
        'filename': safe_name,
        'columns': columns,
        'preview': preview
    })


@app.route('/api/workflow/batch_execute', methods=['POST'])
def workflow_batch_execute():
    """Execute a workflow once per CSV row using a selected input column."""
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    data = request.json or {}
    upload_id = (data.get('upload_id') or '').strip()
    input_column = (data.get('input_column') or '').strip()
    steps = data.get('steps', [])
    flow_id = (data.get('flow_id') or '').strip() or secrets.token_hex(4)
    flow_name = data.get('name', 'Batch Workflow')
    flow_config = data.get('config', {})

    if not upload_id:
        return jsonify({'success': False, 'error': 'upload_id is required'}), 400
    if not input_column:
        return jsonify({'success': False, 'error': 'input_column is required'}), 400
    if not isinstance(steps, list) or len(steps) == 0:
        return jsonify({'success': False, 'error': 'steps are required'}), 400

    upload_matches = [p for p in os.listdir('uploads') if p.startswith(upload_id + '_')]
    if not upload_matches:
        return jsonify({'success': False, 'error': 'Uploaded CSV not found'}), 404

    file_path = os.path.join('uploads', upload_matches[0])
    with open(file_path, 'rb') as f:
        raw = f.read()

    try:
        text = raw.decode('utf-8-sig')
    except Exception:
        text = raw.decode('utf-8', errors='ignore')

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or input_column not in reader.fieldnames:
        return jsonify({'success': False, 'error': f'Column not found: {input_column}'}), 400

    agent_data = active_agents[session_id]
    provider = agent_data['provider']
    observer = agent_data['observer']

    run_id = secrets.token_hex(8)
    results = []
    started_at = datetime.now().isoformat()

    for idx, row in enumerate(reader):
        user_input = (row.get(input_column) or '').strip()
        if user_input == '':
            continue

        context, _events = _execute_workflow_steps(
            steps=steps,
            user_input=user_input,
            data_config=flow_config,
            provider=provider,
            observer=observer,
            session_id=session_id,
            workflow_id=flow_id,
            run_id=run_id
        )

        final_key = f"step{len(steps)}"
        final_output = context.get('history', {}).get(final_key, '')

        results.append({
            'row_index': idx,
            'input': user_input,
            'final_output': final_output,
            'history': context.get('history', {})
        })

    record = {
        'timestamp': started_at,
        'workflow_id': flow_id,
        'workflow_name': flow_name,
        'run_id': run_id,
        'upload_id': upload_id,
        'input_column': input_column,
        'count': len(results),
        'results': results
    }
    runs_table.insert(record)

    logs_table.insert({
        'timestamp': datetime.now().isoformat(),
        'message': f"Batch Workflow Run ({flow_name}) rows={len(results)}",
        'response': {'text': f"Batch run complete. run_id={run_id}", 'reasoning': 'Batch Workflow'},
        'session_id': session_id,
        'type': 'workflow',
        'full_context': {'run_id': run_id, 'workflow_id': flow_id, 'count': len(results)}
    })

    return jsonify({
        'success': True,
        'workflow_id': flow_id,
        'run_id': run_id,
        'count': len(results)
    })


@app.route('/api/workflow/run/export_txt', methods=['GET'])
def workflow_run_export_txt():
    run_id = (request.args.get('run_id') or '').strip()
    if not run_id:
        return jsonify({'success': False, 'error': 'run_id is required'}), 400

    rec = runs_table.get(Query.run_id_equals(run_id))
    if not rec:
        return jsonify({'success': False, 'error': 'run not found'}), 404

    lines = []
    for r in rec.get('results', []):
        lines.append(r.get('final_output', ''))
    content = "\n".join(lines)

    bio = io.BytesIO(content.encode('utf-8'))
    bio.seek(0)
    fname = re.sub(r'[^a-zA-Z0-9._-]+', '_', rec.get('workflow_name', 'workflow'))
    return send_file(
        bio,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"{fname}_{run_id}.txt"
    )


@app.route('/api/workflow/runs', methods=['GET'])
def workflow_runs_list():
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    try:
        limit_raw = (request.args.get('limit') or '100').strip()
        limit = int(limit_raw)
    except Exception:
        limit = 100
    limit = max(1, min(limit, 500))

    workflow_id = (request.args.get('workflow_id') or '').strip()

    rows = runs_table.all()
    if workflow_id:
        rows = [r for r in rows if r.get('workflow_id') == workflow_id]

    rows.sort(key=lambda x: x.get('started_at', ''), reverse=True)
    out = []
    for r in rows[:limit]:
        out.append({
            'run_id': r.get('run_id'),
            'workflow_id': r.get('workflow_id'),
            'flow_name': r.get('flow_name'),
            'status': r.get('status'),
            'started_at': r.get('started_at'),
            'completed_at': r.get('completed_at'),
            'count': r.get('count'),
            'input_column': r.get('input_column'),
            'error': r.get('error')
        })

    return jsonify({'success': True, 'runs': out})


@app.route('/api/workflow/run/details', methods=['GET'])
def workflow_run_details():
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    run_id = (request.args.get('run_id') or '').strip()
    if not run_id:
        return jsonify({'success': False, 'error': 'run_id is required'}), 400

    rec = runs_table.get(Query.run_id_equals(run_id))
    if not rec:
        return jsonify({'success': False, 'error': 'run not found'}), 404

    return jsonify({'success': True, 'run': rec})


@app.route('/api/workflow/import_json', methods=['POST'])
def workflow_import_json():
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'JSON file is required'}), 400

    f = request.files['file']
    raw = f.read()
    if not raw:
        return jsonify({'success': False, 'error': 'Empty file'}), 400

    try:
        text = raw.decode('utf-8')
    except Exception:
        text = raw.decode('utf-8', errors='ignore')

    try:
        definition = json.loads(text)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to parse JSON: {str(e)}'}), 400

    if not definition:
        return jsonify({'success': False, 'error': 'Invalid JSON file'}), 400

    # Validate that it has required workflow structure
    if not isinstance(definition, dict) or 'steps' not in definition:
        return jsonify({'success': False, 'error': 'Invalid workflow format - missing steps'}), 400

    return jsonify({'success': True, 'workflow': definition})


@app.route('/api/memory/store', methods=['POST'])
def store_memory():
    """Store LLM output to memory"""
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    data = request.json
    output_text = data.get('output_text', '')
    input_text = data.get('input_text', '')
    workflow_id = data.get('workflow_id')
    step_index = data.get('step_index')
    step_name = data.get('step_name')

    if not output_text:
        return jsonify({'success': False, 'error': 'output_text is required'}), 400

    try:
        memory_db = get_memory_db()

        # Get provider and model info from session
        agent_data = active_agents[session_id]
        provider_type = agent_data['default_provider']
        provider = agent_data['providers'][provider_type]['provider_obj']
        model = provider.config.get('model', '')

        memory_id = memory_db.store(
            session_id=session_id,
            input_text=input_text,
            output_text=output_text,
            workflow_id=workflow_id,
            step_index=step_index,
            step_name=step_name,
            provider=provider_type,
            model=model,
            tags=data.get('tags')
        )

        return jsonify({
            'success': True,
            'memory_id': memory_id,
            'message': 'Memory stored successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory/list', methods=['GET'])
def list_memory():
    """List all memory entries with pagination"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400

    try:
        memory_db = get_memory_db()

        workflow_id = request.args.get('workflow_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        memories = memory_db.retrieve(
            session_id=session_id,
            workflow_id=workflow_id,
            limit=limit,
            offset=offset
        )

        # Get total count
        all_memories = memory_db.retrieve(session_id=session_id, workflow_id=workflow_id, limit=1000)

        return jsonify({
            'success': True,
            'memories': memories,
            'total': len(all_memories),
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    session_id = session.get('session_id')
    if not session_id or session_id not in active_agents:
        return jsonify({'success': False, 'error': 'No valid session'}), 401

    try:
        limit_raw = (request.args.get('limit') or '100').strip()
        limit = int(limit_raw)
    except Exception:
        limit = 100

    limit = max(1, min(limit, 500))
    scope = (request.args.get('scope') or 'session').strip().lower()

    rows = telemetry_table.all()
    if scope != 'all':
        rows = [r for r in rows if r.get('session_id') == session_id]

    rows.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify({
        'success': True,
        'rows': rows[:limit]
    })


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get metrics for current session"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in active_agents:
        return jsonify({
            'success': False,
            'error': 'No valid session'
        }), 401
    
    agent_data = active_agents[session_id]
    provider = agent_data['provider']
    observer = agent_data['observer']
    
    metrics = {
        'provider_metrics': provider.get_metrics(),
        'observability_metrics': observer.get_metrics(),
        'traces': observer.get_traces(),
        'conversation_count': len(agent_data['history']),
        'session_started': agent_data['created_at']
    }
    
    return jsonify({
        'success': True,
        'metrics': metrics
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history from persistent storage"""
    # Fetch all logs from DB, sorted by timestamp
    try:
        all_logs = logs_table.all()
        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify({
            'success': True,
            'history': all_logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/info', methods=['GET'])
def get_database_info():
    """Get database connection and table information"""
    try:
        from cassandra_db import db
        
        # Get cluster info
        cluster_info = {
            'contact_points': db.contact_points,
            'port': db.port,
            'keyspace': db.keyspace,
            'username': db.username,
            'status': 'connected'
        }
        
        # Get table information
        tables_info = {}
        
        # Flows table
        flows = flows_table.all()
        tables_info['flows'] = {
            'count': len(flows),
            'description': 'Workflow definitions and configurations',
            'columns': ['flow_id', 'name', 'steps', 'config', 'updated_at']
        }
        
        # Logs table
        logs = logs_table.all()
        tables_info['logs'] = {
            'count': len(logs),
            'description': 'Conversation and execution logs',
            'columns': ['id', 'timestamp', 'session_id', 'type', 'message', 'response', 'full_context']
        }
        
        # Workflow runs table
        runs = runs_table.all()
        tables_info['workflow_runs'] = {
            'count': len(runs),
            'description': 'Batch workflow execution records',
            'columns': ['run_id', 'workflow_id', 'flow_name', 'status', 'started_at', 'completed_at']
        }
        
        # Telemetry table
        telemetry = telemetry_table.all()
        tables_info['telemetry'] = {
            'count': len(telemetry),
            'description': 'Performance metrics and events',
            'columns': ['id', 'timestamp', 'session_id', 'type', 'workflow_id', 'latency']
        }
        
        total_records = sum(table['count'] for table in tables_info.values())
        
        return jsonify({
            'success': True,
            'cluster': cluster_info,
            'tables': tables_info,
            'total_records': total_records,
            'database_type': 'Apache Cassandra'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """Get data from a specific table"""
    try:
        valid_tables = ['flows', 'logs', 'workflow_runs', 'telemetry']
        if table_name not in valid_tables:
            return jsonify({'success': False, 'error': 'Invalid table name'}), 400
        
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if table_name == 'flows':
            data = flows_table.all()
        elif table_name == 'logs':
            data = logs_table.all()
        elif table_name == 'workflow_runs':
            data = runs_table.all()
        elif table_name == 'telemetry':
            data = telemetry_table.all()
        
        # Limit results
        limited_data = data[:limit]
        
        return jsonify({
            'success': True,
            'table': table_name,
            'data': limited_data,
            'total_count': len(data),
            'showing': len(limited_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/database')
def database_page():
    """Database management page"""
    return render_template('database.html')


@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear session and remove agent"""
    session_id = session.get('session_id')
    
    if session_id and session_id in active_agents:
        # Export data before clearing
        agent_data = active_agents[session_id]
        observer = agent_data['observer']
        observer.export_observability_data(f'logs/session_{session_id}_export.json')
        
        # Remove from active agents
        del active_agents[session_id]
    
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'Session cleared'
    })


if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Run app
    print("\n" + "="*70)
    print("🚀 AGENT WEB UI STARTING")
    print("="*70)
    print("\nAccess the UI at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000)
