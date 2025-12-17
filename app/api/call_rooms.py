from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.call_room import CallRoom
from app.models.user import User
from app.auth.security import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(tags=["Call Rooms"])


class CallRoomCreate(BaseModel):
    name: str
    slug: str
    is_public: bool = False


class CallRoomDisplay(BaseModel):
    id: int
    name: str
    slug: str
    is_public: bool
    created_by: Optional[int] = None  # Can be None for system-created rooms
    member_count: int
    active_members: List[str] = []  # Usernames of currently connected members

    class Config:
        from_attributes = True


class CallRoomMemberDisplay(BaseModel):
    username: str
    avatar_url: str

    class Config:
        from_attributes = True


@router.get("/call-rooms", response_model=List[CallRoomDisplay])
async def get_call_rooms(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all call rooms the user can access (public rooms + rooms they're invited to)."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get public rooms
    public_rooms = db.query(CallRoom).filter(CallRoom.is_public == True).all()

    # Get rooms where user is a member
    from app.models.call_room import call_room_members
    member_room_ids = db.query(call_room_members.c.call_room_id).filter(
        call_room_members.c.user_id == user.id
    ).all()
    member_rooms = db.query(CallRoom).filter(CallRoom.id.in_([r[0] for r in member_room_ids])).all()

    # Combine and deduplicate
    all_rooms = {room.id: room for room in public_rooms}
    for room in member_rooms:
        all_rooms[room.id] = room

    # Convert to display format
    result = []
    for room in all_rooms.values():
        result.append(CallRoomDisplay(
            id=room.id,
            name=room.name,
            slug=room.slug,
            is_public=room.is_public,
            created_by=room.created_by,
            member_count=len(room.members),
            active_members=[]  # Will be populated by WebSocket manager
        ))

    return result


@router.post("/call-rooms", response_model=CallRoomDisplay)
async def create_call_room(
    room_data: CallRoomCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new call room."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if slug already exists
    existing = db.query(CallRoom).filter(CallRoom.slug == room_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Call room with this slug already exists")

    # Create room
    call_room = CallRoom(
        name=room_data.name,
        slug=room_data.slug,
        created_by=user.id,
        is_public=room_data.is_public
    )

    db.add(call_room)
    db.commit()
    db.refresh(call_room)

    # Add creator as member
    call_room.members.append(user)
    db.commit()

    return CallRoomDisplay(
        id=call_room.id,
        name=call_room.name,
        slug=call_room.slug,
        is_public=call_room.is_public,
        created_by=call_room.created_by,
        member_count=1,
        active_members=[]
    )


@router.post("/call-rooms/{slug}/join")
async def join_call_room(
    slug: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Join a call room (add as member if not already)."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    call_room = db.query(CallRoom).filter(CallRoom.slug == slug).first()
    if not call_room:
        raise HTTPException(status_code=404, detail="Call room not found")

    # Check if user is already a member
    if user not in call_room.members:
        call_room.members.append(user)
        db.commit()

    return {"message": "Joined call room successfully", "slug": slug}


@router.post("/call-rooms/{slug}/leave")
async def leave_call_room(
    slug: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Leave a call room (remove from members)."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    call_room = db.query(CallRoom).filter(CallRoom.slug == slug).first()
    if not call_room:
        raise HTTPException(status_code=404, detail="Call room not found")

    # Remove user from members
    if user in call_room.members:
        call_room.members.remove(user)
        db.commit()

    return {"message": "Left call room successfully", "slug": slug}


@router.get("/call-rooms/{slug}/members", response_model=List[CallRoomMemberDisplay])
async def get_call_room_members(
    slug: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all members of a call room."""
    call_room = db.query(CallRoom).filter(CallRoom.slug == slug).first()
    if not call_room:
        raise HTTPException(status_code=404, detail="Call room not found")

    members = []
    for member in call_room.members:
        members.append(CallRoomMemberDisplay(
            username=member.username,
            avatar_url=member.avatar_url
        ))

    return members


@router.post("/call-rooms/{slug}/invite/{username}")
async def invite_to_call_room(
    slug: str,
    username: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Invite a user to a call room."""
    call_room = db.query(CallRoom).filter(CallRoom.slug == slug).first()
    if not call_room:
        raise HTTPException(status_code=404, detail="Call room not found")

    user_to_invite = db.query(User).filter(User.username == username).first()
    if not user_to_invite:
        raise HTTPException(status_code=404, detail="User not found")

    # Add user to members if not already
    if user_to_invite not in call_room.members:
        call_room.members.append(user_to_invite)
        db.commit()

    return {"message": f"Invited {username} to call room", "slug": slug}
