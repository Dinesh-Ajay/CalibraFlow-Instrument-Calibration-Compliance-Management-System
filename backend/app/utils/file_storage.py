import os
import re
import uuid
from fastapi import UploadFile, HTTPException, status
from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\.\-]", "_", os.path.basename(filename))
    return cleaned or "certificate.pdf"


async def save_uploaded_file(file: UploadFile, subfolder: str = "certificates") -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' not allowed. Permitted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    target_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{sanitize_filename(file.filename)}"
    dest_path = os.path.join(target_dir, unique_name)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit ({settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB)"
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    return dest_path
