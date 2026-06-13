from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    online: bool = False
    last_seen: Optional[datetime] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class MediaItem(BaseModel):
    url: str
    type: Literal["image", "video", "audio", "voice", "file"]
    name: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[float] = None


class MessageIn(BaseModel):
    conversation_id: str
    content: Optional[str] = None
    media: Optional[MediaItem] = None
    reply_to: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: Optional[str] = None
    media: Optional[MediaItem] = None
    reply_to: Optional[str] = None
    seen_by: List[str] = []
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    participants: List[UserPublic]
    last_message: Optional[MessageOut] = None
    unread: int = 0
    updated_at: datetime


class CreateConversation(BaseModel):
    user_id: str


class NotificationOut(BaseModel):
    id: str
    user_id: str
    type: str
    payload: dict
    read: bool = False
    created_at: datetime
