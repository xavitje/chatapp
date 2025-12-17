"""Update room memberships - remove dev-team for users not explicitly invited"""
from app.database.database import SessionLocal
from app.models.user import User
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.message import Message
from app.models.direct_message import DirectMessage

def update_memberships():
    db = SessionLocal()
    try:
        # Get dev-team room
        dev_team_room = db.query(Room).filter(Room.slug == "dev-team").first()

        if dev_team_room:
            # Remove all memberships from dev-team (they can be re-invited later)
            db.query(RoomMember).filter(RoomMember.room_id == dev_team_room.id).delete()
            db.commit()
            print(f"Removed all users from Dev Team room. Room creator can now invite specific users.")

        # Ensure general room exists and all users are members
        general_room = db.query(Room).filter(Room.slug == "general").first()
        if general_room:
            users = db.query(User).all()
            for user in users:
                existing = db.query(RoomMember).filter(
                    RoomMember.user_id == user.id,
                    RoomMember.room_id == general_room.id
                ).first()

                if not existing:
                    membership = RoomMember(user_id=user.id, room_id=general_room.id)
                    db.add(membership)
                    print(f"Added {user.username} to General")

            db.commit()
            print(f"\nUpdate complete! All users have access to General room only.")
            print(f"Dev Team room is now empty - invite users as needed.")

    finally:
        db.close()

if __name__ == "__main__":
    update_memberships()
