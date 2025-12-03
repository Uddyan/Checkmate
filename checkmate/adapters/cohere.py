"""Cohere API adapter"""

from typing import List, Dict, Any, Optional
import os
from .base import Adapter, Conversation, Generation


class CohereAdapter(Adapter):
    """Adapter for Cohere API"""
    
    def __init__(
        self,
        name: str = "cohere",
        api_key: Optional[str] = None,
        model: str = "command-r-plus",
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load the Cohere client"""
        if self._client is not None:
            return self._client
        
        try:
            import cohere
            self._client = cohere.Client(api_key=self.api_key)
            return self._client
        except ImportError:
            raise RuntimeError(
                "cohere package is required for CohereAdapter. "
                "Install with: pip install cohere"
            )
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses using Cohere API.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        client = self._get_client()
        
        # Convert conversation to Cohere format
        # Cohere uses a single prompt string or chat history
        chat_history = []
        prompt = ""
        
        for msg in conversation.messages:
            if msg.role == "system":
                # Cohere doesn't have a separate system role, prepend to first user message
                if not prompt:
                    prompt = f"System: {msg.content}\n\n"
            elif msg.role == "user":
                if chat_history:
                    # Add previous assistant response if exists
                    pass
                prompt += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n"
        
        # Generation parameters
        max_tokens = kwargs.get("max_tokens", 200)
        temperature = kwargs.get("temperature", 0.7)
        num_generations = kwargs.get("num_return_sequences", 1)
        
        try:
            # Use chat endpoint if available, otherwise use generate
            response = client.chat(
                model=self.model,
                message=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature", "num_return_sequences"]}
            )
            
            generations = []
            # Cohere chat returns a single response
            if hasattr(response, 'text'):
                generations.append(Generation(
                    text=response.text,
                    metadata={
                        "adapter": "cohere",
                        "model": self.model,
                        "finish_reason": getattr(response, 'finish_reason', None),
                    }
                ))
            else:
                # Fallback to generate endpoint
                response = client.generate(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    num_generations=num_generations,
                )
                for gen in response.generations:
                    generations.append(Generation(
                        text=gen.text,
                        metadata={
                            "adapter": "cohere",
                            "model": self.model,
                            "finish_reason": getattr(gen, 'finish_reason', None),
                        }
                    ))
            
            return generations if generations else [
                Generation(
                    text="",
                    metadata={"adapter": "cohere", "model": self.model, "error": "No response"}
                )
            ]
            
        except Exception as e:
            raise RuntimeError(f"Cohere API call failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if API key is available and cohere package is installed
        """
        try:
            import cohere
            return self.api_key is not None
        except ImportError:
            return False

