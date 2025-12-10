# SPDX-License-Identifier: Apache-2.0
"""Checkmate - LLM Red-Teaming Scanner.

A production-ready tool for automated security testing of Large Language Models.
"""

__version__ = "1.0.0"

from checkmate.core import CheckmateEngine, CheckmateConfig
from checkmate.probes import BaseProbe, get_probe, list_probes
from checkmate.detectors import BaseDetector, get_detector, list_detectors
from checkmate.adapters import get_adapter, ADAPTERS

__all__ = [
    "__version__",
    "CheckmateEngine",
    "CheckmateConfig",
    "BaseProbe",
    "get_probe",
    "list_probes",
    "BaseDetector",
    "get_detector",
    "list_detectors",
    "get_adapter",
    "ADAPTERS",
]