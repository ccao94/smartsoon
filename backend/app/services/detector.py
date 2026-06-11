import fitz
from app.core.config import IMAGE_EXTENSIONS

# Ce module contient la logique de détection du type de document (image, PDF natif ou PDF scanné).
def detect_document_type(filepath: str) -> str:
    """Détecte le type de document: image, natif ou scanné."""
    
    # Détéction des images selon l'exention de fichier
    if filepath.lower().endswith(IMAGE_EXTENSIONS):
        return "image"
    
    try:
        doc = fitz.open(filepath)
        
        # On vérifie jusqu'à 3 pages maximum pour éviter le cas ou la page 1 contient peu de texte
        max_pages_to_check = min(3, len(doc))
        
        for page_num in range(max_pages_to_check):
            text = doc[page_num].get_text()
            
            # Dès qu'une page contient assez de texte, on valide le format natif
            if len(text.strip()) > 50:
                return "native_pdf"
                
        # Si on a parcouru les 3 premières pages sans trouver de texte, c'est un scan
        return "scanned_pdf"
    
    except Exception:
        # Si le fichier est corrompu ou illisible, on force l'OCR
        return "scanned_pdf"