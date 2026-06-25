# Contracts SmartSoon

Ce dossier contient les contrats d'interface entre les services de la pipeline RAG.
Ces fichiers servent de référence officielle pour tous les développeurs de l'équipe.

---

## ocr_output_schema.json

Schéma JSON renvoyé par l'endpoint `POST /extract` du service OCR. 
C'est la source de vérité pour tous les consommateurs OCR via `POST /rag/process` et l'orchestrateur final `POST /process/full`;

### Structure

La réponse contient deux champs au premier niveau :

| Champ      | Type     | Description                                          |
|------------|----------|------------------------------------------------------|
| `status`   | string   | État de l'extraction (`success` ou `error`)          |
| `document` | object   | Payload complet de l'extraction (voir DocumentResult)|

#### DocumentResult

| Champ            | Type         | Description                                      |
|------------------|--------------|--------------------------------------------------|
| `doc_id`         | string       | SHA256 du fichier, sert d'identifiant unique    |
| `filename`       | string       | Nom original du fichier uploadé                  |
| `doc_type`       | DocTypeEnum  | Format détecté du document                       |
| `ocr_engine`     | OcrEngineEnum| Moteur OCR utilisé pour l'extraction             |
| `ocr_confidence` | number (0-1) | Confiance moyenne sur l'ensemble des pages       |
| `page_count`     | integer      | Nombre total de pages                            |
| `pages`          | array        | Liste des résultats par page (voir PageResult)   |

#### PageResult

| Champ         | Type         | Description                                        |
|---------------|--------------|----------------------------------------------------|
| `page_number` | integer      | Numéro de la page dans le document (1-indexé)      |
| `text`        | string       | Texte brut extrait de la page                      |
| `confidence`  | number (0-1) | Score de confiance OCR pour cette page             |

#### Enums

**DocTypeEnum** : `native_pdf` · `scanned_pdf` · `image`

> Note : Les PDF natifs contenant aussi des images scannées ne sont pas gérés


**OcrEngineEnum** : `tesseract` · `surya` · `none`

> `tesseract` est l'OCR par défaut. `surya` est appelé en fallback si
> `ocr_confidence < 0.75`. `none` est retourné pour les PDF natifs (pas d'OCR
> nécessaire, extraction directe par PyMuPDF).

---

### Exemple de réponse

```json
{
  "status": "success",
  "document": {
    "doc_id": "a3f5b2c8e9d1...",
    "filename": "compte_rendu_hospitalier.pdf",
    "doc_type": "scanned_pdf",
    "ocr_engine": "tesseract",
    "ocr_confidence": 0.901,
    "page_count": 3,
    "pages": [
      {
        "page_number": 1,
        "text": "Compte-rendu d'hospitalisation...",
        "confidence": 0.92
      },
      {
        "page_number": 2,
        "text": "Examen clinique : ...",
        "confidence": 0.89
      },
      {
        "page_number": 3,
        "text": "Conclusion : ...",
        "confidence": 0.89
      }
    ]
  }
}
```

---

### Régénération depuis le code

Le fichier est généré automatiquement depuis les modèles Pydantic de
`backend/app/models/schemas.py`. À relancer à chaque modification de ces modèles.

```bash
cd backend
source smartsoon_env/bin/activate    # si venv pas déjà actif
pip install pydantic                 # si pas déjà installé

python -c "
import json
from app.models.schemas import ExtractResponse
print(json.dumps(ExtractResponse.model_json_schema(), indent=2, ensure_ascii=False))
" > ../contracts/ocr_output_schema.json
```

---

### Intégration avec le pipeline RAG

Le service `medical_pipeline.py` utilise la fonction
`_sanitize_metadata()` qui normalise plusieurs noms de clés vers le format
attendu par ChromaDB.

**Mapping recommandé** pour les appels OCR → RAG :

| Clé OCR (/extract)              | Clé RAG (/rag/process)     |
|---------------------------------|----------------------------|
| `document.doc_id`               | `metadata.document_id`     |
| `document.pages[i].page_number` | `metadata.page_number`     |
| `document.pages[i].text`        | `raw_text`                 |

Le `doc_id` (SHA256) est un identifiant stable et déterministe. Il sert :
- d'identifiant unique pour ChromaDB
- de clé pour le filtrage multi-tenant via `where={'document_id': doc_id}` (mitigation T10 STRIDE)
- d'identifiant dans l'audit trail (`audit_logger.py`)

---

### Validation

Pour vérifier que le schéma est syntaxiquement valide :

```bash
pip install jsonschema

python -c "
import json
import jsonschema

with open('contracts/ocr_output_schema.json') as f:
    schema = json.load(f)

jsonschema.Draft7Validator.check_schema(schema)
print('Schéma valide')
"
```

Pour valider qu'une réponse réelle de `/extract` respecte le schéma :

```bash
# Tester l'endpoint
curl -s -X POST http://localhost:8000/extract \
  -F "file=@data/scansmpl.pdf" > response.json

# Valider la réponse contre le schéma
python -c "
import json
import jsonschema

schema = json.load(open('contracts/ocr_output_schema.json'))
response = json.load(open('response.json'))
jsonschema.validate(instance=response, schema=schema)
print('Réponse conforme au contrat')
"
```

---

### Historique

| Date       | Version | Changements                                    |
|------------|---------|------------------------------------------------|
| 2026-06-21 | 1.0     | Création initiale du contrat  |