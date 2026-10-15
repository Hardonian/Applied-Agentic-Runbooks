"""
Base storage backend interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO


@dataclass
class StorageFile:
    """Represents a file in storage."""
    path: str
    size: int
    content_type: str | None = None
    last_modified: datetime | None = None
    metadata: dict | None = None
    url: str | None = None


class StorageBackend(ABC):
    """Abstract storage backend interface."""
    
    @abstractmethod
    def upload(self, path: str, file_obj: BinaryIO, content_type: str | None = None) -> str:
        """
        Upload a file.
        
        Args:
            path: Storage path
            file_obj: File-like object
            content_type: Optional content type
            
        Returns:
            Storage URL or path
        """
    
    @abstractmethod
    def download(self, path: str) -> BinaryIO:
        """
        Download a file.
        
        Args:
            path: Storage path
            
        Returns:
            File-like object
        """
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Delete a file.
        
        Args:
            path: Storage path
            
        Returns:
            True if deleted, False if not found
        """
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            path: Storage path
            
        Returns:
            True if exists, False otherwise
        """
    
    @abstractmethod
    def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """
        List files.
        
        Args:
            prefix: Path prefix filter
            limit: Maximum number of results
            
        Returns:
            List of storage files
        """
    
    @abstractmethod
    def get_url(self, path: str, expires_in: int | None = None) -> str:
        """
        Get URL for file access.
        
        Args:
            path: Storage path
            expires_in: Optional expiration in seconds (for signed URLs)
            
        Returns:
            URL string
        """
