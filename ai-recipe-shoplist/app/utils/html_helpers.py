"""
HTML helper functions for the recipe shoplist crawler.
"""
from pathlib import Path
from bs4 import BeautifulSoup, Comment  

from app.config.logging_config import get_logger, setup_logging
from ..config.pydantic_config import (
    FETCHER_CLEANER_HTML_TO_TEXT,
)

def remove_html_scripts_and_styles(soup: BeautifulSoup) -> None:
    """Remove script and style elements from the BeautifulSoup object."""
    for element in soup(["window", "script", "noscript", "style", "nav", "header", "footer", "aside", "svg", "link", "meta"]):
        element.decompose()

def remove_html_comments(soup: BeautifulSoup) -> None:
    """Remove comments from the BeautifulSoup object."""
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

def remove_html_tags(soup: BeautifulSoup) -> None:
    """Remove empty tags from the BeautifulSoup object."""
    for element in soup.find_all():
        # Remove tags that have no text and no child elements
        if not element.get_text(strip=True) and not element.find_all():
            element.decompose()
        # Remove other unwanted attributes
        for attr in list(element.attrs or {}):
            if attr not in ['id']:
                del element.attrs[attr]

def remove_whitespaces_and_newlines(text: str) -> str:
    """Remove excessive whitespace and newlines from text."""
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return ''.join(cleaned_lines)

def get_text_from_html(soup: BeautifulSoup) -> str:
    """Extract only text from the BeautifulSoup object."""
    return soup.get_text(separator="\n", strip=True)


def clean_html_for_ai(html_content: str) -> str:
    """
    Clean HTML content for AI processing by removing unnecessary elements.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Cleaned HTML content
    """
    logger = get_logger(__name__)
        
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        body = soup.find('body')
        if body is not None:
            soup = body
        remove_html_scripts_and_styles(soup)
        remove_html_comments(soup)
        remove_html_tags(soup)

        # Get cleaned text
        cleaned = str(soup)
        if FETCHER_CLEANER_HTML_TO_TEXT:
            cleaned = get_text_from_html(soup)
        else:
            cleaned = remove_whitespaces_and_newlines(cleaned)
        return cleaned
    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML: {e}, returning original content")
        return html_content