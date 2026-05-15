"""Documents API — upload, list, detail, delete, reprocess, status."""
import hashlib
import os
import uuid
from datetime import date
from typing import Optional

import magic
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select, desc, func

from app.core.config import settings
from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.core.validators import validate_not_future_date
from app.models import Document, ProcessingStatus, User

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    original_filename: str
    upload_date: str
    report_date: Optional[str] = None
    lab_name: Optional[str] = None
    processing_status: str
    result_count: int = 0

    class Config:
        from_attributes = True


class DocumentDetailOut(DocumentOut):
    raw_ocr_text: Optional[str] = None
    llm_json_payload: Optional[dict] = None
    processing_error: Optional[str] = None


class DocumentStatusOut(BaseModel):
    status: str
    progress_message: Optional[str] = None
    error: Optional[str] = None


# ── MIME type validation ──────────────────────────────

ALLOWED_MIMES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}

EXACT_MIME_MAP = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".webp": "image/webp",
}


def validate_mime(file_content: bytes, filename: str) -> str:
    """Validate file MIME type using python-magic (content-based, not extension)."""
    # Read up to 8KB for MIME detection
    sample = file_content[:8192]

    detected = magic.from_buffer(sample, mime=True)

    if detected in ALLOWED_MIMES:
        return detected

    # Fallback: check extension -> MIME map (some Magic libraries misdetect PDFs)
    ext = os.path.splitext(filename.lower())[1]
    mapped = EXACT_MIME_MAP.get(ext)
    if mapped and mapped in ALLOWED_MIMES:
        return mapped

    raise HTTPException(
        status_code=400,
        detail=f"Invalid file type. Detected: {detected}. Allowed: {', '.join(sorted(ALLOWED_MIMES))}",
    )
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    # MIME validation via python-magic (content-based, not trust Client-Content-Type)
    validate_mime(content, file.filename or "unknown")

    file_hash = hashlib.sha256(content).hexdigest()

    existing = await db.execute(
        select(Document).where(Document.user_id == current_user.id, Document.file_hash == file_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Document already processed")

    doc_id = str(uuid.uuid4())
    file_path = f"/tmp/medi-vault/uploads/{doc_id}_{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        original_filename=file.filename,
        file_hash=file_hash,
        file_path=file_path,
        processing_status=ProcessingStatus.pending,
    )
    db.add(doc)
    await db.commit()

    return {"document_id": doc_id, "status": "pending"}


@router.get("/")
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Document).where(Document.user_id == current_user.id, Document.deleted_at.is_(None))
    if status_filter:
        q = q.where(Document.processing_status == status_filter)
    q = q.order_by(desc(Document.upload_date)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    docs = result.scalars().all()
    return [
        DocumentOut(
            id=str(d.id),
            original_filename=d.original_filename,
            upload_date=d.upload_date.isoformat() if d.upload_date else "",
            report_date=d.report_date.isoformat() if d.report_date else None,
            lab_name=d.lab_name,
            processing_status=d.processing_status.value,
            result_count=0,
        )
        for d in docs
    ]


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetailOut(
        id=str(doc.id),
        original_filename=doc.original_filename,
        upload_date=doc.upload_date.isoformat() if doc.upload_date else "",
        report_date=doc.report_date.isoformat() if doc.report_date else None,
        lab_name=doc.lab_name,
        processing_status=doc.processing_status.value,
        raw_ocr_text=doc.raw_ocr_text,
        llm_json_payload=doc.llm_json_payload,
        processing_error=doc.processing_error,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    from sqlalchemy import update
    await db.execute(update(Document).where(Document.id == doc.id).values(deleted_at=func.now()))
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.commit()
    return None


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.processing_status = ProcessingStatus.pending
    await db.commit()
    return {"document_id": document_id, "status": "pending"}


@router.get("/{document_id}/status")
async def document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    progress = {
        "pending": "Waiting to process",
        "ocr_processing": "Running OCR...",
        "llm_parsing": "Parsing with AI...",
        "normalizing": "Normalizing biomarkers...",
        "complete": "Complete",
        "failed": "Failed",
    }
    return DocumentStatusOut(
        status=doc.processing_status.value,
        progress_message=progress.get(doc.processing_status.value, ""),
        error=doc.processing_error,
    )
