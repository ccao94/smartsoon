## Frontend (Interface de Démo & Debug)

Pour permettre une visualisation interactive et une démonstration fluide du pipeline IA, un dashboard de debug a été développé en React / TypeScript. 

> **Note importante :** 
Ce frontend s'inscrit dans le cadre de notre **Preuve de Concept (POC)** spécifiquement conçue pour la soutenance et le test itératif du pipeline. 
Dans une architecture de production (respectant les normes de santé HDS / RGPD), l'orchestration des étapes intermédiaires serait intégralement centralisée côté backend afin qu'aucune donnée médicale brute ne transite sur le client.

### Lancement rapide

Pour tester le pipeline complet en local :

```bash
# 1. Démarrer le Backend (Modèles IA et API via Docker)
docker-compose up -d

# 2. Lancer le Frontend (Mode développement)
cd frontend
npm install
npm run dev