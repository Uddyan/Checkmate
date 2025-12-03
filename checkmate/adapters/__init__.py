"""Adapter system for checkmate"""

from typing import Dict, Type, Any
from .base import Adapter
from .null import NullAdapter
from .hf_local import HFLocalAdapter
from .openai_compatible import OpenAICompatibleAdapter
from .http_local import HTTPLocalAdapter

# Lazy imports for optional adapters
def _get_anthropic_adapter():
    from .anthropic import AnthropicAdapter
    return AnthropicAdapter

def _get_cohere_adapter():
    from .cohere import CohereAdapter
    return CohereAdapter

def _get_mistral_adapter():
    from .mistral import MistralAdapter
    return MistralAdapter

# Registry of available adapters
ADAPTERS: Dict[str, Type[Adapter]] = {
    "null": NullAdapter,
    "hf_local": HFLocalAdapter,
    "openai_compatible": OpenAICompatibleAdapter,
    "http_local": HTTPLocalAdapter,
    "http_app": HTTPLocalAdapter,
    # Optional adapters - will be loaded lazily if available
    "anthropic": _get_anthropic_adapter,
    "cohere": _get_cohere_adapter,
    "mistral": _get_mistral_adapter,
}


def get_adapter(name: str, **kwargs: Any) -> Adapter:
    """Get an adapter instance by name.
    
    Args:
        name: Name of the adapter to instantiate
        **kwargs: Arguments to pass to the adapter constructor
        
    Returns:
        Configured adapter instance
        
    Raises:
        ValueError: If adapter name is not found
        RuntimeError: If adapter dependencies are not installed
    """
    if name not in ADAPTERS:
        available = ", ".join(ADAPTERS.keys())
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    
    adapter_class_or_factory = ADAPTERS[name]
    
    # Handle lazy-loaded adapters (callable factories)
    if callable(adapter_class_or_factory) and not isinstance(adapter_class_or_factory, type):
        try:
            adapter_class = adapter_class_or_factory()
        except (ImportError, RuntimeError) as e:
            raise RuntimeError(
                f"Adapter '{name}' is not available. "
                f"Required dependencies may not be installed: {e}"
            )
    else:
        adapter_class = adapter_class_or_factory
    
    return adapter_class(**kwargs)
