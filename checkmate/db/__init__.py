# SPDX-License-Identifier: Apache-2.0
"""Checkmate database module.

Provides database storage for scan results and history tracking.
By default, database is disabled. Enable in config:

database:
  enabled: true
  url: postgresql://user:pass@host:5432/checkmate
"""

import logging
from typing import Optional
from checkmate.db.client import DatabaseClient, NullDatabaseClient

__all__ = ["DatabaseClient", "NullDatabaseClient", "get_db_client"]

logger = logging.getLogger(__name__)

# Global DB client instance (lazy initialized)
_db_client: Optional[DatabaseClient] = None
_db_config: Optional[dict] = None


def configure_db(config: Optional[dict]) -> None:
    """Configure database from config dict.
    
    Args:
        config: Database config dict with 'enabled' and 'url' keys
    """
    global _db_config
    _db_config = config


def get_db_client() -> Optional[DatabaseClient]:
    """Get the database client instance.
    
    Returns the configured database client, or None if not configured.
    Uses lazy initialization - connection is established on first call.
    
    Returns:
        DatabaseClient instance or None if database is not enabled
    """
    global _db_client, _db_config
    
    # If already initialized, return cached client
    if _db_client is not None:
        return _db_client
    
    # Check if database is configured and enabled
    if not _db_config:
        return None
    
    if not _db_config.get("enabled", False):
        return None
    
    url = _db_config.get("url")
    if not url:
        logger.warning("Database enabled but no URL provided")
        return None
    
    # Try to create PostgreSQL client
    try:
        from checkmate.db.postgres import PostgresClient
        _db_client = PostgresClient(url)
        _db_client.connect()
        logger.info("Database client initialized")
        return _db_client
        
    except ImportError:
        logger.warning(
            "PostgreSQL support not available. "
            "Install with: pip install checkmate[postgres]"
        )
        return None
        
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")
        return None
