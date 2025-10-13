"""Shopper adapters package init

This package contains adapters for grocery retailers (mock or real).
"""

from .adapters import get_adapters, get_adapter_names

__all__ = ["get_adapters", "get_adapter_names"]
