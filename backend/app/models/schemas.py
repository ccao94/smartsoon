from enum import Enum 
from pydantic import BaseModel, Field

class DocTypeEnum(str, Enum):
    NATIVE_PDF = "native_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"

class OcrEngineEnum(str, Enum):
    TESSERACT = "tesseract"
    SURYA = "surya"
    NONE = "none"

class PageResult(BaseModel):
    page_number: int = Field(..., description="Numéro de la page dans le document (1-indexé)")
    text: str = Field(..., description="Texte brut extrait de la page")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Score de confiance OCR pour cette page, entre 0 et 1"
    )
  
class DocumentResult(BaseModel):
    doc_id: str = Field(..., description="Identifiant unique du fichier (SHA256)")
    filename: str = Field(..., description="Nom original du fichier uploadé")
    doc_type: DocTypeEnum = Field(..., description="Format du document")
    ocr_engine: OcrEngineEnum = Field(..., description="Moteur OCR utilisé pour l'extraction de texte")
    ocr_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Score de confiance OCR moyen sur l'ensemble des pages"
    )
    page_count: int = Field(..., description="Nombre total de pages")
    pages: list[PageResult] = Field(..., description="Liste des résultats d'extraction par page")

class ExtractResponse(BaseModel):
    status: str = Field(..., description="État du processus d'extraction (success/error)")
    document: DocumentResult = Field(..., description="Payload détaillé de l'extraction du document")