from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.message import Message
from app.models.room import Room
from app.models.user import User
from app.api.schemas import MessageDisplay

# --- HELPER FUNCTIES ---

def get_user_by_username(db: Session, username: str):
    """Haalt een gebruiker op basis van de gebruikersnaam."""
    return db.query(User).filter(User.username == username).first()

def get_room_by_slug(db: Session, room_slug: str):
    """Haalt een kamer op basis van de slug."""
    # We voegen de kamer toe als deze nog niet bestaat (voor de demo)
    room = db.query(Room).filter(Room.slug == room_slug).first()
    if not room:
        room = Room(name=room_slug.capitalize(), slug=room_slug)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room

# --- CRUD FUNCTIES ---

def get_message_history(db: Session, room_slug: str, limit: int = 50):
    """Haalt de laatste N berichten uit een kamer op."""
    room = get_room_by_slug(db, room_slug)
    if not room:
        return []

    messages = (
        db.query(Message)
        .join(User, Message.user_id == User.id) # Join om gebruikersnaam op te halen
        .filter(Message.room_id == room.id)
        .order_by(desc(Message.timestamp))
        .limit(limit)
        .all()
    )

    # We draaien de lijst om zodat het oudste bericht bovenaan staat (chronologische volgorde)
    messages.reverse()

    # Converteer naar Pydantic schema voor de frontend
    from app.api.schemas import ReplyContext
    result = []
    for msg in messages:
        reply_context = None
        if msg.reply_to_id:
            reply_msg = db.query(Message).filter(Message.id == msg.reply_to_id).first()
            if reply_msg:
                reply_context = ReplyContext(
                    id=reply_msg.id,
                    username=reply_msg.sender.username,
                    content=reply_msg.content
                )

        # Get attachments
        from app.api.schemas import FileAttachmentDisplay
        attachments = [FileAttachmentDisplay.from_orm(att) for att in msg.attachments] if msg.attachments else []

        # Handle binary content (from corrupted messages)
        content = msg.content
        if isinstance(content, bytes):
            # Skip binary messages or convert to placeholder
            content = "[Bestand - kan niet weergeven]"

        result.append(MessageDisplay(
            id=msg.id,
            content=content,
            timestamp=msg.timestamp,
            username=msg.sender.username,
            room_slug=room_slug,
            avatar_url=msg.sender.avatar_url,
            reply_to=reply_context,
            attachments=attachments
        ))

    return result

def save_message(db: Session, username: str, room_slug: str, content: str, reply_to_id: int = None):
    """Slaat een nieuw bericht op in de database."""
    user = get_user_by_username(db, username)
    room = get_room_by_slug(db, room_slug)

    if not user or not room:
        print("Fout: Gebruiker of kamer niet gevonden.")
        return None

    new_message = Message(
        user_id=user.id,
        room_id=room.id,
        content=content,
        reply_to_id=reply_to_id
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Get reply context if this is a reply
    reply_context = None
    if reply_to_id:
        reply_msg = db.query(Message).filter(Message.id == reply_to_id).first()
        if reply_msg:
            from app.api.schemas import ReplyContext
            reply_context = ReplyContext(
                id=reply_msg.id,
                username=reply_msg.sender.username,
                content=reply_msg.content
            )

    # Get attachments
    from app.api.schemas import FileAttachmentDisplay
    attachments = [FileAttachmentDisplay.from_orm(att) for att in new_message.attachments] if new_message.attachments else []

    # Retourneer het Pydantic object voor onmiddellijke verzending
    return MessageDisplay(
        id=new_message.id,
        content=new_message.content,
        timestamp=new_message.timestamp,
        username=user.username,
        room_slug=room_slug,
        avatar_url=user.avatar_url,
        reply_to=reply_context,
        attachments=attachments
    )