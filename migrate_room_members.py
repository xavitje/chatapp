"""Add room memberships and migrate existing data"""
from app.database.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.message import Message
from app.models.direct_message import DirectMessage

def migrate():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()

        # Get general room (everyone gets access)
        general_room = db.query(Room).filter(Room.slug == "general").first()

        # Add all users to general room only
        if general_room:
            for user in users:
                # Check if membership already exists
                existing = db.query(RoomMember).filter(
                    RoomMember.user_id == user.id,
                    RoomMember.room_id == general_room.id
                ).first()

                if not existing:
                    membership = RoomMember(user_id=user.id, room_id=general_room.id)
                    db.add(membership)
                    print(f"Added {user.username} to {general_room.name}")

        db.commit()
        print(f"\nMigration complete! All {len(users)} users added to default rooms.")

    finally:
        db.close()

if __name__ == "__main__":
    migrate()
