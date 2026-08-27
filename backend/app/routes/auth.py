import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
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
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def forward_to_auth_service(
    method: str,
    path: str,
    json_data: dict = None,
    data: dict = None,
    headers: dict = None,
):
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            req_headers = {}
            if headers and "authorization" in headers:
                req_headers["authorization"] = headers["authorization"]

            resp = await client.request(
                method=method,
                url=url,
                json=json_data,
                data=data,
                headers=req_headers,
            )
            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    detail = err_json.get("detail", err_json.get("message", "Erro no auth-service"))
                except Exception:
                    detail = resp.text or "Erro no auth-service"
                raise HTTPException(status_code=resp.status_code, detail=detail)
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="Erro no auth-service")
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Serviço de autenticação inacessível: {str(exc)}",
            )


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def cadastro(payload: UsuarioCreate):
    return await forward_to_auth_service("POST", "/cadastro", json_data=payload.model_dump())


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await forward_to_auth_service(
        "POST",
        "/login",
        data={"username": form_data.username, "password": form_data.password},
    )


@router.get("/me", response_model=UsuarioOut)
async def me(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não fornecido")
    return await forward_to_auth_service(
        "GET",
        "/me",
        headers={"authorization": auth_header},
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    return await forward_to_auth_service("POST", "/forgot-password", json_data=payload.model_dump())


@router.get("/validate-reset-token/{token}", response_model=ValidateTokenResponse)
async def validate_reset_token(token: str):
    return await forward_to_auth_service("GET", f"/validate-reset-token/{token}")


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(payload: ResetPasswordRequest):
    return await forward_to_auth_service("POST", "/reset-password", json_data=payload.model_dump())


@router.get("/users/{user_id}/role", response_model=UserRoleOut)
async def get_user_role(user_id: int):
    return await forward_to_auth_service("GET", f"/users/{user_id}/role")
