"""Hugging Face local adapter"""

from typing import List, Dict, Any, Optional
import torch
from .base import Adapter, Conversation, Generation


class HFLocalAdapter(Adapter):
    """Adapter for local Hugging Face models"""
    
    def __init__(
        self, 
        name: str = "hf_local",
        model_name: str = "sshleifer/tiny-gpt2",
        device: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        self._tokenizer = None
        self._pipeline = None
    
    def _load_model(self) -> None:
        """Lazy load the model and tokenizer"""
        if self._model is not None:
            return
            
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Add padding token if not present
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=self.device,
                return_full_text=False
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model_name}: {e}")
    
    def generate(self, conversation: Conversation, **kwargs: Any) -> List[Generation]:
        """Generate responses using the local Hugging Face model.
        
        Args:
            conversation: The conversation to generate responses for
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        self._load_model()
        
        # Convert conversation to prompt
        prompt = conversation.to_string()
        
        # Generation parameters
        max_length = kwargs.get("max_length", 100)
        temperature = kwargs.get("temperature", 0.7)
        do_sample = kwargs.get("do_sample", True)
        num_return_sequences = kwargs.get("num_return_sequences", 1)
        
        try:
            results = self._pipeline(
                prompt,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                num_return_sequences=num_return_sequences,
                pad_token_id=self._tokenizer.eos_token_id
            )
            
            generations = []
            for result in results:
                text = result.get("generated_text", "")
                generations.append(Generation(
                    text=text,
                    metadata={
                        "adapter": "hf_local",
                        "model": self.model_name,
                        "device": self.device
                    }
                ))
            
            return generations
            
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if transformers is available, False otherwise
        """
        try:
            import transformers
            return True
        except ImportError:
            return False
