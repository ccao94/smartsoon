from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.services.medical_pipeline import MedicalDataPipeline, process_document
from app.services.logger_service import log_pipeline_event
from typing import Dict, Any

router = APIRouter(prefix="/rag", tags=["RAG & Anonymisation"])

class DocumentPayload(BaseModel):
    raw_text: str = Field(
        ..., 
        description="Texte brut extrait du document médical via OCR ou extraction directe."
    )
    metadata: Dict[str, Any] = Field(
        ..., 
        description="Dictionnaire de métadonnées contenant les identifiants et attributs du document."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "raw_text": "Rapport médical du patient Jean Dupont. Diagnostic de fracture du fémur par le Dr Lambert le 12/04/2026.",
                "metadata": {
                    "document_id": "doc_abc_123",
                    "page_number": 1
                }
            }
        }
    }

class ProcessedDocumentResponse(BaseModel):
    original: str = Field(..., description="Le texte brut d'origine envoyé au pipeline.")
    anonymized: str = Field(..., description="Le texte nettoyé où les données de santé personnelles (PHI) sont masquées.")
    chunks: int = Field(..., description="Nombre total de fragments de texte vectorisés et indexés.")
    document_id: str = Field(..., description="Identifiant unique nettoyé et résolu pour le document.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "original": "Rapport médical du patient Jean Dupont. Diagnostic de fracture du fémur par le Dr Lambert le 12/04/2026.",
                "anonymized": "Rapport médical du patient PERSON. Diagnostic de fracture du fémur par le PERSON le DATE.",
                "chunks": 2,
                "document_id": "doc_abc_123"
            }
        }
    }

@router.post(
    "/process", 
    status_code=status.HTTP_200_OK,
    response_model=ProcessedDocumentResponse,
    summary="Traiter et anonymiser un fragment de document médical"
)
async def process_medical_document(
    payload: DocumentPayload, 
    liasse_id: str = Query("patient_folder_882", description="Identifiant unique de la liasse cible pour la contrainte de cloisonnement du vector store.")
) -> Dict[str, Any]:

    try:
        pipeline = MedicalDataPipeline(target_liasse_id=liasse_id)
        
        resposta: Dict[str, Any] = process_document(pipeline, payload.raw_text, payload.metadata)
        
        log_pipeline_event(
            user_id="anonymous_poc_user",
            dossier_id=liasse_id,
            document_id=resposta["document_id"],
            action="ANONYMIZATION",
            status="SUCCESS",
            metadata_payload={"chunks_generated": resposta["chunks"]}
        )
        
        return resposta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )