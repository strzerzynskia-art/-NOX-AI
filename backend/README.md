# NØX AI — Backend

API FastAPI de NØX AI.

## Démarrage sur Render

- Root Directory : `backend`
- Build Command : `pip install -r requirements.txt`
- Start Command : `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Variables d'environnement

- `OPENAI_API_KEY` : clé API privée du fournisseur compatible OpenAI (facultative pour démarrer le serveur).
- `OPENAI_MODEL` : modèle à utiliser, par défaut `gpt-4o-mini`.

Ne place jamais la clé API dans `index.html`, GitHub Pages ou un dépôt public. Ajoute-la uniquement dans les variables d'environnement privées de Render.

Sans clé API, la création des personnages et l'enregistrement de l'historique fonctionnent, mais le chat renvoie un message expliquant que l'IA n'est pas configurée.

## Endpoints principaux

- `GET /status` : état du serveur.
- `GET /api/health` : état de l'API et présence de la clé IA.
- `GET /api/characters` et `POST /api/characters` : personnages.
- `GET /api/characters/{id}/messages` : historique.
- `GET /api/characters/{id}/memories` : mémoires.
- `POST /api/memories` : ajouter une mémoire.
- `POST /api/chat` : envoyer un message.

La base SQLite est créée automatiquement dans `backend/database/nox_ai.db`. Pour conserver les données lors des redéploiements Render, configure un disque persistant et adapte `DATABASE_PATH` à son point de montage.
