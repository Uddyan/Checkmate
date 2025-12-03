"""OpenAI-compatible API adapter"""

from typing import List, Dict, Any, Optional
import os
from .base import Adapter, Conversation, Generation


class OpenAICompatibleAdapter(Adapter):
    """Adapter for OpenAI-compatible APIs"""
    
    def __init__(
        self,
        name: str = "openai_compatible",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load the OpenAI client"""
        if self._client is not None:
            return self._client
            
        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            return self._client
        except ImportError:
            raise RuntimeError("openai package is required for OpenAICompatibleAdapter")
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses using OpenAI-compatible API.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        client = self._get_client()
        
        # Convert conversation to OpenAI format
        messages = []
        for msg in conversation.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Generation parameters
        max_tokens = kwargs.get("max_tokens", 150)
        temperature = kwargs.get("temperature", 0.7)
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            generations = []
            for choice in response.choices:
                text = choice.message.content or ""
                generations.append(Generation(
                    text=text,
                    metadata={
                        "adapter": "openai_compatible",
                        "model": self.model,
                        "finish_reason": choice.finish_reason
                    }
                ))
            
            return generations
            
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if API key is available and openai package is installed
        """
        try:
            import openai
            return self.api_key is not None
        except ImportError:
            return False
