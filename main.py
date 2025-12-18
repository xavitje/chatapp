from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from app.database.database import engine, Base, SessionLocal
from app.api import auth, chat, pages, direct_messages, profile, rooms, files, call_rooms
from app.models.room import Room

laptop = "127.0.0.1"
vps = "0.0.0.0"

app = FastAPI(title="Modern Real-Time Chat App", description="Backend met FastAPI, DB en WebSockets.")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure default rooms exist on startup
@app.on_event("startup")
def ensure_default_rooms():
    db = SessionLocal()
    try:
        # Check if general room exists
        if not db.query(Room).filter(Room.slug == 'general').first():
            general_room = Room(name='Algemeen', slug='general', description='Algemene chat voor iedereen')
            db.add(general_room)
            print("✅ Created 'general' room")

        # Check if dev-team room exists
        if not db.query(Room).filter(Room.slug == 'dev-team').first():
            dev_room = Room(name='Dev Team', slug='dev-team', description='Chat voor het development team')
            db.add(dev_room)
            print("✅ Created 'dev-team' room")

        db.commit()
    except Exception as e:
        print(f"⚠️  Error ensuring default rooms: {e}")
        db.rollback()
    finally:
        db.close()

app.include_router(auth.router, prefix="/auth")
app.include_router(chat.router, prefix="/api")
app.include_router(direct_messages.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(call_rooms.router, prefix="/api")
app.include_router(pages.router)


@app.get("/")
def read_root():
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    uvicorn.run("main:app", host=laptop, port=5000, reload=True)
