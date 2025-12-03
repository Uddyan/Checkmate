"""Factory for creating vector store instances from configuration."""

import logging
from typing import Optional
from .base import VectorStore

logger = logging.getLogger(__name__)


def create_vector_store(config: dict) -> Optional[VectorStore]:
    """
    Factory function to create vector store from configuration.
    
    Args:
        config: Vector store configuration dict with keys:
            - enabled: bool
            - backend: str ('pgvector', etc.)
            - connection: dict with backend-specific params
            
    Returns:
        VectorStore instance or None if disabled/misconfigured
        
    Example config:
        {
            "enabled": true,
            "backend": "pgvector",
            "connection": {
                "url": "postgresql://user:pass@localhost:5432/checkmate_vectors"
            },
            "collection": "attack_prompts"
        }
    """
    if not config or not config.get('enabled', False):
        logger.info("Vector store disabled in config")
        return None
    
    backend = config.get('backend', 'pgvector').lower()
    
    try:
        if backend == 'pgvector':
            from .pgvector import PgVectorStore
            
            connection_config = config.get('connection', {})
            url = connection_config.get('url')
            
            if not url:
                logger.error("PgVector requires connection.url")
                return None
            
            collection = config.get('collection', 'attack_prompts')
            
            logger.info(f"Creating PgVector store: collection={collection}")
            return PgVectorStore(
                connection_url=url,
                collection=collection
            )
        
        # Add other backends here (Qdrant, Weaviate, etc.)
        else:
            logger.warning(f"Unknown vector store backend: {backend}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}", exc_info=True)
        return None
