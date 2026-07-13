import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Vérifie que le Bearer token correspond à la clé API configurée.
    Lève une 401 si la clé est absente ou incorrecte.
    """
    api_key = os.getenv("OCR_API_KEY", "")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCR_API_KEY non configurée côté serveur.",
        )

    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials