from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.clients import log_client
from app.core.database import get_db
from app.dependencies import current_user, require_permission
from app.models.comentario import Comentario
from app.repositories import comentario_repo
from app.schemas.comentario import ComentarioCreate, ComentarioOut

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])


@router.get("", response_model=List[ComentarioOut])
async def listar_todos_comentarios(
    _user: dict = Depends(require_permission("listar:comentarios")),
    db: Session = Depends(get_db),
):
    """Lista os comentários da comunidade — requer 'listar:comentarios'."""
    return comentario_repo.list_all(db)


@router.get("/{tmdb_movie_id}", response_model=List[ComentarioOut])
async def listar_comentarios(
    tmdb_movie_id: int,
    _user: dict = Depends(require_permission("listar:comentarios")),
    db: Session = Depends(get_db),
):
    """Lista os comentários da comunidade para um filme — requer 'listar:comentarios'."""
    return comentario_repo.list_by_movie(db, tmdb_movie_id)


@router.post("", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
async def comentar(
    payload: ComentarioCreate,
    request: Request,
    background: BackgroundTasks,
    user: dict = Depends(require_permission("criar:comentarios")),
    db: Session = Depends(get_db),
):
    """Cria um comentário do usuário logado para um filme — requer 'criar:comentarios'."""
    comentario = comentario_repo.create(db, user["id"], payload.tmdb_movie_id, payload.texto)
    background.add_task(
        log_client.registrar,
        "comentar",
        request,
        usuario_id=user["id"],
        recurso=f"filme:{payload.tmdb_movie_id}",
        detalhes=f"comentario:{comentario.id}",
    )
    return comentario


@router.delete("/{comentario_id}")
async def deletar_comentario(
    comentario_id: int,
    request: Request,
    background: BackgroundTasks,
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Remove comentário.
    - O autor pode remover se possuir a permissão 'apagar:comentario-proprio'.
    - Moderadores/Admins podem remover se possuírem 'apagar:comentario-de-outro' ou 'administrar:sistema'.
    """
    comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")

    user_perms = user.get("permissions", [])
    user_role = user.get("role", "")

    e_dono = comentario.usuario_id == user["id"]
    pode_apagar_proprio = e_dono and ("apagar:comentario-proprio" in user_perms or user_role == "admin")
    pode_moderar = (
        "apagar:comentario-de-outro" in user_perms
        or "administrar:sistema" in user_perms
        or user_role == "admin"
    )

    if not (pode_apagar_proprio or pode_moderar):
        # Await direto: BackgroundTasks se perde quando a rota levanta exceção
        await log_client.registrar(
            "acesso_negado",
            request,
            usuario_id=user["id"],
            recurso=f"comentario:{comentario_id}",
            detalhes=f"{request.method} {request.url.path}",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o autor ou um administrador podem remover este comentário",
        )

    db.delete(comentario)
    db.commit()
    background.add_task(
        log_client.registrar,
        "apagar_comentario",
        request,
        usuario_id=user["id"],
        recurso=f"comentario:{comentario_id}",
        detalhes="autor" if e_dono else "moderacao",
    )
    return {"detail": "Comentário removido"}
