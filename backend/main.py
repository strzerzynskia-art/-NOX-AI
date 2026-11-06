
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NØX AI",
    description="API de ton assistant de roleplay",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def accueil():
    return {
        "nom": "NØX AI",
        "statut": "En ligne",
        "message": "Bienvenue dans NØX AI !"
    }

@app.get("/status")
def statut():
    return {
        "serveur": "actif",
        "version": "0.1.0"
}
  
