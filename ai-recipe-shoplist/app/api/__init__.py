"""API package for the AI Recipe Shoplist Crawler.

This package contains all API version modules and routers.
"""

from .v1 import api_v1_router as v1_router

__all__ = ["v1_router"]
