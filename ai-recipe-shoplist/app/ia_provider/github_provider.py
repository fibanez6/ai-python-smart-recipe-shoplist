"""GitHub Models provider implementation."""

from ..config.pydantic_config import (
    GITHUB_TOKEN,
    GITHUB_MODEL,
    GITHUB_API_URL,
    GITHUB_MAX_TOKENS,
    GITHUB_TEMPERATURE,
)
from ..config.logging_config import get_logger
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

        if not GITHUB_TOKEN or not GITHUB_API_URL:
            raise ValueError("GITHUB_TOKEN and GITHUB_API_URL environment variables must be set")

        logger.debug(f"[{self.name}] Initializing GitHub Models provider...")

        # Initialize OpenAI Async Client for GitHub Models
        self._client = openai.AsyncOpenAI(base_url=GITHUB_API_URL, api_key=GITHUB_TOKEN)
        self._retry_config = create_ai_retry_config(self.name)

        # Mask token for logging
        self._masked_token = f"{GITHUB_TOKEN[:8]}...{GITHUB_TOKEN[-4:]}" if len(GITHUB_TOKEN) > 12 else "***"
        logger.info(f"[{self.name}] Provider initialized - Model: {GITHUB_MODEL}, API URL: {GITHUB_API_URL}, Token: {self._masked_token}")

    @property
    def name(self) -> str:
        return "GITHUB"
    
    @property
    def model(self) -> str:
        return GITHUB_MODEL
    
    @property
    def max_tokens(self) -> int:
        return GITHUB_MAX_TOKENS

    @property
    def temperature(self) -> float:
        return GITHUB_TEMPERATURE

    @property
    def client(self) -> any:
        return self._client
    
    @property
    def retry_config(self) -> AIRetryConfig:
        return self._retry_config
    
    def __repr__(self) -> str:
        return f"<GitHubProvider(model={GITHUB_MODEL}, base_url={GITHUB_API_URL}, token={self._masked_token})>"