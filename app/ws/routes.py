import json
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..core.security import decode_token
from ..core.db import users, conversations, messages
from ..services.notifier import push_notification
from .manager import manager

router = APIRouter()


async def _persist_message(sender_id: str, conv_id: str, content, media, reply_to):
    conv = await conversations.find_one({"_id": ObjectId(conv_id)})
    if not conv or sender_id not in conv["participants"]:
        return None, None
    doc = {
        "conversation_id": ObjectId(conv_id),
        "sender_id": sender_id,
        "content": content,
        "media": media,
        "reply_to": reply_to,
        "seen_by": [sender_id],
        "created_at": datetime.now(timezone.utc),
    }
    res = await messages.insert_one(doc)
    await conversations.update_one(
        {"_id": ObjectId(conv_id)}, {"$set": {"updated_at": doc["created_at"]}}
    )
    doc["id"] = str(res.inserted_id)
    doc["_id"] = doc["id"]
    doc["conversation_id"] = conv_id
    return doc, conv["participants"]


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = Query(...)):
    uid = decode_token(token)
    if not uid:
        await websocket.close(code=4401)
        return
    user = await users.find_one({"_id": ObjectId(uid)})
    if not user:
        await websocket.close(code=4401)
        return

    await manager.connect(uid, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue
            t = data.get("type")

            if t == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif t == "presence_update":
                # Client sends this when tab focus/blur changes
                active = bool(data.get("active", True))
                await manager.set_active(uid, active)

            elif t == "message":
                conv_id = data["conversation_id"]
                doc, participants = await _persist_message(
                    uid,
                    conv_id,
                    data.get("content"),
                    data.get("media"),
                    data.get("reply_to"),
                )
                if not doc:
                    continue
                payload = {
                    "type": "message",
                    "id": doc["id"],
                    "conversation_id": conv_id,
                    "sender_id": uid,
                    "content": doc.get("content"),
                    "media": doc.get("media"),
                    "reply_to": doc.get("reply_to"),
                    "seen_by": doc["seen_by"],
                    "created_at": doc["created_at"].isoformat(),
                }
                await manager.broadcast(participants, payload)
                # in-app notification for offline / other participants
                for p in participants:
                    if p != uid:
                        notif = await push_notification(
                            p,
                            "message",
                            {
                                "from": user["username"],
                                "conversation_id": conv_id,
                                "preview": (doc.get("content") or "[media]")[:120],
                            },
                        )
                        if manager.is_online(p):
                            await manager.send_to_user(
                                p,
                                {"type": "notification", **{k: v for k, v in notif.items() if k != "_id"}},
                            )

            elif t == "typing":
                conv_id = data["conversation_id"]
                conv = await conversations.find_one({"_id": ObjectId(conv_id)})
                if not conv or uid not in conv["participants"]:
                    continue
                for p in conv["participants"]:
                    if p != uid:
                        await manager.send_to_user(
                            p,
                            {
                                "type": "typing",
                                "user_id": uid,
                                "conversation_id": conv_id,
                                "is_typing": bool(data.get("is_typing")),
                            },
                        )

            elif t == "seen":
                conv_id = data["conversation_id"]
                mid = data["message_id"]
                await messages.update_one(
                    {"_id": ObjectId(mid)}, {"$addToSet": {"seen_by": uid}}
                )
                conv = await conversations.find_one({"_id": ObjectId(conv_id)})
                if conv:
                    for p in conv["participants"]:
                        await manager.send_to_user(
                            p,
                            {
                                "type": "seen",
                                "user_id": uid,
                                "conversation_id": conv_id,
                                "message_id": mid,
                            },
                        )

    except WebSocketDisconnect:
        await manager.disconnect(uid, websocket)
    except Exception:
        await manager.disconnect(uid, websocket)
