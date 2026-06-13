from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ..core.security import get_current_user
from ..core.config import settings
from ..services.storage import storage

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload(file: UploadFile = File(...), current=Depends(get_current_user)):
    # naive size check via Content-Length is unreliable for multipart; rely on chunk count
    info = await storage.save(file)
    ctype = (file.content_type or "").lower()
    if ctype.startswith("image/"):
        mtype = "image"
    elif ctype.startswith("video/"):
        mtype = "video"
    elif ctype.startswith("audio/"):
        mtype = "audio"
    else:
        mtype = "file"
    if info["size"] > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, "File too large")
    return {**info, "type": mtype}
