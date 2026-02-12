"""
LLM Provider Abstractions
Supports Google Gemini and Azure OpenAI with a unified interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import time
from datetime import datetime


class LLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any], observer=None):
        self.config = config
        self.observer = observer
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_latency": 0.0,
            "errors": 0
        }
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from LLM"""
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str, Optional[str]]:
        """Test connection with simple 'hi' message

        Returns:
            Tuple of (success: bool, message: str, response: Optional[str])
        """
        pass

    def _record_metrics(self, latency: float, tokens: int = 0):
        """Record metrics for observability"""
        self.metrics["total_calls"] += 1
        self.metrics["total_latency"] += latency
        self.metrics["total_tokens"] += tokens
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics"""
        return {
            **self.metrics,
            "avg_latency": self.metrics["total_latency"] / max(self.metrics["total_calls"], 1)
        }


class GeminiProvider(LLMProvider):
    """Google Gemini Provider"""
    
    def __init__(self, config: Dict[str, Any], observer=None):
        super().__init__(config, observer)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            from google import genai
            import os
            
            # Set API key
            api_key = self.config.get("api_key")
            os.environ["GOOGLE_API_KEY"] = api_key
            
            self.client = genai.Client(api_key=api_key)
            
            if self.observer:
                self.observer.log("INFO", "Gemini client initialized successfully")
        except Exception as e:
            if self.observer:
                self.observer.log("ERROR", f"Failed to initialize Gemini client: {str(e)}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from Gemini"""
        start_time = time.time()

        try:
            if self.observer:
                self.observer.trace_call("Gemini", prompt)

            model = kwargs.get("model", self.config.get("model", "gemini-2.0-flash-exp"))

            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
            )

            latency = time.time() - start_time
            result = {
                "text": response.text,
                "model": model,
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "provider": "gemini"
            }

            if self.observer:
                self.observer.trace_response("Gemini", result)

            self._record_metrics(latency)

            return result

        except Exception as e:
            latency = time.time() - start_time
            self.metrics["errors"] += 1

            if self.observer:
                self.observer.log("ERROR", f"Gemini generation failed: {str(e)}")

            return {
                "text": "",
                "error": str(e),
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "provider": "gemini"
            }

    def test_connection(self) -> Tuple[bool, str, Optional[str]]:
        """Test connection with simple 'hi' message"""
        try:
            model = self.config.get("model", "gemini-2.0-flash-exp")
            response = self.client.models.generate_content(
                model=model,
                contents="hi"
            )

            response_text = response.text if hasattr(response, 'text') else str(response)
            return True, "Connection successful", response_text
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "API_KEY_INVALID" in error_str:
                return False, "Authentication failed: Invalid API key", None
            elif "403" in error_str or "PERMISSION_DENIED" in error_str:
                return False, "Access forbidden: Check API key permissions", None
            else:
                return False, f"Connection failed: {error_str}", None


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI Provider"""
    
    def __init__(self, config: Dict[str, Any], observer=None):
        super().__init__(config, observer)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            from openai import AzureOpenAI
            
            self.client = AzureOpenAI(
                api_key=self.config.get("api_key"),
                api_version=self.config.get("api_version", "2024-02-01"),
                azure_endpoint=self.config.get("endpoint")
            )
            
            if self.observer:
                self.observer.log("INFO", "Azure OpenAI client initialized successfully")
        except Exception as e:
            if self.observer:
                self.observer.log("ERROR", f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from Azure OpenAI"""
        start_time = time.time()

        try:
            if self.observer:
                self.observer.trace_call("AzureOpenAI", prompt)

            deployment = kwargs.get("deployment", self.config.get("deployment_name"))

            response = self.client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )

            latency = time.time() - start_time
            result = {
                "text": response.choices[0].message.content,
                "model": deployment,
                "latency": latency,
                "tokens": response.usage.total_tokens,
                "timestamp": datetime.now().isoformat(),
                "provider": "azure_openai"
            }

            if self.observer:
                self.observer.trace_response("AzureOpenAI", result)

            self._record_metrics(latency, response.usage.total_tokens)

            return result

        except Exception as e:
            latency = time.time() - start_time
            self.metrics["errors"] += 1

            if self.observer:
                self.observer.log("ERROR", f"Azure OpenAI generation failed: {str(e)}")

            return {
                "text": "",
                "error": str(e),
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "provider": "azure_openai"
            }

    def test_connection(self) -> Tuple[bool, str, Optional[str]]:
        """Test connection with simple 'hi' message"""
        try:
            deployment = self.config.get("deployment_name")
            if not deployment:
                return False, "Deployment name is required", None

            response = self.client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=50
            )

            response_text = response.choices[0].message.content
            return True, "Connection successful", response_text
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "unauthorized" in error_str.lower():
                return False, "Authentication failed: Invalid API key", None
            elif "404" in error_str or "deployment" in error_str.lower():
                return False, "Deployment not found: Check deployment name", None
            elif "base_url" in error_str.lower() or "endpoint" in error_str.lower():
                return False, "Invalid endpoint URL", None
            else:
                return False, f"Connection failed: {error_str}", None


class NVIDIAProvider(LLMProvider):
    """NVIDIA API Provider using OpenAI client"""
    
    def __init__(self, config: Dict[str, Any], observer=None):
        super().__init__(config, observer)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize NVIDIA API client"""
        try:
            from openai import OpenAI
            
            self.client = OpenAI(
                base_url=self.config.get("base_url", "https://integrate.api.nvidia.com/v1"),
                api_key=self.config.get("api_key")
            )
            
            if self.observer:
                self.observer.log("INFO", "NVIDIA client initialized successfully")
        except Exception as e:
            if self.observer:
                self.observer.log("ERROR", f"Failed to initialize NVIDIA client: {str(e)}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from NVIDIA API"""
        start_time = time.time()

        try:
            if self.observer:
                self.observer.trace_call("NVIDIA", prompt)

            model = kwargs.get("model", self.config.get("model", "nvidia/nemotron-3-nano-30b-a3b"))
            temperature = kwargs.get("temperature", 1.0)
            top_p = kwargs.get("top_p", 1.0)
            max_tokens = kwargs.get("max_tokens", self.config.get("max_tokens", 16384))
            streaming = kwargs.get("streaming", self.config.get("streaming", True))

            # Prepare extra_body for NVIDIA-specific features
            extra_body = {}
            if self.config.get("reasoning_budget"):
                extra_body["reasoning_budget"] = self.config.get("reasoning_budget", 16384)
            if self.config.get("enable_thinking"):
                extra_body["chat_template_kwargs"] = {"enable_thinking": True}

            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"content": prompt, "role": "user"}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                extra_body=extra_body if extra_body else None,
                stream=streaming
            )

            # Handle streaming response
            full_response = ""
            reasoning_content = ""

            if streaming:
                for chunk in completion:
                    # Capture reasoning content if available
                    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                    if reasoning:
                        reasoning_content += reasoning

                    # Capture regular content
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
            else:
                full_response = completion.choices[0].message.content

            latency = time.time() - start_time
            result = {
                "text": full_response,
                "reasoning": reasoning_content if reasoning_content else None,
                "model": model,
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "provider": "nvidia"
            }

            if self.observer:
                self.observer.trace_response("NVIDIA", result)

            self._record_metrics(latency)

            return result

        except Exception as e:
            latency = time.time() - start_time
            self.metrics["errors"] += 1

            if self.observer:
                self.observer.log("ERROR", f"NVIDIA generation failed: {str(e)}")

            return {
                "text": "",
                "error": str(e),
                "latency": latency,
                "timestamp": datetime.now().isoformat(),
                "provider": "nvidia"
            }

    def test_connection(self) -> Tuple[bool, str, Optional[str]]:
        """Test connection with simple 'hi' message"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "nvidia/nemotron-3-nano-30b-a3b"),
                messages=[{"content": "hi", "role": "user"}],
                max_tokens=50,
                stream=False
            )

            response_text = response.choices[0].message.content
            return True, "Connection successful", response_text
        except Exception as e:
            error_str = str(e)
            if "401" in error_str:
                return False, "Authentication failed: Invalid API key", None
            elif "403" in error_str:
                return False, "Access forbidden: Check API key permissions", None
            else:
                return False, f"Connection failed: {error_str}", None


class LLMProviderFactory:
    """Factory to create LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any], observer=None) -> LLMProvider:
        """Create an LLM provider based on type"""
        providers = {
            "nvidia": NVIDIAProvider,
            "gemini": GeminiProvider,
            "azure_openai": AzureOpenAIProvider
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return providers[provider_type](config, observer)
