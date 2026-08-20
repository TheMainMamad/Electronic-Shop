import secrets
import uuid
from pathlib import Path
from typing import Protocol

from app.common.errors import AppError
from app.core.config import get_settings

settings = get_settings()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_BYTES = settings.max_upload_size_mb * 1024 * 1024


class UnsupportedFileError(AppError):
    code = "UNSUPPORTED_FILE_TYPE"
    message = "فرمت فایل پشتیبانی نمی‌شود. فقط تصاویر jpg، png و webp مجاز است."


class FileTooLargeError(AppError):
    code = "FILE_TOO_LARGE"
    message = "حجم فایل بیش از حد مجاز است."


class StorageBackend(Protocol):
    def save(self, *, content: bytes, content_type: str) -> str: ...


class LocalImageStorage:
    """Local filesystem storage. Swap for an S3-compatible backend by
    implementing the same `save` signature — callers never construct paths
    themselves, so nothing else needs to change."""

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.storage_root) / "products"
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, *, content: bytes, content_type: str) -> str:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise UnsupportedFileError()
        if len(content) > MAX_UPLOAD_BYTES:
            raise FileTooLargeError()

        extension = ALLOWED_IMAGE_TYPES[content_type]
        # Never trust the client-provided filename: generate our own.
        filename = f"{uuid.uuid4().hex}{secrets.token_hex(4)}{extension}"
        destination = self.root / filename
        destination.write_bytes(content)
        return f"/media/products/{filename}"


_storage: StorageBackend | None = None


def get_image_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        _storage = LocalImageStorage()
    return _storage
