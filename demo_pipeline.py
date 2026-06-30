import requests
import json
from pathlib import Path
import sys

# Configuration
BASE_URL = "http://localhost:8000"
LIASSE_ID = "Demo_Soutenance_Finale"
INPUT_DIR = Path("data/samples/inputs")

def run_demo(file_path: Path):
    print(f"\n>>> DÉBUT DU TRAITEMENT : {file_path.name} <<<")

    # 1. Extraction (OCR)
    print("Étape 1/3 : Extraction OCR...")
    with open(file_path, "rb") as f:
        resp_extract = requests.post(f"{BASE_URL}/extract", files={"file": f})
    
    if resp_extract.status_code != 200:
        print(f"Erreur OCR : {resp_extract.text}")
        return

    doc_data = resp_extract.json()["document"]
    raw_text = doc_data["pages"][0]["text"]
    doc_id = doc_data["doc_id"]
    print(f"  [OK] Texte extrait. DocID: {doc_id}")

    # 2. Anonymisation (RAG Process)
    print("Étape 2/3 : Anonymisation des données sensibles...")
    payload_anon = {
        "raw_text": raw_text,
        "metadata": {"document_id": doc_id, "page_number": 1}
    }
    resp_anon = requests.post(f"{BASE_URL}/rag/process?liasse_id={LIASSE_ID}", json=payload_anon)
    
    if resp_anon.status_code != 200:
        print(f"Erreur Anonymisation : {resp_anon.text}")
        return
    print(f"  [OK] Anonymisation réussie.")

    # 3. Génération (RAG Full)
    print("Étape 3/3 : Synthèse IA via Mistral...")
    payload_full = {
        "document_id": doc_id,
        "query": "Quel est le nom du patient (si présent) et quel est le montant des honoraires ?",
        "dossier_type": "Accident de la route",
        "motif_expertise": "Chiffrage"
    }
    resp_final = requests.post(f"{BASE_URL}/rag/process/full?liasse_id={LIASSE_ID}", json=payload_full)
    
    print("\n--- RÉSULTAT DU RAPPORT D'EXPERTISE ---")
    print(json.dumps(resp_final.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # Liste des fichiers disponibles
    files = list(INPUT_DIR.glob("*.pdf"))
    if not files:
        print("Aucun PDF trouvé dans data/samples/inputs/")
        sys.exit(1)

    print("--- BIENVENUE DANS LA DÉMO SMART-SOON ---")
    print("Fichiers disponibles :")
    for i, f in enumerate(files):
        print(f"{i+1}. {f.name}")
    
    choice = input("\nChoisissez le numéro du fichier à analyser : ")
    try:
        selected_file = files[int(choice)-1]
        run_demo(selected_file)
    except (ValueError, IndexError):
        print("Choix invalide.")