# Script om de database opnieuw te initialiseren met alle modellen
# Let op: Dit verwijdert alle bestaande data!

from app.database.database import engine, Base
from app.models.user import User
from app.models.room import Room
from app.models.message import Message
from app.models.direct_message import DirectMessage

def init_db():
    """Drop alle tabellen en maak ze opnieuw aan."""
    from app.database.database import SessionLocal

    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    # Add default rooms
    print("\nAdding default rooms...")
    db = SessionLocal()
    try:
        default_rooms = [
            Room(name="Algemeen", slug="general"),
            Room(name="Dev Team", slug="dev-team"),
        ]
        for room in default_rooms:
            existing = db.query(Room).filter(Room.slug == room.slug).first()
            if not existing:
                db.add(room)
        db.commit()
        print("Default rooms added!")
    except Exception as e:
        print(f"Error adding default rooms: {e}")
        db.rollback()
    finally:
        db.close()

    # Create avatars directory
    import os
    os.makedirs("static/avatars", exist_ok=True)
    print("\nCreated avatars directory")

    print("\nDatabase initialized successfully!")
    print("\nDe volgende tabellen zijn aangemaakt:")
    print("- users")
    print("- rooms")
    print("- messages")
    print("- direct_messages")

if __name__ == "__main__":
    init_db()
