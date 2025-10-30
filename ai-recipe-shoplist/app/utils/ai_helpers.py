"""
AI utility functions for response processing and data handling.
"""

import json
import logging
import re
from typing import Any, Union

from ..config.pydantic_config import LOG_SETTINGS
from ..services.tokenizer_service import TokenizerService  # Import TokenizerService
from ..utils.str_helpers import count_chars, count_lines, count_words

# Get module logger
logger = logging.getLogger(__name__)


def clean_json_response(response: str) -> str:
    """
    Clean AI response by removing markdown code block markers and extra text.
    
    Args:
        response: Raw AI response that may contain markdown markers
        
    Returns:
        Cleaned JSON string ready for parsing
        
    Examples:
        >>> clean_json_response('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
        
        >>> clean_json_response('Here is the data: {"key": "value"}')
        '{"key": "value"}'
    """
    if not response:
        return response
    
    # Remove markdown code block markers
    if response.startswith('```json'):
        response = response[7:]  # Remove ```json
    elif response.startswith('```'):
        response = response[3:]   # Remove ```
    
    if response.endswith('```'):
        response = response[:-3]  # Remove trailing ```
    
    # Strip whitespace
    response = response.strip()
    
    # If response still doesn't start with { or [, try to find JSON
    if not response.startswith(('{', '[')):
        # Look for JSON starting with { or [
        json_start = -1
        for i, char in enumerate(response):
            if char in ('{', '['):
                json_start = i
                break
        
        if json_start >= 0:
            response = response[json_start:]
    
    return response


def safe_json_parse(response: str, fallback: Any = None) -> Any:
    """
    Safely parse JSON response with automatic cleaning and fallback.
    
    Args:
        response: Raw AI response
        fallback: Value to return if parsing fails
        
    Returns:
        Parsed JSON object or fallback value
    """
    try:
        # Check if response looks like an error message
        if not response or isinstance(response, str) and (
            response.startswith(("Internal", "Error", "HTTP", "500", "429", "503")) or
            "error" in response.lower() or
            "exception" in response.lower() or
            len(response.strip()) < 2
        ):
            logger.warning(f"AI response appears to be an error: {response[:100]}...")
            return fallback
            
        cleaned_response = clean_json_response(response)
        
        # Double-check that we have something that looks like JSON
        if not cleaned_response or not cleaned_response.strip().startswith(('{', '[')):
            logger.warning(f"Response doesn't appear to be JSON: {cleaned_response[:100]}...")
            return fallback
            
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"JSON parsing failed: {e}. Response: {response[:200]}...")
        return fallback


def extract_json_from_text(text: str) -> Union[dict, list, None]:
    """
    Extract the first valid JSON object or array from text.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        First valid JSON object/array found, or None
    """
    # Try to find JSON objects {...} or arrays [...]
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple object pattern
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',  # Simple array pattern
    ]
    
    for pattern in json_patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            try:
                candidate = match.group(0)
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    
    return None


def normalize_ai_response(response: str, expected_type: str = "auto") -> Any:
    """
    Normalize AI response to expected format.
    
    Args:
        response: Raw AI response
        expected_type: Expected response type ("object", "array", "string", "auto")
        
    Returns:
        Normalized response
    """
    if not response:
        return None
    
    # Try JSON parsing first
    json_result = safe_json_parse(response)
    if json_result is not None:
        return json_result
    
    # If JSON parsing fails, try extraction
    extracted = extract_json_from_text(response)
    if extracted is not None:
        return extracted
    
    # If expected type is string, return cleaned text
    if expected_type == "string":
        return clean_json_response(response)
    
    # Return None if nothing worked
    return None

def format_ai_prompt(template: str, **kwargs) -> str:
    """
    Format AI prompt template with parameters.
    
    Args:
        template: Prompt template with {placeholders}
        **kwargs: Values to substitute in template
        
    Returns:
        Formatted prompt string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required template parameter: {e}")


def log_ai_chat_query(provider_name: str, chat_params: list[dict[str, str]], logger: logging.Logger, level: int = logging.DEBUG) -> None:
    """
    Log AI chat parameters statistics.
    
    Args:
        provider_name: Name of the AI provider
        messages: List of chat messages
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
    """
    if logger.isEnabledFor(level):
        # Log chat parameters except messages
        params_copy = {k: v for k, v in chat_params.items() if k != 'messages'}
        if params_copy:
            logger.debug(f"[{provider_name}] API call - chat params: {params_copy}")

        # Log each message
        for i, msg in enumerate(chat_params.get('messages', [])):
            max_length = LOG_SETTINGS.chat_message_max_length
            if max_length == 0:
                content = msg.get('content', '')
            else:
                content = msg.get('content', '')[:max_length] + '...' if len(msg.get('content', '')) > max_length else msg.get('content', '')

            if LOG_SETTINGS.chat_message_single_line:
                content = content.replace(chr(10), ' ')  # replace newlines with spaces for single line logging

            logger.debug(f"[{provider_name}] Message {i+1} ({msg.get('role', 'unknown')}): \n\"\"\"\n{content}\n\"\"\"")

def log_ai_chat_response(provider_name: str, response: str, logger: logging.Logger, level: int = logging.DEBUG) -> None:
    """
    Log AI response at specified log level.
    
    Args:
        response: AI response string
        provider_name: Name of the AI provider
        logger: Logger instance
        level: Logging level (e.g., logging.DEBUG)
    """
    usage = response.usage
    stats = {
            "Prompt tokens:": usage.prompt_tokens,
            "Completion tokens:": usage.completion_tokens,
            "Total tokens:": usage.total_tokens
        }

    logger.info(f"[{provider_name}] OpenAI API call stats: {stats} ")

    if logger.isEnabledFor(level):
        try:
            message = response.choices[0].message
            if hasattr(message, 'refusal') and message.refusal:
                logger.log(level, f"[{provider_name}] AI Response refused: {message.refusal}")
                return
            elif hasattr(message, 'parsed') and message.parsed:
                parsed = message.parsed.model_dump_json(indent=2)
                logger.debug((f"[{provider_name}] AI Response parsed:", parsed))
                return
            else:
                content = message.content if hasattr(message, 'content') else message
                max_length = LOG_SETTINGS.chat_message_max_length
                if  max_length > 0:
                    content = content[:max_length] + ('...' if len(content) > max_length else '')
                
                logger.log(level, f"[{provider_name}] AI Response:\n\"\"\"\n{content}\n\"\"\"")
        except Exception as e:
            logger.error(f"[{provider_name}] Error logging AI response: {e}")

    if LOG_SETTINGS.chat_full_responses:
        try:
            logger.log(level, f"[{provider_name}] Full AI Response:\n\"\"\"\n{response}\n\"\"\"")
        except Exception as e:
            logger.error(f"[{provider_name}] Error logging full AI response: {e}")



# Common prompt templates


PRODUCT_MATCHING_SYSTEM = "You are a grocery shopping expert. Rank products by relevance and quality."

PRODUCT_MATCHING_PROMPT = """
Rank these grocery products by how well they match the ingredient "{ingredient}".
Consider:
1. Name similarity and relevance
2. Brand quality
3. Value for money (price vs size)
4. Organic/premium options

Products:
{products_json}

Return the products array sorted by match quality (best first).
Include a "match_score" field (0-100) for each product.
Return only valid JSON.
"""

ALTERNATIVES_PROMPT = """
Suggest 3-5 alternative ingredients for "{ingredient}" that could be used in cooking.
Consider:
- Similar taste profile
- Similar cooking properties
- Availability in grocery stores
- Dietary restrictions (if any)

Return as a JSON array of strings, no additional text.
"""

RECIPE_SHOPPING_ASSISTANT_SYSTEM =  """
Simulate real-world shopping assistant. that does the following steps:
- Reads recipes online — extracts the list of ingredients and quantities
- Creates a unified shopping list — merging duplicate ingredients and standardizing units.
- Searches Coles, Woolworths and Aldi (Australia's three main grocery chains) to:
-- Find each ingredient, with quantity and unit.
-- Maximize savings by finding the best prices for each ingredient.
-- Suggest the best store (or a mixed basket for cheapest total).
"""

RECIPE_SHOPPING_ASSISTANT_PROMPT = """
Given me a recipe URL "{url}", extract ingredients and find current prices from Coles and Woolworths (using real web data).
"""