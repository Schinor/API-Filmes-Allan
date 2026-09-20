from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from app.clients import log_client
from app.clients.auth_client import forward_request
from app.dependencies import current_user
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
async def login(
    request: Request,
    background: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        resposta = await forward_request(
            "POST",
            "/login",
            data={"username": form_data.username, "password": form_data.password},
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            # Await direto: BackgroundTasks se perde quando a rota levanta exceção
            await log_client.registrar(
                "login_falhou",
                request,
                detalhes=f"email:{form_data.username[:150]}",
            )
        raise

    background.add_task(
        log_client.registrar,
        "login",
        request,
        usuario_id=(resposta.get("user") or {}).get("id"),
    )
    return resposta


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    background: BackgroundTasks,
    user: dict = Depends(current_user),
):
    """Registra o logout na trilha de auditoria. O JWT é stateless, então nada é invalidado."""
    background.add_task(log_client.registrar, "logout", request, usuario_id=user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
