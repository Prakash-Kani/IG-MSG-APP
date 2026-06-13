import os
import uuid
import aiofiles
from typing import Optional
from fastapi import UploadFile
from ..core.config import settings


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    async def save(self, file: UploadFile) -> dict:
        ext = os.path.splitext(file.filename or "")[1]
        name = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(self.base_dir, name)
        size = 0
        async with aiofiles.open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                await f.write(chunk)
        return {"url": f"/uploads/{name}", "name": file.filename, "size": size}


class GDriveStorage:
    """Google Drive via PyDrive2 OAuth (no API KEY, uses client_secrets.json)."""

    def __init__(self, folder_id: str = ""):
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive

        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile("credentials.json")
        self.drive = GoogleDrive(gauth)
        self.folder_id = folder_id

    async def save(self, file: UploadFile) -> dict:
        ext = os.path.splitext(file.filename or "")[1]
        name = f"{uuid.uuid4().hex}{ext}"
        tmp = os.path.join("/tmp", name)
        size = 0
        async with aiofiles.open(tmp, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                await f.write(chunk)
        meta = {"title": name}
        if self.folder_id:
            meta["parents"] = [{"id": self.folder_id}]
        gfile = self.drive.CreateFile(meta)
        gfile.SetContentFile(tmp)
        gfile.Upload()
        gfile.InsertPermission({"type": "anyone", "value": "anyone", "role": "reader"})
        os.remove(tmp)
        url = f"https://drive.google.com/uc?id={gfile['id']}"
        return {"url": url, "name": file.filename, "size": size}


def get_storage():
    if settings.STORAGE_BACKEND == "gdrive":
        return GDriveStorage(settings.GDRIVE_FOLDER_ID)
    return LocalStorage(settings.UPLOAD_DIR)


storage = get_storage()
