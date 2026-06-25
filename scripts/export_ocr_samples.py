"""
Export OCR sur tous les fichiers de data/samples/inputs/
Sauvegarde les JSON dans data/samples/ocr_outputs/

Lancement (depuis la racine du repo) :
    python3 scripts/export_ocr_samples.py

Prérequis : backend démarré (docker-compose up -d)
"""
import json
import sys
from pathlib import Path

import requests

API_URL = "http://localhost:8000/extract"
HEALTH_URL = "http://localhost:8000/health"
INPUT_DIR = Path("data/samples/inputs")
OUTPUT_DIR = Path("data/samples/ocr_outputs")
ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}


def main() -> int:
    # Vérifier le dossier d'entrée
    if not INPUT_DIR.exists():
        print(f"✗ Dossier introuvable : {INPUT_DIR}")
        print(f"  Crée-le et mets-y tes fichiers PDF/PNG d'abord.")
        return 1

    # Créer le dossier de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Healthcheck du backend
    try:
        requests.get(HEALTH_URL, timeout=3).raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Backend injoignable sur localhost:8000")
        print(f"  Détail : {e}")
        print(f"  Lance d'abord : docker-compose up -d")
        return 1

    # Lister les fichiers valides
    files = sorted(f for f in INPUT_DIR.iterdir() if f.suffix.lower() in ALLOWED_EXTS)
    if not files:
        print(f"✗ Aucun fichier .pdf/.jpg/.png trouvé dans {INPUT_DIR}")
        return 1

    print(f"→ {len(files)} fichier(s) à traiter\n")
    success_count = 0

    # Traiter chaque fichier
    for file in files:
        print(f"  [...] {file.name}", end="", flush=True)
        try:
            with open(file, "rb") as f:
                response = requests.post(
                    API_URL,
                    files={"file": (file.name, f, "application/octet-stream")},
                    timeout=120,
                )
        except requests.RequestException as e:
            print(f"\r  [✗] {file.name} — erreur réseau : {e}")
            continue

        if response.status_code != 200:
            print(f"\r  [✗] {file.name} — HTTP {response.status_code}")
            print(f"        {response.text[:200]}")
            continue

        # Sauvegarder le JSON
        output_file = OUTPUT_DIR / f"{file.stem}.json"
        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(response.json(), out, ensure_ascii=False, indent=2)

        # Récap visuel
        data = response.json()
        doc = data.get("document", {})
        word_count = sum(len(p.get("text", "").split()) for p in doc.get("pages", []))
        print(
            f"\r  [✓] {file.name:50s} "
            f"type={doc.get('doc_type', '?'):12s} "
            f"engine={doc.get('ocr_engine', '?'):9s} "
            f"conf={doc.get('ocr_confidence', 0):.3f} "
            f"pages={doc.get('page_count', 0)} "
            f"mots={word_count}"
        )
        success_count += 1

    print(f"\n{success_count}/{len(files)} fichier(s) exportés dans {OUTPUT_DIR}/")
    return 0 if success_count == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
