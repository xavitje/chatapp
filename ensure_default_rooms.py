"""
Ensure default chat rooms exist in the database
"""
from app.database.database import SessionLocal
from app.models.room import Room

def ensure_default_rooms():
    db = SessionLocal()
    try:
        # Check if general room exists
        general_room = db.query(Room).filter(Room.slug == 'general').first()
        if not general_room:
            general_room = Room(
                name='Algemeen',
                slug='general',
                description='Algemene chat voor iedereen'
            )
            db.add(general_room)
            print("✅ Created 'general' room")
        else:
            print("ℹ️  'general' room already exists")

        # Check if dev-team room exists
        dev_room = db.query(Room).filter(Room.slug == 'dev-team').first()
        if not dev_room:
            dev_room = Room(
                name='Dev Team',
                slug='dev-team',
                description='Chat voor het development team'
            )
            db.add(dev_room)
            print("✅ Created 'dev-team' room")
        else:
            print("ℹ️  'dev-team' room already exists")

        db.commit()
        print("✅ Default rooms ensured")
    except Exception as e:
        print(f"❌ Error ensuring default rooms: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ensure_default_rooms()
