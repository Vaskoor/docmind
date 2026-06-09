from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
import mimetypes
from datetime import datetime

from app.database import get_db, User, File as FileModel
from app.schemas import FileResponse, UpdateFileCategoryRequest
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/files", tags=["files"])

ALLOWED_EXTENSIONS = {
    "pdf", "csv", "docx", "doc", "txt", "json",
    "xlsx", "xls", "pptx", "ppt", "md", "html", "xml"
}

CATEGORY_KEYWORDS = {
    "medical": ["medical", "clinical", "patient", "hospital", "health", "drug", "trial", "diagnosis", "pharma", "disease"],
    "legal": ["contract", "legal", "law", "nda", "agreement", "compliance", "court", "statute", "regulation", "attorney"],
    "research": ["research", "study", "paper", "journal", "experiment", "hypothesis", "analysis", "methodology", "findings"],
    "news": ["news", "article", "press", "report", "breaking", "update", "announcement", "media", "feed"],
    "political": ["political", "senate", "congress", "government", "policy", "election", "bill", "legislation", "vote", "parliament"],
    "financial": ["financial", "revenue", "budget", "investment", "stock", "earnings", "quarterly", "profit", "balance", "fiscal"],
}


def detect_category(filename: str) -> str:
    """Simple keyword-based category detection from filename."""
    name_lower = filename.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def process_file_background(file_id: str, file_path: str, db_session_factory):
    """
    Background task: simulate file processing / chunking.
    In production, replace this with real LangChain/LlamaIndex chunking + embedding.
    """
    import time
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_record:
            return

        file_record.status = "processing"
        db.commit()

        # Simulate processing time based on file size
        size_mb = file_record.file_size / (1024 * 1024)
        time.sleep(min(size_mb * 0.5, 5))  # max 5 seconds in demo

        # Simulate chunk count based on file size and type
        base_chunks = max(10, int(file_record.file_size / 1500))
        file_record.chunk_count = base_chunks
        file_record.status = "ready"
        db.commit()

    except Exception as e:
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file_record:
            file_record.status = "error"
            file_record.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=List[FileResponse])
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Check storage limit
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    saved_files = []
    user_dir = os.path.join(settings.UPLOAD_DIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)

    for upload in files:
        if not upload.filename:
            continue

        # Validate extension
        ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '.{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Read file to check size
        content = await upload.read()
        file_size = len(content)

        if file_size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File '{upload.filename}' exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )

        # Check user storage
        if current_user.storage_used_bytes + file_size > current_user.storage_limit_bytes:
            raise HTTPException(
                status_code=413,
                detail="Storage limit exceeded. Please upgrade your plan or delete files."
            )

        # Store file
        file_id = str(uuid.uuid4())
        stored_name = f"{file_id}.{ext}"
        file_path = os.path.join(user_dir, stored_name)

        with open(file_path, "wb") as f:
            f.write(content)

        # Auto-detect category
        category = detect_category(upload.filename)

        # Create DB record
        file_record = FileModel(
            id=file_id,
            user_id=current_user.id,
            original_name=upload.filename,
            stored_name=stored_name,
            file_path=file_path,
            file_type=ext,
            file_size=file_size,
            category=category,
            status="pending",
        )
        db.add(file_record)

        # Update user storage
        current_user.storage_used_bytes += file_size

        saved_files.append(file_record)

        # Schedule background processing
        background_tasks.add_task(
            process_file_background,
            file_id,
            file_path,
            None  # passed via factory inside the task
        )

    db.commit()
    for f in saved_files:
        db.refresh(f)

    return saved_files


@router.get("", response_model=List[FileResponse])
async def list_files(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FileModel).filter(FileModel.user_id == current_user.id)

    if category and category != "all":
        query = query.filter(FileModel.category == category)
    if status:
        query = query.filter(FileModel.status == status)
    if search:
        query = query.filter(FileModel.original_name.ilike(f"%{search}%"))

    return query.order_by(FileModel.uploaded_at.desc()).all()


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.patch("/{file_id}/category", response_model=FileResponse)
async def update_category(
    file_id: str,
    payload: UpdateFileCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file.category = payload.category
    db.commit()
    db.refresh(file)
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FastAPIFileResponse(
        path=file.file_path,
        filename=file.original_name,
        media_type="application/octet-stream"
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from disk
    if os.path.exists(file.file_path):
        os.remove(file.file_path)

    # Update user storage
    current_user.storage_used_bytes = max(0, current_user.storage_used_bytes - file.file_size)

    db.delete(file)
    db.commit()
    return {"deleted": file_id, "message": "File deleted successfully"}
