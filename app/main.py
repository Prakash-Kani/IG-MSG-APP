from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from .core.config import settings
from .core.db import ensure_indexes
from .routers import auth, users, conversations, uploads, notifications
from .ws.routes import router as ws_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    await ensure_indexes()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(uploads.router)
app.include_router(notifications.router)
app.include_router(ws_router)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")
