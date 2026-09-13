from typing import Callable, Optional
from fastapi import Header, Depends, HTTPException, status
from .clients.auth_client import get_authenticated_user
from .core.security import decode_token


async def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não enviado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Tenta decodificação rápida local de JWT com validação da assinatura
    token_str = authorization.replace("Bearer ", "").replace("bearer ", "").strip()
    try:
        payload = decode_token(token_str)
        user_id = payload.get("sub")
        if user_id:
            return {
                "id": int(user_id),
                "nome": payload.get("nome", ""),
                "email": payload.get("email", ""),
                "role": payload.get("role", "amigo-do-wilson"),
                "permissions": payload.get("permissions", []),
            }
    except Exception:
        pass

    # Fallback para consulta remota ao microsserviço de autenticação
    return await get_authenticated_user(authorization)


def require_permission(permission: str) -> Callable:
    async def dependency(user: dict = Depends(current_user)) -> dict:
        user_permissions = user.get("permissions", [])
        user_role = user.get("role", "")
        # Acesso permitido se possuir a permissão requerida, permissão suprema de admin ou role admin
        if (
            permission not in user_permissions
            and "administrar:sistema" not in user_permissions
            and user_role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: permissão '{permission}' necessária",
            )
        return user
    return dependency
