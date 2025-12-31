"""
Framework adapters for integrating Paracle with external multi-agent frameworks.

This package provides adapters for popular frameworks like LangChain, MSAF,
and LlamaIndex, following the Adapter pattern from hexagonal architecture.
"""

__version__ = "0.0.1"

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import (
    AdapterConfigurationError,
    AdapterError,
    AdapterExecutionError,
    AdapterNotFoundError,
    FeatureNotSupportedError,
)
from paracle_adapters.registry import AdapterRegistry

__all__ = [
    "FrameworkAdapter",
    "AdapterError",
    "AdapterNotFoundError",
    "AdapterConfigurationError",
    "AdapterExecutionError",
    "FeatureNotSupportedError",
    "AdapterRegistry",
]
