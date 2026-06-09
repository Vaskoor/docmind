from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db, User, File as FileModel, Chatbot, APIKey
from app.schemas import (
    UserResponse, UpdateProfileRequest, UpdatePasswordRequest,
    UpdatePreferencesRequest, APIKeyResponse, CreateAPIKeyResponse,
    DashboardStats
)
from app.auth import get_current_user, verify_password, hash_password, generate_api_key

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.first_name:
        current_user.first_name = payload.first_name.strip()
    if payload.last_name:
        current_user.last_name = payload.last_name.strip()
    if payload.organization is not None:
        current_user.organization = payload.organization

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
async def change_password(
    payload: UpdatePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.patch("/me/preferences", response_model=UserResponse)
async def update_preferences(
    payload: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/plan")
async def upgrade_plan(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if plan not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    current_user.plan = plan
    db.commit()
    return {"message": f"Plan upgraded to {plan}", "plan": plan}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import os, shutil
    # Delete user uploads folder
    user_dir = f"uploads/{current_user.id}"
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}


# ── Dashboard Stats ────────────────────────────────────────────────────────────

@router.get("/me/stats", response_model=DashboardStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(FileModel).filter(FileModel.user_id == current_user.id).all()
    bots = db.query(Chatbot).filter(
        Chatbot.user_id == current_user.id,
        Chatbot.status == "active"
    ).count()

    total_chunks = sum(f.chunk_count for f in files)

    # Group by category
    by_cat = {}
    for f in files:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1

    # Group by file type
    by_type = {}
    for f in files:
        by_type[f.file_type] = by_type.get(f.file_type, 0) + 1

    storage_gb = current_user.storage_used_bytes / (1024 ** 3)

    return DashboardStats(
        total_files=len(files),
        active_chatbots=bots,
        total_chunks=total_chunks,
        storage_used_bytes=current_user.storage_used_bytes,
        storage_limit_bytes=current_user.storage_limit_bytes,
        storage_used_gb=round(storage_gb, 2),
        files_by_category=by_cat,
        files_by_type=by_type,
    )


# ── API Keys ──────────────────────────────────────────────────────────────────

@router.get("/me/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(APIKey).filter(APIKey.user_id == current_user.id).all()


@router.post("/me/api-keys", response_model=CreateAPIKeyResponse, status_code=201)
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Limit to 5 active keys
    key_count = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()
    if key_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 API keys allowed")

    raw_key, prefix, hashed = generate_api_key()

    api_key = APIKey(
        user_id=current_user.id,
        name=name,
        key_prefix=prefix,
        hashed_key=hashed,
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return CreateAPIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,  # Only shown once!
        key_prefix=prefix,
        created_at=api_key.created_at,
    )


@router.delete("/me/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    db.commit()
    return {"message": "API key revoked"}
