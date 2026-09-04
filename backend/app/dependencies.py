from fastapi import Header, Depends
from .clients.auth_client import get_authenticated_user


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    return await get_authenticated_user(authorization)
