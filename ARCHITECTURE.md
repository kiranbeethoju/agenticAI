# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                          │
│                    (Python Code/Scripts)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ import agent
                            │ agent = create_agent()
                            │ agent.chat("message")
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SIMPLIFIED AGENT                             │
│                      (agent.py)                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Chat interface (chat, multi_turn_chat)                 │  │
│  │  • Conversation history management                        │  │
│  │  • Provider selection & routing                           │  │
│  │  • Metrics aggregation                                    │  │
│  │  • Configuration loading                                  │  │
│  │  • Data export                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   GEMINI     │  │ AZURE OPENAI │  │   CUSTOM     │
│   PROVIDER   │  │   PROVIDER   │  │   PROVIDER   │
│  (built-in)  │  │  (built-in)  │  │  (add more)  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        │   (llm_providers.py)                  │
        │    • Base LLMProvider class           │
        │    • GeminiProvider implementation    │
        │    • AzureOpenAIProvider              │
        │    • Provider metrics                 │
        │                                       │
        └───────────────────┼───────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │   EXTERNAL LLM APIs                 │
        │  • Google Gemini API                │
        │  • Azure OpenAI API                 │
        └─────────────────────────────────────┘
                            │
                            │ (All calls traced)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                           │
│                   (observability.py)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LOGGING                                                  │  │
│  │  • Multi-level logging (DEBUG/INFO/ERROR)                │  │
│  │  • File + Console output                                 │  │
│  │  • Timestamps & formatting                               │  │
│  │  → Output: logs/agent.log                                │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  TRACING                                                  │  │
│  │  • API call tracing                                      │  │
│  │  • Response tracing                                      │  │
│  │  • Input/Output capture                                  │  │
│  │  → Exportable to JSON                                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  METRICS                                                  │  │
│  │  • Latency tracking                                      │  │
│  │  • Token usage                                           │  │
│  │  • API call counts                                       │  │
│  │  • Error counts                                          │  │
│  │  → Exportable to JSON                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │   DATA EXPORTS                      │
        │  • logs/agent.log                   │
        │  • logs/observability.json          │
        │  • logs/conversation_history.json   │
        │  • logs/metrics.json                │
        └─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION                                 │
│                     (config.yaml)                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LLM Providers:                                           │  │
│  │    • API keys                                            │  │
│  │    • Model names                                         │  │
│  │    • Enable/disable                                      │  │
│  │                                                           │  │
│  │  Agent Settings:                                         │  │
│  │    • Temperature, max_tokens                             │  │
│  │    • Max iterations                                      │  │
│  │                                                           │  │
│  │  Observability:                                          │  │
│  │    • Logging levels                                      │  │
│  │    • Tracing options                                     │  │
│  │    • Metrics toggles                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
```
User Code
    │
    │ agent.chat("message")
    ▼
SimplifiedAgent
    │
    │ 1. Select provider (from config)
    │ 2. Log request
    ▼
LLMProvider
    │
    │ 3. Trace call
    │ 4. Make API request
    ▼
Google Gemini API
    │
    │ 5. Generate response
    ▼
LLMProvider
    │
    │ 6. Trace response
    │ 7. Record metrics
    ▼
SimplifiedAgent
    │
    │ 8. Update conversation history
    │ 9. Return response
    ▼
User Code
```

### 2. Observability Flow
```
Every API Call Triggers:
    │
    ├─→ LOGGING
    │   ├─ Console output
    │   └─ File: logs/agent.log
    │
    ├─→ TRACING
    │   ├─ Call details (input, timestamp)
    │   └─ Response details (output, latency)
    │
    └─→ METRICS
        ├─ Latency measurement
        ├─ Token counting
        └─ Error tracking
```

## Component Responsibilities

### agent.py (SimplifiedAgent)
- **Purpose**: Main orchestration layer
- **Responsibilities**:
  - Initialize providers
  - Route requests to appropriate provider
  - Manage conversation history
  - Aggregate metrics from all providers
  - Export data
  - Handle configuration

### llm_providers.py
- **Purpose**: Abstract LLM provider interactions
- **Responsibilities**:
  - Define provider interface (LLMProvider base class)
  - Implement Gemini provider
  - Implement Azure OpenAI provider
  - Track per-provider metrics
  - Handle provider-specific errors

### observability.py (Observer)
- **Purpose**: Track everything that happens
- **Responsibilities**:
  - Configure and manage logging
  - Trace API calls and responses
  - Collect and store metrics
  - Export observability data

### config.yaml
- **Purpose**: Central configuration
- **Responsibilities**:
  - Store API credentials
  - Define provider settings
  - Configure agent parameters
  - Set observability options

## File Dependencies

```
config.yaml
    │
    └─→ agent.py
           │
           ├─→ llm_providers.py
           │      │
           │      └─→ google.genai
           │      └─→ openai (Azure)
           │
           └─→ observability.py
                  │
                  └─→ logging
```

## Class Hierarchy

```
LLMProvider (ABC)
    │
    ├─→ GeminiProvider
    │      └─ Uses: google.genai.Client
    │
    └─→ AzureOpenAIProvider
           └─ Uses: openai.AzureOpenAI

Observer
    ├─ Logger
    ├─ Traces []
    └─ Metrics {}

SimplifiedAgent
    ├─ Config (dict)
    ├─ Observer
    ├─ Providers (dict of LLMProvider)
    ├─ ConversationHistory []
    └─ Default Provider
```

## Key Design Patterns

### 1. Factory Pattern
```python
LLMProviderFactory.create_provider("gemini", config, observer)
# Returns: GeminiProvider instance
```

### 2. Strategy Pattern
```python
# Different providers, same interface
provider.generate(prompt)  # Works for any provider
```

### 3. Observer Pattern
```python
# Observer tracks all provider actions
provider = GeminiProvider(config, observer)
provider.generate(prompt)  # Automatically logged/traced
```

### 4. Singleton-like Configuration
```python
# Single config.yaml controls entire system
agent = create_agent("config.yaml")
```

## Extension Points

### Add New LLM Provider
```python
# 1. Create new provider class in llm_providers.py
class CustomProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        # Your implementation
        pass

# 2. Add to factory
providers = {
    "gemini": GeminiProvider,
    "azure_openai": AzureOpenAIProvider,
    "custom": CustomProvider  # Add here
}

# 3. Configure in config.yaml
llm_providers:
  custom:
    enabled: true
    api_key: "..."
```

### Add Custom Metrics
```python
# In observability.py
observer.record_metric("custom_metric", value)

# Then export
metrics = observer.get_metrics()
```

### Add Custom Tools
```python
# Extend SimplifiedAgent
class ToolEnabledAgent(SimplifiedAgent):
    def use_tool(self, tool_name, params):
        # Your tool logic
        pass
```

## Testing Architecture

```
test_llm_api.py
    │
    ├─→ Test 1: Gemini API
    │   ├─ Import google.genai
    │   ├─ Initialize client
    │   └─ Test API call
    │
    └─→ Test 2: Agent System
        ├─ Import agent
        ├─ Create instance
        ├─ Test chat
        └─ Verify metrics

simple_test.py
    └─→ Quick API validation
        └─ Try multiple models

quickstart.py
    └─→ Demonstrate system
        └─ Show all features working
```

## Production Considerations

### Current Implementation
- ✅ Error handling
- ✅ Logging
- ✅ Metrics
- ✅ Configuration management
- ✅ Data export

### Future Enhancements
- ⏭️  Retry logic with exponential backoff
- ⏭️  Rate limiting
- ⏭️  Response caching
- ⏭️  Async/await support
- ⏭️  Streaming responses
- ⏭️  Cost tracking
- ⏭️  Multiple API key rotation
- ⏭️  Request queuing

## Security Considerations

### Current Implementation
- API keys in config.yaml (not committed to git)
- No hardcoded credentials
- Error messages sanitized (no key exposure)

### Recommendations
- Use environment variables for production
- Implement secrets management (e.g., AWS Secrets Manager)
- Add API key validation
- Implement rate limiting per user/key

## Performance Profile

### Latency Breakdown
```
Total Response Time
    │
    ├─ Agent overhead:     ~5-10ms
    ├─ Provider overhead:  ~5-10ms
    ├─ Network latency:    ~100-300ms
    └─ LLM generation:     ~500-2000ms
       (varies by prompt)
```

### Memory Usage
- Config: ~1KB
- Agent state: ~10KB
- Conversation history: ~1KB per message
- Logs: Grows over time (configure rotation)
- Traces: ~500 bytes per API call

## Scalability

### Current Limitations
- Synchronous API calls
- In-memory conversation history
- File-based logging

### Scaling Options
1. **Horizontal**: Multiple agent instances
2. **Vertical**: Async processing
3. **Storage**: Database for history/logs
4. **Caching**: Redis for responses
5. **Queue**: Message queue for requests
