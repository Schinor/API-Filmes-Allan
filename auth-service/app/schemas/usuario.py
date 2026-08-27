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


class UserRoleOut(BaseModel):
    user_id: int
    role: str
