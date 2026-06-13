import json
import asyncio
from typing import Dict, Set
from datetime import datetime, timezone
from fastapi import WebSocket
from ..core.db import presence


class ConnectionManager:
    def __init__(self):
        # user_id -> set of websockets (multi-device)
        self.active: Dict[str, Set[WebSocket]] = {}
        # user_id -> whether their tab is focused
        self.tab_active: Dict[str, bool] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.active.setdefault(user_id, set()).add(ws)
            self.tab_active[user_id] = True  # assume focused on connect
        await presence.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "online": True, "last_seen": datetime.now(timezone.utc)}},
            upsert=True,
        )
        await self.broadcast_presence(user_id, True)

    async def disconnect(self, user_id: str, ws: WebSocket):
        async with self.lock:
            conns = self.active.get(user_id, set())
            conns.discard(ws)
            if not conns:
                self.active.pop(user_id, None)
                self.tab_active.pop(user_id, None)
        if user_id not in self.active:
            await presence.update_one(
                {"user_id": user_id},
                {"$set": {"online": False, "last_seen": datetime.now(timezone.utc)}},
                upsert=True,
            )
            await self.broadcast_presence(user_id, False)

    async def set_active(self, user_id: str, active: bool):
        """Update tab-focus state and broadcast presence."""
        async with self.lock:
            self.tab_active[user_id] = active
        # online = connected AND tab is focused
        online = user_id in self.active and active
        await presence.update_one(
            {"user_id": user_id},
            {"$set": {"online": online, "last_seen": datetime.now(timezone.utc)}},
            upsert=True,
        )
        await self.broadcast_presence(user_id, online)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active and self.tab_active.get(user_id, False)

    def is_connected(self, user_id: str) -> bool:
        """Returns True if connected at all (even if tab inactive)."""
        return user_id in self.active

    async def send_to_user(self, user_id: str, data: dict):
        conns = list(self.active.get(user_id, []))
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception:
                pass

    async def broadcast(self, user_ids, data: dict):
        for uid in user_ids:
            await self.send_to_user(uid, data)

    async def broadcast_presence(self, user_id: str, online: bool):
        snapshot = list(self.active.keys())
        payload = {
            "type": "presence",
            "user_id": user_id,
            "online": online,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        for uid in snapshot:
            await self.send_to_user(uid, payload)


manager = ConnectionManager()
