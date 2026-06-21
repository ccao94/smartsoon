from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.medical_pipeline import MedicalDataPipeline, process_document

router = APIRouter(prefix="/rag", tags=["RAG & Anonymization"])

# pydantic schema for ocr ingestion payload
class DocumentPayload(BaseModel):
    raw_text: str
    metadata: dict

@router.post("/process")
async def process_medical_document(payload: DocumentPayload, liasse_id: str = "patient_folder_882"):
    try:
        pipeline = MedicalDataPipeline(target_liasse_id=liasse_id)
        resposta = process_document(pipeline, payload.raw_text, payload.metadata)
        return resposta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))