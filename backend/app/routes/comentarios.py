from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import current_user
from app.models.comentario import Comentario
from app.repositories import comentario_repo
from app.schemas.comentario import ComentarioCreate, ComentarioOut

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])


@router.get("", response_model=List[ComentarioOut])
async def listar_meus_comentarios(
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Lista todos os comentários do usuário logado — isolado por usuario_id."""
    return comentario_repo.list_by_user(db, user["id"])


@router.get("/{tmdb_movie_id}", response_model=List[ComentarioOut])
async def listar_comentarios(
    tmdb_movie_id: int,
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Lista comentários do usuário logado para um filme específico — isolado por usuario_id."""
    return comentario_repo.list_by_user_and_movie(db, user["id"], tmdb_movie_id)


@router.post("", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
async def comentar(
    payload: ComentarioCreate,
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Cria um comentário do usuário logado para um filme."""
    return comentario_repo.create(db, user["id"], payload.tmdb_movie_id, payload.texto)


@router.delete("/{comentario_id}")
async def deletar_comentario(
    comentario_id: int,
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")

    e_dono = comentario.usuario_id == user["id"]
    e_admin = user.get("role") == "admin"

    if not (e_dono or e_admin):
        raise HTTPException(
            status_code=403,
            detail="Apenas o autor ou um administrador podem remover este comentário",
        )

    db.delete(comentario)
    db.commit()
    return {"detail": "Comentário removido"}

