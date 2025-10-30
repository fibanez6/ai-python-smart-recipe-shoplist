import logging
from typing import Optional

import tiktoken

from app.utils.str_helpers import count_chars, count_lines, count_words

from ..config.logging_config import get_logger
from ..config.pydantic_config import TIKTOKEN_SETTINGS

# Get module logger
logger = get_logger(__name__)

class TokenizerService:
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the tokenizer service."""

        self.name = "TokenizerService"
        self.model = model_name or TIKTOKEN_SETTINGS.model

        if self.model is None:
            logger.debug(f"[{self.name}] Initializing tokenizer for encoder: {TIKTOKEN_SETTINGS.encoder}")
            self.tokenizer = tiktoken.get_encoding(TIKTOKEN_SETTINGS.encoder)
        else:
            logger.debug(f"[{self.name}] Initializing tokenizer for model: {self.model}")
            self.tokenizer = tiktoken.encoding_for_model(self.model)

        logger.info(f"[{self.name}] Tokenizer initialized for model: {self.model}")

    def get_tokens(self, text: str) -> str:
        """Count the number of tokens in the given text."""

        return self.tokenizer.encode(text)

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""
        
        tokens = self.tokenizer.encode(text)
        return len(tokens)
    
    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within the specified token limit."""

        tokens = self.get_tokens(text)
        num_tokens = len(tokens)

        logger.debug(f"[{self.name}] Counting tokens: {num_tokens} (limit: {max_tokens})")

        self.log_ai_token_stats(text, num_tokens, max_tokens)

        if num_tokens <= max_tokens:
            return text
        
        logger.warning(f"[{self.name}] Text exceeds max token limit ({num_tokens} > {max_tokens}), truncating...")
        truncated_tokens = tokens[:max_tokens]

        self.log_ai_token_stats(text, max_tokens)

        return self.tokenizer.decode(truncated_tokens)

    def log_ai_token_stats(self, text: str, num_tokens: int, max_tokens: int) -> None:
        """
        Log statistics about the given text, including character, word, line, and token counts.

        Args:
            text: The input text to analyze.
            num_tokens: Number of tokens in the text.
            max_tokens: Maximum allowed tokens.
        """
        if logger.isEnabledFor(logging.DEBUG):
            stats = {
                "chars": count_chars(text),
                "words": count_words(text),
                "lines": count_lines(text),
                "tokens": num_tokens,
                "max_tokens": max_tokens
            }
            logger.debug((f"[{self.name}] Content stats:", stats))

    def __repr__(self) -> str:
        return f"<TokenizerService(model={self.model}, encoder={TIKTOKEN_SETTINGS.encoder})>"