from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.services.connection_manager import manager

router = APIRouter(tags=["Pages"])

# Initialiseer Jinja2 voor het renderen van de templates
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render de login pagina."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render de registratie pagina."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/chat/{room_slug}", response_class=HTMLResponse)
async def chat_page(request: Request, room_slug: str):
    """Render de hoofdchatpagina."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "room_slug": room_slug} # Geef de room_slug door aan de template
    )


@router.get("/direct-messages", response_class=HTMLResponse)
async def direct_messages_page(request: Request):
    """Render de directe berichten pagina."""
    return templates.TemplateResponse("direct_messages.html", {"request": request})


@router.get("/api/users/online")
async def get_online_users(db: Session = Depends(get_db)):
    """Get list of online users with their status."""
    online_usernames = manager.get_online_users()
    users = db.query(User).all()

    return [{
        "username": user.username,
        "avatar_url": user.avatar_url,
        "is_online": user.username in online_usernames,
        "last_seen": user.last_seen.isoformat() if user.last_seen else None
    } for user in users]
