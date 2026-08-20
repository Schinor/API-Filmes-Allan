from pydantic import BaseModel, EmailStr, ConfigDict

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str