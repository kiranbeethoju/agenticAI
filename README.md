# Simplified Agent System

A high-capability, fully observable agent system in Python with support for multiple LLM providers (Google Gemini & Azure OpenAI).

## 🎯 Features

- **Multi-Provider Support**: Google Gemini and Azure OpenAI
- **Full Observability**: Comprehensive logging, tracing, and metrics
- **Easy Configuration**: YAML-based configuration
- **Conversation History**: Track all interactions
- **Metrics & Analytics**: Detailed performance metrics
- **Export Capabilities**: Export all data for analysis
- **Simple API**: Easy-to-use Python interface

## 📁 Project Structure

```
agenticAI/
├── config.yaml              # Configuration file
├── agent.py                 # Main agent system
├── llm_providers.py         # LLM provider implementations
├── observability.py         # Observability module
├── test_llm_api.py         # API credential test script
├── examples.py             # Usage examples
├── requirements.txt        # Dependencies
└── logs/                   # Output directory (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config.yaml` and add your API credentials:

```yaml
llm_providers:
  gemini:
    enabled: true
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.0-flash-exp"
    default: true
  
  azure_openai:
    enabled: false
    api_key: "YOUR_AZURE_KEY"
    endpoint: "YOUR_AZURE_ENDPOINT"
    deployment_name: "YOUR_DEPLOYMENT"
```

### 3. Test Your Credentials

```bash
python test_llm_api.py
```

### 4. Run Examples

```bash
python examples.py
```

## 💻 Usage

### Basic Usage

```python
from agent import create_agent

# Create agent
agent = create_agent()

# Simple chat
response = agent.chat("What is artificial intelligence?")
print(response)
```

### Multi-turn Conversation

```python
from agent import create_agent

agent = create_agent()

messages = [
    "What is machine learning?",
    "How does it work?",
    "Give me an example"
]

responses = agent.multi_turn_chat(messages)

for response in responses:
    print(response['text'])
```

### Custom Parameters

```python
agent = create_agent()

# Low temperature for factual responses
response = agent.chat(
    "What is the capital of France?",
    temperature=0.1
)

# High temperature for creative responses
response = agent.chat(
    "Write a creative story",
    temperature=0.9
)
```

### Access Metrics

```python
agent = create_agent()

# Generate some responses
agent.chat("Hello!")
agent.chat("How are you?")

# Print metrics
agent.print_metrics()

# Get raw metrics
metrics = agent.get_metrics()
print(metrics)
```

### Export Data

```python
agent = create_agent()

# Have conversations...
agent.chat("Test message 1")
agent.chat("Test message 2")

# Export all data
agent.export_data("logs")
```

## ⚙️ Configuration

The `config.yaml` file controls all agent behavior:

### LLM Providers

```yaml
llm_providers:
  gemini:
    enabled: true
    api_key: "YOUR_KEY"
    model: "gemini-2.0-flash-exp"
    default: true
```

### Agent Settings

```yaml
agent:
  name: "SimplifiedAgent"
  max_iterations: 10
  temperature: 0.7
  max_tokens: 2000
```

### Observability

```yaml
observability:
  logging:
    enabled: true
    level: "INFO"
    format: "detailed"
    file: "logs/agent.log"
  
  tracing:
    enabled: true
    trace_calls: true
    trace_responses: true
  
  metrics:
    enabled: true
    track_latency: true
    track_token_usage: true
```

## 📊 Observability Features

### Logging

All operations are logged with timestamps and severity levels:

```
2026-01-11 14:52:28 - AgentObserver - INFO - Agent initialization started
2026-01-11 14:52:29 - AgentObserver - INFO - Gemini client initialized successfully
2026-01-11 14:52:30 - AgentObserver - INFO - Generating response (iteration 1)
```

### Tracing

API calls and responses are traced:

```python
agent.observer.get_traces()
# Returns list of all traced operations
```

### Metrics

Comprehensive metrics tracking:

- Total API calls
- Token usage
- Latency (average and per-call)
- Error counts
- Conversation counts

## 🧪 Testing

### Test API Credentials

```bash
python test_llm_api.py
```

This will:
1. Test Gemini API connection
2. Verify credentials
3. Make a sample API call
4. Test the complete agent system

### Expected Output

```
✓ TEST PASSED - API credentials are working correctly!
✓ AGENT SYSTEM TEST PASSED!
```

## 📈 Metrics Example

```
AGENT METRICS
==============================================================

Agent Stats:
  Total Iterations: 5
  Total Conversations: 5

Provider Metrics:

  GEMINI:
    Total Calls: 5
    Total Tokens: 0
    Avg Latency: 0.847s
    Errors: 0
==============================================================
```

## 🔧 Advanced Features

### Multiple Providers

```python
# Use specific provider
response = agent.chat("Hello", provider_name="gemini")
response = agent.chat("Hello", provider_name="azure_openai")
```

### Conversation History

```python
history = agent.get_conversation_history()

for conv in history:
    print(f"Q: {conv['prompt']}")
    print(f"A: {conv['response']['text']}")
    print(f"Provider: {conv['provider']}")
```

### Reset Agent State

```python
agent.reset()  # Clear history and reset counters
```

## 📋 Requirements

- Python 3.8+
- google-genai
- openai (for Azure OpenAI)
- pyyaml

## 🐛 Troubleshooting

### Import Error for google.genai

```bash
pip install google-genai
```

### API Authentication Failed

- Check your API key in `config.yaml`
- Verify the key is valid and has not expired
- Check your API quota/limits

### Module Not Found

Make sure you're running scripts from the project directory:

```bash
cd /Users/kiran/Documents/agenticAI
python test_llm_api.py
```

## 📝 License

This is a demonstration project. Use at your own discretion.

## 🤝 Support

For issues or questions, check the logs in the `logs/` directory for detailed error information.
