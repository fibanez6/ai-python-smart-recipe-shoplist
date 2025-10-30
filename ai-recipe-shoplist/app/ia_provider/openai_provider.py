"""OpenAI GPT provider implementation."""

from ..config.logging_config import get_logger
from ..config.pydantic_config import OPENAI_SETTINGS
from ..utils.retry_utils import AIRetryConfig, create_ai_retry_config
from .base_provider import BaseAIProvider

try:
    import openai
except ImportError:
    openai = None

# Get module logger
logger = get_logger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider with tenacity-based retry logic."""

    __slots__ = ("_client", "_retry_config")
    
    def __init__(self):
        super().__init__()
        
        if not openai:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        if not OPENAI_SETTINGS.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Initialize OpenAI Async Client
        self._client = openai.AsyncOpenAI(api_key=OPENAI_SETTINGS.api_key)
        self._retry_config = create_ai_retry_config(self.name)
        
        # Mask token for logging
        api_key = OPENAI_SETTINGS.api_key
        self._masked_api_key= f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        logger.info(f"OpenAI provider initialized - Model: {self.model}, Api key: {self._masked_api_key}")

    @property
    def name(self) -> str:
        return "OPENAI"

    @property
    def model(self) -> str:
        return OPENAI_SETTINGS.model

    @property
    def max_tokens(self) -> int:
        return OPENAI_SETTINGS.max_tokens

    @property
    def temperature(self) -> float:
        return OPENAI_SETTINGS.temperature

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config
    
    def __repr__(self) -> str:
        return f"<OpenAIProvider(model={OPENAI_SETTINGS.model}, api_key: {self._masked_api_key} )>"