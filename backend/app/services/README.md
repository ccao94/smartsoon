# Services - Logique métier du pipeline SmartSoon

Ce dossier contient toute la logique de traitement, de l'OCR jusqu'à la génération du rapport.

## Fichiers

### `detector.py`
Détecte le type d'un document uploadé : image, PDF natif (texte extractible) ou PDF scanné.
Vérifie jusqu'à 3 pages pour éviter les faux positifs.

### `ocr_tesseract.py`
Moteur OCR principal. Extrait le texte des PDF scannés et des images via Tesseract.
Retourne un score de confiance par page (0 à 1).

### `ocr_surya.py`
Fallback OCR prévu pour les documents mal reconnus par Tesseract (score < 0.75).
Actuellement en mock - retourne un stub. Justifié dans les Perspectives du poster.

### `medical_pipeline.py`
Cœur de l'anonymisation et de la vectorisation. Contient la classe `MedicalDataPipeline` :
- Initialise Presidio avec des regex médicales françaises (patient, docteur, NISS, RPPS, dates, téléphones).
- `anonymize_text()` : masque les données sensibles avec des tags (`<PATIENT>`, `<DOCTOR>`, etc.).
- `index_document()` : découpe le texte anonymisé en chunks de 512 tokens et les indexe dans ChromaDB avec le modèle E5-Large.
- `search()` : recherche sémantique dans ChromaDB avec isolation par `document_id`.

### `logger_service.py`
Audit trail du pipeline. Chaque action (anonymisation, indexation) est loggée avec un hash SHA256 des métadonnées. Stockage en mémoire (VirtualPostgresDB) pour le POC.

### `llm_generator.py`
Client Mistral EU. Envoie les chunks anonymisés avec un system prompt strict qui impose le format JSON et les citations obligatoires. Température à 0.1 pour rester factuel. Inclut un Output Guard qui bloque la réponse si du PHI est détecté.

### `orchestrator.py`
Chef d'orchestre du pipeline RAG. Connecte `search()` (ChromaDB) à `generate_report()` (Mistral). Enrichit la requête avec le type de dossier et le motif d'expertise.