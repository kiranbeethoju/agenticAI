"""
Flask Web Application for Agent System
Requires credentials before allowing any agent operations
"""

from flask import Flask, render_template, request, jsonify, session, Response
from flask_cors import CORS
import os
import yaml
import json
import time
from datetime import datetime
import secrets
from tinydb import TinyDB, Query

# Create necessary directories
os.makedirs('workflows', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Initialize Database
db = TinyDB('db.json')
flows_table = db.table('flows')
logs_table = db.table('logs')

# Import agent components
from llm_providers import LLMProviderFactory
from observability import Observer
from agent import SimplifiedAgent

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure session key
CORS(app)

# Global variables
active_agents = {}


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
    
    Workflow = Query()
    flows_table.upsert({
        'name': name,
        'steps': steps,
        'flow_id': flow_id,
        'config': data.get('config', {}),
        'updated_at': datetime.now().isoformat()
    }, Workflow.flow_id == flow_id)
    
    return jsonify({'success': True, 'flow_id': flow_id})


@app.route('/api/workflow/delete', methods=['POST'])
def delete_flow():
    """Delete a workflow from the database"""
    data = request.json
    flow_id = data.get('flow_id')
    
    if flow_id:
        Workflow = Query()
        flows_table.remove(Workflow.flow_id == flow_id)
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
    
    agent_data = active_agents[session_id]
    provider = agent_data['provider']
    observer = agent_data['observer']
    
    # Execution Engine
    def run_dynamic_workflow():
        context = {"input": user_input, "history": {}}
        
        # Helper to execute a single step (used for both sequential and parallel)
        def run_step_logic(step_index, step):
            step_name = step.get('name', f'Step {step_index+1}')
            prompt_template = step.get('prompt', '')
            
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
                    
                    yield f"data: {json.dumps({'type': 'system', 'content': f'Starting Parallel Group: {', '.join(names)}'})}\n\n"
                    
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
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': f"Workflow Run: {user_input[:50]}...",
                'response': {'text': summary, 'reasoning': "Workflow Execution"},
                'session_id': session_id,
                'type': 'workflow',
                'full_context': context["history"] # Store full step details
            }
            agent_data['history'].append(log_entry)
            logs_table.insert(log_entry)

            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[WORKFLOW ERROR] {error_msg}")
            if "401" in error_msg:
                error_msg = f"LLM Authentication failed for model. Please verify your API Key and Model permissions. Detail: {error_msg[:100]}"
            
            # Record failed execution
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': f"Workflow Run (Failed): {user_input[:50]}...",
                'response': {'text': f"Error: {error_msg}", 'reasoning': "Execution Failed"},
                'session_id': session_id,
                'type': 'workflow'
            }
            agent_data['history'].append(log_entry)
            logs_table.insert(log_entry)
            
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    return Response(run_dynamic_workflow(), mimetype='text/event-stream')

@app.route('/api/workflow/export', methods=['POST'])
def export_workflow_script():
    """Convert UI workflow to a downloadable Python script"""
    data = request.json
    flow_id = data.get('flow_id', secrets.token_hex(4))
    name = data.get('name', 'MyWorkflow')
    steps = data.get('steps', [])
    config = data.get('config', {})
    
    script_content = f"""# AGENTIC WORKFLOW SCRIPT
# FlowID: {flow_id}
# Name: {name}
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import json
import requests

# Workflow Definition
WORKFLOW_DEFINITION = {json.dumps(data, indent=4)}

def execute_step(step, input_data, api_key, base_url):
    print(f"\\n>>> Executing Step: {{step['name']}}")
    prompt = step['prompt'].replace('{{{{input}}}}', input_data)
    # Basic execution logic for the exported script
    # In a real scenario, this would call the LLM API directly
    print(f"Prompt: {{prompt[:50]}}...")
    return "Sample output for " + step['name']

if __name__ == "__main__":
    print(f"--- Running Workflow: {name} ---")
    user_input = input("Enter input: ")
    history = {{}}
    
    for i, step in enumerate(WORKFLOW_DEFINITION['steps']):
        res = execute_step(step, user_input, "YOUR_API_KEY", "BASE_URL")
        history[f"step{{i+1}}"] = res
        
    print("\\n--- Workflow Complete ---")
"""
    
    return Response(
        script_content,
        mimetype="text/x-python",
        headers={"Content-disposition": f"attachment; filename=flow_{flow_id}.py"}
    )


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
