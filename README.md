# IG-style Messenger (FastAPI + MongoDB + WebSockets)

A self-hosted, **Instagram DM–style** messenger written in pure Python.
No third-party API keys required. Real-time messaging, seen/unseen,
typing indicators, online presence, in-app push notifications, replies,
and media (image / video / audio / voice-note) uploads.

## Features

- JWT auth (register / login)
- Search users
- Conversations (1:1)
- Send text + media (image/video/audio/voice-note)
- Reply to a specific message
- WebSocket real-time fan-out
- Seen / unseen receipts
- Typing indicator
- Online / last-seen presence tracking
- In-app notification queue (no external push service / no API key)
- Pluggable storage: **local disk** (default) or **Google Drive** via OAuth (PyDrive2 — no API key, uses `client_secrets.json`)
- Minimal Instagram-like web UI (vanilla JS) at `/`

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start MongoDB locally (or set MONGO_URI in .env)
# mongod --dbpath ./data

cp .env .env.local   # edit if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Google Drive storage (optional, no API key)

1. In Google Cloud Console create an **OAuth Client ID** (Desktop app).
2. Download `client_secrets.json` and put it in the project root.
3. Set `STORAGE_BACKEND=gdrive` and optionally `GDRIVE_FOLDER_ID` in `.env`.
4. First upload triggers a browser OAuth consent and saves `credentials.json`.

## Project layout

```
app/
  main.py
  core/      config, security, db
  models/    pydantic schemas
  routers/   auth, users, conversations, messages, uploads, notifications
  services/  storage (local / gdrive), notifier
  ws/        connection manager + websocket route
static/      index.html (IG-like UI)
uploads/     local media (when STORAGE_BACKEND=local)
```

## WebSocket protocol

Connect: `ws://HOST/ws?token=<JWT>`

Client → Server JSON events:
- `{type:"message", conversation_id, content, media?, reply_to?}`
- `{type:"typing", conversation_id, is_typing}`
- `{type:"seen", conversation_id, message_id}`
- `{type:"ping"}`

Server → Client:
- `{type:"message", ...}`
- `{type:"typing", user_id, conversation_id, is_typing}`
- `{type:"seen", user_id, conversation_id, message_id}`
- `{type:"presence", user_id, online, last_seen}`
- `{type:"notification", ...}`
