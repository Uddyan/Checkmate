# SPDX-License-Identifier: Apache-2.0
"""Detector registry for Checkmate."""

from typing import Dict, Type, Any
from checkmate.detectors.base import BaseDetector


# Registry of available detectors
_REGISTRY: Dict[str, Type[BaseDetector]] = {}


def register_detector(name: str, detector_class: Type[BaseDetector]) -> None:
    """Register a detector class."""
    _REGISTRY[name] = detector_class


def get_detector(name: str, **kwargs: Any) -> BaseDetector:
    """Get a detector instance by name.
    
    Args:
        name: Detector name
        **kwargs: Arguments to pass to detector constructor
        
    Returns:
        Detector instance
        
    Raises:
        ValueError: If detector name not found
    """
    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown detector '{name}'. Available: {available}")
    
    return _REGISTRY[name](**kwargs)


def list_detectors() -> Dict[str, str]:
    """List all registered detectors with descriptions."""
    return {name: cls.description for name, cls in _REGISTRY.items()}


# Register built-in detectors
def _register_builtins():
    from checkmate.detectors.mitigation import MitigationBypassDetector, BasicDetector
    from checkmate.detectors.data_leak import DataLeakDetector
    from checkmate.detectors.toxicity import ToxicityDetector
    from checkmate.detectors.tool_abuse import ToolAbuseDetector
    from checkmate.detectors.rag_consistency import RAGConsistencyDetector
    
    register_detector("mitigation_bypass", MitigationBypassDetector)
    register_detector("data_leak", DataLeakDetector)
    register_detector("toxicity", ToxicityDetector)
    register_detector("tool_abuse", ToolAbuseDetector)
    register_detector("rag_consistency", RAGConsistencyDetector)
    register_detector("basic", BasicDetector)


_register_builtins()
