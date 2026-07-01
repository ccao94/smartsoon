# SmartSoon

POC d'assistance IA pour la rédaction de rapports d'expertise médicale.
Projet EFREI ING2 - Innovation Projects 2025-2026.

**Partenaire :** SOON Expertise (Cyril NICOLOTTO)
**Mentor :** Julien SAID

---

## Architecture du Pipeline (RAG)

Pipeline sécurisé conçu sous FastAPI (Python), structuré en 5 étapes :

1. **Ingestion & Contrôle** (`/extract`) - Upload du PDF, hash SHA256 pour la traçabilité, validation du format.
2. **Extraction OCR** - Tesseract pour les PDF scannés, PyMuPDF pour les natifs. Score de confiance > 0.75 requis.
3. **Anonymisation** (`/rag/process`) - Microsoft Presidio + spaCy masquent les données personnelles (`<PATIENT>`, `<DOCTOR>`, `<NISS>`, `<RPPS>`). Mécanisme fail-closed : si du PHI résiduel est détecté, le pipeline bloque.
4. **Vectorisation** - Découpage sémantique (512 tokens) et indexation dans ChromaDB avec isolation par dossier patient (`liasse_id`).
5. **Génération LLM** (`/rag/process/full`) - Synthèse via Mistral EU avec citations obligatoires. Un Output Guard vérifie que la réponse ne contient pas de PHI.

---

## Stack

- **Backend** : Python / FastAPI
- **Base de données** : PostgreSQL
- **Pipeline IA** : Tesseract OCR, Microsoft Presidio, ChromaDB, Mistral EU
- **Infra** : Docker, docker-compose

---

## Setup

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé
- Une clé API Mistral (gratuite sur [console.mistral.ai](https://console.mistral.ai))

### Lancer le projet

```bash
git clone https://github.com/ccao94/smartsoon.git
cd smartsoon
cp .env.example .env
# Éditer .env pour ajouter votre clé MISTRAL_API_KEY
docker-compose up --build
```

L'API est accessible sur `http://localhost:8000`.
Documentation Swagger : `http://localhost:8000/docs`.

### Ce que ça lance

- **backend** : API Python sur http://localhost:8000
- **db** : PostgreSQL sur localhost:5432 (user: smartsoon, password: smartsoon_dev)

### Commandes utiles

```bash
docker-compose up -d             # Lancer en arrière-plan
docker-compose logs -f backend   # Voir les logs
docker-compose down              # Arrêter tout
docker-compose up --build        # Rebuild après modif
docker-compose down -v           # Reset complet (supprime la BDD)
```

### Ajouter un package Python

1. Ajouter le package dans `backend/requirements.txt`
2. Rebuild : `docker-compose up --build`

---

## Lancer la démo

Un script interactif permet de tester le pipeline complet sur les documents du corpus.

```bash
# Mettre les PDF de test dans data/samples/inputs/
python demo_pipeline.py
```

Le script liste les fichiers disponibles, demande d'en choisir un, et exécute toute la chaîne : OCR → Anonymisation → Vectorisation → Génération Mistral. Le rapport JSON final s'affiche dans le terminal.

Il est aussi possible de tester chaque étape individuellement via le Swagger (`/docs`).

---

## Structure du projet

```
smartsoon/
├── backend/
│   ├── app/
│   │   ├── main.py                    # Point d'entrée FastAPI
│   │   ├── core/
│   │   │   ├── config.py              # Extensions autorisées, taille max
│   │   │   └── prompts.py             # System prompt Mistral
│   │   ├── models/
│   │   │   └── schemas.py             # Modèles Pydantic (OCR)
│   │   ├── routers/
│   │   │   ├── extract.py             # Endpoint /extract (OCR)
│   │   │   └── rag.py                 # Endpoints /rag/process et /rag/process/full
│   │   └── services/
│   │       ├── detector.py            # Détection natif vs scanné
│   │       ├── ocr_tesseract.py       # Moteur OCR Tesseract
│   │       ├── ocr_surya.py           # Fallback OCR (mock)
│   │       ├── medical_pipeline.py    # Anonymisation Presidio + ChromaDB
│   │       ├── llm_generator.py       # Client Mistral EU + Output Guard
│   │       ├── orchestrator.py        # Orchestrateur search → Mistral
│   │       └── logger_service.py      # Audit trail (logs immuables)
│   ├── requirements.txt
│   └── Dockerfile
├── contracts/                          # Contrats d'interface (schémas JSON)
├── data/samples/
│   ├── inputs/                         # PDF de test (non versionnés)
│   ├── ocr_outputs/                    # Résultats OCR (JSON)
│   └── anon_outputs/                   # Résultats anonymisés (JSON)
├── scripts/
│   ├── export_ocr_samples.py          # Export OCR batch
│   └── export_anon_samples.py         # Export OCR + anonymisation batch
├── demo_pipeline.py                    # Script de démo interactif
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Équipe

| Nom | Rôle |
|-----|------|
| Cao Cuong CAO | PM / Orchestration & Vectorisation |
| Laurent CHHUOK | Software Engineer / Pipeline OCR |
| Igor GUO | Software Engineer / Infra & API |
| Igor CONDE ELEOTERIO | Data IA Engineer / Anonymisation Presidio |
| Thoma BOUDHOU | Cybersecurity Engineer / Audit & Fail-Closed |
| Robin DEBRY | Bio-informatics Engineer / Métier & Données |