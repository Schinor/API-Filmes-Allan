from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FavoritoPerfilOut(BaseModel):
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PerfilOut(BaseModel):
    usuario_id: int
    nome: str
    bio: Optional[str] = None
    # URL relativa ao catálogo (/storage/...), pré-assinada e com expiração; null sem foto
    foto_url: Optional[str] = None
    favoritos: List[FavoritoPerfilOut] = []
    # Só para a UI esconder/mostrar os botões — não é controle de acesso
    pode_editar: bool = False


class PerfilBioUpdate(BaseModel):
    """Sem campo usuario_id de propósito: a identidade vem do JWT (extras são ignorados)."""

    bio: Optional[str] = Field(default=None, max_length=280)

    @field_validator("bio")
    @classmethod
    def normalizar(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        valor = valor.strip()
        return valor or None
