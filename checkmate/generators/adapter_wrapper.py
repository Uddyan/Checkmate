"""Generator wrapper for Adapters to work with harnesses"""

from typing import List, Union
import checkmate.attempt
from checkmate.generators.base import Generator
from checkmate.adapters.base import Adapter


class AdapterGenerator(Generator):
    """Wrapper to convert an Adapter to a Generator for use with harnesses"""
    
    def __init__(self, adapter: Adapter, name: str = None, **kwargs):
        """Initialize generator from an adapter
        
        Args:
            adapter: The adapter to wrap
            name: Optional name override
        """
        super().__init__(name=name or adapter.name, **kwargs)
        self.adapter = adapter
        self.name = adapter.name
        self.modality = {"in": {"text"}}  # Default modality
    
    def _call_model(
        self, prompt: checkmate.attempt.Conversation, generations_this_call: int = 1
    ) -> List[Union[checkmate.attempt.Message, None]]:
        """Call the underlying adapter to generate responses"""
        from checkmate.core.types import Conversation, Message
        
        # Convert checkmate.attempt.Conversation to core.types.Conversation
        messages = []
        for turn in prompt.turns:
            messages.append(Message(
                role=turn.role,
                content=turn.content.text if hasattr(turn.content, 'text') else str(turn.content)
            ))
        
        core_conversation = Conversation(messages=messages)
        
        # Call adapter
        generations = self.adapter.generate(core_conversation)
        
        # Convert back to checkmate.attempt.Message format
        results = []
        for gen in generations:
            msg = checkmate.attempt.Message(gen.text)
            results.append(msg)
        
        return results


