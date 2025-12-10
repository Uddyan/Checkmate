# SPDX-License-Identifier: Apache-2.0
"""Vector database client stub for Checkmate.

This module provides a placeholder for future vector database integration.
Implement the VectorClient class to enable semantic search over prompts
and responses.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class VectorClient(ABC):
    """Abstract base class for vector database clients."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the vector database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close vector database connection."""
        pass
    
    @abstractmethod
    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """Insert or update a vector.
        
        Args:
            id: Unique vector ID
            vector: Embedding vector
            metadata: Associated metadata
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of matching results with scores
        """
        pass
    
    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete a vector by ID."""
        pass


class NullVectorClient(VectorClient):
    """No-op vector client (used when vector DB is not configured)."""
    
    def connect(self) -> None:
        pass
    
    def disconnect(self) -> None:
        pass
    
    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        pass
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []
    
    def delete(self, id: str) -> None:
        pass


# Future implementation example:
# class PineconeClient(VectorClient):
#     def __init__(self, api_key: str, index_name: str):
#         self.api_key = api_key
#         self.index_name = index_name
#
#     def connect(self):
#         import pinecone
#         pinecone.init(api_key=self.api_key)
#         self.index = pinecone.Index(self.index_name)
#     ...
