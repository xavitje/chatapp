from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.auth.security import get_current_user
from app.models.file_attachment import FileAttachment
from app.models.message import Message
from app.models.room import Room
from app.models.user import User
from typing import List
import os
from pathlib import Path
import uuid
from datetime import datetime

router = APIRouter(tags=["Files"])

# Maximum file size: 500MB (0.5GB)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes

# Allowed file types
ALLOWED_CONTENT_TYPES = [
    # Images
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    # Documents
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "text/csv",
    # Archives
    "application/zip", "application/x-rar-compressed", "application/x-7z-compressed",
    # Video
    "video/mp4", "video/mpeg", "video/webm",
    # Audio
    "audio/mpeg", "audio/wav", "audio/webm"
]


@router.post("/rooms/{room_slug}/upload")
async def upload_file(
    room_slug: str,
    file: UploadFile = File(...),
    content: str = Form(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Upload een bestand naar een chatroom met optionele tekst."""

    # Store the message content before reading file
    message_text = content

    # Check file size
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of 500MB. Your file: {file_size / (1024*1024):.2f}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload empty file"
        )

    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed: {file.content_type}"
        )

    # Get user and room
    user = db.query(User).filter(User.username == current_user).first()
    room = db.query(Room).filter(Room.slug == room_slug).first()

    if not user or not room:
        raise HTTPException(status_code=404, detail="User or room not found")

    # Create uploads directory
    upload_dir = Path("static/uploads") / room_slug
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    # Save file
    try:
        with file_path.open("wb") as buffer:
            file_content = await file.read()
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create message for file
    # Use provided message text or default message
    message_content = message_text if message_text else f"📎 {file.filename}"

    message = Message(
        user_id=user.id,
        room_id=room.id,
        content=message_content
    )
    db.add(message)
    db.flush()  # Get message.id without committing

    # Create file attachment record
    attachment = FileAttachment(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=f"/static/uploads/{room_slug}/{unique_filename}",
        file_size=file_size,
        content_type=file.content_type,
        message_id=message.id,
        user_id=user.id
    )
    db.add(attachment)
    db.commit()
    db.refresh(message)

    # Broadcast message via WebSocket
    from app.services.connection_manager import manager
    from app.api.schemas import MessageDisplay, FileAttachmentDisplay

    # Create message display with attachment
    attachment_display = FileAttachmentDisplay(
        id=attachment.id,
        original_filename=attachment.original_filename,
        file_path=attachment.file_path,
        file_size=attachment.file_size,
        content_type=attachment.content_type
    )

    message_display = MessageDisplay(
        id=message.id,
        content=message.content,
        timestamp=message.timestamp,
        username=user.username,
        room_slug=room_slug,
        avatar_url=user.avatar_url,
        attachments=[attachment_display]
    )

    # Broadcast to WebSocket connections
    await manager.broadcast(message_display.model_dump_json(), room_slug)

    return {
        "message": "File uploaded successfully",
        "file_id": attachment.id,
        "file_url": attachment.file_path,
        "file_size": file_size,
        "message_id": message.id
    }


@router.get("/rooms/{room_slug}/search")
async def search_messages(
    room_slug: str,
    q: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Zoek berichten in een specifieke chatroom."""

    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters"
        )

    # Get room
    room = db.query(Room).filter(Room.slug == room_slug).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Search messages
    search_term = f"%{q}%"
    messages = (
        db.query(Message)
        .join(User, Message.user_id == User.id)
        .filter(Message.room_id == room.id)
        .filter(Message.content.ilike(search_term))
        .filter(Message.is_deleted == False)
        .order_by(Message.timestamp.desc())
        .limit(50)
        .all()
    )

    results = []
    for msg in messages:
        results.append({
            "id": msg.id,
            "content": msg.content,
            "username": msg.sender.username,
            "avatar_url": msg.sender.avatar_url,
            "timestamp": msg.timestamp.isoformat()
        })

    return {
        "query": q,
        "count": len(results),
        "results": results
    }
