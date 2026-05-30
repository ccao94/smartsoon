# SmartSoon

POC d'assistance IA à la rédaction de rapports d'expertise médicale.
Projet EFREI ING2 - Innovation Projects 2025-2026.

## Stack

- **Backend** : Python / FastAPI
- **Frontend** : React / Vite / TypeScript
- **Pipeline IA** : Tesseract OCR, Microsoft Presidio, ChromaDB, Mistral EU
- **Infra** : Docker, docker-compose

## Setup

### Prérequis
- Docker + Docker Compose

### Lancer le projet
```bash
cp .env.example .env
docker-compose up --build
```

L'API est accessible sur `http://localhost:8000`.
Documentation Swagger : `http://localhost:8000/docs`.

## Équipe

| Nom | Rôle |
|-----|------|
| Cao Cuong CAO | PM / Software Engineer |
| Laurent CHHUOK | Software Engineer |
| Igor GUO | Software Engineer |
| Thoma BOUDHOU | Cybersecurity Engineer |
| Igor CONDE ELEOTERIO | Data / IA Engineer |
| Robin DEBRY | Bio-informatics Engineer |