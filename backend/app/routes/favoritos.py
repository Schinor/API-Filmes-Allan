from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.repositories import favorito_repo
from app.schemas.favoritos import FavoritoCreate, FavoritoOut

router = APIRouter(prefix="/api/favoritos", tags=["favoritos"])


@router.get("", response_model=List[FavoritoOut])
def listar_favoritos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista favoritos do usuário logado — isolado por usuario_id."""
    return favorito_repo.list_by_user(db, current_user.id)


@router.post("", response_model=FavoritoOut, status_code=status.HTTP_201_CREATED)
def favoritar(
    payload: FavoritoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adiciona um filme aos favoritos do usuário logado."""
    fav = favorito_repo.create(
        db,
        usuario_id=current_user.id,
        tmdb_movie_id=payload.tmdb_movie_id,
        titulo=payload.titulo,
        poster_path=payload.poster_path,
    )
    if fav is None:
        raise HTTPException(status_code=409, detail="Filme já está nos favoritos")
    return fav


@router.delete("/{tmdb_movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def desfavoritar(
    tmdb_movie_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove um filme dos favoritos do usuário logado."""
    removed = favorito_repo.delete(db, current_user.id, tmdb_movie_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
