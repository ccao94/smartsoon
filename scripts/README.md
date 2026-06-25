# Scripts utilitaires SmartSoon

Ce dossier contient les scripts utilitaires du projet : automatisations,
outils de test et de génération de données. Ces scripts ne font pas partie
du code applicatif (`backend/app/`) mais l'utilisent ou interagissent
avec lui via l'API.

---

## export_ocr_samples.py

### Objectif

Automatise l'export des résultats OCR pour tous les fichiers présents
dans `data/samples/inputs/`. Chaque fichier est envoyé à l'endpoint
`POST /extract` du backend et la réponse JSON est sauvegardée dans
`data/samples/ocr_outputs/`.

Sert principalement à fournir une **matière première reproductible**
pour les tâches en aval :
- Calibration des chunks RAG 
- Constitution de corpus de test sécurité
- Fixtures de non-régression OCR
- Données de démo

### Prérequis

- Backend démarré localement (`docker-compose up -d`)
- Endpoint `/health` qui répond `200 OK`
- Python 3 avec la lib `requests` :

```bash
pip install requests
```

### Utilisation

Depuis la racine du repo :

```bash
python3 scripts/export_ocr_samples.py
```

Le script :

1. Vérifie que le backend répond sur `http://localhost:8000/health`
2. Liste tous les fichiers `.pdf`, `.jpg`, `.jpeg`, `.png` dans `data/samples/inputs/`
3. Envoie chaque fichier en `POST` sur `/extract`
4. Sauvegarde la réponse JSON dans `data/samples/ocr_outputs/<nom_fichier>.json`
5. Affiche un récap par fichier (type détecté, moteur OCR, confiance, pages, mots)

### Exemple de sortie

```
→ 19 fichier(s) à traiter

  [✓] 1A_mission_AXA_Lambert.pdf       type=scanned_pdf  engine=tesseract conf=0.925 pages=1 mots=202
  [✓] 1B_certificat_medical_Lambert.pdf type=native_pdf  engine=none      conf=1.000 pages=1 mots=255
  [✓] 2A_mission_MAIF_Ouedraogo.pdf    type=native_pdf  engine=none      conf=1.000 pages=1 mots=181
  ...

19/19 fichier(s) exportés dans data/samples/ocr_outputs/
```

### Structure des dossiers attendus

```
project_root/
├── data/
│   └── samples/
│       ├── inputs/              # Sources PDF/PNG (non versionnés, .gitignore)
│       │   ├── 1A_mission.pdf
│       │   └── ...
│       └── ocr_outputs/         # JSON exportés (versionnés)
│           ├── 1A_mission.json
│           └── ...
└── scripts/
    └── export_ocr_samples.py
```

### Format de sortie

Chaque JSON respecte le contrat défini dans `contracts/ocr_output_schema.json` :

```json
{
  "status": "success",
  "document": {
    "doc_id": "<sha256>",
    "filename": "1A_mission.pdf",
    "doc_type": "native_pdf",
    "ocr_engine": "none",
    "ocr_confidence": 1.0,
    "page_count": 1,
    "pages": [
      {
        "page_number": 1,
        "text": "...",
        "confidence": 1.0
      }
    ]
  }
}
```

### Cas d'erreur gérés

| Cause | Comportement |
|---|---|
| Backend injoignable | Arrêt immédiat avec message clair |
| Dossier `inputs/` absent | Arrêt avec message d'instruction |
| Aucun fichier valide | Arrêt sans erreur |
| Fichier rejeté par `/extract` (415, 422, 413...) | Affiche l'erreur, continue avec les autres fichiers |
| Timeout (> 120s par fichier) | Affiche l'erreur, continue avec les autres |

Le script renvoie le code de retour `0` si tous les fichiers ont été
exportés avec succès, `1` si au moins un échec.

### Quand relancer le script

À chaque fois que :
- Un nouveau fichier source est ajouté dans `data/samples/inputs/`
- Le code OCR (`extract.py`, `detector.py`, `ocr_tesseract.py`) est modifié
- Le seuil de confiance Tesseract est ajusté (passage à Surya)
- Le contrat de schéma est modifié (régénération nécessaire)

### Configuration

Les chemins et URLs sont définis en haut du script via des constantes :

```python
API_URL    = "http://localhost:8000/extract"
HEALTH_URL = "http://localhost:8000/health"
INPUT_DIR  = Path("data/samples/inputs")
OUTPUT_DIR = Path("data/samples/ocr_outputs")
```

Modifier ces valeurs si le backend tourne sur un autre port ou si la
structure des dossiers évolue.

---

## Conventions

- Les scripts dans ce dossier sont **autonomes** : ils ne sont pas
  importés par le code applicatif
- Ils sont **idempotents** quand c'est possible : peuvent être relancés
  sans dommage
- Ils utilisent l'API HTTP plutôt que les modules Python directement,
  pour rester découplés du code applicatif