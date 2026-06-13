from fastapi import APIRouter, HTTPException
from ..models.schemas import UserRegister, UserLogin, TokenOut, UserPublic
from ..core.db import users
from ..core.security import hash_password, verify_password, create_access_token
from datetime import datetime, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(body: UserRegister):
    if await users.find_one({"$or": [{"username": body.username}, {"email": body.email}]}):
        raise HTTPException(400, "Username or email already exists")
    doc = {
        "username": body.username,
        "email": body.email,
        "full_name": body.full_name,
        "password_hash": hash_password(body.password),
        "avatar_url": None,
        "created_at": datetime.now(timezone.utc),
    }
    res = await users.insert_one(doc)
    uid = str(res.inserted_id)
    token = create_access_token(uid)
    return TokenOut(
        access_token=token,
        user=UserPublic(id=uid, username=body.username, full_name=body.full_name),
    )


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin):
    u = await users.find_one({"username": body.username})
    if not u or not verify_password(body.password, u["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    uid = str(u["_id"])
    token = create_access_token(uid)
    return TokenOut(
        access_token=token,
        user=UserPublic(
            id=uid,
            username=u["username"],
            full_name=u.get("full_name"),
            avatar_url=u.get("avatar_url"),
        ),
    )
