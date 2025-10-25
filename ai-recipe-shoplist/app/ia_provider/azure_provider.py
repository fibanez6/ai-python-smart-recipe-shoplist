"""Azure OpenAI provider implementation."""

from ..config.pydantic_config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_MAX_TOKENS,
    AZURE_OPENAI_TEMPERATURE,
)
from ..config.logging_config import get_logger
from ..utils.retry_utils import AIRetryConfig, create_ai_retry_config
from .base_provider import BaseAIProvider
import azure.identity.aio

# Azure OpenAI imports
try:
    import openai
except ImportError:
    openai = None

# Get module logger
logger = get_logger(__name__)

class AzureProvider(BaseAIProvider):
    """Azure OpenAI provider with tenacity-based retry logic."""

    __slots__ = ("_client", "_retry_config")
    
    def __init__(self):
        super().__init__()

        if not openai:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables must be set")

        logger.debug(f"[{self.name}] Initializing Azure OpenAI provider...")

        self.azure_credential = azure.identity.aio.DefaultAzureCredential()
        self.token_provider = azure.identity.aio.get_bearer_token_provider(
            self.azure_credential, "https://cognitiveservices.azure.com/.default"
        )

        # Initialize OpenAI Async Client for Azure
        self._client = openai.AsyncAzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION
        )
        self._retry_config = create_ai_retry_config(self.name)

        # Mask token for logging
        self._masked_token = f"{AZURE_OPENAI_API_KEY[:8]}...{AZURE_OPENAI_API_KEY[-4:]}" if len(AZURE_OPENAI_API_KEY) > 12 else "***"
        logger.info(f"[{self.name}] Provider initialized - Model: {AZURE_OPENAI_DEPLOYMENT_NAME}, API URL: {AZURE_OPENAI_ENDPOINT}, Token: {self._masked_token}")

    @property
    def name(self) -> str:
        return "AZURE"
    
    @property
    def model(self) -> str:
        return AZURE_OPENAI_DEPLOYMENT_NAME
    
    @property
    def max_tokens(self) -> int:
        return AZURE_OPENAI_MAX_TOKENS

    @property
    def temperature(self) -> float:
        return AZURE_OPENAI_TEMPERATURE

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config

    def __repr__(self) -> str:
        return f"<AzureProvider(model={AZURE_OPENAI_DEPLOYMENT_NAME}, base_url={AZURE_OPENAI_ENDPOINT}, token={self._masked_token})>"