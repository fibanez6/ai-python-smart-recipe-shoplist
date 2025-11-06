"""
Modern configuration management using Pydantic Settings.

This module provides type-safe, validated configuration with automatic
environment variable loading and .env file support.
"""
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings
from typing_extensions import Literal, get_args


class WebFetcherSettings(BaseSettings):
    """Web fetcher configuration settings."""
    
    timeout: int = Field(default=30, description="Request timeout in seconds")
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; AI-Recipe-Crawler/1.0; +https://github.com/your-repo)",
        description="User agent string for requests"
    )
    
    model_config = ConfigDict(env_prefix="FETCHER_")

class WebScraperSettings(BaseSettings):
    """Web scraper configuration settings."""
    html_to_text: bool = Field(default=False, description="Convert HTML content to text after extraction")

    model_config = ConfigDict(env_prefix="WEB_SCRAPER_")


class AIProviderSettings(BaseSettings):
    """AI provider configuration settings."""

    provider: Literal["openai", "azure", "ollama", "github", "stub"] = Field(
        default="openai", description="AI provider to use"
    )
    provider_chat_enabled: bool = Field(default=True, description="Enable or disable AI provider chat")
    
    model_config = ConfigDict(env_prefix="")

class OpenAISettings(BaseSettings):
    """OpenAI configuration settings."""
    
    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    max_tokens: int = Field(default=2000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for responses")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum number of retries")
    base_delay: float = Field(default=1.0, description="Base delay between retries")
    max_delay: float = Field(default=60.0, description="Maximum delay between retries")
    rpm_limit: int = Field(default=500, description="Requests per minute limit")
    
    model_config = ConfigDict(env_prefix="OPENAI_")

class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI configuration settings."""
    
    api_key: str = Field(default="", description="Azure OpenAI API key")
    endpoint: str = Field(default="", description="Azure OpenAI endpoint")
    api_version: str = Field(default="2024-02-15-preview", description="Azure OpenAI API version")
    deployment_name: str = Field(default="", description="Azure OpenAI deployment name")
    max_tokens: int = Field(default=2000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for responses")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum number of retries")
    base_delay: float = Field(default=1.0, description="Base delay between retries")
    max_delay: float = Field(default=60.0, description="Maximum delay between retries")
    rpm_limit: int = Field(default=500, description="Requests per minute limit")
    
    model_config = ConfigDict(env_prefix="AZURE_OPENAI_")

class OllamaSettings(BaseSettings):
    """Ollama configuration settings."""
    
    host: str = Field(default="http://localhost:11434", description="Ollama host URL")
    model: str = Field(default="llama3.1", description="Ollama model to use")
    max_tokens: int = Field(default=2000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for responses")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum number of retries")
    base_delay: float = Field(default=1.0, description="Base delay between retries")
    max_delay: float = Field(default=60.0, description="Maximum delay between retries")
    rpm_limit: int = Field(default=60, description="Requests per minute limit")
    
    model_config = ConfigDict(env_prefix="OLLAMA_")

class GitHubSettings(BaseSettings):
    """GitHub Models configuration settings."""
    
    token: str = Field(default="", description="GitHub token")
    model: str = Field(default="gpt-4o-mini", description="GitHub model to use")
    api_url: str = Field(default="https://models.inference.ai.azure.com", description="GitHub API URL")
    max_tokens: int = Field(default=4000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for responses")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum number of retries")
    base_delay: float = Field(default=1.0, description="Base delay between retries")
    max_delay: float = Field(default=60.0, description="Maximum delay between retries")
    rpm_limit: int = Field(default=15, description="Requests per minute limit")
    
    model_config = ConfigDict(env_prefix="GITHUB_")

class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    level: str = Field(default="INFO", description="Log level")
    debug_enabled: bool = Field(default=False, description="Enable debug mode")
    file_enabled: bool = Field(default=True, description="Enable file logging")
    file_path: str = Field(default="logs/app.log", description="Log file path")
    max_size: int = Field(default=10485760, description="Maximum log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files to keep")
    max_length: int = Field(default=500, description="Maximum length in characters (0 = no limit)")
    chat_message_max_length: int = Field(default=500, description="Maximum length of chat messages to log (0 = no limit)")
    chat_message_single_line: bool = Field(default=False, description="Log chat messages in a single line")
    chat_full_responses: bool = Field(default=False, description="Log full chat responses")
    format_string: str | None = Field(default=None, description="Log format string")
    
    model_config = ConfigDict(env_prefix="LOG_")

class ServerSettings(BaseSettings):
    """Server configuration settings."""
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    model_config = ConfigDict(env_prefix="SERVER_")

class RetrySettings(BaseSettings):
    """Global retry configuration settings."""
    
    max_attempts: int = Field(default=3, description="Maximum retry attempts")
    base_delay: float = Field(default=1.0, description="Base delay between retries")
    max_delay: float = Field(default=60.0, description="Maximum delay between retries")
    multiplier: float = Field(default=2.0, description="Delay multiplier")
    rpm_limit: int = Field(default=15, description="Requests per minute limit")
    
    model_config = ConfigDict(env_prefix="RETRY_")

class MockSettings(BaseSettings):
    """Mock/stub configuration settings."""
    
    use_mock_ai_responses: bool = Field(default=False, description="Use mock AI responses")
    
    model_config = ConfigDict(env_prefix="")

class TiktokenSettings(BaseSettings):
    """tiktoken configuration settings."""

    model: str | None = Field(default=None, description="AI provider to use")
    encoder: str = Field(default="o200k_base", description="AI provider to use")

    model_config = ConfigDict(env_prefix="TIKTOKEN_")

class StorageSettings(BaseSettings):
    """Storage configuration settings."""

    base_path: Path = Field(default=Path("tmp/web_cache"), description="Temporary folder for caching")
    enabled: bool = Field(default=True, description="Enable storage to disk")

    model_config = ConfigDict(env_prefix="STORAGE_")

class CacheSettings(BaseSettings):
    """Cache configuration settings."""

    enabled: bool = Field(default=True, description="Enable caching")
    ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour)")
    max_size: int = Field(default=10485760, description="Maximum cache size in bytes (10MB)")
    ai_ttl: int = Field(default=300, description="AI response cache TTL in seconds (5 minutes)")

    model_config = ConfigDict(env_prefix="CACHE_")

class AppSettings(BaseSettings):
    """Main application settings that combines all configuration sections."""
    
    # Configuration sections
    web_fetcher: WebFetcherSettings = Field(default_factory=WebFetcherSettings)
    web_scraper: WebScraperSettings = Field(default_factory=WebScraperSettings)
    ai_provider: AIProviderSettings = Field(default_factory=AIProviderSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    azure: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    retry: RetrySettings = Field(default_factory=RetrySettings)
    mock: MockSettings = Field(default_factory=MockSettings)
    tiktoken: TiktokenSettings = Field(default_factory=TiktokenSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)

    @field_validator('web_fetcher', 'web_scraper', 'ai_provider', 'openai', 'azure', 
                     'ollama', 'github', 'logging', 'server', 'retry', 'mock', 'tiktoken', 
                     'storage', 'cache', mode='before')
    @classmethod
    def ensure_settings_instances(cls, v, info):
        """Ensure all settings are properly instantiated."""
        field_name = info.field_name
        field_type = cls.model_fields[field_name].annotation
        
        if isinstance(v, dict):
            return field_type(**v)
        return v if v is not None else field_type()
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore",
    )
    
    def validate_required_config(self) -> list[str]:
        """Validate that required configuration values are set."""
        missing = []
        
        # Check AI provider configuration
        if self.ai_provider.provider == "openai" and not self.openai.api_key:
            missing.append("OPENAI_API_KEY")
        elif self.ai_provider.provider == "azure" and (not self.azure.api_key or not self.azure.endpoint):
            missing.extend([k for k in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"] 
                           if not getattr(self.azure, k.lower().replace("azure_openai_", ""))])
        elif self.ai_provider.provider == "github" and not self.github.token:
            missing.append("GITHUB_TOKEN")
        
        return missing
    
    def get_config_summary(self) -> dict:
        """Get a summary of all configuration with sensitive data masked."""
        
        def mask_sensitive(key: str, value: any) -> any:
            """Mask sensitive configuration values."""
            sensitive_keys = ['key', 'token', 'secret', 'password']
            # Skip max_tokens and similar non-sensitive keys
            if key.lower() in ['max_tokens', 'max_token']:
                return value
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 0:
                    return f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                return "***"
            return value
        
        def filter_ai_providers(section: str) -> dict:
            """Show effective AI provider configuration."""
            # ai_provider_keys = ["openai", "azure", "ollama", "github", "stub"]
            ai_provider_keys = list(get_args(AIProviderSettings.model_fields["provider"].annotation))
            if section in ai_provider_keys:
                if section == self.ai_provider.provider:
                    return {section: self.ai_provider.provider}
                else:
                    return {}
            return {section: self.ai_provider.provider}
        
        summary = {}
        for section_name, section in self.__dict__.items():
            if hasattr(section, '__dict__'):
                summary[section_name] = {
                    key: mask_sensitive(key, value) 
                    for key, value in section.__dict__.items()
                    if not key.startswith('_') and filter_ai_providers(section_name)
                }
        
        return summary


# Global settings instance
settings = AppSettings()

SERVER_SETTINGS = settings.server

FETCHER_SETTINGS = settings.web_fetcher
WEB_SCRAPER_SETTINGS = settings.web_scraper
STORAGE_SETTINGS = settings.storage
CACHE_SETTINGS = settings.cache

LOG_SETTINGS = settings.logging

# AI provider settings
AI_SERVICE_SETTINGS = settings.ai_provider

TIKTOKEN_SETTINGS = settings.tiktoken

GITHUB_SETTINGS = settings.github
AZURE_SETTINGS = settings.azure
OLLAMA_SETTINGS = settings.ollama
OPENAI_SETTINGS = settings.openai

USE_MOCK_AI_RESPONSES = settings.mock.use_mock_ai_responses

# Retry settings
RETRY_SETTINGS = settings.retry

# Utility functions for backward compatibility
def get_config_summary() -> dict:
    """Get a summary of all loaded configuration values (without sensitive data)."""
    return settings.get_config_summary()


def validate_required_config() -> list:
    """Validate that required configuration values are set. Returns list of missing keys."""
    return settings.validate_required_config()