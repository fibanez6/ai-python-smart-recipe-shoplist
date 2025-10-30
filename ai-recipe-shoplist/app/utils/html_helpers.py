"""
HTML helper functions for the recipe shoplist crawler.
"""
import logging

from bs4 import BeautifulSoup, Comment

from app.config.logging_config import get_logger, log_function_call, setup_logging

from ..config.pydantic_config import FETCHER_SETTINGS


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

def clean_html(html_content: str) -> str:
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
        if FETCHER_SETTINGS.cleaner_html_to_text:
            cleaned = get_text_from_html(soup)
        else:
            cleaned = remove_whitespaces_and_newlines(cleaned)
        return cleaned
    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML: {e}, returning original content")
        return html_content
    
def clean_html_with_selectors(html_content: str, selectors: dict[str, str]) -> list[dict]:
    """
    Clean HTML content for AI processing using specific CSS selectors.
    
    Args:
        html_content: Raw HTML content
        selectors: Dictionary of CSS selectors to extract specific parts of the HTML.   
    Returns:
        Cleaned HTML content
    """
    logger = get_logger(__name__)

    log_function_call("Html_helper.clean_html_with_selectors", {
        "html_content": html_content[:50],
        "html_selectors": selectors
        })
        
    product_tile_selector = _get_product_tile_selector(selectors)
    if product_tile_selector:
        filtered_selectors = {k: v for k, v in selectors.items() if k != "product_tile"}
        return _extract_by_product_tile_selector(html_content, product_tile_selector, filtered_selectors)
    return _extract_by_selectors(html_content, selectors)
    

def _get_product_tile_selector(selectors: dict[str, str]) -> str | None:
    """Get the selector for a specific product tile."""
    return selectors.get("product_tile", None)


def _extract_by_product_tile_selector(html_content: str, product_title: str, selectors: dict[str, str]) -> list[dict]:
    """Get the selector for a specific product tile."""
    
    logger = get_logger(__name__)

    log_function_call("Html_helper._extract_by_product_tile_selector", {
        "html_content": html_content[:50],
        "product_title": product_title,
        "html_selectors": selectors
        })

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract parts based on selectors
        data = []

        title_elements = soup.select(product_title)
        logger.debug(f"[WebFetcher] Product Tile: Found {len(title_elements)} elements")

        for tile in title_elements:
            tile_data = {}
            for name, selector in selectors.items():
                element = tile.select_one(selector)
                if element:
                    if element.name == "img":
                        tile_data[name] = element.get("src", "")
                    elif element.name == "a":
                        tile_data[name] = element.get("href", "")
                    else:
                        tile_data[name] = element.get_text(strip=True)
            data.append(tile_data)

        if logger.isEnabledFor(logging.DEBUG):
            for idx, item in enumerate(data):
                logger.debug(f"([WebFetcher] Element {idx}: {item}")

        return data

    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML with selectors: {e}, returning original content")
        return html_content


def _extract_by_selectors(html_content: str, selectors: dict[str, str]) -> list[dict]:
    """Extract product tiles from HTML content using the given selectors."""

    logger = get_logger(__name__)

    log_function_call("Html_helper._extract_by_product_tile_selector", {
        "html_content": html_content[:50],
        "html_selectors": selectors
    })

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract parts based on selectors
        data = {}
        for name, selector in selectors.items():
            elements = soup.select(selector)
            logger.debug(f"[WebFetcher] Selector '{name}': Found {len(elements)} elements with selector '{selector}'")
            # for idx, element in enumerate(elements):
            #     logger.debug(f"[WebFetcher] Selector '{name}' Element {idx}: {str(element.text)[:400]}")

            for element in elements:
                if element.name == "img":
                    data.setdefault(name, []).append(element.get("src", ""))
                elif element.name == "a":
                    data.setdefault(name, []).append(element.get("href", ""))
                else:
                    data.setdefault(name, []).append(element.get_text(strip=True))

        # Zip all lists together by index, combining elements from each selector
        zipped = [dict(zip(data.keys(), values)) for values in zip(*data.values())]
 
        
        if logger.isEnabledFor(logging.DEBUG):
            for idx, item in enumerate(zipped):
                logger.debug(f"([WebFetcher] Element {idx}: {item}")

        return zipped
    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML with selectors: {e}, returning original content")
        return html_content


def clean_html_for_ai(html_content: str, selectors: dict[str, str]) -> str | list[dict]:
    """Wrapper to clean HTML content for AI processing."""
    if selectors:
        return clean_html_with_selectors(html_content, selectors)
    return clean_html(html_content)