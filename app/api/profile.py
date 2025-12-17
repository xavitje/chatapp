from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.database.database import get_db
from app.models.user import User
from app.auth.security import get_current_user
from app.api.schemas import UserBase
from pydantic import BaseModel
import shutil
import os
from pathlib import Path

router = APIRouter(tags=["User Profile"])


class UserSettings(BaseModel):
    theme_preference: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserProfile(BaseModel):
    username: str
    avatar_url: str
    theme_preference: str
    notifications_enabled: bool
    is_active: bool
    public_key: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/profile/me", response_model=UserProfile)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Haal het profiel van de ingelogde gebruiker op."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/profile/{username}", response_model=UserProfile)
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    """Haal het profiel van een specifieke gebruiker op."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/profile/settings")
async def update_settings(
    settings: UserSettings,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update gebruikersinstellingen."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if settings.theme_preference is not None:
        user.theme_preference = settings.theme_preference
    if settings.notifications_enabled is not None:
        user.notifications_enabled = settings.notifications_enabled

    db.commit()
    db.refresh(user)

    return {"message": "Settings updated successfully", "user": UserProfile.from_orm(user)}


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Upload een avatar afbeelding."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")

    # Create avatars directory if it doesn't exist
    avatars_dir = Path("static/avatars")
    avatars_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    file_extension = file.filename.split(".")[-1]
    filename = f"{user.username}_{user.id}.{file_extension}"
    file_path = avatars_dir / filename

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update user avatar URL
    user.avatar_url = f"/static/avatars/{filename}"
    db.commit()
    db.refresh(user)

    return {"message": "Avatar uploaded successfully", "avatar_url": user.avatar_url}


class PublicKeyRequest(BaseModel):
    public_key: str


@router.post("/profile/public-key")
async def store_public_key(
    request: PublicKeyRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Store user's public key for E2E encryption."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.public_key = request.public_key
    db.commit()
    return {"message": "Public key stored successfully"}

@router.get("/profile/{username}/public-key")
async def get_public_key(username: str, db: Session = Depends(get_db)):
    """Get a user's public key for E2E encryption."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.public_key:
        raise HTTPException(status_code=404, detail="User has no public key")

    return {"username": username, "public_key": user.public_key}
