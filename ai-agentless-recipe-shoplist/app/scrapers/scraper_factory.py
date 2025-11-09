from typing import Protocol

from app.config.store_config import StoreConfig
from app.scrapers.api_request_client import ApiResquetClient
from app.scrapers.html_scraper import HTMLScraper


class ScraperProtocol(Protocol):
    async def query_products(self, url: str, store_config: StoreConfig) -> dict:
        ...


class ScraperFactory:
    """Factory class to create scraper instances based on store configuration."""

    @staticmethod
    def create_scraper(store_config: StoreConfig) -> ScraperProtocol:
        if store_config.search_type == "html":
            return HTMLScraper()
        elif store_config.search_type == "coles_rapidapi":
            return ApiResquetClient(store_config.name)
        elif store_config.search_type == "Aldi_api":
            return ApiResquetClient(store_config.name)
        else:
            raise ValueError(f"Unknown scraper type: {store_config.search_type}")