import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter(
    prefix="/extract",
    tags=["Extraction"]
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in bytes
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

@router.post("", status_code=status.HTTP_200_OK)
async def create_extract_skeleton(file: UploadFile = File(...)):

    # 1. Validate file extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # 2. Validate file size (50 MB limit)
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the 50 MB limit. Current size: {file_size / (1024 * 1024):.2f} MB"
        )
    
    return {
        "status": "received",
        "filename": file.filename
    }