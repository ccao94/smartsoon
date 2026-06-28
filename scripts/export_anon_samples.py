"""
Export OCR + Anonymisation sur tous les fichiers de data/samples/inputs/
Sauvegarde les JSON OCR dans data/samples/ocr_outputs/
Sauvegarde les JSON anonymisés dans data/samples/anon_outputs/

Lancement (depuis la racine du repo) :
    python3 scripts/export_ocr_samples.py

Prérequis : backend démarré (docker-compose up -d)
"""
import json
import sys
from pathlib import Path

import requests

API_URL    = "http://localhost:8000/extract"
RAG_URL    = "http://localhost:8000/rag/process"
HEALTH_URL = "http://localhost:8000/health"
INPUT_DIR  = Path("data/samples/inputs")
OCR_DIR    = Path("data/samples/ocr_outputs")
ANON_DIR   = Path("data/samples/anon_outputs")
ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}
LIASSE_ID  = "test_pipeline_complet"


def main() -> int:
    if not INPUT_DIR.exists():
        print(f"✗ Dossier introuvable : {INPUT_DIR}")
        print(f"  Crée-le et mets-y tes fichiers PDF/PNG d'abord.")
        return 1

    OCR_DIR.mkdir(parents=True, exist_ok=True)
    ANON_DIR.mkdir(parents=True, exist_ok=True)

    try:
        requests.get(HEALTH_URL, timeout=3).raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Backend injoignable sur localhost:8000")
        print(f"  Détail : {e}")
        print(f"  Lance d'abord : docker-compose up -d")
        return 1

    files = sorted(f for f in INPUT_DIR.iterdir() if f.suffix.lower() in ALLOWED_EXTS)
    if not files:
        print(f"✗ Aucun fichier .pdf/.jpg/.png trouvé dans {INPUT_DIR}")
        return 1

    print(f"→ {len(files)} fichier(s) à traiter\n")
    success_count = 0

    for file in files:
        print(f"  [...] {file.name}", end="", flush=True)

        # ÉTAPE 1 : OCR
        try:
            with open(file, "rb") as f:
                response = requests.post(
                    API_URL,
                    files={"file": (file.name, f, "application/octet-stream")},
                    timeout=120,
                )
        except requests.RequestException as e:
            print(f"\r  [✗] {file.name} — erreur réseau OCR : {e}")
            continue

        if response.status_code != 200:
            print(f"\r  [✗] {file.name} — HTTP {response.status_code} sur /extract")
            continue

        ocr_data = response.json()
        doc = ocr_data.get("document", {})
        doc_id = doc.get("doc_id", file.stem)
        pages = doc.get("pages", [])

        # Sauvegarde JSON OCR
        ocr_output = OCR_DIR / f"{file.stem}.json"
        with open(ocr_output, "w", encoding="utf-8") as out:
            json.dump(ocr_data, out, ensure_ascii=False, indent=2)

        # ÉTAPE 2 : Anonymisation page par page via /rag/process
        anon_pages = []
        anon_ok = True

        for page in pages:
            payload = {
                "raw_text": page.get("text", ""),
                "metadata": {
                    "document_id": doc_id,
                    "page_number": page.get("page_number", 1)
                }
            }
            try:
                anon_response = requests.post(
                    f"{RAG_URL}?liasse_id={LIASSE_ID}",
                    json=payload,
                    timeout=60,
                )
            except requests.RequestException as e:
                print(f"\r  [✗] {file.name} — erreur réseau anonymisation : {e}")
                anon_ok = False
                break

            if anon_response.status_code != 200:
                print(f"\r  [✗] {file.name} — HTTP {anon_response.status_code} sur /rag/process")
                anon_ok = False
                break

            anon_pages.append(anon_response.json())

        if not anon_ok:
            continue

        # Sauvegarde JSON anonymisé
        anon_output = ANON_DIR / f"{file.stem}.json"
        with open(anon_output, "w", encoding="utf-8") as out:
            json.dump({
                "document_id": doc_id,
                "filename": file.name,
                "pages": anon_pages
            }, out, ensure_ascii=False, indent=2)

        word_count = sum(len(p.get("text", "").split()) for p in pages)
        print(
            f"\r  [✓] {file.name:50s} "
            f"type={doc.get('doc_type', '?'):12s} "
            f"engine={doc.get('ocr_engine', '?'):9s} "
            f"conf={doc.get('ocr_confidence', 0):.3f} "
            f"pages={doc.get('page_count', 0)} "
            f"mots={word_count}"
        )
        success_count += 1

    print(f"\n{success_count}/{len(files)} fichier(s) traités (OCR + anonymisation)")
    print(f"  OCR     → {OCR_DIR}/")
    print(f"  Anonymisé → {ANON_DIR}/")
    return 0 if success_count == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())