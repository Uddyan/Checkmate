# SPDX-License-Identifier: Apache-2.0
"""Database client stub for Checkmate.

This module provides a placeholder for future database integration.
Implement the DatabaseClient class to enable persistent storage of
scan results.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class DatabaseClient(ABC):
    """Abstract base class for database clients."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    def save_scan(self, scan_data: Dict[str, Any]) -> str:
        """Save scan results to database.
        
        Args:
            scan_data: Scan results dictionary
            
        Returns:
            Unique scan ID
        """
        pass
    
    @abstractmethod
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scan results by ID.
        
        Args:
            scan_id: Unique scan ID
            
        Returns:
            Scan data dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def list_scans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent scans.
        
        Args:
            limit: Maximum number of scans to return
            
        Returns:
            List of scan metadata dictionaries
        """
        pass


class NullDatabaseClient(DatabaseClient):
    """No-op database client (used when DB is not configured)."""
    
    def connect(self) -> None:
        pass
    
    def disconnect(self) -> None:
        pass
    
    def save_scan(self, scan_data: Dict[str, Any]) -> str:
        return ""
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        return None
    
    def list_scans(self, limit: int = 100) -> List[Dict[str, Any]]:
        return []


# Future implementation example:
# class PostgresClient(DatabaseClient):
#     def __init__(self, connection_string: str):
#         self.connection_string = connection_string
#         self.conn = None
#
#     def connect(self):
#         import psycopg2
#         self.conn = psycopg2.connect(self.connection_string)
#     ...
