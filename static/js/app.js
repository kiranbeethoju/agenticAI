document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Check for existing session on page load
    checkExistingSession();

    // Elements
    const authOverlay = document.getElementById('auth-overlay');
    const appContainer = document.getElementById('app-container');
    const validateBtn = document.getElementById('validate-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const thinkingIndicator = document.getElementById('thinking-indicator');
    const thinkingContent = document.getElementById('thinking-content');
    const authError = document.getElementById('auth-error');
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const providerFields = document.querySelectorAll('.provider-fields');

    let currentProvider = 'nvidia';
    let isProcessing = false;

    // --- Authentication & Initialization ---

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            providerFields.forEach(f => f.classList.remove('active'));

            btn.classList.add('active');
            currentProvider = btn.dataset.provider;
            document.getElementById(`${currentProvider}-fields`).classList.add('active');
        });
    });

    // Test Connection Button
    const testConnectionBtn = document.getElementById('test-connection-btn');
    if (testConnectionBtn) {
        testConnectionBtn.addEventListener('click', async () => {
            const apiKey = document.getElementById(`${currentProvider}-api-key`)?.value;
            if (!apiKey) {
                showError('API Key is required');
                return;
            }

            testConnectionBtn.disabled = true;
            testConnectionBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Testing...';

            const payload = {
                provider: currentProvider,
                api_key: apiKey
            };

            // Add provider-specific fields
            if (currentProvider === 'nvidia') {
                payload.base_url = document.getElementById('nvidia-base-url')?.value || 'https://integrate.api.nvidia.com/v1';
            } else if (currentProvider === 'azure_openai') {
                payload.endpoint = document.getElementById('azure-endpoint')?.value;
                payload.deployment_name = document.getElementById('azure-deployment-name')?.value;
                payload.api_version = document.getElementById('azure-api-version')?.value || '2024-02-01';
            } else if (currentProvider === 'gemini') {
                payload.model = 'gemini-2.0-flash-exp';
            }

            try {
                const response = await fetch('/api/provider/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    appendLog('system', `✓ Connection successful! Response: "${data.response?.substring(0, 100) || 'OK'}..."`);
                } else {
                    showError(data.error || 'Connection failed');
                }
            } catch (err) {
                showError('Network error occurred');
            } finally {
                testConnectionBtn.disabled = false;
                testConnectionBtn.innerHTML = '<i data-lucide="wifi"></i> Test Connection';
                lucide.createIcons();
            }
        });
    }

    // Validate Credentials
    validateBtn.addEventListener('click', async () => {
        const apiKey = document.getElementById(`${currentProvider}-api-key`).value;
        const baseUrl = currentProvider === 'nvidia' ? document.getElementById('nvidia-base-url').value : null;

        if (!apiKey) {
            showError('API Key is required');
            return;
        }

        // For Azure, validate required fields
        if (currentProvider === 'azure_openai') {
            const endpoint = document.getElementById('azure-endpoint')?.value;
            const deploymentName = document.getElementById('azure-deployment-name')?.value;
            if (!endpoint) {
                showError('Azure Endpoint is required');
                return;
            }
            if (!deploymentName) {
                showError('Deployment Name is required');
                return;
            }
        }

        validateBtn.disabled = true;
        validateBtn.innerHTML = '<span>Validating...</span>';
        authError.textContent = '';

        try {
            const payload = {
                provider: currentProvider,
                api_key: apiKey,
                base_url: baseUrl
            };

            // Add Azure-specific fields
            if (currentProvider === 'azure_openai') {
                payload.endpoint = document.getElementById('azure-endpoint')?.value;
                payload.deployment_name = document.getElementById('azure-deployment-name')?.value;
                payload.api_version = document.getElementById('azure-api-version')?.value || '2024-02-01';
            }

            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                // Store session config for pre-filling builder
                window.sessionConfig = {
                    model: data.model,
                    api_key: data.api_key
                };

                // Update provider names in various panels safely
                const elements = ['active-provider-name', 'tele-provider', 'm-provider'];
                elements.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = currentProvider.toUpperCase();
                });

                authOverlay.classList.add('hidden');
                appContainer.classList.remove('hidden');

                // Pre-fill builder configuration with placeholders
                if (window.sessionConfig) {
                    const modelInput = document.getElementById('flow-model');
                    const keyInput = document.getElementById('flow-api-key');
                    if (modelInput) modelInput.placeholder = window.sessionConfig.model || "Model name...";
                    if (keyInput) keyInput.placeholder = "Using session API key...";
                }

                refreshMetrics();
            } else {
                showError(data.error || 'Validation failed');
            }
        } catch (err) {
            showError('Network error occurred');
        } finally {
            validateBtn.disabled = false;
            validateBtn.innerHTML = '<span>Initialize Agent</span> <i data-lucide="arrow-right"></i>';
            lucide.createIcons();
        }
    });

    function showError(msg) {
        authError.textContent = msg;
        setTimeout(() => { authError.textContent = ''; }, 5000);
    }

    // Check for existing session
    async function checkExistingSession() {
        try {
            const response = await fetch('/api/session-check');
            const data = await response.json();
            
            if (data.has_session) {
                // Session exists, hide auth overlay
                authOverlay.classList.add('hidden');
                appContainer.classList.remove('hidden');
                
                // Update UI with session info
                if (data.provider) {
                    const providerElements = document.querySelectorAll('.current-provider');
                    providerElements.forEach(el => el.textContent = data.provider.toUpperCase());
                }
                
                refreshMetrics();
            }
        } catch (error) {
            console.log('Session check failed, showing login');
        }
    }

    // --- Chat Functionality ---

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = (messageInput.scrollHeight) + 'px';
    });

    let currentMode = 'general';
    let currentFlowId = null;
    let workflowSteps = [
        { id: 1, name: 'Analysis', prompt: 'Analyze this: {{input}}', enable_llm: true, enable_tool: false, tools: [] },
        { id: 2, name: 'Detailing', prompt: 'Expand on {{step1}}', enable_llm: true, enable_tool: false, tools: [] }
    ];

    // Mode Switching
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = mode;

            const mainGrid = document.getElementById('main-grid');
            const library = document.getElementById('flow-library');
            const builder = document.getElementById('workflow-builder');

            if (mode === 'workflow') {
                mainGrid.classList.add('workflow-mode');
                library.classList.remove('hidden');
                builder.classList.remove('hidden');
                loadSavedFlows();
                renderWorkflowSteps();
            } else {
                mainGrid.classList.remove('workflow-mode');
                library.classList.add('hidden');
                builder.classList.add('hidden');
            }
        });
    });

    // Workflow logic
    window.updateStepProvider = (stepId, providerType) => {
        const step = workflowSteps.find(s => s.id === stepId);
        if (!step) return;

        if (!providerType) {
            delete step.provider_config;
        } else {
            step.provider_config = step.provider_config || {};
            step.provider_config.provider = providerType;
        }
        renderWorkflowSteps();
    };

    window.updateStepProviderField = (stepId, field, value) => {
        const step = workflowSteps.find(s => s.id === stepId);
        if (!step) return;

        if (!step.provider_config) step.provider_config = {};
        step.provider_config[field] = value;
    };

    window.testStepProvider = async (stepId) => {
        const step = workflowSteps.find(s => s.id === stepId);
        if (!step || !step.provider_config) return;

        const providerConfig = step.provider_config;
        const response = await fetch('/api/provider/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(providerConfig)
        });
        const data = await response.json();

        if (data.success) {
            appendLog('system', `✓ Connection successful for step "${step.name}": ${data.response?.substring(0, 100) || 'OK'}...`);
        } else {
            appendLog('error', `✗ Connection failed for step "${step.name}": ${data.error || 'Unknown error'}`);
        }
    };

    function renderWorkflowSteps() {
        const container = document.getElementById('steps-container');

        container.innerHTML = workflowSteps.map((step, idx) => {
            // Calculate available variables for this step
            // Always available: {{input}}
            // Previous steps: {{stepN}} or {{StepName}}
            // Note: If parallel to previous, technically shouldn't access previous, but we show all for simplicity

            const vars = ['{{input}}', '{{memory}}'];
            for (let i = 0; i < idx; i++) {
                const pStep = workflowSteps[i];
                // Prioritize Name over Step N to avoid duplicates
                if (pStep.name && pStep.name.trim() !== "" && pStep.name !== `Step ${i + 1}`) {
                    vars.push(`{{${pStep.name}}}`);
                } else {
                    vars.push(`{{step${i + 1}}}`);
                }
            }

            if (step.enable_tool) {
                vars.push('{{tool_input}}');
                vars.push('{{tool_results}}');
            }

            const enableLLM = (step.enable_llm === undefined || step.enable_llm === null) ? true : !!step.enable_llm;
            const enableTool = !!step.enable_tool;
            const tools = Array.isArray(step.tools) ? step.tools : [];
            const tool0 = tools[0] || { type: 'google_search', query_template: '{{input}}', max_results: 5 };
            const toolQuery = tool0.query_template || tool0.query || '{{input}}';
            const toolMax = (tool0.max_results === undefined || tool0.max_results === null) ? 5 : tool0.max_results;

            // Provider selection
            const providerConfig = step.provider_config || {};
            const selectedProvider = providerConfig.provider || '';

            return `
            <div class="step-card ${step.parallel ? 'parallel-step' : ''}" id="step-card-${step.id}">
                <div class="step-card-header">
                    <div class="step-title">
                        <span class="step-badge">${idx + 1}</span>
                        <h4>${step.name}</h4>
                    </div>
                    <div class="step-ctrls">
                        <button class="icon-btn small maximize-btn" onclick="window.toggleMaximizeStep(${step.id})" title="Maximize">
                             <i data-lucide="maximize-2"></i>
                        </button>
                        <button class="close-modal" onclick="window.toggleMaximizeStep(${step.id})" title="Close">
                             <i data-lucide="x"></i>
                        </button>
                        ${idx > 0 ? `
                        <label class="parallel-toggle" title="Run in parallel with ${workflowSteps[idx - 1].name}">
                            <input type="checkbox" ${step.parallel ? 'checked' : ''} onchange="window.toggleParallel(${step.id})">
                            <i data-lucide="zap"></i> ${step.parallel ? `With Step ${idx}` : 'Parallel'}
                        </label>
                        ` : ''}
                        <div class="step-reorder">
                            <button class="reorder-btn" onclick="window.moveStep(${idx}, -1)"><i data-lucide="chevron-up"></i></button>
                            <button class="reorder-btn" onclick="window.moveStep(${idx}, 1)"><i data-lucide="chevron-down"></i></button>
                            <button class="icon-btn danger small" onclick="window.removeWorkflowStep(${step.id})"><i data-lucide="trash-2"></i></button>
                        </div>
                    </div>
                </div>
                <div class="step-card-body">
                    <div class="step-provider-config">
                        <label>Provider:</label>
                        <select onchange="window.updateStepProvider(${step.id}, this.value)">
                            <option value="">Use Session Default</option>
                            <option value="nvidia" ${selectedProvider === 'nvidia' ? 'selected' : ''}>NVIDIA API</option>
                            <option value="azure_openai" ${selectedProvider === 'azure_openai' ? 'selected' : ''}>Azure OpenAI</option>
                            <option value="gemini" ${selectedProvider === 'gemini' ? 'selected' : ''}>Google Gemini</option>
                        </select>
                        ${selectedProvider ? `<button type="button" class="icon-btn small" onclick="window.testStepProvider(${step.id})"><i data-lucide="wifi"></i> Test</button>` : ''}

                        <div id="provider-fields-${step.id}" class="provider-fields-inline">
                            ${selectedProvider === 'azure_openai' ? `
                                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:8px;">
                                    <input class="glass-input" type="text" value="${providerConfig.endpoint || ''}" placeholder="Azure Endpoint" onchange="window.updateStepProviderField(${step.id}, 'endpoint', this.value)" />
                                    <input class="glass-input" type="text" value="${providerConfig.deployment_name || ''}" placeholder="Deployment Name" onchange="window.updateStepProviderField(${step.id}, 'deployment_name', this.value)" />
                                </div>
                                <input class="glass-input" type="text" value="${providerConfig.model || ''}" placeholder="Model (optional)" onchange="window.updateStepProviderField(${step.id}, 'model', this.value)" />
                            ` : ''}
                            ${selectedProvider && selectedProvider !== 'azure_openai' ? `
                                <input class="glass-input" type="text" value="${providerConfig.model || ''}" placeholder="Model (optional)" onchange="window.updateStepProviderField(${step.id}, 'model', this.value)" />
                            ` : ''}
                        </div>
                    </div>

                    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:10px;">
                        <label class="step-toggle ${enableLLM ? 'active' : ''}" title="Enable/Disable LLM call for this step">
                            <input type="checkbox" ${enableLLM ? 'checked' : ''} onchange="window.toggleEnableLLM(${step.id}, this.checked)">
                            <i data-lucide="cpu"></i> LLM
                        </label>
                        <label class="step-toggle ${enableTool ? 'active' : ''}" title="Enable/Disable tool execution for this step">
                            <input type="checkbox" ${enableTool ? 'checked' : ''} onchange="window.toggleEnableTool(${step.id}, this.checked)">
                            <i data-lucide="search"></i> Tool
                        </label>
                    </div>

                    ${enableTool ? `
                        <div style="border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 10px; margin-bottom: 10px;">
                            <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom: 8px;">
                                <div style="opacity:0.9;">Tool: <strong>GoogleSearch</strong></div>
                                <div style="opacity:0.6; font-size: 12px;">(via DuckDuckGo)</div>
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr 110px; gap:10px;">
                                <input class="glass-input" type="text" value="${toolQuery.replace(/"/g, '&quot;')}" placeholder="Query template (e.g. {{input}})" onchange="window.updateToolQuery(${step.id}, this.value)" />
                                <input class="glass-input" type="number" min="1" max="10" value="${toolMax}" onchange="window.updateToolMaxResults(${step.id}, this.value)" />
                            </div>
                            <div style="opacity:0.6; font-size: 12px; margin-top: 6px;">Tip: Use <code>{{input}}</code>, <code>{{step1}}</code>, or step name variables in the query.</div>
                        </div>
                    ` : ''}

                    <div class="prompt-label">Prompt Template:</div>
                    <textarea id="prompt-${step.id}" onchange="window.updateStepPrompt(${step.id}, this.value)" placeholder="e.g. Analyze this: {{input}}">${step.prompt}</textarea>
                    
                    <div class="variable-chips">
                        <span class="chip-label">Insert:</span>
                        ${vars.map(v => `<button class="var-chip" onclick="window.insertVar(${step.id}, '${v}')">${v}</button>`).join('')}
                    </div>
                </div>
            </div>
        `}).join('');
        lucide.createIcons();
    }

    window.toggleMaximizeStep = (id) => {
        console.log("Maximizing step:", id);
        const card = document.getElementById(`step-card-${id}`);
        if (card) {
            card.classList.toggle('maximized');
            // If maximizing, also focus the textarea
            if (card.classList.contains('maximized')) {
                const textarea = card.querySelector('textarea');
                if (textarea) textarea.focus();
            }
        }
        lucide.createIcons();
    };

    window.insertVar = (stepId, variable) => {
        const textarea = document.getElementById(`prompt-${stepId}`);
        if (textarea) {
            // Insert at cursor or end
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const text = textarea.value;
            const newText = text.substring(0, start) + variable + text.substring(end);

            textarea.value = newText;
            textarea.focus();
            // Move cursor after insertion
            textarea.selectionStart = textarea.selectionEnd = start + variable.length;

            // Trigger update
            window.updateStepPrompt(stepId, newText);
        }
    };

    window.toggleParallel = (id) => {
        const stepIdx = workflowSteps.findIndex(s => s.id === id);
        if (stepIdx === 0) {
            appendLog('system', "The first step cannot be parallel as it has no predecessor to run with.");
            return;
        }

        const step = workflowSteps[stepIdx];
        if (step) {
            if (!step.parallel) {
                const ok = confirm(`Group "${step.name}" to run concurrently with "${workflowSteps[stepIdx - 1].name}"?`);
                if (!ok) return;
                step.parallel = true;
                appendLog('system', `Step "${step.name}" now grouped with "${workflowSteps[stepIdx - 1].name}" for parallel execution.`);
            } else {
                step.parallel = false;
                appendLog('system', `Step "${step.name}" returned to sequential execution.`);
            }

            renderWorkflowSteps();
        }
    };

    window.moveStep = (idx, dir) => {
        const newIdx = idx + dir;
        if (newIdx < 0 || newIdx >= workflowSteps.length) return;
        const temp = workflowSteps[idx];
        workflowSteps[idx] = workflowSteps[newIdx];
        workflowSteps[newIdx] = temp;
        renderWorkflowSteps();
    };

    window.updateStepPrompt = (id, val) => {
        const step = workflowSteps.find(s => s.id === id);
        if (step) step.prompt = val;
    };

    window.toggleEnableLLM = (id, enabled) => {
        const step = workflowSteps.find(s => s.id === id);
        if (!step) return;
        step.enable_llm = !!enabled;
        renderWorkflowSteps();
    };

    window.toggleEnableTool = (id, enabled) => {
        const step = workflowSteps.find(s => s.id === id);
        if (!step) return;
        step.enable_tool = !!enabled;
        if (step.enable_tool) {
            if (!Array.isArray(step.tools) || step.tools.length === 0) {
                step.tools = [{ type: 'google_search', query_template: '{{input}}', max_results: 5 }];
            } else {
                step.tools = step.tools.map((t, i) => i === 0 ? ({
                    type: (t.type || 'google_search'),
                    query_template: t.query_template || t.query || '{{input}}',
                    max_results: (t.max_results === undefined || t.max_results === null) ? 5 : t.max_results
                }) : t);
            }
        }
        renderWorkflowSteps();
    };

    window.updateToolQuery = (id, val) => {
        const step = workflowSteps.find(s => s.id === id);
        if (!step) return;
        if (!Array.isArray(step.tools) || step.tools.length === 0) {
            step.tools = [{ type: 'google_search', query_template: '{{input}}', max_results: 5 }];
        }
        step.tools[0].type = step.tools[0].type || 'google_search';
        step.tools[0].query_template = val;
    };

    window.updateToolMaxResults = (id, val) => {
        const step = workflowSteps.find(s => s.id === id);
        if (!step) return;
        if (!Array.isArray(step.tools) || step.tools.length === 0) {
            step.tools = [{ type: 'google_search', query_template: '{{input}}', max_results: 5 }];
        }
        const n = parseInt(val, 10);
        step.tools[0].max_results = isNaN(n) ? 5 : Math.max(1, Math.min(n, 10));
    };

    window.removeWorkflowStep = (id) => {
        workflowSteps = workflowSteps.filter(s => s.id !== id);
        renderWorkflowSteps();
    };

    document.getElementById('add-step-btn').addEventListener('click', () => {
        workflowSteps.push({
            id: Date.now(),
            name: `Step ${workflowSteps.length + 1}`,
            prompt: 'Process output from previous step...',
            enable_llm: true,
            enable_tool: false,
            tools: []
        });
        renderWorkflowSteps();
    });

    // Save & Load Logic
    const saveBtn = document.getElementById('save-flow-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const name = document.getElementById('flow-name').value;
            const model = document.getElementById('flow-model').value;
            const apiKey = document.getElementById('flow-api-key').value;

            const res = await fetch('/api/workflow/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    steps: workflowSteps,
                    flow_id: currentFlowId,
                    config: { model, api_key: apiKey }
                })
            });
            const data = await res.json();
            if (data.success) {
                currentFlowId = data.flow_id;
                saveBtn.innerHTML = '<i data-lucide="check"></i> Saved';
                setTimeout(() => {
                    saveBtn.innerHTML = '<i data-lucide="save"></i> Save';
                    lucide.createIcons();
                }, 2000);
                loadSavedFlows();
            }
        });
    }

    window.deleteFlow = async (id) => {
        if (!confirm('Are you sure you want to delete this workflow?')) return;

        await fetch('/api/workflow/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ flow_id: id })
        });

        if (currentFlowId === id) {
            currentFlowId = null;
            document.getElementById('flow-name').value = 'New Workflow';
            workflowSteps = [];
            renderWorkflowSteps();
        }
        loadSavedFlows();
    };

    async function loadSavedFlows() {
        const list = document.getElementById('flows-list');
        if (!list) return;
        const res = await fetch('/api/workflow/list');
        const data = await res.json();
        list.innerHTML = data.flows.map(f => `
            <div class="flow-item ${f.flow_id === currentFlowId ? 'active' : ''}">
                <span onclick="window.selectFlow('${f.flow_id}')" style="flex:1;">${f.name}</span>
                <button class="icon-btn danger small" onclick="window.deleteFlow('${f.flow_id}')">
                    <i data-lucide="trash-2" style="width:14px; height:14px;"></i>
                </button>
            </div>
        `).join('') || '<p style="padding:10px; opacity:0.5;">No flows saved.</p>';
        lucide.createIcons();
    }

    window.selectFlow = async (id) => {
        const res = await fetch('/api/workflow/list');
        const data = await res.json();
        const flow = data.flows.find(f => f.flow_id === id);
        if (flow) {
            currentFlowId = flow.flow_id;
            workflowSteps = JSON.parse(JSON.stringify(flow.steps));
            document.getElementById('flow-name').value = flow.name;

            const config = flow.config || {};
            const modelInput = document.getElementById('flow-model');
            const keyInput = document.getElementById('flow-api-key');

            // Clear overrides and use placeholders for session defaults
            modelInput.value = config.model || '';
            keyInput.value = config.api_key || '';

            if (window.sessionConfig) {
                if (!modelInput.value) modelInput.placeholder = `Session: ${window.sessionConfig.model}`;
                if (!keyInput.value) keyInput.placeholder = "Using session API key...";
            }

            renderWorkflowSteps();
            loadSavedFlows();
        }
    };

    const runFlowBtn = document.getElementById('run-flow-btn');
    if (runFlowBtn) {
        runFlowBtn.addEventListener('click', () => {
            const text = messageInput.value.trim() || "Run workflow";
            handleWorkflowExecution(text);
        });
    }

    async function handleWorkflowExecution(text) {
        if (isProcessing) return;

        if (currentMode !== 'workflow') {
            appendLog('system', "Switching to Workflow mode to execute...");
            setMode('workflow');
        }

        appendLog('user', text);
        isProcessing = true;
        setLoadingState(true);
        setWorkflowStep('plan');

        const payload = {
            input: text,
            steps: workflowSteps,
            message: text,
            config: {
                model: (document.getElementById('flow-model')?.value || '').trim(),
                api_key: (document.getElementById('flow-api-key')?.value || '').trim()
            }
        };

        try {
            setWorkflowStep('exec');
            const response = await fetch('/api/workflow/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let currentAssistantBubble = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.replace('data: ', '');
                        if (dataStr === '[DONE]') {
                            setWorkflowStep('comp');
                            continue;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'step_start') {
                                appendLog('system', `Starting: ${data.name}`);
                                currentAssistantBubble = createLogBubble('assistant');
                            } else if (data.type === 'step_content') {
                                currentAssistantBubble.textContent += data.content;
                                scrollChat();
                            } else if (data.type === 'reasoning') {
                                showThinkingStreaming(data.content);
                            } else if (data.type === 'content') {
                                if (!currentAssistantBubble) currentAssistantBubble = createLogBubble('assistant');
                                currentAssistantBubble.textContent += data.content;
                                scrollChat();
                            } else if (data.type === 'error') {
                                appendLog('error', data.content);
                            } else if (data.type === 'system') {
                                appendLog('system', data.content);
                            }
                        } catch (e) { }
                    }
                }
            }
            refreshMetrics();
        } catch (err) {
            appendLog('error', 'Execution failed: ' + err.message);
            setWorkflowStep(null);
        } finally {
            isProcessing = false;
            setLoadingState(false);
            setTimeout(() => setWorkflowStep(null), 5000);
        }
    }

    // Submit Task
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (!text || isProcessing) return;

        if (currentMode === 'workflow') {
            messageInput.value = '';
            messageInput.style.height = 'auto';
            handleWorkflowExecution(text);
            return;
        }

        appendLog('user', text);
        messageInput.value = '';
        messageInput.style.height = 'auto';
        isProcessing = true;
        setLoadingState(true);
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let currentAssistantBubble = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.replace('data: ', '');
                        if (dataStr === '[DONE]') continue;
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'reasoning') {
                                showThinkingStreaming(data.content);
                            } else if (data.type === 'content') {
                                if (!currentAssistantBubble) currentAssistantBubble = createLogBubble('assistant');
                                currentAssistantBubble.textContent += data.content;
                                scrollChat();
                            } else if (data.type === 'error') {
                                appendLog('error', data.content);
                            }
                        } catch (e) { }
                    }
                }
            }
        } catch (err) {
            appendLog('error', 'Failure: ' + err.message);
        } finally {
            isProcessing = false;
            setLoadingState(false);
            thinkingIndicator.classList.add('hidden');
        }
    });

    // Configuration Toggle
    window.toggleFlowConfig = () => {
        const panel = document.getElementById('flow-config-panel');
        panel.classList.toggle('hidden');
    };

    document.getElementById('export-flow-btn').addEventListener('click', async () => {
        const name = document.getElementById('flow-name').value;
        const res = await fetch('/api/workflow/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                steps: workflowSteps,
                config: {
                    model: document.getElementById('flow-model').value,
                    api_key: document.getElementById('flow-api-key').value
                }
            })
        });

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `flow_${name.toLowerCase().replace(/\s+/g, '_')}.py`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    });

    // CSV Batch Run
    let currentCsvUploadId = null;
    let lastBatchRunId = null;

    const csvFileInput = document.getElementById('csv-file-input');
    const csvSelectBtn = document.getElementById('csv-select-btn');
    const csvInputColumn = document.getElementById('csv-input-column');
    const runCsvBtn = document.getElementById('run-csv-btn');
    const downloadRunTxtBtn = document.getElementById('download-run-txt-btn');

    if (csvSelectBtn && csvFileInput) {
        csvSelectBtn.addEventListener('click', () => csvFileInput.click());
    }

    if (csvFileInput) {
        csvFileInput.addEventListener('change', async () => {
            const file = csvFileInput.files && csvFileInput.files[0];
            if (!file) return;

            try {
                const fd = new FormData();
                fd.append('file', file);

                const res = await fetch('/api/workflow/csv/preview', {
                    method: 'POST',
                    body: fd
                });
                const data = await res.json();
                if (!data.success) {
                    appendLog('error', data.error || 'CSV preview failed');
                    return;
                }

                currentCsvUploadId = data.upload_id;
                lastBatchRunId = null;
                if (downloadRunTxtBtn) downloadRunTxtBtn.classList.add('hidden');

                if (csvInputColumn) {
                    csvInputColumn.innerHTML = (data.columns || []).map(c => `<option value="${c}">${c}</option>`).join('');
                    csvInputColumn.classList.remove('hidden');
                }
                if (runCsvBtn) runCsvBtn.classList.remove('hidden');

                appendLog('system', `CSV uploaded: ${data.filename}. Select input column and run.`);
            } catch (err) {
                appendLog('error', 'CSV upload failed: ' + err.message);
            } finally {
                lucide.createIcons();
            }
        });
    }

    if (runCsvBtn) {
        runCsvBtn.addEventListener('click', async () => {
            if (!currentCsvUploadId) {
                appendLog('error', 'Please upload a CSV first.');
                return;
            }
            const col = csvInputColumn?.value;
            if (!col) {
                appendLog('error', 'Please select a CSV column.');
                return;
            }

            try {
                runCsvBtn.disabled = true;
                appendLog('system', `Starting CSV batch run using column: ${col}`);

                const payload = {
                    upload_id: currentCsvUploadId,
                    input_column: col,
                    steps: workflowSteps,
                    flow_id: currentFlowId,
                    name: document.getElementById('flow-name')?.value || 'Workflow',
                    config: {
                        model: (document.getElementById('flow-model')?.value || '').trim(),
                        api_key: (document.getElementById('flow-api-key')?.value || '').trim()
                    }
                };

                const res = await fetch('/api/workflow/batch_execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!data.success) {
                    appendLog('error', data.error || 'Batch execution failed');
                    return;
                }

                lastBatchRunId = data.run_id;
                if (!currentFlowId && data.workflow_id) currentFlowId = data.workflow_id;

                appendLog('system', `Batch run complete. RunID: ${data.run_id} | Rows processed: ${data.count}`);
                if (downloadRunTxtBtn) downloadRunTxtBtn.classList.remove('hidden');
            } catch (err) {
                appendLog('error', 'Batch execution failed: ' + err.message);
            } finally {
                runCsvBtn.disabled = false;
            }
        });
    }

    if (downloadRunTxtBtn) {
        downloadRunTxtBtn.addEventListener('click', () => {
            if (!lastBatchRunId) {
                appendLog('error', 'No batch run available to download yet.');
                return;
            }
            window.location.href = `/api/workflow/run/export_txt?run_id=${encodeURIComponent(lastBatchRunId)}`;
        });
    }

    // Import JSON Workflow
    const jsonImportBtn = document.getElementById('import-json-btn');
    const jsonImportInput = document.getElementById('json-import-input');

    if (jsonImportBtn && jsonImportInput) {
        jsonImportBtn.addEventListener('click', () => jsonImportInput.click());
    }

    if (jsonImportInput) {
        jsonImportInput.addEventListener('change', async () => {
            const file = jsonImportInput.files && jsonImportInput.files[0];
            if (!file) return;

            try {
                const fd = new FormData();
                fd.append('file', file);
                const res = await fetch('/api/workflow/import_json', {
                    method: 'POST',
                    body: fd
                });
                const data = await res.json();
                if (!data.success) {
                    appendLog('error', data.error || 'Import failed');
                    return;
                }

                const wf = data.workflow || {};
                if (!wf.steps || !Array.isArray(wf.steps)) {
                    appendLog('error', 'Imported JSON does not contain workflow steps.');
                    return;
                }

                workflowSteps = JSON.parse(JSON.stringify(wf.steps));
                renderWorkflowSteps();

                const name = wf.name || wf.workflow_name || 'Imported Workflow';
                const flowNameInput = document.getElementById('flow-name');
                if (flowNameInput) flowNameInput.value = name;

                const cfg = wf.config || {};
                const modelInput = document.getElementById('flow-model');
                const keyInput = document.getElementById('flow-api-key');
                if (modelInput && cfg.model !== undefined) modelInput.value = cfg.model || '';
                if (keyInput && cfg.api_key !== undefined) keyInput.value = cfg.api_key || '';

                currentFlowId = wf.flow_id || null;
                appendLog('system', `Imported workflow from JSON: ${file.name}`);
                lucide.createIcons();
            } catch (err) {
                appendLog('error', 'Import failed: ' + err.message);
            } finally {
                jsonImportInput.value = '';
            }
        });
    }

    function setWorkflowStep(step) {
        document.querySelectorAll('.step-item').forEach(s => s.classList.remove('active'));
        if (step) {
            const el = document.getElementById(`step-${step}`);
            if (el) el.classList.add('active');
        }
    }

    function createLogBubble(role) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `<div class="content"><p></p></div>`;
        chatMessages.appendChild(div);
        return div.querySelector('p');
    }

    function updateContentBubble(bubble, text) {
        bubble.textContent = text;
    }

    function showThinkingStreaming(text) {
        thinkingIndicator.classList.remove('hidden');
        thinkingContent.textContent += text;
        scrollChat();
    }

    function appendLog(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}`;

        // Handle system logs specially
        if (role === 'system') {
            div.innerHTML = `<div class="content"><p><span class="sys-label">[SYSTEM]</span> ${escapeHtml(text)}</p></div>`;
        } else {
            div.innerHTML = `<div class="content"><p>${escapeHtml(text)}</p></div>`;
        }

        chatMessages.appendChild(div);
        scrollChat();
    }

    function scrollChat() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function setLoadingState(loading) {
        const btn = document.getElementById('send-btn');
        btn.disabled = loading;
        btn.innerHTML = loading ? '<i data-lucide="loader-2" class="spin"></i>' : '<i data-lucide="send"></i>';
        lucide.createIcons();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Navigation & Dashboard ---

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Check if it's a database link (external navigation)
            if (item.tagName === 'A' && item.href) {
                // Let the browser handle the navigation
                return;
            }
            
            const viewName = item.dataset.view;
            if (!viewName) return;

            // Update URL without page reload
            history.pushState({ view: viewName }, '', `#${viewName}`);

            navItems.forEach(i => i.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));

            item.classList.add('active');
            document.getElementById(`${viewName}-view`).classList.add('active');

            if (viewName === 'history') loadHistory();
            if (viewName === 'observability') {
                refreshMetrics();
                refreshTelemetry();
            }
        });
    });

    // Batch Jobs (CSV Runs)
    const batchRunsListEl = document.getElementById('batch-runs-list');
    const batchRunsLimitEl = document.getElementById('batch-runs-limit');
    const refreshBatchRunsBtn = document.getElementById('refresh-batch-runs-btn');

    if (batchRunsLimitEl) {
        batchRunsLimitEl.addEventListener('change', () => refreshBatchRuns());
    }
    if (refreshBatchRunsBtn) {
        refreshBatchRunsBtn.addEventListener('click', () => refreshBatchRuns());
    }

    async function refreshBatchRuns() {
        if (!batchRunsListEl) return;

        const limit = batchRunsLimitEl ? batchRunsLimitEl.value : '100';
        try {
            const res = await fetch(`/api/workflow/runs?limit=${encodeURIComponent(limit)}`);
            const data = await res.json();
            if (!data.success) {
                batchRunsListEl.innerHTML = `<p class="empty-msg">${escapeHtml(data.error || 'Failed to load batch runs')}</p>`;
                return;
            }

            const runs = data.runs || [];
            if (runs.length === 0) {
                batchRunsListEl.innerHTML = '<p class="empty-msg">No batch runs recorded yet.</p>';
                return;
            }

            batchRunsListEl.innerHTML = runs.map(r => {
                const ts = r.timestamp ? new Date(r.timestamp).toLocaleString() : '';
                const wfName = r.workflow_name || 'Workflow';
                const wfId = r.workflow_id || '';
                const runId = r.run_id || '';
                const col = r.input_column || '';
                const count = (r.count !== undefined && r.count !== null) ? r.count : '';

                return `
                    <div class="trace-item">
                        <div class="trace-header">
                            <span class="trace-time">${escapeHtml(ts)}</span>
                            <span class="trace-comp">${escapeHtml(wfName)}</span>
                            <span class="trace-type">RUN</span>
                        </div>
                        <div class="trace-detail">RunID: <code>${escapeHtml(runId)}</code> | WorkflowID: <code>${escapeHtml(wfId)}</code>${col ? ` | Column: ${escapeHtml(col)}` : ''}${count !== '' ? ` | Rows: ${escapeHtml(String(count))}` : ''}</div>
                        <div style="display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;">
                            <button class="icon-btn" onclick="window.downloadBatchRunTxt('${runId}')"><i data-lucide=\"file-text\"></i> Output</button>
                            <button class="icon-btn" onclick="window.viewBatchRunDetails('${runId}')"><i data-lucide=\"list\"></i> Details</button>
                        </div>
                    </div>
                `;
            }).join('');

            lucide.createIcons();
        } catch (err) {
            batchRunsListEl.innerHTML = '<p class="empty-msg">Failed to load batch runs.</p>';
        }
    }

    window.downloadBatchRunTxt = (runId) => {
        if (!runId) return;
        window.location.href = `/api/workflow/run/export_txt?run_id=${encodeURIComponent(runId)}`;
    };

    window.viewBatchRunDetails = async (runId) => {
        if (!runId) return;
        try {
            const res = await fetch(`/api/workflow/run/details?run_id=${encodeURIComponent(runId)}`);
            const data = await res.json();
            if (!data.success) {
                alert(data.error || 'Failed to load run details');
                return;
            }
            const run = data.run || {};
            const pretty = JSON.stringify(run, null, 2);
            alert(pretty);
        } catch (err) {
            alert('Failed to load run details');
        }
    };

    // Telemetry Table (top 100/200 rows)
    const telemetryListEl = document.getElementById('telemetry-list');
    const telemetryLimitEl = document.getElementById('telemetry-limit');
    const refreshTelemetryBtn = document.getElementById('refresh-telemetry-btn');

    if (telemetryLimitEl) {
        telemetryLimitEl.addEventListener('change', () => refreshTelemetry());
    }
    if (refreshTelemetryBtn) {
        refreshTelemetryBtn.addEventListener('click', () => refreshTelemetry());
    }

    async function refreshTelemetry() {
        if (!telemetryListEl) return;

        const limit = telemetryLimitEl ? telemetryLimitEl.value : '100';
        try {
            const res = await fetch(`/api/telemetry?limit=${encodeURIComponent(limit)}`);
            const data = await res.json();
            if (!data.success) {
                telemetryListEl.innerHTML = `<p class="empty-msg">${escapeHtml(data.error || 'Failed to load telemetry')}</p>`;
                return;
            }

            const rows = data.rows || [];
            if (rows.length === 0) {
                telemetryListEl.innerHTML = '<p class="empty-msg">No telemetry recorded yet.</p>';
                return;
            }

            telemetryListEl.innerHTML = rows.map(r => {
                const time = r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : '';
                const type = (r.type || '').toUpperCase();
                const component = r.step_name || r.model || r.workflow_id || '';
                const latency = (typeof r.latency === 'number') ? `${r.latency.toFixed(3)}s` : '';
                const preview = r.output_preview || r.input_preview || '';
                return `
                    <div class="trace-item">
                        <div class="trace-header">
                            <span class="trace-time">${escapeHtml(time)}</span>
                            <span class="trace-comp">${escapeHtml(component)}</span>
                            <span class="trace-type">${escapeHtml(type)}</span>
                        </div>
                        <div class="trace-detail">${latency ? `Latency: ${escapeHtml(latency)} | ` : ''}Preview: ${escapeHtml(String(preview))}</div>
                    </div>
                `;
            }).join('');
        } catch (err) {
            telemetryListEl.innerHTML = '<p class="empty-msg">Failed to load telemetry.</p>';
        } finally {
            lucide.createIcons();
        }
    }

    async function refreshMetrics() {
        try {
            const response = await fetch('/api/metrics');
            const data = await response.json();

            if (data.success) {
                const m = data.metrics;
                const latency = m.provider_metrics.avg_latency.toFixed(2) + 's';

                // Update Workstation Telemetry
                const teleLat = document.getElementById('tele-latency');
                if (teleLat) teleLat.textContent = latency;

                // Update Metrics View
                const mAvgLat = document.getElementById('m-avg-latency');
                if (mAvgLat) mAvgLat.textContent = latency;

                const mTotalReq = document.getElementById('m-total-requests');
                if (mTotalReq) mTotalReq.textContent = m.conversation_count;

                // Update Traces List
                const tracesList = document.getElementById('traces-list');
                if (tracesList && m.traces) {
                    if (m.traces.length === 0) {
                        tracesList.innerHTML = '<p class="empty-msg">No traces recorded yet.</p>';
                    } else {
                        tracesList.innerHTML = m.traces.slice().reverse().map(t => {
                            const time = new Date(t.timestamp).toLocaleTimeString();
                            const icon = t.type === 'call' ? 'arrow-right' : 'arrow-left';
                            const colorClass = t.type === 'call' ? 'trace-call' : 'trace-resp';

                            let detail = '';
                            if (t.type === 'call') {
                                detail = `<div class="trace-detail">Input: ${escapeHtml(t.input)}</div>`;
                            } else {
                                detail = `<div class="trace-detail">Latency: ${t.output?.latency?.toFixed(3)}s | Preview: ${escapeHtml(t.output?.text_preview || '')}</div>`;
                            }

                            return `
                                <div class="trace-item ${colorClass}">
                                    <div class="trace-header">
                                        <span class="trace-time">${time}</span>
                                        <span class="trace-comp">${t.component}</span>
                                        <span class="trace-type">${t.type.toUpperCase()}</span>
                                    </div>
                                    ${detail}
                                </div>
                            `;
                        }).join('');
                    }
                }
            }
        } catch (err) { }
    }

    // Auto-refresh metrics
    setInterval(refreshMetrics, 5000);

    async function loadHistory() {
        const list = document.getElementById('history-list');
        list.innerHTML = '<p class="loading">Loading history...</p>';

        // Also refresh batch runs when entering history
        refreshBatchRuns();

        try {
            const response = await fetch('/api/history');
            const data = await response.json();

            if (data.success && data.history.length > 0) {
                list.innerHTML = data.history.map(item => {
                    const typeBadge = item.type === 'workflow'
                        ? '<span class="badge detail-badge">WORKFLOW</span>'
                        : (item.type === 'tool'
                            ? '<span class="badge" style="background: rgba(255,215,0,0.15); border: 1px solid rgba(255,215,0,0.35); color: #ffd700;">TOOL</span>'
                            : '<span class="badge success-badge">CHAT</span>');

                    let content = `<div class="h-response"><strong>Result:</strong> ${escapeHtml(item.response.text)}</div>`;

                    // Add details toggle for workflows/tools
                    if (item.full_context) {
                        const details = JSON.stringify(item.full_context, null, 2);
                        content += `
                            <details class="h-details">
                                <summary>Show Full Execution Details</summary>
                                <pre>${escapeHtml(details)}</pre>
                            </details>
                         `;
                    }

                    return `
                    <div class="history-card">
                        <div class="h-header">
                            <span class="h-time">${new Date(item.timestamp).toLocaleString()}</span>
                            ${typeBadge}
                        </div>
                        <div class="h-query"><strong>Input:</strong> ${escapeHtml(item.message)}</div>
                        ${content}
                    </div>
                `}).join('');
            } else {
                list.innerHTML = '<p class="empty">No conversation history yet.</p>';
            }
        } catch (err) {
            list.innerHTML = '<p class="error">Failed to load history.</p>';
        }
    }

    // --- Memory Management ---

    let selectedMemoryId = null;

    async function loadMemory() {
        const limit = document.getElementById('memory-limit')?.value || 10;
        const workflowId = document.getElementById('memory-workflow-filter')?.value || null;

        try {
            const response = await fetch(`/api/memory/list?limit=${limit}${workflowId ? '&workflow_id=' + workflowId : ''}`);
            const data = await response.json();

            if (data.success) {
                renderMemoryItems(data.memories);
            } else {
                document.getElementById('memory-items').innerHTML = `<p class="empty">${data.error || 'Failed to load memory'}</p>`;
            }
        } catch (err) {
            appendLog('error', 'Failed to load memory: ' + err.message);
        }
    }

    function renderMemoryItems(memories) {
        const container = document.getElementById('memory-items');

        if (!memories || memories.length === 0) {
            container.innerHTML = '<p class="empty">No memory entries found.</p>';
            return;
        }

        container.innerHTML = memories.map(mem => {
            const date = new Date(mem.created_at).toLocaleString();
            const meta = mem.step_name ? `Step ${mem.step_index + 1} (${mem.step_name})` : `Memory`;
            const workflowInfo = mem.workflow_id ? `<span class="memory-item-meta">Workflow: ${mem.workflow_id.substring(0, 8)}...</span>` : '';

            return `
                <div class="memory-item" onclick="selectMemory(${mem.id}, '${mem.output_text.replace(/'/g, "\\'")}')" data-memory-id="${mem.id}">
                    <div class="memory-item-header">
                        <div>
                            <div class="memory-item-title">${meta}</div>
                            <div class="memory-item-meta">${date}</div>
                        </div>
                        <button class="icon-btn danger small" onclick="event.stopPropagation(); deleteMemory(${mem.id})">
                            <i data-lucide="trash-2" style="width:14px; height:14px;"></i>
                        </button>
                    </div>
                    <div class="memory-item-content">
                        ${escapeHtml(mem.output_text.substring(0, 300))}...
                    </div>
                </div>
            `;
        }).join('');

        lucide.createIcons();
    }

    function selectMemory(id, text) {
        selectedMemoryId = id;

        // Update selection visual
        document.querySelectorAll('.memory-item').forEach(el => el.classList.remove('selected'));
        const selectedItem = document.querySelector(`[data-memory-id="${id}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }

        // Update preview text
        document.getElementById('memory-preview-text').value = text;
    }

    async function deleteMemory(id) {
        if (!confirm('Delete this memory entry?')) return;

        try {
            const response = await fetch('/api/memory/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory_id: id })
            });

            const data = await response.json();

            if (data.success) {
                appendLog('system', `Memory entry deleted`);
                loadMemory();
            } else {
                appendLog('error', data.error || 'Failed to delete memory');
            }
        } catch (err) {
            appendLog('error', 'Failed to delete memory: ' + err.message);
        }
    }

    // Make memory functions globally accessible for onclick handlers
    window.selectMemory = selectMemory;
    window.deleteMemory = deleteMemory;

    document.getElementById('refresh-memory-btn')?.addEventListener('click', loadMemory);

    document.getElementById('clear-memory-btn')?.addEventListener('click', async () => {
        if (!confirm('Clear ALL memory entries for this session?')) return;

        try {
            const response = await fetch('/api/memory/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.success) {
                appendLog('system', `Cleared ${data.message}`);
                loadMemory();
            } else {
                appendLog('error', data.error || 'Failed to clear memory');
            }
        } catch (err) {
            appendLog('error', 'Failed to clear memory: ' + err.message);
        }
    });

    document.getElementById('memory-workflow-filter')?.addEventListener('change', loadMemory);

    document.getElementById('memory-limit')?.addEventListener('change', loadMemory);

    document.getElementById('search-memory-btn')?.addEventListener('click', async () => {
        const query = document.getElementById('memory-search-input')?.value?.trim();
        if (!query) {
            appendLog('system', 'Please enter a search query');
            return;
        }

        try {
            const limit = document.getElementById('memory-limit')?.value || 20;
            const response = await fetch(`/api/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`);
            const data = await response.json();

            if (data.success) {
                renderMemoryItems(data.memories);
                appendLog('system', `Found ${data.count} memory entries matching "${query}"`);
            } else {
                appendLog('error', data.error || 'Memory search failed');
            }
        } catch (err) {
            appendLog('error', 'Failed to search memory: ' + err.message);
        }
    });

    document.getElementById('insert-memory-btn')?.addEventListener('click', async () => {
        const previewText = document.getElementById('memory-preview-text').value;
        if (!previewText) {
            appendLog('system', 'No memory selected to insert');
            return;
        }

        // Copy to clipboard
        navigator.clipboard.writeText(previewText);
        appendLog('system', 'Memory text copied to clipboard! Paste it into any workflow step prompt.');
    });

    document.getElementById('copy-memory-btn')?.addEventListener('click', () => {
        const previewText = document.getElementById('memory-preview-text').value;
        if (!previewText) {
            appendLog('system', 'No memory to copy');
            return;
        }

        navigator.clipboard.writeText(previewText);
        appendLog('system', 'Memory text copied to clipboard!');
    });

    // Auto-load memory when switching to memory view
    const memoryViewBtn = document.querySelector('[data-view="memory"]');
    if (memoryViewBtn) {
        memoryViewBtn.addEventListener('click', () => {
            setTimeout(() => loadMemory(), 100);
        });
    }

    // --- Session Management ---

    logoutBtn.addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        location.reload();
    });
});
