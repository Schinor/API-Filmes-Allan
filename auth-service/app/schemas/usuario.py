from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, computed_field


class PermissaoOut(BaseModel):
    id: int
    action: str
    resource: str
    description: Optional[str] = None

    @computed_field
    @property
    def slug(self) -> str:
        return f"{self.action}:{self.resource}"

    model_config = ConfigDict(from_attributes=True)


class PapelOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    permissoes: List[PermissaoOut] = []

    model_config = ConfigDict(from_attributes=True)


class PapelCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    permission_ids: List[int] = []


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: Optional[str] = "amigo-do-wilson"


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    role: str = "amigo-do-wilson"
    role_id: Optional[int] = None
    permissions: List[str] = []
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: str


class UserRoleOut(BaseModel):
    user_id: int
    role: str
    role_id: Optional[int] = None
    permissions: List[str] = []
