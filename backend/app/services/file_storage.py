import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

BASE_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


async def save_uploaded_file(file: UploadFile, subfolder: str = "certificates") -> str:
    target_dir = BASE_UPLOAD_DIR / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    original = os.path.basename(file.filename or "upload.bin")
    safe_name = original.replace("/", "_").replace("\\", "_")
    ext = Path(safe_name).suffix
    name = f"{uuid.uuid4().hex}{ext}"
    full_path = target_dir / name
    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)
    return str(full_path)
