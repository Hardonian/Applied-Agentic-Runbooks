"""Supabase Storage backend."""

import os
from typing import BinaryIO

from agent_factory.database.supabase_client import (
    get_supabase_storage_bucket,
    is_supabase_configured,
)
from agent_factory.storage.base import StorageBackend, StorageFile


class SupabaseStorage(StorageBackend):
    """Supabase Storage backend implementation."""
    
    def __init__(self, bucket_name: str = "agent-factory"):
        """
        Initialize Supabase storage backend.
        
        Args:
            bucket_name: Name of the Supabase storage bucket
        """
        if not is_supabase_configured():
            raise ValueError(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
            )
        
        self.bucket_name = bucket_name
        self._bucket = None
    
    @property
    def bucket(self):
        """Get Supabase storage bucket (lazy initialization)."""
        if self._bucket is None:
            self._bucket = get_supabase_storage_bucket(self.bucket_name)
            if not self._bucket:
                raise ValueError(f"Failed to get Supabase storage bucket: {self.bucket_name}")
        return self._bucket
    
    def upload(self, path: str, file_obj: BinaryIO, content_type: str | None = None) -> str:
        """
        Upload a file to Supabase storage.
        
        Args:
            path: Destination path in storage
            file_obj: File-like object to upload
            content_type: MIME type of the file
            
        Returns:
            Storage path
        """
        file_data = file_obj.read()
        
        # Upload to Supabase
        self.bucket.upload(
            path,
            file_data,
            file_options={"content-type": content_type} if content_type else None
        )
        
        return path
    
    def download(self, path: str) -> BinaryIO:
        """
        Download a file from Supabase storage.
        
        Args:
            path: Path to file in storage
            
        Returns:
            File-like object
        """
        from io import BytesIO
        result = self.bucket.download(path)
        file_obj = BytesIO(result)
        file_obj.seek(0)
        return file_obj
    
    def delete(self, path: str) -> bool:
        """
        Delete a file from Supabase storage.
        
        Args:
            path: Path to file in storage
            
        Returns:
            True if deleted successfully
        """
        try:
            self.bucket.remove([path])
            return True
        except Exception:
            return False
    
    def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """
        List files in Supabase storage.
        
        Args:
            prefix: Path prefix to filter files
            limit: Maximum number of results
            
        Returns:
            List of StorageFile objects
        """
        result = self.bucket.list(prefix=prefix or "", limit=limit)
        
        supabase_url = os.getenv("SUPABASE_URL")
        files = []
        
        for item in result:
            file_path = item.get("name", "")
            public_url = f"{supabase_url}/storage/v1/object/public/{self.bucket_name}/{file_path}"
            
            files.append(StorageFile(
                path=file_path,
                url=public_url,
                size=item.get("metadata", {}).get("size", 0),
                content_type=item.get("metadata", {}).get("mimetype"),
            ))
        
        return files
    
    def get_url(self, path: str, expires_in: int | None = None) -> str:
        """
        Get public URL for a file.
        
        Args:
            path: Path to file in storage
            expires_in: Optional expiration in seconds (for signed URLs)
                        Note: Supabase Storage doesn't support signed URLs in the same way as S3
                        This parameter is accepted for interface compatibility but ignored
            
        Returns:
            Public URL
        """
        supabase_url = os.getenv("SUPABASE_URL")
        return f"{supabase_url}/storage/v1/object/public/{self.bucket_name}/{path}"
    
    def exists(self, path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            path: Path to file in storage
            
        Returns:
            True if file exists
        """
        try:
            files = self.list_files(prefix=path)
            return any(f.path == path for f in files)
        except Exception:
            return False
