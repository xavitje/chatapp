from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base

class Room(Base):
    """Database model voor een chatkamer."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False) # Gebruikt in de URL/WebSocket
    description = Column(String, default="")

    # Relatie naar berichten in deze kamer
    messages = relationship("Message", back_populates="room")
    members = relationship("RoomMember", back_populates="room")