from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.clients import log_client
from app.clients.auth_client import usuario_premium
from app.core.api_responses import (
    AUTH_SERVICE_INDISPONIVEL,
    FAVORITO_DUPLICADO,
    FAVORITO_NAO_ENCONTRADO,
    UNAUTHORIZED,
    forbidden,
    forbidden_favoritar,
)
from app.core.config import settings
from app.core.database import get_db
from app.dependencies import negar_acesso, require_permission
from app.repositories import favorito_repo
from app.schemas.favoritos import FavoritoCreate, FavoritoOut

router = APIRouter(prefix="/api/favoritos", tags=["favoritos"])


@router.get(
    "",
    response_model=List[FavoritoOut],
    responses={**UNAUTHORIZED, **forbidden("listar:favoritos")},
)
async def listar_favoritos(
    user: dict = Depends(require_permission("listar:favoritos")),
    db: Session = Depends(get_db),
):
    """Lista favoritos do usuário logado — requer permissão 'listar:favoritos'."""
    return favorito_repo.list_by_user(db, user["id"])


@router.post(
    "",
    response_model=FavoritoOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        **UNAUTHORIZED,
        **forbidden_favoritar("adicionar:favoritos"),
        **FAVORITO_DUPLICADO,
        **AUTH_SERVICE_INDISPONIVEL,
    },
)
async def favoritar(
    payload: FavoritoCreate,
    request: Request,
    background: BackgroundTasks,
    user: dict = Depends(require_permission("adicionar:favoritos")),
    db: Session = Depends(get_db),
):
    """Adiciona um filme aos favoritos do usuário logado — requer 'adicionar:favoritos'.

    Plano gratuito: até LIMITE_FAVORITOS_FREE favoritos; Premium: sem limite.
    """
    if favorito_repo.get_by_user_and_movie(db, user["id"], payload.tmdb_movie_id):
        raise HTTPException(status_code=409, detail="Filme já está nos favoritos")

    limite = settings.LIMITE_FAVORITOS_FREE
    # Só consulta o auth-service quando o limite entra em jogo; abaixo dele todo mundo pode
    if favorito_repo.count_by_user(db, user["id"]) >= limite and not await usuario_premium(user["id"]):
        raise negar_acesso(
            request,
            user["id"],
            "favoritos:limite-free",
            f"Limite de {limite} favoritos atingido. Assine o Premium para favoritos ilimitados.",
        )

    fav = favorito_repo.create(
        db,
        usuario_id=user["id"],
        tmdb_movie_id=payload.tmdb_movie_id,
        titulo=payload.titulo,
        poster_path=payload.poster_path,
    )
    if fav is None:
        raise HTTPException(status_code=409, detail="Filme já está nos favoritos")
    background.add_task(
        log_client.registrar,
        "favoritar",
        request,
        usuario_id=user["id"],
        recurso=f"filme:{payload.tmdb_movie_id}",
    )
    return fav


@router.delete(
    "/{tmdb_movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**UNAUTHORIZED, **forbidden("remover:favoritos"), **FAVORITO_NAO_ENCONTRADO},
)
async def desfavoritar(
    tmdb_movie_id: int,
    user: dict = Depends(require_permission("remover:favoritos")),
    db: Session = Depends(get_db),
):
    """Remove um filme dos favoritos do usuário logado — requer 'remover:favoritos'."""
    removed = favorito_repo.delete(db, user["id"], tmdb_movie_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
