"""AI Provider Factory Module"""
from enum import Enum

from app.ia_provider.base_provider import BaseAIProvider

from ..config.logging_config import get_logger
from ..ia_provider import (
    AzureProvider,
    BaseAIProvider,
    GitHubProvider,
    OllamaProvider,
    OpenAIProvider,
    StubProvider,
)

# Get module logger
logger = get_logger(__name__)

class AIProvider(str, Enum):
    """Available AI providers."""
    OPENAI = "openai"
    AZURE = "azure"
    OLLAMA = "ollama"
    GITHUB = "github"
    STUB = "stub"

    @staticmethod
    def create_provider(provider_name: str) -> BaseAIProvider:
        """Create AI provider based on configuration."""
        provider_map = {
            AIProvider.OPENAI: OpenAIProvider,
            AIProvider.AZURE: AzureProvider,
            AIProvider.OLLAMA: OllamaProvider,
            AIProvider.GITHUB: GitHubProvider,
            AIProvider.STUB: StubProvider,
        }
        
        if provider_name not in provider_map:
            raise ValueError(f"Unknown AI provider: {provider_name}")
        
        try:
            return provider_map[provider_name]()
        except Exception as e:
            print(f"[AIProvider] Error initializing {provider_name} provider: {e}")
            raise