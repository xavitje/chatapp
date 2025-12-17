from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.api.schemas import DirectMessageCreate, DirectMessageDisplay, UserInfo
from app.models.user import User
from app.models.direct_message import DirectMessage
from app.auth.security import get_current_user

router = APIRouter(tags=["Direct Messages"])


@router.get("/users", response_model=List[UserInfo])
def get_all_users(db: Session = Depends(get_db)):
    """Haal alle geregistreerde gebruikers op."""
    users = db.query(User).filter(User.is_active == True).all()
    return [UserInfo(username=user.username, is_active=user.is_active) for user in users]


@router.post("/direct-message", status_code=status.HTTP_201_CREATED)
async def send_direct_message(
    message_data: DirectMessageCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Stuur een direct bericht naar een andere gebruiker."""
    # Get sender
    sender = db.query(User).filter(User.username == current_user.username).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    # Get receiver
    receiver = db.query(User).filter(User.username == message_data.receiver_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Can't send message to yourself
    if sender.id == receiver.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")

    # Create message
    new_message = DirectMessage(
        sender_id=sender.id,
        receiver_id=receiver.id,
        content=message_data.content
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "message": "Direct message sent successfully",
        "message_id": new_message.id
    }


@router.get("/direct-messages/{username}", response_model=List[DirectMessageDisplay])
async def get_conversation(
    username: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Haal het gesprek op tussen de huidige gebruiker en een andere gebruiker."""
    # Get current user
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get other user
    other_user = db.query(User).filter(User.username == username).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all messages between these two users
    messages = db.query(DirectMessage).filter(
        ((DirectMessage.sender_id == user.id) & (DirectMessage.receiver_id == other_user.id)) |
        ((DirectMessage.sender_id == other_user.id) & (DirectMessage.receiver_id == user.id))
    ).order_by(DirectMessage.timestamp).all()

    # Mark messages as read if they're sent to current user
    for msg in messages:
        if msg.receiver_id == user.id and not msg.is_read:
            msg.is_read = True
    db.commit()

    # Convert to display format
    return [
        DirectMessageDisplay(
            id=msg.id,
            content=msg.content,
            timestamp=msg.timestamp,
            sender_username=msg.sender.username,
            receiver_username=msg.receiver.username,
            is_read=msg.is_read
        )
        for msg in messages
    ]


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Haal het aantal ongelezen berichten op voor de huidige gebruiker."""
    user = db.query(User).filter(User.username == current_user.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    unread_count = db.query(DirectMessage).filter(
        DirectMessage.receiver_id == user.id,
        DirectMessage.is_read == False
    ).count()

    return {"unread_count": unread_count}
