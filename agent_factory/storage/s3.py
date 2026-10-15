"""
S3 storage backend.
"""

import os
from io import BytesIO
from typing import BinaryIO

from agent_factory.storage.base import StorageBackend, StorageFile
from agent_factory.storage.local import LocalStorage


class S3Storage(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region: str = "us-east-1",
    ):
        """
        Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID (optional, uses env vars if not provided)
            aws_secret_access_key: AWS secret access key (optional, uses env vars if not provided)
            region: AWS region
        """
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 package is required for S3Storage")
        
        self.bucket_name = bucket_name
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region or os.getenv("AWS_REGION", "us-east-1"),
        )
    
    def upload(self, path: str, file_obj: BinaryIO, content_type: str | None = None) -> str:
        """Upload a file."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        self.s3_client.upload_fileobj(file_obj, self.bucket_name, path, ExtraArgs=extra_args)
        return path
    
    def download(self, path: str) -> BinaryIO:
        """Download a file."""
        file_obj = BytesIO()
        self.s3_client.download_fileobj(self.bucket_name, path, file_obj)
        file_obj.seek(0)
        return file_obj
    
    def delete(self, path: str) -> bool:
        """Delete a file."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception:
            return False
    
    def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """List files."""
        files = []
        
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix, MaxKeys=limit)
        
        for page in pages:
            for obj in page.get("Contents", []):
                files.append(StorageFile(
                    path=obj["Key"],
                    size=obj["Size"],
                    last_modified=obj["LastModified"],
                ))
        
        return files
    
    def get_url(self, path: str, expires_in: int | None = None) -> str:
        """Get URL for file access."""
        if expires_in:
            # Generate presigned URL
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": path},
                ExpiresIn=expires_in,
            )
        else:
            # Public URL
            return f"https://{self.bucket_name}.s3.amazonaws.com/{path}"


def get_storage_backend(storage_type: str | None = None, **kwargs) -> StorageBackend:
    """
    Get storage backend instance.
    
    Args:
        storage_type: Type of storage ("local", "s3", or "supabase")
                      If None, auto-detect from environment
        **kwargs: Additional arguments
        
    Returns:
        StorageBackend instance
    """
    # Auto-detect storage type from environment
    if storage_type is None:
        storage_type = os.getenv("STORAGE_TYPE", "local")
    
    if storage_type == "local":
        base_path = str(kwargs.get("base_path") or os.getenv("STORAGE_PATH", "./storage"))
        return LocalStorage(base_path=base_path)
    elif storage_type == "s3":
        bucket_name = kwargs.get("bucket_name") or os.getenv("AWS_S3_BUCKET")
        if not bucket_name:
            raise ValueError("bucket_name required for S3 storage")
        return S3Storage(
            bucket_name=bucket_name,
            aws_access_key_id=kwargs.get("aws_access_key_id"),
            aws_secret_access_key=kwargs.get("aws_secret_access_key"),
            region=kwargs.get("region", "us-east-1"),
        )
    elif storage_type == "supabase":
        try:
            from agent_factory.storage.supabase import SupabaseStorage
        except ImportError:
            raise ImportError("Supabase storage requires supabase package. Install with: pip install supabase")
        
        bucket_name = str(kwargs.get("bucket_name") or os.getenv("SUPABASE_STORAGE_BUCKET", "agent-factory"))
        return SupabaseStorage(bucket_name=bucket_name)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
