# Routers - Endpoints de l'API SmartSoon

Ce dossier contient les routes FastAPI exposées par l'application.

## Fichiers

### `extract.py`
**Endpoint :** `POST /extract`

Reçoit un fichier PDF ou image, détecte son type (natif, scanné, image), et extrait le texte via Tesseract ou PyMuPDF. Retourne le texte brut avec un score de confiance OCR et un `doc_id` (hash SHA256 du fichier).

Attention : cet endpoint retourne le texte **non anonymisé**. Il ne doit pas être exposé en production sans protection.

### `rag.py`
**Endpoint :** `POST /rag/process`

Reçoit du texte brut + métadonnées, anonymise via Presidio, découpe en chunks et indexe dans ChromaDB. Retourne le texte original, le texte anonymisé, le nombre de chunks et le `document_id`.

Paramètre `liasse_id` : identifiant du dossier patient pour le cloisonnement des données dans ChromaDB.

**Endpoint :** `POST /rag/process/full`

Reçoit un `document_id` et une question. L'orchestrateur cherche les chunks correspondants dans ChromaDB et les envoie à Mistral EU pour générer un rapport JSON structuré avec citations.

Paramètre `liasse_id` : doit être le même que celui utilisé lors de l'indexation via `/rag/process`.
