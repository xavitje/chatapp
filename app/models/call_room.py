from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

# Association table for call room members
call_room_members = Table(
    'call_room_members',
    Base.metadata,
    Column('call_room_id', Integer, ForeignKey('call_rooms.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow)
)

class CallRoom(Base):
    __tablename__ = "call_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    is_public = Column(Boolean, default=True)  # Public rooms visible to all by default
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships - use string references to avoid circular imports
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_call_rooms")
    members = relationship("User", secondary=call_room_members)
