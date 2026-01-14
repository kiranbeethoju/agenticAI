"""
Simplified Agent System
A high-capability agent with proper configurability and observability
"""

import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from llm_providers import LLMProviderFactory, LLMProvider
from observability import Observer


class SimplifiedAgent:
    """Main agent class with full observability and configurability"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize agent with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize observability
        self.observer = Observer(self.config.get("observability", {}))
        self.observer.log("INFO", "Agent initialization started")
        
        # Initialize LLM providers
        self.providers = {}
        self._initialize_providers()
        
        # Get default provider
        self.default_provider = self._get_default_provider()
        
        # Agent state
        self.conversation_history = []
        self.iteration_count = 0
        
        self.observer.log("INFO", "Agent initialization completed")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_providers(self):
        """Initialize all enabled LLM providers"""
        llm_config = self.config.get("llm_providers", {})
        
        for provider_name, provider_config in llm_config.items():
            if provider_config.get("enabled", False):
                try:
                    provider = LLMProviderFactory.create_provider(
                        provider_name,
                        provider_config,
                        self.observer
                    )
                    self.providers[provider_name] = provider
                    self.observer.log("INFO", f"Provider '{provider_name}' initialized successfully")
                except Exception as e:
                    self.observer.log("ERROR", f"Failed to initialize provider '{provider_name}': {str(e)}")
    
    def _get_default_provider(self) -> Optional[LLMProvider]:
        """Get the default LLM provider"""
        llm_config = self.config.get("llm_providers", {})
        
        for provider_name, provider_config in llm_config.items():
            if provider_config.get("default", False) and provider_name in self.providers:
                return self.providers[provider_name]
        
        # If no default specified, return first available
        if self.providers:
            return list(self.providers.values())[0]
        
        return None
    
    def generate_response(self, prompt: str, provider_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a response using specified or default provider"""
        self.iteration_count += 1
        
        # Select provider
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        elif self.default_provider:
            provider = self.default_provider
        else:
            error_msg = "No LLM provider available"
            self.observer.log("ERROR", error_msg)
            return {"error": error_msg}
        
        # Get agent config
        agent_config = self.config.get("agent", {})
        
        # Merge kwargs with agent config
        generation_params = {
            "temperature": agent_config.get("temperature", 0.7),
            "max_tokens": agent_config.get("max_tokens", 2000),
            **kwargs
        }
        
        # Generate response
        self.observer.log("INFO", f"Generating response (iteration {self.iteration_count})")
        response = provider.generate(prompt, **generation_params)
        
        # Track in conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "provider": response.get("provider")
        })
        
        # Record metrics
        if self.observer.config.get("metrics", {}).get("track_latency", False):
            self.observer.record_metric("response_latency", response.get("latency", 0))
        
        if self.observer.config.get("metrics", {}).get("track_token_usage", False):
            self.observer.record_metric("token_usage", response.get("tokens", 0))
        
        return response
    
    def chat(self, message: str, provider_name: Optional[str] = None, **kwargs) -> str:
        """Simple chat interface"""
        response = self.generate_response(message, provider_name, **kwargs)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        return response.get("text", "")
    
    def multi_turn_chat(self, messages: List[str], provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Multi-turn conversation"""
        responses = []
        
        for i, message in enumerate(messages):
            self.observer.log("INFO", f"Processing message {i+1}/{len(messages)}")
            response = self.generate_response(message, provider_name)
            responses.append(response)
            
            # Check max iterations
            max_iterations = self.config.get("agent", {}).get("max_iterations", 10)
            if self.iteration_count >= max_iterations:
                self.observer.log("WARNING", f"Max iterations ({max_iterations}) reached")
                break
        
        return responses
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all providers"""
        metrics = {
            "agent": {
                "total_iterations": self.iteration_count,
                "total_conversations": len(self.conversation_history)
            },
            "providers": {}
        }
        
        for provider_name, provider in self.providers.items():
            metrics["providers"][provider_name] = provider.get_metrics()
        
        metrics["observability"] = self.observer.get_metrics()
        
        return metrics
    
    def print_metrics(self):
        """Print formatted metrics"""
        metrics = self.get_metrics()
        
        print("\n" + "="*60)
        print("AGENT METRICS")
        print("="*60)
        
        print(f"\nAgent Stats:")
        print(f"  Total Iterations: {metrics['agent']['total_iterations']}")
        print(f"  Total Conversations: {metrics['agent']['total_conversations']}")
        
        print(f"\nProvider Metrics:")
        for provider_name, provider_metrics in metrics["providers"].items():
            print(f"\n  {provider_name.upper()}:")
            print(f"    Total Calls: {provider_metrics['total_calls']}")
            print(f"    Total Tokens: {provider_metrics['total_tokens']}")
            print(f"    Avg Latency: {provider_metrics['avg_latency']:.3f}s")
            print(f"    Errors: {provider_metrics['errors']}")
        
        print("="*60 + "\n")
    
    def export_data(self, directory: str = "logs"):
        """Export all agent data"""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Export conversation history
        import json
        
        with open(dir_path / "conversation_history.json", 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        
        # Export metrics
        with open(dir_path / "metrics.json", 'w') as f:
            json.dump(self.get_metrics(), f, indent=2)
        
        # Export observability data
        self.observer.export_observability_data(str(dir_path / "observability.json"))
        
        self.observer.log("INFO", f"All data exported to {directory}/")
    
    def reset(self):
        """Reset agent state"""
        self.conversation_history = []
        self.iteration_count = 0
        self.observer.log("INFO", "Agent state reset")


def create_agent(config_path: str = "config.yaml") -> SimplifiedAgent:
    """Factory function to create an agent"""
    return SimplifiedAgent(config_path)
