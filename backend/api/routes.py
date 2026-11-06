from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["NØX AI"])


@router.get("/")
def api_accueil():
    return {
        "message": "API NØX AI opérationnelle"
    }


@router.get("/characters")
def liste_personnages():
    return {
        "characters": [],
        "total": 0
    }


@router.post("/chat")
def envoyer_message(message: str):
    return {
        "user_message": message,
        "response": "Le système de conversation NØX AI sera bientôt connecté."
}
