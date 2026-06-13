from fastapi import APIRouter, Depends
from bson import ObjectId
from ..core.security import get_current_user
from ..core.db import notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(current=Depends(get_current_user), limit: int = 50):
    cur = notifications.find({"user_id": current["id"]}).sort("created_at", -1).limit(limit)
    out = []
    async for n in cur:
        n["id"] = str(n.pop("_id"))
        out.append(n)
    return out


@router.post("/{nid}/read")
async def mark_read(nid: str, current=Depends(get_current_user)):
    await notifications.update_one(
        {"_id": ObjectId(nid), "user_id": current["id"]}, {"$set": {"read": True}}
    )
    return {"ok": True}
