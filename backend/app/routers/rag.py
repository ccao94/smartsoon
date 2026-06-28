from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.services.medical_pipeline import MedicalDataPipeline, process_document
from app.services.logger_service import log_pipeline_event
from app.services.orchestrator import run_full_rag_pipeline
from typing import Dict, Any

router = APIRouter(prefix="/rag", tags=["RAG & Anonymisation"])


# --- Modèles d'ingestion ---

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


# --- Endpoint ingestion et anonymisation ---

@router.post(
    "/process", 
    status_code=status.HTTP_200_OK,
    response_model=ProcessedDocumentResponse,
    summary="Traiter et anonymiser un fragment de document médical"
)
async def process_medical_document(
    payload: DocumentPayload, 
    liasse_id: str = Query("patient_folder_882", description="Identifiant unique de la liasse cible pour le cloisonnement.")
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


# --- Modèle et endpoint orchestration LLM (C3) ---

class GenerationPayload(BaseModel):
    document_id: str = Field(..., description="Identifiant du document préalablement indexé.")
    query: str = Field(..., description="La consigne ou question pour le rapport d'expertise.")
    dossier_type: str = Field("Accident corporel", description="Le type de dossier traité.")
    motif_expertise: str = Field("Évaluation des préjudices", description="Motif de l'expertise médicale.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "document_id": "doc_abc_123",
                "query": "Dresse la liste des lésions imputables à l'accident et leur date de consolidation.",
                "dossier_type": "Accident de la route",
                "motif_expertise": "Chiffrage des préjudices corporels"
            }
        }
    }


@router.post(
    "/process/full", 
    status_code=status.HTTP_200_OK,
    summary="Générer un rapport d'expertise complet (RAG LLM)"
)
async def process_full_report(
    payload: GenerationPayload,
    liasse_id: str = Query("patient_folder_882", description="Identifiant de la liasse cible.")
) -> Dict[str, Any]:
    """
    Exécute la chaîne d'orchestration finale :
    Recherche sémantique (ChromaDB) -> Synthèse structurée (Mistral EU).
    """
    try:
        response = run_full_rag_pipeline(
            liasse_id=liasse_id,
            document_id=payload.document_id,
            query=payload.query,
            dossier_type=payload.dossier_type,
            motif_expertise=payload.motif_expertise
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la génération du rapport."
        )