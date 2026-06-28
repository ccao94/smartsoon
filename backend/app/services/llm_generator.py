import os
import json
import logging
from typing import Optional
from mistralai import Mistral

logger = logging.getLogger(__name__)

# Prompt système très strict pour forcer les citations et éviter les hallucinations
SYSTEM_PROMPT = """Tu es un assistant médical spécialisé dans la rédaction de rapports d'expertise.

RÈGLES STRICTES :
1. Tu ne peux utiliser QUE les informations présentes dans les chunks fournis.
2. Pour chaque affirmation, tu DOIS citer la source au format {document_id, page_number}.
3. Tu ne dois JAMAIS utiliser de connaissances externes ou inventer des informations.
4. Si les chunks ne contiennent pas assez d'informations, dis-le explicitement.
5. Réponds uniquement en JSON avec le format suivant :

{
  "sections": [
    {
      "title": "Titre de la section",
      "content": "Contenu rédigé avec citations",
      "citations": [
        {"document_id": "xxx", "page_number": 1, "excerpt": "extrait utilisé"}
      ]
    }
  ],
  "confidence": 0.85,
  "missing_info": ["liste des informations manquantes si applicable"]
}
"""

def generate_report(
    chunks: list[dict],
    query: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """
    Envoie les chunks anonymisés à Mistral EU et retourne une réponse structurée
    avec citations obligatoires des sources.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your_mistral_api_key_here":
        logger.error("MISTRAL_API_KEY manquante ou non valide.")
        return {"error": "Clé API Mistral manquante ou non configurée."}

    model = model or os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    max_tokens = max_tokens or int(os.getenv("MISTRAL_MAX_TOKENS", "2000"))

    # Formatage des chunks pour le contexte
    context = _format_chunks(chunks)

    user_message = f"""Voici les extraits de la liasse médicale (anonymisés) :

{context}

INSTRUCTION : {query}"""

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
            temperature=0.1,  # Température très basse pour rester factuel
            response_format={"type": "json_object"},
        )

        raw_text = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        logger.info(f"Réponse Mistral: {usage['total_tokens']} tokens utilisés")

        # Parsing du JSON retourné
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Mistral n'a pas retourné un JSON valide, encapsulage du texte brut")
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
    """Formate les chunks en une chaîne lisible pour le contexte du prompt."""
    lines = []
    for i, chunk in enumerate(chunks):
        doc_id = chunk.get("document_id", "unknown")
        page = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        lines.append(f"[Source {i+1} | doc={doc_id} | page={page}]\n{text}\n")
    return "\n".join(lines)