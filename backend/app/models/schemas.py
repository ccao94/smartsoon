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
  page_number: int = Field(..., description="The page number in the document")
  text: str = Field(..., description="Extracted raw text from the page")
  confidence: float = Field(
    ..., 
    ge=0.0, 
    le=1.0, 
    description="OCR confidence score for this page, between 0 and 1")
  
class DocumentResult(BaseModel):
  doc_id: str = Field(..., description="Unique identifier of the file")
  filename: str = Field(..., description="Original name of the uploaded file")
  doc_type: DocTypeEnum = Field(..., description="Document format")
  ocr_engine: OcrEngineEnum = Field(..., description="OCR engine applied to extract text")
  ocr_confidence: float = Field(
    ..., 
    ge=0.0, 
    le=1.0, 
    description="Mean OCR confidence score across all pages"
  )
  page_count: int = Field(..., description="Total number of pages")
  pages: list[PageResult] = Field(..., description="List of extraction results per page")

class ExtractResponse(BaseModel):
  status: str = Field(..., description="Status of the extraction process (success/error)")
  document: DocumentResult = Field(..., description="Detailed document extraction payload")