# Core - Configuration et constantes

Ce dossier contient la configuration globale de l'application.

## Fichiers

### `config.py`
Définit les extensions autorisées (PDF, JPG, PNG) et la taille maximale des fichiers (50 Mo).

### `prompts.py`
Contient le system prompt envoyé à Mistral EU (`SYSTEM_PROMPT_MEDICAL`). Ce prompt impose à l'IA de ne répondre qu'en JSON, de citer ses sources avec `document_id` et `page_number`, et de signaler les informations manquantes. Séparé de `llm_generator.py` pour faciliter les modifications sans toucher au code client.