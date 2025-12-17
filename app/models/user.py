from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String, default="/static/default-avatar.svg")
    theme_preference = Column(String, default="dark")
    notifications_enabled = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=False)
    public_key = Column(String, nullable=True)  # For E2E encryption

    # Relaties
    messages = relationship("Message", back_populates="sender")
    sent_messages = relationship("DirectMessage", foreign_keys="DirectMessage.sender_id", back_populates="sender")
    received_messages = relationship("DirectMessage", foreign_keys="DirectMessage.receiver_id", back_populates="receiver")
    room_memberships = relationship("RoomMember", back_populates="user")
    created_call_rooms = relationship("CallRoom", foreign_keys="CallRoom.created_by", back_populates="creator")