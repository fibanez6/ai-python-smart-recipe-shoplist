"""Azure OpenAI provider implementation."""

import azure.identity.aio

from ..config.logging_config import get_logger
from ..config.pydantic_config import AZURE_SETTINGS
from ..utils.retry_utils import AIRetryConfig, create_ai_retry_config
from .base_provider import BaseAIProvider

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

        if not AZURE_SETTINGS.api_key or not AZURE_SETTINGS.endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables must be set")

        logger.debug(f"[{self.name}] Initializing Azure OpenAI provider...")

        self.azure_credential = azure.identity.aio.DefaultAzureCredential()
        self.token_provider = azure.identity.aio.get_bearer_token_provider(
            self.azure_credential, "https://cognitiveservices.azure.com/.default"
        )

        # Initialize OpenAI Async Client for Azure
        self._client = openai.AsyncAzureOpenAI(
            api_key=AZURE_SETTINGS.api_key,
            azure_endpoint=AZURE_SETTINGS.endpoint,
            api_version=AZURE_SETTINGS.api_version
        )
        self._retry_config = create_ai_retry_config(self.name)

        # Mask token for logging
        apikey = AZURE_SETTINGS.api_key
        self._masked_token = f"{apikey[:8]}...{apikey[-4:]}" if len(apikey) > 12 else "***"
        logger.info(f"[{self.name}] Provider initialized - Model: {AZURE_SETTINGS.deployment_name}, API URL: {AZURE_SETTINGS.endpoint}, Token: {self._masked_token}")

    @property
    def name(self) -> str:
        return "AZURE"
    
    @property
    def model(self) -> str:
        return AZURE_SETTINGS.deployment_name

    @property
    def max_tokens(self) -> int:
        return AZURE_SETTINGS.max_tokens

    @property
    def temperature(self) -> float:
        return AZURE_SETTINGS.temperature

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config

    def __repr__(self) -> str:
        return f"<AzureProvider(model={AZURE_SETTINGS.deployment_name}, base_url={AZURE_SETTINGS.endpoint}, token={self._masked_token})>"