"""
Framework adapters for integrating Paracle with external multi-agent frameworks.

This package provides adapters for popular frameworks like LangChain, MSAF,
LlamaIndex, CrewAI, and AutoGen, following the Adapter pattern from hexagonal
architecture.

Available Adapters:
- LangChainAdapter: LangChain/LangGraph integration (agents, tools, workflows)
- MSAFAdapter: Microsoft Azure AI Agent Framework integration
- LlamaIndexAdapter: LlamaIndex integration (RAG, query engines, agents)
- CrewAIAdapter: CrewAI integration (role-based crews, tasks)
- AutoGenAdapter: Microsoft AutoGen integration (group chats, code execution)

Usage:
    >>> from paracle_adapters import AdapterRegistry
    >>> registry = AdapterRegistry()
    >>> registry.register("langchain", LangChainAdapter)
    >>> adapter = registry.create("langchain", llm=my_llm)

Note: Each adapter requires its respective framework to be installed.
Install optional dependencies with:
    pip install paracle[langchain]  # LangChain + LangGraph
    pip install paracle[llamaindex]  # LlamaIndex
    pip install paracle[crewai]  # CrewAI
    pip install paracle[autogen]  # AutoGen
    pip install paracle[adapters]  # All adapters
"""

__version__ = "1.0.1"

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import (
    AdapterConfigurationError,
    AdapterError,
    AdapterExecutionError,
    AdapterNotFoundError,
    FeatureNotSupportedError,
)
from paracle_adapters.registry import AdapterRegistry

# Lazy imports for optional framework adapters
_ADAPTER_CLASSES: dict[str, str] = {
    "langchain": "paracle_adapters.langchain_adapter:LangChainAdapter",
    "llamaindex": "paracle_adapters.llamaindex_adapter:LlamaIndexAdapter",
    "crewai": "paracle_adapters.crewai_adapter:CrewAIAdapter",
    "autogen": "paracle_adapters.autogen_adapter:AutoGenAdapter",
    "msaf": "paracle_adapters.msaf_adapter:MSAFAdapter",
}


def get_adapter_class(name: str):
    """
    Lazily load an adapter class by name.

    Args:
        name: Adapter name (langchain, llamaindex, crewai, autogen, msaf)

    Returns:
        Adapter class

    Raises:
        AdapterNotFoundError: If adapter not found
        ImportError: If framework not installed
    """
    if name not in _ADAPTER_CLASSES:
        raise AdapterNotFoundError(name)

    module_path, class_name = _ADAPTER_CLASSES[name].split(":")
    try:
        import importlib

        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        raise ImportError(
            f"Framework '{name}' is not installed. "
            f"Install with: pip install paracle[{name}]"
        ) from e


def list_available_adapters() -> dict[str, bool]:
    """
    List all adapters and their availability.

    Returns:
        Dictionary of adapter names and whether they're available
    """
    availability = {}

    for name in _ADAPTER_CLASSES:
        try:
            get_adapter_class(name)
            availability[name] = True
        except ImportError:
            availability[name] = False

    return availability


__all__ = [
    # Base
    "FrameworkAdapter",
    # Exceptions
    "AdapterError",
    "AdapterNotFoundError",
    "AdapterConfigurationError",
    "AdapterExecutionError",
    "FeatureNotSupportedError",
    # Registry
    "AdapterRegistry",
    # Utilities
    "get_adapter_class",
    "list_available_adapters",
]
