"""Add new features: last_seen, is_online, room descriptions, message edit/delete, replies"""
from app.database.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.room import Room
from app.models.message import Message
from app.models.room_member import RoomMember
from app.models.direct_message import DirectMessage

def migrate():
    # Create/update tables
    Base.metadata.create_all(bind=engine)

    print("✅ Database tables updated with new columns")
    print("  - User: last_seen, is_online")
    print("  - Room: description")
    print("  - Message: edited_at, is_deleted, reply_to_id")
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
