from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: Optional[str] = "usuario"


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    role: str = "usuario"
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UsuarioOut] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    nova_senha: str


class ResetPasswordResponse(BaseModel):
    message: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    message: Optional[str] = None


class UserRoleOut(BaseModel):
    user_id: int
    role: str
