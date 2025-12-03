"""Null adapter for offline testing"""

from typing import List, Dict, Any
from .base import Adapter, Conversation, Generation


class NullAdapter(Adapter):
    """Null adapter that returns empty responses for offline testing"""
    
    def __init__(self, name: str = "null", **kwargs: Any):
        super().__init__(name=name, **kwargs)
        self.active = True
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate empty responses for testing.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters (ignored)
            
        Returns:
            List containing a single empty generation
        """
        return [Generation(text="", metadata={"adapter": "null"})]
    
    def is_available(self) -> bool:
        """Null adapter is always available.
        
        Returns:
            True
        """
        return True
