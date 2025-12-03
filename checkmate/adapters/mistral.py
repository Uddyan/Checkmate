"""Mistral AI API adapter"""

from typing import List, Dict, Any, Optional
import os
from .base import Adapter, Conversation, Generation


class MistralAdapter(Adapter):
    """Adapter for Mistral AI API"""
    
    def __init__(
        self,
        name: str = "mistral",
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load the Mistral client"""
        if self._client is not None:
            return self._client
        
        try:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
            return self._client
        except ImportError:
            raise RuntimeError(
                "mistralai package is required for MistralAdapter. "
                "Install with: pip install mistralai"
            )
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses using Mistral AI API.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        client = self._get_client()
        
        # Convert conversation to Mistral format
        messages = []
        for msg in conversation.messages:
            # Mistral uses "user" and "assistant" roles
            role = "user" if msg.role in ["user", "human", "system"] else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        # Generation parameters
        max_tokens = kwargs.get("max_tokens", 500)
        temperature = kwargs.get("temperature", 0.7)
        
        try:
            response = client.chat.complete(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
            )
            
            generations = []
            for choice in response.choices:
                text = choice.message.content or ""
                generations.append(Generation(
                    text=text,
                    metadata={
                        "adapter": "mistral",
                        "model": self.model,
                        "finish_reason": choice.finish_reason,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                            "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                        }
                    }
                ))
            
            return generations if generations else [
                Generation(
                    text="",
                    metadata={"adapter": "mistral", "model": self.model, "error": "No response"}
                )
            ]
            
        except Exception as e:
            raise RuntimeError(f"Mistral API call failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if API key is available and mistralai package is installed
        """
        try:
            from mistralai import Mistral
            return self.api_key is not None
        except ImportError:
            return False

