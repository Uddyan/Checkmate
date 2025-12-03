"""Core type definitions for checkmate"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class ProbeType(Enum):
    """Types of probes"""
    TOXICITY = "toxicity"
    JAILBREAK = "jailbreak"
    INJECTION = "injection"
    HALLUCINATION = "hallucination"
    BIAS = "bias"


class DetectorType(Enum):
    """Types of detectors"""
    TOXICITY = "toxicity"
    SAFETY = "safety"
    BIAS = "bias"
    ACCURACY = "accuracy"


@dataclass
class Probe:
    """A probe for testing model vulnerabilities"""
    name: str
    probe_type: ProbeType
    description: str
    tags: List[str]
    active: bool = True
    
    def __str__(self) -> str:
        return f"Probe(name='{self.name}', type='{self.probe_type.value}')"


@dataclass
class Buff:
    """A buff for augmenting prompts"""
    name: str
    description: str
    active: bool = True
    
    def apply(self, text: str) -> str:
        """Apply the buff to text.
        
        Args:
            text: Input text
            
        Returns:
            Transformed text
        """
        # Base implementation - subclasses should override
        return text
    
    def __str__(self) -> str:
        return f"Buff(name='{self.name}')"


@dataclass
class Detector:
    """A detector for identifying model failures"""
    name: str
    detector_type: DetectorType
    description: str
    active: bool = True
    
    def detect(self, text: str) -> float:
        """Detect issues in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detection score (0.0 = no issues, 1.0 = severe issues)
        """
        # Base implementation - subclasses should override
        return 0.0
    
    def __str__(self) -> str:
        return f"Detector(name='{self.name}', type='{self.detector_type.value}')"


@dataclass
class Attempt:
    """A single attempt at probing a model"""
    probe_name: str
    prompt: str
    response: str
    score: float
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"Attempt(probe='{self.probe_name}', score={self.score:.3f})"


@dataclass
class Score:
    """A score from a detector"""
    detector_name: str
    value: float
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"Score(detector='{self.detector_name}', value={self.value:.3f})"


@dataclass
class Message:
    """A single message in a conversation"""
    role: str
    content: str


@dataclass
class Conversation:
    """A conversation between user and model"""
    messages: List[Message]
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation"""
        self.messages.append(Message(role=role, content=content))
    
    def to_string(self) -> str:
        """Convert conversation to string format"""
        parts = []
        for msg in self.messages:
            parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(parts)


@dataclass
class RunConfig:
    """Configuration for a checkmate run"""
    adapters: List[str]
    probes: List[str]
    detectors: List[str]
    buffs: List[str]
    output_dir: str
    max_attempts: int = 10
    seed: Optional[int] = None
    
    def __str__(self) -> str:
        return f"RunConfig(adapters={self.adapters}, probes={self.probes})"
