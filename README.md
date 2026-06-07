# SmartSoon

POC d'assistance IA pour la rédaction de rapports d'expertise médicale.
Projet EFREI ING2 - Innovation Projects 2025-2026.

Partenaire : SOON Expertise (Cyril NICOLOTTO)
Mentor : Julien SAID

## Stack

- **Backend** : Python / FastAPI
- **Base de données** : PostgreSQL
- **Pipeline IA** : Tesseract OCR, Microsoft Presidio, ChromaDB, Mistral EU
- **Infra** : Docker, docker-compose

## Setup

### Prérequis

- Installer [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Vérifier que Docker tourne : `docker --version`

### Lancer le projet

```bash
git clone https://github.com/ccao94/smartsoon.git
cd smartsoon
cp .env.example .env
docker-compose up --build
```

L'API est accessible sur `http://localhost:8000`.
Documentation Swagger : `http://localhost:8000/docs`.

### Ce que ça lance

- **backend** : API Python sur http://localhost:8000
- **db** : PostgreSQL sur localhost:5432 (user: smartsoon, password: smartsoon_dev)

### Commandes utiles

```bash
# Lancer en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f backend

# Arrêter tout
docker-compose down

# Rebuild après modif du Dockerfile ou requirements.txt
docker-compose up --build

# Se connecter à la base PostgreSQL
docker exec -it smartsoon-db-1 psql -U smartsoon

# Supprimer les volumes (reset la BDD)
docker-compose down -v
```

### Ajouter un package Python

1. Ajouter le package dans `backend/requirements.txt`
2. Rebuild : `docker-compose up --build`

### Données de test

Mettre les PDF de test dans le dossier `data/` à la racine du projet.

## Structure du repo