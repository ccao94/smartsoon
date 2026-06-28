"""
Wrapper Surya OCR

Le pipeline Surya n'est pas implémenté dans ce POC :
- L'intégration Surya dans le container Docker provoque des conflits
  de dépendances (numpy/spacy/transformers) non résolvables sans
  refonte complète des deps.
- L'implémentation Surya réelle est reportée post-POC en tant que
  microservice GPU dédié

"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def run_surya(filepath: str) -> Dict[str, Any]:
    """
    Stub honnête — Surya non implémenté dans ce POC.
    
    Args:
        filepath: chemin vers le fichier (non utilisé en stub).
    
    Returns:
        dict avec status='unavailable' et pages vides.
        Le code appelant doit gérer ce cas en gardant le résultat
        Tesseract.
    """
    logger.warning(
        f"Fallback Surya appelé pour {filepath} mais non implémenté. "
        "Le résultat Tesseract sera conservé."
    )
    return {
        "pages": [],
        "avg_confidence": 0.0,
        "engine": "none",
        "status": "unavailable",
        "error": "Surya OCR non implémenté dans ce POC (reporté post-POC).",
    }