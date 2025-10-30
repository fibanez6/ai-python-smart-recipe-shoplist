"""Ollama local LLM provider implementation."""

from ..config.logging_config import get_logger
from ..config.pydantic_config import OLLAMA_SETTINGS
from ..utils.retry_utils import (
    AIRetryConfig,
    NetworkError,
    create_ai_retry_config,
    with_ai_retry,
)
from .base_provider import BaseAIProvider

# Ollama imports
try:
    import ollama
except ImportError:
    ollama = None

# Get module logger
logger = get_logger(__name__)

class OllamaProvider(BaseAIProvider):
    """Ollama local LLM provider with tenacity-based retry logic."""
    
    def __init__(self):
        super().__init__()

        if not ollama:
            raise ImportError("Ollama library not installed. Run: pip install ollama")
        
        logger.debug(f"[{self.name}] Initializing Ollama Models provider...")
        
        try:
            self._client = ollama.AsyncClient(host=OLLAMA_SETTINGS.host)
            self._client.list()
            self._retry_config = create_ai_retry_config(self.name, requests_per_minute=0)  # 0 = no rate limiting

            logger.info(f"[{self.name}] Provider initialized - Model: {OLLAMA_SETTINGS.model}, Host: {OLLAMA_SETTINGS.host}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama at {OLLAMA_SETTINGS.host}: {e}")

    async def complete_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Complete a chat conversation using Ollama with tenacity retry logic."""
        
        @with_ai_retry(self.retry_config)
        async def make_ollama_request():
            try:
                # Format prompt for Ollama
                prompt = ""
                for msg in messages:
                    if msg["role"] == "system":
                        prompt += f"System: {msg['content']}\n\n"
                    elif msg["role"] == "user":
                        prompt += f"Human: {msg['content']}\n\n"
                prompt += "Assistant: "
                
                response = await self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        "temperature": kwargs.get("temperature", self.temperature),
                        "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    }
                )
                return response['response']
            except Exception as e:
                # Convert connection errors to our retry framework
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["connection", "timeout", "network"]):
                    raise NetworkError(f"Ollama connection error: {e}")
                else:
                    raise  # Let tenacity decide if it's retryable
        
        try:
            return await make_ollama_request()
        except Exception as e:
            logger.error(f"[{self.name}] API error: {e}")
            raise

    @property
    def name(self) -> str:
        return "OLLAMA"
    
    @property
    def model(self) -> str:
        return OLLAMA_SETTINGS.model

    @property
    def max_tokens(self) -> int:
        return OLLAMA_SETTINGS.max_tokens

    @property
    def temperature(self) -> float:
        return OLLAMA_SETTINGS.temperature

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config
    
    def __repr__(self) -> str:
        return f"<OllamaProvider(model={OLLAMA_SETTINGS.model}, host={OLLAMA_SETTINGS.host})>"