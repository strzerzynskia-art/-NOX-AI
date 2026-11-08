import os
import httpx
from fastapi import APIRouter, HTTPException

from api.schemas import CharacterSchema, MessageSchema, MemorySchema
from database.database import (
    initialiser_database, sauvegarder_personnage, recuperer_personnages,
    recuperer_personnage, sauvegarder_message, recuperer_messages,
    sauvegarder_memoire, recuperer_memoires, get_connection, USE_POSTGRES
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
        character = recuperer_personnage(character_id)
        # Enregistrer le premier message comme message du personnage :
        # il apparaîtra dans l'historique et sera pris en compte par l'IA.
        if character and character.get("first_message", "").strip():
            sauvegarder_message(character_id, "assistant", character["first_message"].strip())
        return {"message": "Personnage créé", "id": character_id, "character": character}
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


async def extraire_memoires(character, history, api_key, model):
    """Repère uniquement les faits durables réellement établis dans l'échange."""
    if not character.get("enhanced_memory") or len(history) < 2:
        return []
    conversation = "\n".join(
        ("Joueur" if item["role"] == "user" else character["name"]) + ": " + item["content"]
        for item in history[-12:] if item["role"] in ("user", "assistant")
    )
    prompt = """Analyse cette conversation de roleplay. Retourne uniquement un tableau JSON.
Garde seulement les faits utiles pour les prochaines conversations : relations établies,
événements importants, promesses, préférences, informations personnelles révélées,
évolution durable du personnage. N'invente rien. N'enregistre pas les éléments incertains,
les détails banals, ni les actions/pensées supposées du joueur.
Chaque élément doit être un objet avec "type" (relation, event, preference ou fact)
et "content" (une phrase courte et précise). Maximum 5 éléments. Si rien d'important,
retourne []."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key or 'ollama'}", "Content-Type": "application/json"},
                json={"model": model, "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": conversation}
                ], "temperature": 0.1}
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        import json
        extracted = json.loads(raw)
        if not isinstance(extracted, list):
            return []
        existing = {m["content"].casefold() for m in recuperer_memoires(character["id"], 100)}
        saved = []
        for item in extracted[:5]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()[:1000]
            kind = str(item.get("type", "event")).strip().lower()
            if content and content.casefold() not in existing and kind in ("relation", "event", "preference", "fact"):
                sauvegarder_memoire(character["id"], content, kind)
                existing.add(content.casefold())
                saved.append(content)
        return saved
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        # Une extraction mémoire ratée ne doit jamais bloquer la discussion.
        return []


async def generer_reponse(character, history, user_text, memories):
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    if not api_key:
        return ("Le personnage et l'historique sont bien enregistrés. Pour activer les réponses IA, "
                "configure un fournisseur IA dans les variables d'environnement Render.")
    memory_text = "\n".join(f"- [{m.get('memory_type', 'event')}] {m['content']}" for m in memories)
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
                f"{base_url}/chat/completions",
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
    if message.character_id is not None:
        character = recuperer_personnage(message.character_id)
    elif message.speaker_name:
        matches = [c for c in recuperer_personnages() if c["name"].casefold() == message.speaker_name.casefold()]
        character = matches[0] if matches else None
    else:
        character = None
    if not character:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    character_id = character["id"]
    if not message.content.strip() and not message.image:
        raise HTTPException(status_code=400, detail="Ajoute un texte ou une image.")
    sauvegarder_message(character_id, "user", message.content or "Image envoyée", message.image)
    history = recuperer_messages(character_id, 60)
    memories = recuperer_memoires(character_id, 30) if character.get("enhanced_memory") else []
    answer = await generer_reponse(character, history[:-1], message.content, memories)
    sauvegarder_message(character_id, "assistant", answer)
    # Après chaque réponse, mémoriser automatiquement les faits durables si l'IA est configurée.
    ai_enabled = bool(os.getenv("AI_MODEL") or os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY"))
    saved_memories = []
    if ai_enabled and character.get("enhanced_memory"):
        updated_history = recuperer_messages(character_id, 12)
        saved_memories = await extraire_memoires(character, updated_history, os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", ""), os.getenv("AI_MODEL", "qwen2.5:1.5b"))
    return {"speaker": message.speaker_name, "user_message": message.content, "response": answer,
            "memories_saved": len(saved_memories)}


@router.get("/health")
def health():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
        database_status = "connected"
    except Exception:
        database_status = "error"
    return {
        "status": "ok" if database_status == "connected" else "degraded",
        "database": "postgresql" if USE_POSTGRES else "sqlite",
        "database_status": database_status,
        "ai_configured": bool(os.getenv("AI_MODEL") or os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")),
        "ai_provider": os.getenv("AI_BASE_URL", "http://localhost:11434/v1"),
        "ai_model": os.getenv("AI_MODEL", "qwen2.5:1.5b")
    }
