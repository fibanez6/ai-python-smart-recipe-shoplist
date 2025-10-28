"""Base AI provider abstract class and common utilities."""

from dataclasses import dataclass
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import rich

from ..config.logging_config import get_logger
from ..utils.ai_helpers import (
    PRODUCT_MATCHING_PROMPT,
    PRODUCT_MATCHING_SYSTEM,
    RECIPE_EXTRACTION_PROMPT,
    RECIPE_EXTRACTION_SYSTEM,
    format_ai_prompt,
    log_ai_response,
    safe_json_parse,
)
from ..utils.str_helpers import (
    count_chars,
    count_words,
    count_lines,
)
from ..models import Recipe

# Get module logger
logger = get_logger(__name__)

from ..utils.retry_utils import (
    AIRetryConfig,
    NetworkError,
    RateLimitError,
    ServerError,
    with_ai_retry,
)

from ..config.pydantic_config import AI_PROVIDER_CHAT_ENABLED  # Import the new config variable

from ..services.tokenizer_service import TokenizerService  # Import TokenizerService

@dataclass
class ChatMessageResult:
    content: str
    parsed: Any = None
    refusal: Any = None

class BaseAIProvider(ABC):
    """Complete a chat conversation using AI Models with tenacity retry logic."""

    def __init__(self):
        self.tokenizer = TokenizerService()

    @property
    @abstractmethod
    def name(self) -> str:
        """Each child must define a name"""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Each child must define a model"""
        pass

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Each child must define a max_tokens"""
        pass

    @property
    @abstractmethod
    def temperature(self) -> float:
        """Each child must define a temperature"""
        pass

    @property
    @abstractmethod
    def retry_config(self) -> AIRetryConfig:
        """Each child must define a retry configuration"""
        pass

    def truncate_to_max_tokens(self, text: str) -> str:
        """Truncate text to fit within the provider's max token limit."""

        if logger.isEnabledFor(logging.DEBUG):
            stats = {
                "chars": count_chars(text),
                "words": count_words(text),
                "lines": count_lines(text),
                "tokens": self.tokenizer.count_tokens(text)
            }
            logger.debug(f"[{self.name}] Stats text content before truncation: {stats}")

        truncated = self.tokenizer.truncate_to_token_limit(text, self.max_tokens)

        if logger.isEnabledFor(logging.DEBUG):
            stats = {
                "chars": count_chars(truncated),
                "words": count_words(truncated),
                "lines": count_lines(truncated),
                "tokens": self.tokenizer.count_tokens(truncated)
            }
            logger.debug(f"[{self.name}] Stats text content after truncation: {stats}")

        return truncated

    async def complete_chat(self, params: any, **kwargs) -> ChatMessageResult:
        """Complete a chat conversation."""

        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        messages = params.get('messages') or []

        logger.debug(f"[{self.name}] API call - Model: {self.model}, Messages: {len(messages)}, Max tokens: {max_tokens}, Temperature: {temperature}")

        # Log messages in debug mode (truncate for readability)
        if logger.isEnabledFor(logging.DEBUG):
            for i, msg in enumerate(messages):
                content = msg.get('content', '')[:200] + '...' if len(msg.get('content', '')) > 200 else msg.get('content', '')
                content = content.replace(chr(10), '; ') # replace newlines for cleaner logging
                logger.debug(f"[{self.name}] Message {i+1} ({msg.get('role', 'unknown')}): {content}")

        @with_ai_retry(self.retry_config)
        async def chat_completion_request():            
            try:
                chat_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **params
                }

                if "response_format" in chat_params:
                    response = await self.client.chat.completions.parse(**chat_params)
                else:
                    response = await self.client.chat.completions.create(**chat_params)

                logger.info(f"[{self.name}] OpenAI API call stats: {response.usage} ")

                message = response.choices[0].message

                log_ai_response(self.name, message, logger, level=logging.DEBUG)

                return ChatMessageResult(
                    content=message.content or None,
                    parsed=getattr(message, "parsed", None),
                    refusal=getattr(message, "refusal", None)
                )
            except Exception as e:
                # Convert provider-specific errors to our retry framework
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    raise RateLimitError(f"{self.name} rate limit: {e}")
                elif any(keyword in error_str for keyword in ["server", "503", "502", "500"]):
                    raise ServerError(f"{self.name} server error: {e}")
                elif any(keyword in error_str for keyword in ["timeout", "connection"]):
                    raise NetworkError(f"{self.name} network error: {e}")
                else:
                    raise  # Let tenacity decide if it's retryable

        if not AI_PROVIDER_CHAT_ENABLED:
            logger.info(f"[{self.name}] AI provider chat calls are disabled. Skipping API call.")
            return ChatMessageResult(
                content="",
                parsed=None,
                refusal="AI provider chat calls are disabled."
            )
        else:
            try:
                return await chat_completion_request()
            except Exception as e:
                logger.error(f"[{self.name}] OpenAI API error: {e}")
                raise

    async def extract_recipe_data(self, html_content: str, url: str) -> Recipe:
        """Extract structured recipe data from HTML using AI."""

        logger.info(f"[{self.name}] Extracting recipe data from URL: {url}")

        # Truncate HTML if too long
        html_content = self.truncate_to_max_tokens(html_content)

        # Set system message
        system = RECIPE_EXTRACTION_SYSTEM

        # Use centralized prompt template
        prompt = format_ai_prompt(RECIPE_EXTRACTION_PROMPT, html_content=html_content)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[{self.name}] System message: {system}")
            logger.debug(f"[{self.name}] User message: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "response_format": Recipe
        }
        
        try:
            message = await self.complete_chat(chat_params)
            return message.parsed if message.parsed else Recipe.default()
        except Exception as e:
            logger.error(f"[{self.name}] Error in extract_recipe_data: {e}")
            # Only log response if it was defined
            try:
                logger.debug(f"[{self.name}] Raw response that failed to parse: {response[:500]}...")
            except NameError:
                logger.debug(f"[{self.name}] No response received due to earlier error")
            
            # Return minimal structure if parsing fails
            return Recipe.default()
    
    async def match_products(self, ingredient: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match and rank products for an ingredient using AI."""

        logger.info(f"[{self.name}] Matching products for ingredient")

        if not products:
            return []
        
        # Set system message
        system = PRODUCT_MATCHING_SYSTEM
        
        # Use centralized prompt template
        prompt = format_ai_prompt(
            PRODUCT_MATCHING_PROMPT,
            ingredient=ingredient,
            products_json=json.dumps(products, indent=2)
        )

        logger.debug(f"[{self.name}] System message: {system}")
        logger.debug(f"[{self.name}] User message: {prompt}")

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = await self.complete_chat(chat_params)
            response = response.content

            # Use centralized JSON parsing
            ranked_products = safe_json_parse(response, fallback=products)
            return ranked_products if isinstance(ranked_products, list) else products
        except Exception as e:
            logger.error(f"[{self.name}] Error ranking products: {e}")
            # Only log response if it was defined
            try:
                logger.debug(f"[{self.name}] Raw response that failed to parse: {response[:500]}...")
            except NameError:
                logger.debug(f"[{self.name}] No response received due to earlier error")
            # Fallback: return original products with default scores
            for i, product in enumerate(products):
                product["match_score"] = 100 - (i * 10)  # Simple scoring
            return products
        
    async def close(self):
        await self._client.aclose()