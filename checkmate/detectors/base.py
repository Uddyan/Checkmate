# SPDX-License-Identifier: Apache-2.0
"""Base class for Checkmate detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Detection:
    """Represents a single detection finding."""
    detector_name: str
    severity: str  # "low" | "medium" | "high" | "critical"
    score: float = 1.0
    owasp_category: Optional[str] = None
    message: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "detector": self.detector_name,
            "severity": self.severity,
            "score": self.score,
            "owasp_category": self.owasp_category,
            "message": self.message,
            "tags": self.tags,
            "flagged": self.score >= 0.5,
        }


class BaseDetector(ABC):
    """Base class for all Checkmate detectors."""
    
    name: str = "base"
    description: str = ""
    threshold: float = 0.5
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    @abstractmethod
    def analyze(self, prompt: str, response: str) -> List[Detection]:
        """Analyze prompt and response for issues.
        
        Args:
            prompt: The prompt sent to the model
            response: The model's response
            
        Returns:
            List of Detection objects (empty if no issues found)
        """
        pass
    
    def detect(self, response: str) -> float:
        """Legacy method for backward compatibility.
        
        Args:
            response: Model response text
            
        Returns:
            Detection score (0.0 = no issues, 1.0 = severe issues)
        """
        # Call analyze with empty prompt for backward compatibility
        detections = self.analyze("", response)
        if not detections:
            return 0.0
        # Return max score from all detections
        return max(d.score for d in detections)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
