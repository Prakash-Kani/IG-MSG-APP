from datetime import datetime, timezone
from ..core.db import notifications


async def push_notification(user_id: str, ntype: str, payload: dict):
    doc = {
        "user_id": user_id,
        "type": ntype,
        "payload": payload,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    }
    res = await notifications.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    return doc
