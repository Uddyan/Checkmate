# SPDX-License-Identifier: Apache-2.0
"""Base class for Checkmate probes."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProbe(ABC):
    """Base class for all Checkmate probes."""
    
    name: str = "base"
    description: str = ""
    tags: List[str] = []
    
    @abstractmethod
    def generate_prompts(self) -> List[str]:
        """Generate prompts to send to the target model.
        
        Returns:
            List of prompt strings
        """
        pass
    
    def run(self, adapter) -> List[Dict[str, Any]]:
        """Run the probe against a model adapter.
        
        Args:
            adapter: Model adapter instance
            
        Returns:
            List of result dictionaries with prompt, response, and metadata
        """
        from checkmate.adapters.base import Conversation, Message
        
        prompts = self.generate_prompts()
        results = []
        
        for prompt in prompts:
            # Create a conversation with the prompt
            conversation = Conversation(messages=[Message(role="user", content=prompt)])
            
            try:
                generations = adapter.generate(conversation)
                response = generations[0].text if generations else ""
            except Exception as e:
                response = f"[ERROR] {str(e)}"
            
            results.append({
                "probe": self.name,
                "prompt": prompt,
                "response": response,
                "metadata": {
                    "tags": self.tags,
                },
            })
        
        return results
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
