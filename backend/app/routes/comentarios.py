from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.repositories import comentario_repo
from app.schemas.comentario import ComentarioCreate, ComentarioOut

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])


@router.get("", response_model=List[ComentarioOut])
def listar_meus_comentarios(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista todos os comentários do usuário logado — isolado por usuario_id."""
    return comentario_repo.list_by_user(db, current_user.id)


@router.get("/{tmdb_movie_id}", response_model=List[ComentarioOut])
def listar_comentarios(
    tmdb_movie_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista comentários do usuário logado para um filme específico — isolado por usuario_id."""
    return comentario_repo.list_by_user_and_movie(db, current_user.id, tmdb_movie_id)


@router.post("", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
def comentar(
    payload: ComentarioCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria um comentário do usuário logado para um filme."""
    return comentario_repo.create(db, current_user.id, payload.tmdb_movie_id, payload.texto)


@router.delete("/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_comentario(
    comentario_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove um comentário — só o próprio dono pode remover."""
    removed = comentario_repo.delete(db, comentario_id, current_user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
