"""
String utility functions for text processing.
"""

import re
from typing import Any

def count_chars(text: str) -> int:
    """Return the number of characters in the given text."""
    return len(text)

def count_words(text: str) -> int:
    """Return the number of words in the given text."""
    return len(re.findall(r'\w+', text))

def count_lines(text: str) -> int:
    """Return the number of lines in the given text."""
    if not text:
        return 0
    return text.count('\n') + 1

def object_to_str(obj: Any) -> str:
    """Convert an object to a string representation for hashing."""
    if hasattr(obj, 'model_dump_json'):
        return obj.model_dump_json()
    elif hasattr(obj, 'json'):
        return obj.json()
    elif hasattr(obj, '__dict__'):
        return str(obj.__dict__)
    else:
        return str(obj)
    