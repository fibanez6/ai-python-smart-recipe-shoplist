"""
HTML helper functions for the recipe shoplist crawler.
"""
import logging

from bs4 import BeautifulSoup, Comment

from app.config.logging_config import get_logger, log_function_call, setup_logging

from ..config.pydantic_config import WEB_DATA_SERVICE_SETTINGS

# Get module logger
logger = get_logger(__name__)

def _remove_html_scripts_and_styles(soup: BeautifulSoup) -> None:
    """Remove script and style elements from the BeautifulSoup object."""
    for element in soup(["window", "script", "noscript", "style", "nav", "header", "footer", "aside", "svg", "link", "meta"]):
        element.decompose()

def _remove_html_comments(soup: BeautifulSoup) -> None:
    """Remove comments from the BeautifulSoup object."""
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

def _remove_html_tags(soup: BeautifulSoup) -> None:
    """Remove empty tags from the BeautifulSoup object."""
    for element in soup.find_all():
        # Remove tags that have no text and no child elements
        if not element.get_text(strip=True) and not element.find_all():
            element.decompose()
        # Remove other unwanted attributes
        for attr in list(element.attrs or {}):
            if attr not in ['id']:
                del element.attrs[attr]

def _remove_whitespaces_and_newlines(text: str) -> str:
    """Remove excessive whitespace and newlines from text."""
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return ''.join(cleaned_lines)

def _get_text_from_html(soup: BeautifulSoup) -> str:
    """Extract only text from the BeautifulSoup object."""
    return soup.get_text(separator="\n", strip=True)

def _get_product_tile_selector(selectors: dict[str, str]) -> str | None:
    """Get the selector for a specific product tile."""
    return selectors.get("product_tile", None)

def _extract_by_product_tile_selector(html_content: str, product_title: str, selectors: dict[str, str]) -> list[dict]:
    """Get the selector for a specific product tile."""
    
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
                        tile_data[name] = element.get("src", None)
                    elif element.name == "a":
                        tile_data[name] = element.get("href", None)
                    else:
                        tile_data[name] = element.get_text(strip=True)
                else:
                    logger.warning(f"[WebFetcher] Product Tile: Selector '{name}' not found in tile")

            # Remove keys with empty string or None values
            tile_data = {k: v for k, v in tile_data.items() if v not in ("", None)}

            # Append tile data to the list
            data.append(tile_data)

        if logger.isEnabledFor(logging.DEBUG):
            for idx, item in enumerate(data):
                logger.debug(f"([WebFetcher] Element {idx}: {item}")

        return data

    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML with selectors: {e}, returning original content")
        return html_content

def _extract_by_selectors(html_content: str, selectors: dict[str, str]) -> list[dict]:
    """Extract elements from HTML content using the given selectors."""

    log_function_call("Html_helper._extract_by_selectors", {
        "html_content": html_content[:50],
        "html_selectors": selectors
    })

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_data = {}

        for name, selector in selectors.items():
            elements = soup.select(selector)
            logger.debug(f"[WebFetcher] Selector '{name}': Found {len(elements)} elements with selector '{selector}'")
            values = []
            for element in elements:
                if element.name == "img":
                    values.append(element.get("src", ""))
                elif element.name == "a":
                    values.append(element.get("href", ""))
                else:
                    values.append(element.get_text(strip=True))
            extracted_data[name] = values

        # Zip all lists together by index, combining elements from each selector
        result = [dict(zip(extracted_data.keys(), values)) for values in zip(*extracted_data.values())]
 
        # # Combine extracted values by index
        # result = [
        #     {key: values[i] for key, values in extracted_data.items()}
        #     for i in range(min(len(v) for v in extracted_data.values()))  # Only zip up to the shortest list
        # ]

        if logger.isEnabledFor(logging.DEBUG):
            for idx, item in enumerate(result):
                logger.debug(f"[WebFetcher] Element {idx}: {item}")

        return result
    except Exception as e:
        logger.warning(f"[WebFetcher] Error extracting HTML with selectors: {e}, returning original content")
        return html_content

def clean_html(html_content: str) -> dict:
    """
    Clean HTML content for AI processing by removing unnecessary elements.

    Args:
        html_content: Raw HTML content

    Returns:
        Cleaned HTML content as a string.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        soup = soup.find('body') or soup

        _remove_html_scripts_and_styles(soup)
        _remove_html_comments(soup)
        _remove_html_tags(soup)

        if WEB_DATA_SERVICE_SETTINGS.html_to_text:
            return {"data_processed_format": "text", "data": _get_text_from_html(soup)}
        else:
            return {"data_processed_format": "html", "data": _remove_whitespaces_and_newlines(str(soup))}

    except Exception as e:
        logger.warning(f"[WebFetcher] Error cleaning HTML: {e}, returning original content")
        return html_content
    
def clean_html_with_selectors(html_content: str, selectors: dict[str, str]) -> dict:
    """
    Clean and extract HTML content using specific CSS selectors.

    Args:
        html_content: Raw HTML content.
        selectors: Dictionary of CSS selectors to extract specific parts of the HTML.

    Returns:
        List of dictionaries with extracted content.
    """
    log_function_call(
        "Html_helper.clean_html_with_selectors",
        {
            "html_content": html_content[:50],
            "html_selectors": selectors,
        },
    )

    product_tile_selector = _get_product_tile_selector(selectors)
    if product_tile_selector:
        filtered_selectors = {
            k: v for k, v in selectors.items() if k != "product_tile"
        }
        return {
            "data_processed_format": "dict",
            "data": _extract_by_product_tile_selector(html_content, product_tile_selector, filtered_selectors)
        }
    return {
        "data_processed_format": "dict", 
        "data": _extract_by_selectors(html_content, selectors)
        }