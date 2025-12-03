"""Vector store for attack prompt corpus.

Provides optional vector database integration for storing and retrieving
attack prompts. Falls back to static prompts if unavailable.
"""

from .base import VectorStore
from .factory import create_vector_store

__all__ = ['VectorStore', 'create_vector_store']
