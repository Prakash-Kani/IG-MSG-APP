from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
from ..core.security import get_current_user
from ..core.db import conversations, users, messages, presence
from ..models.schemas import CreateConversation, ConversationOut, UserPublic, MessageOut

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


async def _user_public(uid: str) -> UserPublic:
    u = await users.find_one({"_id": ObjectId(uid)})
    p = await presence.find_one({"user_id": uid}) or {}
    return UserPublic(
        id=uid,
        username=u["username"],
        full_name=u.get("full_name"),
        avatar_url=u.get("avatar_url"),
        online=p.get("online", False),
        last_seen=p.get("last_seen"),
    )


def _msg_out(m) -> MessageOut:
    return MessageOut(
        id=str(m["_id"]),
        conversation_id=str(m["conversation_id"]),
        sender_id=m["sender_id"],
        content=m.get("content"),
        media=m.get("media"),
        reply_to=m.get("reply_to"),
        seen_by=m.get("seen_by", []),
        created_at=m["created_at"],
    )


@router.post("", response_model=ConversationOut)
async def create_or_get(body: CreateConversation, current=Depends(get_current_user)):
    if body.user_id == current["id"]:
        raise HTTPException(400, "Cannot DM yourself")
    parts = sorted([current["id"], body.user_id])
    conv = await conversations.find_one({"participants": parts})
    if not conv:
        doc = {
            "participants": parts,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await conversations.insert_one(doc)
        conv = {**doc, "_id": res.inserted_id}
    return ConversationOut(
        id=str(conv["_id"]),
        participants=[await _user_public(p) for p in conv["participants"]],
        last_message=None,
        unread=0,
        updated_at=conv["updated_at"],
    )


@router.get("", response_model=list[ConversationOut])
async def list_my(current=Depends(get_current_user)):
    cur = conversations.find({"participants": current["id"]}).sort("updated_at", -1)
    out = []
    async for conv in cur:
        last = await messages.find_one(
            {"conversation_id": conv["_id"]}, sort=[("created_at", -1)]
        )
        unread = await messages.count_documents(
            {
                "conversation_id": conv["_id"],
                "sender_id": {"$ne": current["id"]},
                "seen_by": {"$ne": current["id"]},
            }
        )
        out.append(
            ConversationOut(
                id=str(conv["_id"]),
                participants=[await _user_public(p) for p in conv["participants"]],
                last_message=_msg_out(last) if last else None,
                unread=unread,
                updated_at=conv["updated_at"],
            )
        )
    return out


@router.get("/{conv_id}/messages", response_model=list[MessageOut])
async def history(conv_id: str, limit: int = 50, before: str | None = None, current=Depends(get_current_user)):
    conv = await conversations.find_one({"_id": ObjectId(conv_id)})
    if not conv or current["id"] not in conv["participants"]:
        raise HTTPException(404, "Not found")
    q = {"conversation_id": ObjectId(conv_id)}
    if before:
        b = await messages.find_one({"_id": ObjectId(before)})
        if b:
            q["created_at"] = {"$lt": b["created_at"]}
    cur = messages.find(q).sort("created_at", -1).limit(limit)
    items = [ _msg_out(m) async for m in cur ]
    items.reverse()
    return items
