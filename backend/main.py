from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.core import router as core_router

app = FastAPI(
    title="NØX AI",
    description="API de ton assistant de roleplay",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)
app.include_router(core_router)


@app.get("/")
def accueil():
    return {
        "nom": "NØX AI",
        "statut": "En ligne",
        "message": "Bienvenue dans NØX AI !",
        "version": "0.2.0"
    }


@app.get("/status")
def statut():
    return {"serveur": "actif", "version": "0.2.0"}
