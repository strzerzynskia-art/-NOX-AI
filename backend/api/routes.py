from fastapi import APIRouter
from api.schemas import CharacterSchema, MessageSchema

router = APIRouter(prefix="/api", tags=["NØX AI"])

# Stockage temporaire des personnages
personnages = []


@router.get("/")
def api_accueil():
    return {
        "message": "API NØX AI opérationnelle"
    }


@router.get("/characters")
def liste_personnages():
    return {
        "characters": personnages,
        "total": len(personnages)
    }


@router.post("/characters")
def creer_personnage(personnage: CharacterSchema):
    personnages.append(personnage.model_dump())

    return {
        "message": "Personnage créé avec succès",
        "character": personnage
    }


@router.post("/chat")
def envoyer_message(message: MessageSchema):
    return {
        "speaker": message.speaker_name,
        "user_message": message.content,
        "response": "NØX AI a bien reçu ton message."
             }
