from fastapi import FastAPI

app = FastAPI(
    title="NØX CORE",
    description="Le moteur principal de NØX AI",
    version="0.1.0"
)


@app.get("/")
async def home():
    return {
        "name": "NØX CORE",
        "message": "Bienvenue dans NØX AI",
        "version": "0.1.0"
    }


@app.get("/status")
async def status():
    return {
        "online": True,
        "engine": "NØX CORE",
        "version": "0.1.0"
    }


@app.get("/api/info")
async def info():
    return {
        "project": "NØX AI",
        "features": [
            "Character System",
            "Roleplay Engine",
            "Conversation Memory",
            "Relationship Engine",
            "Scenario Manager"
        ]
  }
