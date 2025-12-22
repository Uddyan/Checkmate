# SPDX-License-Identifier: Apache-2.0
"""Probe registry for Checkmate."""

from typing import Dict, Type, Any
from checkmate.probes.base import BaseProbe


# Registry of available probes
_REGISTRY: Dict[str, Type[BaseProbe]] = {}


def register_probe(name: str, probe_class: Type[BaseProbe]) -> None:
    """Register a probe class."""
    _REGISTRY[name] = probe_class


def get_probe(name: str, **kwargs: Any) -> BaseProbe:
    """Get a probe instance by name.
    
    Args:
        name: Probe name
        **kwargs: Arguments to pass to probe constructor
        
    Returns:
        Probe instance
        
    Raises:
        ValueError: If probe name not found
    """
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown probe '{name}'. Available: {available}")
    
    return _REGISTRY[name](**kwargs)


def list_probes() -> Dict[str, str]:
    """List all registered probes with descriptions."""
    return {name: cls.description for name, cls in _REGISTRY.items()}


# Register built-in probes
def _register_builtins():
    from checkmate.probes.smoke_probe import SmokeProbe
    from checkmate.probes.prompt_injection import PromptInjectionProbe
    from checkmate.probes.data_exfil import DataExfilProbe
    from checkmate.probes.context_override import ContextOverrideProbe
    from checkmate.probes.agent_abuse import AgentAbuseProbe
    from checkmate.probes.rag_injection import RAGInjectionProbe
    
    register_probe("smoke_test", SmokeProbe)
    register_probe("prompt_injection", PromptInjectionProbe)
    register_probe("data_exfil", DataExfilProbe)
    register_probe("context_override", ContextOverrideProbe)
    register_probe("agent_abuse", AgentAbuseProbe)
    register_probe("rag_injection", RAGInjectionProbe)


_register_builtins()
