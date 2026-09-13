from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import require_permission
from app.repositories import favorito_repo
from app.schemas.favoritos import FavoritoCreate, FavoritoOut

router = APIRouter(prefix="/api/favoritos", tags=["favoritos"])


@router.get("", response_model=List[FavoritoOut])
async def listar_favoritos(
    user: dict = Depends(require_permission("listar:favoritos")),
    db: Session = Depends(get_db),
):
    """Lista favoritos do usuário logado — requer permissão 'listar:favoritos'."""
    return favorito_repo.list_by_user(db, user["id"])


@router.post("", response_model=FavoritoOut, status_code=status.HTTP_201_CREATED)
async def favoritar(
    payload: FavoritoCreate,
    user: dict = Depends(require_permission("adicionar:favoritos")),
    db: Session = Depends(get_db),
):
    """Adiciona um filme aos favoritos do usuário logado — requer 'adicionar:favoritos'."""
    fav = favorito_repo.create(
        db,
        usuario_id=user["id"],
        tmdb_movie_id=payload.tmdb_movie_id,
        titulo=payload.titulo,
        poster_path=payload.poster_path,
    )
    if fav is None:
        raise HTTPException(status_code=409, detail="Filme já está nos favoritos")
    return fav


@router.delete("/{tmdb_movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desfavoritar(
    tmdb_movie_id: int,
    user: dict = Depends(require_permission("remover:favoritos")),
    db: Session = Depends(get_db),
):
    """Remove um filme dos favoritos do usuário logado — requer 'remover:favoritos'."""
    removed = favorito_repo.delete(db, user["id"], tmdb_movie_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
