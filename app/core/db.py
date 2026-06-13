from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

users = db["users"]
conversations = db["conversations"]
messages = db["messages"]
notifications = db["notifications"]
presence = db["presence"]


async def ensure_indexes():
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)
    await conversations.create_index("participants")
    await messages.create_index([("conversation_id", 1), ("created_at", -1)])
    await notifications.create_index([("user_id", 1), ("created_at", -1)])
    await presence.create_index("user_id", unique=True)
