from fastapi import APIRouter, HTTPException
from app.core.api_responses import TMDB_INDISPONIVEL
from app.services.tmdb_service import get_tom_hanks_movies, get_movie_detail

router = APIRouter(prefix="/api/filmes", tags=["filmes"])


@router.get("", responses={**TMDB_INDISPONIVEL})
async def listar_filmes():
    """Lista todos os filmes com Tom Hanks via TMDB. Sem autenticação — catálogo público."""
    try:
        filmes = await get_tom_hanks_movies()
        return filmes
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar TMDB: {str(e)}")


@router.get("/{movie_id}", responses={**TMDB_INDISPONIVEL})
async def detalhe_filme(movie_id: int):
    """Retorna detalhes de um filme específico via TMDB."""
    try:
        return await get_movie_detail(movie_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar TMDB: {str(e)}")
