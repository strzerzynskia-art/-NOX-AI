import os
import httpx
from fastapi import APIRouter, HTTPException

from api.schemas import CharacterSchema, MessageSchema, MemorySchema
from database.database import (
    initialiser_database, sauvegarder_personnage, recuperer_personnages,
    recuperer_personnage, sauvegarder_message, recuperer_messages,
    sauvegarder_memoire, recuperer_memoires
)

router = APIRouter(prefix="/api", tags=["NØX AI"])
initialiser_database()


@router.get("/")
def api_accueil():
    return {"message": "API NØX AI opérationnelle"}


@router.get("/characters")
def liste_personnages():
    characters = recuperer_personnages()
    return {"characters": characters, "total": len(characters)}


@router.get("/characters/{character_id}")
def detail_personnage(character_id: int):
    character = recuperer_personnage(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return character


@router.post("/characters")
def creer_personnage(personnage: CharacterSchema):
    try:
        character_id = sauvegarder_personnage(personnage)
        return {"message": "Personnage créé", "id": character_id, "character": recuperer_personnage(character_id)}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Erreur de sauvegarde : {error}")


@router.get("/characters/{character_id}/messages")
def historique_personnage(character_id: int):
    if not recuperer_personnage(character_id):
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return {"messages": recuperer_messages(character_id)}


@router.get("/characters/{character_id}/memories")
def memoires_personnage(character_id: int):
    if not recuperer_personnage(character_id):
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return {"memories": recuperer_memoires(character_id)}


@router.post("/memories")
def ajouter_memoire(memory: MemorySchema):
    matches = [c for c in recuperer_personnages() if c["name"].casefold() == memory.character_name.casefold()]
    if not matches:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    memory_id = sauvegarder_memoire(matches[0]["id"], memory.content, memory.memory_type)
    return {"message": "Mémoire enregistrée", "id": memory_id}


async def generer_reponse(character, history, user_text, memories):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return ("Le personnage et l'historique sont bien enregistrés. Pour activer les réponses IA, "
                "ajoute OPENAI_API_KEY dans les variables d'environnement Render.")
    memory_text = "\n".join(f"- {m['content']}" for m in memories)
    system_prompt = f"""Tu es {character['name']}, un personnage fictif de roleplay.
Âge : {character.get('age') or 'non précisé'}
Apparence : {character.get('appearance', '')}
Personnalité : {character.get('personality', '')}
Traits : {', '.join(character.get('personality_tags', []))}
Histoire : {character.get('backstory', '')}
Secrets (à révéler progressivement, pas automatiquement) : {character.get('secrets', '')}
Relations : {character.get('relationships', '')}
Scénario : {character.get('scenario', '')}
Souviens-toi des faits et relations établis. Ne décide pas des actions ou pensées du joueur.
Mémoires importantes :
{memory_text}
Réponds en français, de façon naturelle et cohérente avec le personnage."""
    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-30:]:
        if item["role"] in ("user", "assistant"):
            messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": user_text})
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.85}
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as error:
        raise HTTPException(status_code=502, detail=f"Erreur du fournisseur IA ({error.response.status_code})")
    except (httpx.HTTPError, KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Le service IA est momentanément indisponible")


@router.post("/chat")
async def envoyer_message(message: MessageSchema):
    matches = [c for c in recuperer_personnages() if c["name"].casefold() == message.speaker_name.casefold()]
    if not matches:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    character = matches[0]
    character_id = character["id"]
    sauvegarder_message(character_id, "user", message.content)
    history = recuperer_messages(character_id, 60)
    memories = recuperer_memoires(character_id, 30) if character.get("enhanced_memory") else []
    answer = await generer_reponse(character, history[:-1], message.content, memories)
    sauvegarder_message(character_id, "assistant", answer)
    return {"speaker": message.speaker_name, "user_message": message.content, "response": answer}


@router.get("/health")
def health():
    return {"status": "ok", "ai_configured": bool(os.getenv("OPENAI_API_KEY"))}
