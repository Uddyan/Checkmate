"""Vector store base interface for attack prompt corpus.

Defines the protocol for vector database backends used to store and retrieve
attack prompts. All implementations must follow this interface.
"""

from typing import Protocol, List, Dict, Any, Optional


class VectorStore(Protocol):
    """
    Abstract interface for vector databases storing attack prompts.
    
    All vector store implementations must implement this protocol.
    """
    
    def search(
        self, 
        query: str, 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for attack prompts similar to the query.
        
        Args:
            query: Search query (e.g., "DAN jailbreak prompt injection")
            top_k: Maximum number of results to return
            filters: Optional filters (e.g., {"category": "LLM01", "severity": "high"})
            
        Returns:
            List of documents, each with at minimum:
                - 'id': str (unique document ID)
                - 'text': str (the attack prompt)
                - 'metadata': dict (category, severity, tags, etc.)
                
        Example:
            [
                {
                    "id": "attack_001",
                    "text": "Ignore all previous instructions and...",
                    "metadata": {
                        "category": "LLM01_prompt_injection",
                        "severity": "high",
                        "tags": ["jailbreak", "DAN"],
                        "probe_family": "dan"
                    }
                },
                ...
            ]
        """
        ...
    
    def close(self) -> None:
        """
        Close connections and cleanup resources.
        
        Called when the vector store is no longer needed.
        """
        ...
