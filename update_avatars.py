"""Update avatar URLs from .png to .svg"""
from app.database.database import SessionLocal
# Import all models to ensure relationships are properly set up
from app.models.user import User
from app.models.message import Message
from app.models.room import Room
from app.models.direct_message import DirectMessage

def update_avatar_urls():
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.avatar_url == '/static/default-avatar.png').all()
        for user in users:
            user.avatar_url = '/static/default-avatar.svg'
        db.commit()
        print(f'Updated {len(users)} users')
    finally:
        db.close()

if __name__ == "__main__":
    update_avatar_urls()
