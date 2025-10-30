"""GitHub Models provider implementation."""

from ..config.logging_config import get_logger
from ..config.pydantic_config import GITHUB_SETTINGS
from ..utils.retry_utils import AIRetryConfig, create_ai_retry_config
from .base_provider import BaseAIProvider

try:
    import openai
except ImportError:
    openai = None

# Get module logger
logger = get_logger(__name__)

class GitHubProvider(BaseAIProvider):
    """GitHub Models provider with tenacity-based retry logic."""

    __slots__ = ("_client", "_retry_config")
    
    def __init__(self):
        super().__init__()

        if not openai:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

        if not GITHUB_SETTINGS.token or not GITHUB_SETTINGS.api_url:
            raise ValueError("GITHUB_TOKEN and GITHUB_API_URL environment variables must be set")

        logger.debug(f"[{self.name}] Initializing GitHub Models provider...")

        # Initialize OpenAI Async Client for GitHub Models
        self._client = openai.AsyncOpenAI(base_url=GITHUB_SETTINGS.api_url, api_key=GITHUB_SETTINGS.token)
        self._retry_config = create_ai_retry_config(self.name)

        # Mask token for logging
        self._masked_token = f"{GITHUB_SETTINGS.token[:8]}...{GITHUB_SETTINGS.token[-4:]}" if len(GITHUB_SETTINGS.token) > 12 else "***"
        logger.info(f"[{self.name}] Provider initialized - Model: {GITHUB_SETTINGS.model}, API URL: {GITHUB_SETTINGS.api_url}, Token: {self._masked_token}")

    @property
    def name(self) -> str:
        return "GITHUB"
    
    @property
    def model(self) -> str:
        return GITHUB_SETTINGS.model
    
    @property
    def max_tokens(self) -> int:
        return GITHUB_SETTINGS.max_tokens

    @property
    def temperature(self) -> float:
        return GITHUB_SETTINGS.temperature

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config
    
    def __repr__(self) -> str:
        return f"<GitHubProvider(model={GITHUB_SETTINGS.model}, base_url={GITHUB_SETTINGS.api_url}, token={self._masked_token})>"