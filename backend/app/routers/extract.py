import os
import hashlib
import tempfile
import fitz
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.detector import detect_document_type
from app.services.ocr_tesseract import run_tesseract
from app.services.ocr_surya import run_surya
from app.models.schemas import ExtractResponse, DocumentResult, PageResult, DocTypeEnum, OcrEngineEnum
from app.core import config

router = APIRouter(
    prefix="/extract",
    tags=["Extraction"]
)

MAX_FILE_SIZE = config.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

@router.post("", status_code=status.HTTP_200_OK, response_model=ExtractResponse)
async def create_extract(file: UploadFile = File(...)):

    # 1. Valider l'extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension '{ext}' non supportée. Extensions autorisées : {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Valider la taille
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop lourd ({len(content) / (1024*1024):.2f} Mo). Limite : 50 Mo."
        )

    # 3. Sauvegarder temporairement sur disque
    doc_id = hashlib.sha256(content).hexdigest()
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # 4. Détecter le type de document
        doc_type = detect_document_type(tmp_path)

        # 5. OCR ou extraction directe
        if doc_type == "native_pdf":
            doc = fitz.open(tmp_path)
            pages = [
                {"page_number": i + 1, "text": doc[i].get_text(), "confidence": 1.0}
                for i in range(len(doc))
            ]
            result = {"pages": pages, "avg_confidence": 1.0, "engine": "none"}
        else:
            result = run_tesseract(tmp_path)
            if result["avg_confidence"] < 0.75:
                result = run_surya(tmp_path)

        # 6. Construire et retourner ExtractResponse
        page_results = [PageResult(**p) for p in result["pages"]]
        return ExtractResponse(
            status="success",
            document=DocumentResult(
                doc_id=doc_id,
                filename=file.filename,
                doc_type=DocTypeEnum(doc_type),
                ocr_engine=OcrEngineEnum(result["engine"]),
                ocr_confidence=result["avg_confidence"],
                page_count=len(page_results),
                pages=page_results
            )
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)