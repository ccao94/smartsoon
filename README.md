# SmartSoon

POC d'assistance IA pour la redaction de rapports d'expertise medicale.
Projet EFREI ING2 - Innovation Projects

Partenaire : SOON Expertise (Cyril NICOLOTTO)
Mentor : Julien SAID

## Stack

- **Backend** : Python / FastAPI
- **Base de donnees** : PostgreSQL
- **Pipeline IA** : Tesseract OCR, Microsoft Presidio, ChromaDB, Mistral EU
- **Infra** : Docker, docker-compose

## Setup

### Prerequis

- Installer [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Verifier que Docker tourne : `docker --version`

### Lancer le projet

```bash
git clone https://github.com/ccao94/smartsoon.git
cd smartsoon
cp .env.example .env
docker-compose up --build
```

L'API est accessible sur `http://localhost:8000`.
Documentation Swagger : `http://localhost:8000/docs`.

### Ce que ca lance

- **backend** : API Python sur http://localhost:8000
- **db** : PostgreSQL sur localhost:5432 (user: smartsoon, password: smartsoon_dev)

### Commandes utiles

```bash
# Lancer en arriere-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f backend

# Arreter tout
docker-compose down

# Rebuild apres modif du Dockerfile ou requirements.txt
docker-compose up --build

# Se connecter a la base PostgreSQL
docker exec -it smartsoon-db-1 psql -U smartsoon

# Supprimer les volumes (reset la BDD)
docker-compose down -v
```

### Ajouter un package Python

1. Ajouter le package dans `backend/requirements.txt`
2. Rebuild : `docker-compose up --build`

### Donnees de test

Mettre les PDF de test dans le dossier `data/` a la racine du projet.

## Structure du repo
smartsoon/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── data/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

## Equipe

| Nom | Role |
|-----|------|
| Cao Cuong CAO | PM / Software Engineer |
| Laurent CHHUOK | Software Engineer |
| Igor GUO | Software Engineer |
| Thoma BOUDHOU | Cybersecurity Engineer |
| Igor CONDE ELEOTERIO | Data / IA Engineer |
| Robin DEBRY | Bio-informatics Engineer |