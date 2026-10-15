"""
Tests for storage abstraction layer.
"""

import tempfile
from io import BytesIO

from agent_factory.storage.local import LocalStorage


def test_local_storage_upload():
    """Test local storage upload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        file_obj = BytesIO(b"test content")
        path = storage.upload("test.txt", file_obj)
        
        assert path == "test.txt"
        assert storage.exists("test.txt")


def test_local_storage_download():
    """Test local storage download."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        # Upload file
        file_obj = BytesIO(b"test content")
        storage.upload("test.txt", file_obj)
        
        # Download file
        downloaded = storage.download("test.txt")
        content = downloaded.read()
        
        assert content == b"test content"


def test_local_storage_delete():
    """Test local storage delete."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        # Upload file
        file_obj = BytesIO(b"test content")
        storage.upload("test.txt", file_obj)
        
        # Delete file
        deleted = storage.delete("test.txt")
        
        assert deleted is True
        assert not storage.exists("test.txt")


def test_local_storage_exists():
    """Test local storage exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        assert not storage.exists("nonexistent.txt")
        
        file_obj = BytesIO(b"test content")
        storage.upload("test.txt", file_obj)
        
        assert storage.exists("test.txt")


def test_local_storage_list_files():
    """Test local storage list files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        # Upload multiple files
        storage.upload("file1.txt", BytesIO(b"content1"))
        storage.upload("file2.txt", BytesIO(b"content2"))
        storage.upload("subdir/file3.txt", BytesIO(b"content3"))
        
        files = storage.list_files()
        
        assert len(files) >= 3
        file_paths = [f.path for f in files]
        assert "file1.txt" in file_paths
        assert "file2.txt" in file_paths


def test_local_storage_get_url():
    """Test local storage get URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorage(base_path=tmpdir)
        
        file_obj = BytesIO(b"test content")
        storage.upload("test.txt", file_obj)
        
        url = storage.get_url("test.txt")
        
        assert url.startswith("file://")
        assert "test.txt" in url
