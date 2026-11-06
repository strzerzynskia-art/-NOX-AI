from fastapi import APIRouter, HTTPException

from api.schemas import CharacterSchema, MessageSchema
from database.database import (
    initialiser_database,
    sauvegarder_personnage,
    recuperer_personnages
)

router = APIRouter(prefix="/api", tags=["NØX AI"])

# Initialisation de la base de données
initialiser_database()


@router.get("/")
def api_accueil():
    return {
        "message": "API NØX AI opérationnelle"
    }


@router.get("/characters")
def liste_personnages():
    personnages = recuperer_personnages()

    return {
        "characters": personnages,
        "total": len(personnages)
    }


@router.post("/characters")
def creer_personnage(personnage: CharacterSchema):
    try:
        personnage_id = sauvegarder_personnage(personnage)

        return {
            "message": "Personnage sauvegardé avec succès",
            "id": personnage_id,
            "character": personnage
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la sauvegarde du personnage"
        )


@router.post("/chat")
def envoyer_message(message: MessageSchema):
    return {
        "speaker": message.speaker_name,
        "user_message": message.content,
        "response": "NØX AI a bien reçu ton message."
    }
