from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User
from app.auth.security import get_current_user
from pydantic import BaseModel

router = APIRouter(tags=["Rooms"])


class RoomCreate(BaseModel):
    name: str
    slug: str


class RoomInfo(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


@router.get("/rooms", response_model=List[RoomInfo])
def get_all_rooms(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Haal alle chat kamers op waar de gebruiker lid van is."""
    # Get user
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get rooms where user is a member
    room_memberships = db.query(RoomMember).filter(RoomMember.user_id == user.id).all()
    rooms = [membership.room for membership in room_memberships]

    return rooms


@router.post("/rooms", status_code=status.HTTP_201_CREATED)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Maak een nieuwe chat kamer aan."""
    # Get user
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if room already exists
    existing_room = db.query(Room).filter(Room.slug == room_data.slug).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room with this slug already exists")

    # Create new room
    new_room = Room(
        name=room_data.name,
        slug=room_data.slug
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    # Add creator as first member
    room_member = RoomMember(
        room_id=new_room.id,
        user_id=user.id
    )
    db.add(room_member)
    db.commit()

    return {
        "message": f"Room '{new_room.name}' created successfully",
        "room": RoomInfo.from_orm(new_room)
    }


class InviteUser(BaseModel):
    username: str


@router.post("/rooms/{room_slug}/invite")
def invite_user_to_room(
    room_slug: str,
    invite_data: InviteUser,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Nodig een gebruiker uit voor een room."""
    # Get room
    room = db.query(Room).filter(Room.slug == room_slug).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Get user to invite
    user_to_invite = db.query(User).filter(User.username == invite_data.username).first()
    if not user_to_invite:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already a member
    existing_member = db.query(RoomMember).filter(
        RoomMember.room_id == room.id,
        RoomMember.user_id == user_to_invite.id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this room")

    # Add user as member
    room_member = RoomMember(
        room_id=room.id,
        user_id=user_to_invite.id
    )
    db.add(room_member)
    db.commit()

    return {"message": f"User '{invite_data.username}' invited to room '{room.name}'"}


@router.get("/rooms/{room_slug}/members")
def get_room_members(
    room_slug: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Haal alle members van een room op."""
    room = db.query(Room).filter(Room.slug == room_slug).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    members = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
    return [{"username": member.user.username, "avatar_url": member.user.avatar_url} for member in members]


@router.delete("/rooms/{room_slug}")
def delete_room(
    room_slug: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Verwijder een chat kamer."""
    room = db.query(Room).filter(Room.slug == room_slug).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Don't allow deleting default rooms
    if room_slug in ["general", "dev-team"]:
        raise HTTPException(status_code=400, detail="Cannot delete default rooms")

    db.delete(room)
    db.commit()

    return {"message": f"Room '{room.name}' deleted successfully"}
