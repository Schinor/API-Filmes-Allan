import os
import httpx
from fastapi import HTTPException

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")


async def get_authenticated_user(authorization: str | None) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não enviado")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": authorization},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Serviço de autenticação indisponível")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return resp.json()  # {"id": ..., "nome": ..., "email": ..., "role": ...}
