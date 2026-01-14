document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

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

    // Validate Credentials
    validateBtn.addEventListener('click', async () => {
        const apiKey = document.getElementById(`${currentProvider}-api-key`).value;
        const baseUrl = currentProvider === 'nvidia' ? document.getElementById('nvidia-base-url').value : null;

        if (!apiKey) {
            showError('API Key is required');
            return;
        }

        validateBtn.disabled = true;
        validateBtn.innerHTML = '<span>Validating...</span>';
        authError.textContent = '';

        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: currentProvider,
                    api_key: apiKey,
                    base_url: baseUrl
                })
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

    // --- Chat Functionality ---

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = (messageInput.scrollHeight) + 'px';
    });

    let currentMode = 'general';
    let currentFlowId = null;
    let workflowSteps = [
        { id: 1, name: 'Analysis', prompt: 'Analyze this: {{input}}' },
        { id: 2, name: 'Detailing', prompt: 'Expand on {{step1}}' }
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
    function renderWorkflowSteps() {
        const container = document.getElementById('steps-container');

        container.innerHTML = workflowSteps.map((step, idx) => {
            // Calculate available variables for this step
            // Always available: {{input}}
            // Previous steps: {{stepN}} or {{StepName}}
            // Note: If parallel to previous, technically shouldn't access previous, but we show all for simplicity

            const vars = ['{{input}}'];
            for (let i = 0; i < idx; i++) {
                const pStep = workflowSteps[i];
                // Prioritize Name over Step N to avoid duplicates
                if (pStep.name && pStep.name.trim() !== "" && pStep.name !== `Step ${i + 1}`) {
                    vars.push(`{{${pStep.name}}}`);
                } else {
                    vars.push(`{{step${i + 1}}}`);
                }
            }

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

    window.removeWorkflowStep = (id) => {
        workflowSteps = workflowSteps.filter(s => s.id !== id);
        renderWorkflowSteps();
    };

    document.getElementById('add-step-btn').addEventListener('click', () => {
        workflowSteps.push({
            id: Date.now(),
            name: `Step ${workflowSteps.length + 1}`,
            prompt: 'Process output from previous step...'
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
        item.addEventListener('click', () => {
            const viewName = item.dataset.view;

            navItems.forEach(i => i.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));

            item.classList.add('active');
            document.getElementById(`${viewName}-view`).classList.add('active');

            if (viewName === 'history') loadHistory();
            if (viewName === 'observability') refreshMetrics();
        });
    });

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

        try {
            const response = await fetch('/api/history');
            const data = await response.json();

            if (data.success && data.history.length > 0) {
                list.innerHTML = data.history.map(item => {
                    const typeBadge = item.type === 'workflow'
                        ? '<span class="badge detail-badge">WORKFLOW</span>'
                        : '<span class="badge success-badge">CHAT</span>';

                    let content = `<div class="h-response"><strong>Result:</strong> ${escapeHtml(item.response.text)}</div>`;

                    // Add details toggle for workflows
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

    // --- Session Management ---

    logoutBtn.addEventListener('click', async () => {
        await fetch('/api/logout', { method: 'POST' });
        location.reload();
    });
});
