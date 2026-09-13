from typing import Callable
from fastapi import Header, Depends, HTTPException, status
from .clients.auth_client import get_authenticated_user


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    return await get_authenticated_user(authorization)


def require_permission(permission: str) -> Callable:
    async def dependency(user: dict = Depends(current_user)) -> dict:
        user_permissions = user.get("permissions", [])
        user_role = user.get("role", "")
        # Usuário possui a permissão específica ou é admin com permissão suprema
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
