import logging
from typing import Dict, Any

from app.services.medical_pipeline import MedicalDataPipeline
from app.services.llm_generator import generate_report

logger = logging.getLogger(__name__)


def run_full_rag_pipeline(
    liasse_id: str,
    document_id: str,
    query: str,
    dossier_type: str = "Standard",
    motif_expertise: str = "Non spécifié"
) -> Dict[str, Any]:
    """
    Orchestre la recherche vectorielle et la génération LLM.
    Prérequis : le document doit déjà avoir été indexé via /rag/process.
    """
    try:
        # Initialisation du pipeline ciblé sur la bonne liasse (isolation des données)
        pipeline = MedicalDataPipeline(target_liasse_id=liasse_id)

        # 1. Recherche dans ChromaDB (IG1)
        logger.info(f"Recherche des chunks pour doc_id={document_id}, liasse={liasse_id}")
        results = pipeline.search(query=query, document_id=document_id, n=5)

        if not results:
            logger.warning("Aucun contexte trouvé dans la base vectorielle.")
            return {"status": "error", "message": "Aucune information pertinente trouvée dans les documents."}

        # 2. Formatage des chunks pour le LLM
        chunks_for_llm = []
        for r in results:
            chunks_for_llm.append({
                "document_id": document_id,
                "page_number": r.get("metadata", {}).get("page_number", "?"),
                "text": r.get("text", "")
            })

        # 3. Enrichissement de la requête avec le contexte médical SOON
        enriched_query = f"[Dossier : {dossier_type} | Motif : {motif_expertise}]\nRequête de l'expert : {query}"

        # 4. Appel Mistral EU (C2)
        logger.info(f"Envoi de {len(chunks_for_llm)} chunks à Mistral EU pour génération.")
        llm_response = generate_report(chunks=chunks_for_llm, query=enriched_query)

        if "error" in llm_response:
            logger.error(f"Échec de la génération LLM : {llm_response['error']}")
            return {"status": "error", "message": llm_response["error"]}

        return {
            "status": "success",
            "data": llm_response
        }

    except Exception as e:
        logger.error(f"Erreur d'orchestration : {str(e)}", exc_info=True)
        return {"status": "error", "message": "Une erreur interne a bloqué la génération du rapport."}