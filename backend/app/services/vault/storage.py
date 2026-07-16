"""Object storage adapters for the Digital Evidence Vault."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ...core.config import ROOT, get_settings


class StorageAdapter(ABC):
    backend: str

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError


class LocalFilesystemStorage(StorageAdapter):
    backend = "local"

    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        configured = (settings.vault_local_path or "").strip()
        self.root = Path(configured) if configured else (root or (ROOT / "storage" / "vault"))
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.lstrip("/").replace("..", "_")
        path = self.root / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(f"Evidence object not found: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()


class S3Storage(StorageAdapter):
    """S3-compatible adapter (boto3). Used when VAULT_STORAGE=s3."""

    backend = "s3"

    def __init__(self) -> None:
        settings = get_settings()
        bucket = (settings.vault_s3_bucket or "").strip()
        if not bucket:
            raise ValueError("VAULT_S3_BUCKET is required when VAULT_STORAGE=s3")
        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise ValueError("boto3 is required for VAULT_STORAGE=s3") from exc

        kwargs: dict = {"region_name": settings.vault_s3_region or "us-east-1"}
        if settings.vault_s3_endpoint_url:
            kwargs["endpoint_url"] = settings.vault_s3_endpoint_url
        if settings.vault_s3_access_key and settings.vault_s3_secret_key:
            kwargs["aws_access_key_id"] = settings.vault_s3_access_key
            kwargs["aws_secret_access_key"] = settings.vault_s3_secret_key
        self.bucket = bucket
        self.client = boto3.client("s3", **kwargs)

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def get_storage_adapter() -> StorageAdapter:
    settings = get_settings()
    backend = (settings.vault_storage or "local").strip().lower()
    if backend == "s3":
        return S3Storage()
    return LocalFilesystemStorage()
