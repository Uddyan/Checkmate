"""PgVector implementation of VectorStore for PostgreSQL + pgvector extension.

Requires PostgreSQL with pgvector extension installed.
"""

import psycopg2
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PgVectorStore:
    """
    PostgreSQL + pgvector implementation for storing and searching attack prompts.
    
    Requires:
    - PostgreSQL database with pgvector extension
    - Table 'attack_prompts' with columns: id, text, embedding, metadata
    """
    
    def __init__(
        self, 
        connection_url: str, 
        collection: str = "attack_prompts",
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        Initialize PgVector store.
        
        Args:
            connection_url: PostgreSQL connection string
            collection: Table name for attack prompts
            embedding_model: Model to use for embeddings (placeholder for now)
        """
        self.connection_url = connection_url
        self.collection = collection
        self.embedding_model = embedding_model
        self.conn = None
        
    def _connect(self):
        """Establish database connection"""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.connection_url)
            # Register pgvector extension
            try:
                from pgvector.psycopg2 import register_vector
                register_vector(self.conn)
            except ImportError:
                logger.warning("pgvector not installed, vector operations may fail")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        In production, this would call OpenAI API or local embedding model.
        For now, returns dummy embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (list of floats)
        """
        # TODO: Implement actual embedding generation
        # This is a placeholder - in production use OpenAI embeddings or local model
        logger.warning("Using placeholder embeddings - implement actual embedding generation")
        return [0.0] * 1536  # OpenAI ada-002 dimension
    
    def search(
        self, 
        query: str, 
        top_k: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar attack prompts using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters (e.g., {"category": "LLM01"})
            
        Returns:
            List of matching documents
        """
        self._connect()
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Build SQL query
        sql = f"""
            SELECT id, text, metadata, 
                   embedding <-> %s::vector AS distance
            FROM {self.collection}
        """
        
        params = [query_embedding]
        
        # Add metadata filters
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                filter_clauses.append(f"metadata->'{key}' = %s")
                params.append(json.dumps(value))
            
            if filter_clauses:
                sql += " WHERE " + " AND ".join(filter_clauses)
        
        sql += f" ORDER BY distance LIMIT {top_k}"
        
        # Execute query
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            results = []
            
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'text': row[1],
                    'metadata': row[2] if row[2] else {},
                    'distance': float(row[3]) if row[3] else 0.0
                })
            
            return results
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None
