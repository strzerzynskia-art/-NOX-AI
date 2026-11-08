import os
import secrets

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/core", tags=["NØX CORE"])


def verifier_cle_nox(x_nox_api_key: str = Header(default="")):
    """Protège les routes privées de NØX CORE."""
    expected = os.getenv("NOX_API_KEY", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="NØX CORE n'est pas encore configuré. Ajoute NOX_API_KEY dans Render."
        )
    if not x_nox_api_key or not secrets.compare_digest(x_nox_api_key, expected):
        raise HTTPException(status_code=401, detail="Clé API NØX invalide.")
    return True


@router.get("/status")
def core_status(_authorized: bool = __import__("fastapi").Depends(verifier_cle_nox)):
    return {
        "name": "NØX CORE",
        "status": "online",
        "access": "private",
        "version": "0.1.0"
    }
