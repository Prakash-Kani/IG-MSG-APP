from fastapi import APIRouter, Depends, Query
from ..core.security import get_current_user
from ..core.db import users, presence
from ..models.schemas import UserPublic
from bson import ObjectId

router = APIRouter(prefix="/api/users", tags=["users"])


def serialize(u, p=None):
    return UserPublic(
        id=str(u["_id"]),
        username=u["username"],
        full_name=u.get("full_name"),
        avatar_url=u.get("avatar_url"),
        online=(p or {}).get("online", False),
        last_seen=(p or {}).get("last_seen"),
    )


@router.get("/me", response_model=UserPublic)
async def me(current=Depends(get_current_user)):
    p = await presence.find_one({"user_id": current["id"]})
    return serialize(current, p)


@router.get("/search", response_model=list[UserPublic])
async def search(q: str = Query("", min_length=0), current=Depends(get_current_user)):
    cur = users.find(
        {
            "_id": {"$ne": ObjectId(current["id"])},
            "$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"full_name": {"$regex": q, "$options": "i"}},
            ],
        }
    ).limit(20)
    out = []
    async for u in cur:
        p = await presence.find_one({"user_id": str(u["_id"])})
        out.append(serialize(u, p))
    return out
