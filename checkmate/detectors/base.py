# SPDX-License-Identifier: Apache-2.0
"""Base class for Checkmate detectors."""

from abc import ABC, abstractmethod


class BaseDetector(ABC):
    """Base class for all Checkmate detectors."""
    
    name: str = "base"
    description: str = ""
    threshold: float = 0.5
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    @abstractmethod
    def detect(self, response: str) -> float:
        """Detect issues in a model response.
        
        Args:
            response: Model response text
            
        Returns:
            Detection score (0.0 = no issues, 1.0 = severe issues)
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
