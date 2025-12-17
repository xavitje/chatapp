# app/api/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Basismodel voor gebruikers
class UserBase(BaseModel):
    username: str

# Model voor registratie (inclusief wachtwoord)
class UserCreate(UserBase):
    password: str

# Model voor het inloggen
class UserLogin(BaseModel):
    username: str
    password: str

# Reply context schema
class ReplyContext(BaseModel):
    id: int
    username: str
    content: str

# File attachment schema
class FileAttachmentDisplay(BaseModel):
    id: int
    original_filename: str
    file_path: str
    file_size: int
    content_type: str

    class Config:
        from_attributes = True

# Model voor het bericht dat naar de frontend gaat (vereist later in Fase 3.4)
class MessageDisplay(BaseModel):
    id: int
    content: str
    timestamp: datetime
    username: str
    room_slug: str
    avatar_url: Optional[str] = None
    reply_to: Optional[ReplyContext] = None
    attachments: Optional[list[FileAttachmentDisplay]] = []

    class Config:
        from_attributes = True


# Direct message schemas
class DirectMessageCreate(BaseModel):
    receiver_username: str
    content: str


class DirectMessageDisplay(BaseModel):
    id: int
    content: str
    timestamp: datetime
    sender_username: str
    receiver_username: str
    is_read: bool

    class Config:
        from_attributes = True


# User list schema
class UserInfo(BaseModel):
    username: str
    is_active: bool

    class Config:
        from_attributes = True