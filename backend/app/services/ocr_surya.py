import logging

logger = logging.getLogger(__name__)

def run_surya(filepath: str) -> dict:
    logger.info(f"Surya fallback utilisé pour {filepath}")
    
    # TODO: Implémentation réelle de Surya (pipeline lourd)
    # Pour l'instant, on retourne un mock au bon format
    return {
        "pages": [
            {"page_number": 1, "text": "[Texte extrait par Surya OCR...]", "confidence": 0.85}
        ],
        "avg_confidence": 0.85,
        "engine": "surya"
    }