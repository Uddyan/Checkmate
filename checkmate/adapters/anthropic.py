"""Anthropic Claude API adapter"""

from typing import List, Dict, Any, Optional
import os
from .base import Adapter, Conversation, Generation


class AnthropicAdapter(Adapter):
    """Adapter for Anthropic Claude API"""
    
    def __init__(
        self,
        name: str = "anthropic",
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load the Anthropic client"""
        if self._client is not None:
            return self._client
        
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            return self._client
        except ImportError:
            raise RuntimeError(
                "anthropic package is required for AnthropicAdapter. "
                "Install with: pip install anthropic"
            )
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses using Anthropic Claude API.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        client = self._get_client()
        
        # Convert conversation to Anthropic format
        messages = []
        system_prompt = None
        
        for msg in conversation.messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                # Anthropic uses "user" and "assistant" roles
                role = "user" if msg.role in ["user", "human"] else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        # Generation parameters
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.7)
        
        try:
            response = client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
            )
            
            generations = []
            # Anthropic returns content as a list of content blocks
            for content_block in response.content:
                if content_block.type == "text":
                    generations.append(Generation(
                        text=content_block.text,
                        metadata={
                            "adapter": "anthropic",
                            "model": self.model,
                            "stop_reason": response.stop_reason,
                            "usage": {
                                "input_tokens": response.usage.input_tokens,
                                "output_tokens": response.usage.output_tokens,
                            }
                        }
                    ))
            
            return generations if generations else [
                Generation(
                    text="",
                    metadata={"adapter": "anthropic", "model": self.model, "error": "No text content"}
                )
            ]
            
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if API key is available and anthropic package is installed
        """
        try:
            import anthropic
            return self.api_key is not None
        except ImportError:
            return False

