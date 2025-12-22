"""Base adapter interface for checkmate

Adapters connect Checkmate to different LLM backends (OpenAI, HTTP endpoints, etc.).

## Agent/Tool Testing Integration

For agent testing, adapters can optionally populate `tool_calls` on Generation objects:

```python
from checkmate.core.types import ToolCall

generation = Generation(
    text="I'll transfer the funds now.",
    metadata={},
    tool_calls=[ToolCall(name="transfer_funds", arguments={"amount": 1000})]
)
```

## RAG Testing Integration

For RAG testing, adapters can optionally populate `retrieved_chunks`:

```python
from checkmate.core.types import RetrievedChunk

generation = Generation(
    text="According to the policy...",
    metadata={},
    retrieved_chunks=[RetrievedChunk(id="doc1", text="The policy states...")]
)
```
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Import types for tool calls and RAG chunks
from checkmate.core.types import ToolCall, RetrievedChunk


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
    """A single generation from a model.
    
    Attributes:
        text: The generated text response
        metadata: Additional metadata from the model
        tool_calls: Optional list of tool/function calls for agent testing.
            Adapters should populate this when the model invokes tools.
            Used by ToolAbuseDetector to detect suspicious tool usage.
        retrieved_chunks: Optional list of retrieved document chunks for RAG testing.
            Adapters should populate this when RAG context is available.
            Used by RAGConsistencyDetector to detect hallucinations.
    """
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: Optional[List[ToolCall]] = None
    retrieved_chunks: Optional[List[RetrievedChunk]] = None


class Adapter(ABC):
    """Base class for all model adapters.
    
    Adapters wrap different LLM backends and provide a unified interface
    for sending prompts and receiving responses.
    
    ## Extending for Agent Testing
    
    To support agent/tool abuse testing, override `generate()` to parse
    tool calls from the model's response and include them in the Generation:
    
    ```python
    def generate(self, conversation, **kwargs):
        response = self._call_model(conversation)
        tool_calls = self._parse_tool_calls(response)  # Your parsing logic
        return [Generation(
            text=response.text,
            metadata={},
            tool_calls=tool_calls  # Attach tool calls here
        )]
    ```
    
    ## Extending for RAG Testing
    
    To support RAG testing, attach retrieved chunks when available:
    
    ```python
    def generate(self, conversation, **kwargs):
        chunks = self._retrieve_context(conversation)  # Your RAG logic
        response = self._call_model(conversation, context=chunks)
        return [Generation(
            text=response.text,
            metadata={},
            retrieved_chunks=[RetrievedChunk(id=c.id, text=c.text) for c in chunks]
        )]
    ```
    """
    
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
            List of generated responses. Adapters MAY populate:
            - tool_calls: for agent testing
            - retrieved_chunks: for RAG testing
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
