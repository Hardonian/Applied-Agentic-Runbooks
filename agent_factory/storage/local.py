"""
Local filesystem storage backend.
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from agent_factory.storage.base import StorageBackend, StorageFile


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, base_path: str = "./storage"):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, path: str, file_obj: BinaryIO, content_type: str | None = None) -> str:
        """Upload a file."""
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(file_obj.read())
        
        return str(file_path.relative_to(self.base_path))
    
    def download(self, path: str) -> BinaryIO:
        """Download a file."""
        file_path = self.base_path / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(file_path, "rb") as f:
            return BytesIO(f.read())
    
    def delete(self, path: str) -> bool:
        """Delete a file."""
        file_path = self.base_path / path
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        file_path = self.base_path / path
        return file_path.exists()
    
    def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """List files."""
        files = []
        prefix_path = self.base_path / prefix if prefix else self.base_path
        
        if not prefix_path.exists():
            return files
        
        count = 0
        for file_path in prefix_path.rglob("*"):
            if file_path.is_file() and count < limit:
                stat = file_path.stat()
                files.append(StorageFile(
                    path=str(file_path.relative_to(self.base_path)),
                    size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                ))
                count += 1
        
        return files
    
    def get_url(self, path: str, expires_in: int | None = None) -> str:
        """Get URL for file access."""
        # For local storage, return file:// URL
        file_path = self.base_path / path
        return f"file://{file_path.absolute()}"
