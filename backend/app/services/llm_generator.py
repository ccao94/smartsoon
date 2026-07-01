import os
import json
import logging
import re
from typing import Optional
from mistralai.client import Mistral
from app.core.prompts import SYSTEM_PROMPT_MEDICAL

logger = logging.getLogger(__name__)
SYSTEM_PROMPT = SYSTEM_PROMPT_MEDICAL

def _check_output_phi(text: str) -> bool:
    """Output guard basique pour détecter une fuite évidente (ex: Numéro de sécu)."""
    # Regex basique pour détecter 13 à 15 chiffres (Numéro de sécu NIR)
    nir_pattern = re.compile(r"([12]\s?\d{2}\s?\d{2}\s?\d{2,6}[\s,.]?\d{3,5}[\s,.]?\d{2,3}[\s,.]?\d{2})")
    if nir_pattern.search(text):
        return True # PHI détecté
    return False

def generate_report(
    chunks: list[dict],
    query: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your_mistral_api_key_here":
        logger.error("MISTRAL_API_KEY manquante ou non valide.")
        return {"error": "Clé API Mistral manquante ou non configurée."}

    model = model or os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    max_tokens = max_tokens or int(os.getenv("MISTRAL_MAX_TOKENS", "2000"))

    context = _format_chunks(chunks)
    user_message = f"Voici les extraits de la liasse médicale (anonymisés) :\n\n{context}\n\nINSTRUCTION : {query}"

    client = Mistral(api_key=api_key)
    logger.info(f"Appel de Mistral EU model={model}, chunks={len(chunks)}")

    try:
        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw_text = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        # OUTPUT GUARD
        if _check_output_phi(raw_text):
             logger.error("Output Guard déclenché : PHI détecté dans la réponse de Mistral.")
             return {"error": "La réponse a été bloquée pour des raisons de sécurité (présence de données sensibles)."}

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Mistral n'a pas retourné un JSON valide")
            result = {
                "sections": [{"title": "Réponse brute", "content": raw_text, "citations": []}],
                "confidence": 0.0,
                "missing_info": ["Le modèle n'a pas respecté le format JSON demandé"],
            }

        result["usage"] = usage
        return result

    except Exception as e:
        logger.error(f"Erreur API Mistral : {str(e)}")
        return {"error": f"La génération LLM a échoué : {str(e)}"}

def _format_chunks(chunks: list[dict]) -> str:
    lines = []
    for i, chunk in enumerate(chunks):
        doc_id = chunk.get("document_id", "unknown")
        page = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        lines.append(f"[Source {i+1} | doc={doc_id} | page={page}]\n{text}\n")
    return "\n".join(lines)