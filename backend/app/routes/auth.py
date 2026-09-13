from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from app.clients.auth_client import forward_request
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioOut,
    Token,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ValidateTokenResponse,
    UserRoleOut,
    UserRoleUpdate,
    PapelOut,
    PapelCreate,
    PermissaoOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def cadastro(payload: UsuarioCreate):
    return await forward_request("POST", "/cadastro", json_data=payload.model_dump())


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await forward_request(
        "POST",
        "/login",
        data={"username": form_data.username, "password": form_data.password},
    )


@router.get("/me", response_model=UsuarioOut)
async def me(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não fornecido")
    return await forward_request(
        "GET",
        "/me",
        headers={"authorization": auth_header},
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    return await forward_request("POST", "/forgot-password", json_data=payload.model_dump())


@router.get("/validate-reset-token/{token}", response_model=ValidateTokenResponse)
async def validate_reset_token(token: str):
    return await forward_request("GET", f"/validate-reset-token/{token}")


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(payload: ResetPasswordRequest):
    return await forward_request("POST", "/reset-password", json_data=payload.model_dump())


@router.get("/users/{user_id}/role", response_model=UserRoleOut)
async def get_user_role(user_id: int):
    return await forward_request("GET", f"/users/{user_id}/role")


@router.get("/users", response_model=List[UsuarioOut])
async def list_users(request: Request):
    auth_header = request.headers.get("authorization")
    return await forward_request(
        "GET",
        "/users",
        headers={"authorization": auth_header} if auth_header else None,
    )


@router.put("/users/{user_id}/role", response_model=UsuarioOut)
async def update_user_role(user_id: int, payload: UserRoleUpdate, request: Request):
    auth_header = request.headers.get("authorization")
    return await forward_request(
        "PUT",
        f"/users/{user_id}/role",
        json_data=payload.model_dump(),
        headers={"authorization": auth_header} if auth_header else None,
    )


@router.get("/roles", response_model=List[PapelOut])
async def list_roles():
    return await forward_request("GET", "/roles")


@router.post("/roles", response_model=PapelOut, status_code=status.HTTP_201_CREATED)
async def create_or_update_role(payload: PapelCreate, request: Request):
    auth_header = request.headers.get("authorization")
    return await forward_request(
        "POST",
        "/roles",
        json_data=payload.model_dump(),
        headers={"authorization": auth_header} if auth_header else None,
    )


@router.get("/permissions", response_model=List[PermissaoOut])
async def list_permissions(request: Request):
    auth_header = request.headers.get("authorization")
    return await forward_request(
        "GET",
        "/permissions",
        headers={"authorization": auth_header} if auth_header else None,
    )


@router.get("/admin/status")
async def admin_status(request: Request):
    auth_header = request.headers.get("authorization")
    return await forward_request(
        "GET",
        "/admin/status",
        headers={"authorization": auth_header} if auth_header else None,
    )
