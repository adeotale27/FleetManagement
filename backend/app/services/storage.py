from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.repositories.base import TenantRepository, utcnow

ALLOWED = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
MAX = 8 * 1024 * 1024


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, upload: UploadFile) -> tuple[str, int, str]:
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in ALLOWED:
            raise AppError("FILE_TYPE", "This file type is not allowed")
        data = await upload.read()
        if len(data) > MAX:
            raise AppError("FILE_TOO_LARGE", "File must be under 8 MB")
        name = f"{uuid4().hex}-{Path(upload.filename or 'file').name}"
        path = self.root / name
        path.write_bytes(data)
        return str(path), len(data), content_type


class FileService:
    def __init__(self, db):
        self.repo = TenantRepository(db, "files")
        self.storage = LocalStorage(get_settings().storage_dir)

    async def upload(self, tenant_id: str, user_id: str, entity: str, entity_id: str, upload: UploadFile) -> dict:
        stored, size, mime = await self.storage.save(upload)
        return await self.repo.insert(
            tenant_id,
            {
                "filename": upload.filename,
                "stored_path": stored,
                "size": size,
                "mime": mime,
                "entity": entity,
                "entity_id": entity_id,
                "status": "active",
                "uploaded_at": utcnow(),
            },
            user_id,
        )
