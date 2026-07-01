"""
Script de démonstration interactif - Pipeline SmartSoon complet.
Enchaîne OCR, anonymisation et génération Mistral sur un fichier au choix.

Prérequis : backend démarré (docker compose up -d)
"""
import requests
import json
from pathlib import Path
import sys

BASE_URL = "http://localhost:8000"
LIASSE_ID = "Demo_Soutenance_Finale"
INPUT_DIR = Path("data/samples/inputs")


def run_demo(file_path: Path):
    print(f"\n>>> DÉBUT DU TRAITEMENT : {file_path.name} <<<")

    # 1. Extraction OCR
    print("Étape 1/3 : Extraction OCR...")
    with open(file_path, "rb") as f:
        resp_extract = requests.post(f"{BASE_URL}/extract", files={"file": f})

    if resp_extract.status_code != 200:
        print(f"Erreur OCR : {resp_extract.text}")
        return

    doc_data = resp_extract.json()["document"]
    pages = doc_data["pages"]
    doc_id = doc_data["doc_id"]
    print(f"  [OK] {len(pages)} page(s) extraite(s). DocID: {doc_id[:16]}...")

    # 2. Anonymisation page par page
    print("Étape 2/3 : Anonymisation des données sensibles...")
    for page in pages:
        payload_anon = {
            "raw_text": page["text"],
            "metadata": {
                "document_id": doc_id,
                "page_number": page["page_number"]
            }
        }
        resp_anon = requests.post(
            f"{BASE_URL}/rag/process?liasse_id={LIASSE_ID}",
            json=payload_anon
        )
        if resp_anon.status_code != 200:
            print(f"  Erreur anonymisation page {page['page_number']} : {resp_anon.text}")
            return
    print(f"  [OK] {len(pages)} page(s) anonymisée(s) et indexée(s).")

    # 3. Génération Mistral
    print("Étape 3/3 : Synthèse IA via Mistral...")
    query = input("  Question pour l'IA (Entrée = question par défaut) : ").strip()
    if not query:
        query = "Résume les informations principales de ce document médical."

    payload_full = {
        "document_id": doc_id,
        "query": query,
        "dossier_type": "Accident de la route",
        "motif_expertise": "Chiffrage des préjudices corporels"
    }
    resp_final = requests.post(
        f"{BASE_URL}/rag/process/full?liasse_id={LIASSE_ID}",
        json=payload_full
    )

    print("\n--- RÉSULTAT DU RAPPORT D'EXPERTISE ---")
    print(json.dumps(resp_final.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    files = sorted(INPUT_DIR.glob("*.pdf"))
    if not files:
        print(f"Aucun PDF trouvé dans {INPUT_DIR}/")
        print("Placez vos fichiers de test dans ce dossier.")
        sys.exit(1)

    print("--- DÉMO SMARTSOON ---")
    print(f"{len(files)} fichier(s) disponible(s) :\n")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f.name}")

    choice = input("\nNuméro du fichier à analyser : ")
    try:
        selected_file = files[int(choice) - 1]
        run_demo(selected_file)
    except (ValueError, IndexError):
        print("Choix invalide.")