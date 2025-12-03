"""Base adapter interface for checkmate"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


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
class Generation:
    """A single generation from a model"""
    text: str
    metadata: Dict[str, Any]


class Adapter(ABC):
    """Base class for all model adapters"""
    
    def __init__(self, name: str = "", **kwargs: Any):
        self.name = name
        self.active = True
    
    @abstractmethod
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses for a conversation.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the adapter is available for use.
        
        Returns:
            True if the adapter can be used, False otherwise
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
