from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from app.database.database import engine, Base
from app.api import auth, chat, pages, direct_messages, profile, rooms, files, call_rooms

laptop = "127.0.0.1"
vps = "0.0.0.0"

app = FastAPI(title="Modern Real-Time Chat App", description="Backend met FastAPI, DB en WebSockets.")

app.mount("/static", StaticFiles(directory="static"), name="static")

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
