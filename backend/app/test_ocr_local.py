import os
from app.services.detector import detect_document_type
from app.services.ocr_tesseract import run_tesseract
import fitz

def test_pipeline_complet(test_file):
    print(f"\n--- TEST DU FICHIER : {test_file} ---")
    
    if not os.path.exists(test_file):
        print("Erreur : Fichier non trouvé.")
        return

    # 1. Détection du type
    doc_type = detect_document_type(test_file)
    print(f"Type détecté : {doc_type}")

    # 2. Branchement selon le type
    if doc_type == "image":
        result = run_tesseract(test_file)
        print(f"Confiance Tesseract : {result['avg_confidence']}")
        print(f"Extrait : {result['pages'][0]['text'][:200]}...")

    elif doc_type == "scanned_pdf":
        print("Lancement OCR Tesseract pour PDF scanné...")
        result = run_tesseract(test_file)
        print(f"Confiance moyenne : {result['avg_confidence']}")
        print(f"Extrait (Page 1) : {result['pages'][0]['text'][:200]}...")

    elif doc_type == "native_pdf":
        print("Extraction native (sans OCR) :")
        doc = fitz.open(test_file)
        text = doc[0].get_text()
        print(f"Extrait (Page 1) : {text[:200]}...")

if __name__ == "__main__":
    # Liste des fichiers de test ici
    fichiers = ["data/scansmpl.pdf"]
    for f in fichiers:
        if os.path.exists(f):
            test_pipeline_complet(f)