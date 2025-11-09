import logging

import requests
import rich

from app.config.store_config import StoreConfig
from app.utils.json_extractor import JSONExtractor

from ..config.logging_config import get_logger, log_function_call

logger = get_logger(__name__)

class ApiResquetClient:
    def __init__(self, api_name: str):
        self.name = api_name
        logger.debug(f"Initialized {self.name}")

    async def fetch_json_data(self, url: str, headers: dict = None, params: dict = None) -> dict:
        try:

            log_function_call(f"{self.name}.fetch", {
                "url": url,
                "headers": headers,
                "params": params
            })

            # Make the GET request
            response = requests.get(url, headers=headers, params=params)

            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response data keys: {list(data.keys())}")

            return data

        except Exception as e:
            logger.error(f"Error occurred while fetching: {e}")
            raise
    

    async def query_products(self, product_name: str, store_config: StoreConfig) -> dict:
        """Query products from Coles RapidAPI."""

        # Request parameters
        url = store_config.search_api_url
        headers = store_config.search_headers
        params = store_config.get_query_params(product_name)
        
        logger.info(f"[{self.name}] Scraping URL: {url} with params: {params}")

        # Make the API request
        result = await self.fetch_json_data(url, headers=headers, params=params)

        # Log response data for debugging
        if logger.isEnabledFor(logging.DEBUG):
            rich.print(result)
            # logger.debug(f"Response data preview: {result.get(store_config.search_api_result_jsonpath, [])}")

        # Extract relevant data using JSON rules
        cleaned = JSONExtractor(store_config.search_api_result_jsonrules).extract(result)

        # Log the number of items received
        items_size = len(cleaned)
        log_level = logging.INFO if items_size > 0 else logging.WARNING
        logger.log(log_level, f"Successfully fetched data for query and received {items_size} products.")

        return {
            "data": cleaned,
            "data_from": "Coles RapidAPI",
            "data_size": len(str(cleaned)),
            "data_format": "json"
        }
