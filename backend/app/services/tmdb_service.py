"""
Serviço para consumir a API do TMDB.
Todas as chamadas partem do servidor — nunca do browser do usuário.
"""
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app.core.config import settings

TMDB_BASE = settings.TMDB_BASE_URL
POSTER_BASE = "https://image.tmdb.org/t/p/w500"

_TOM_HANKS_ID: Optional[int] = None


def _get_auth_params_and_headers(extra_params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os parâmetros de query e cabeçalhos adequados para a autenticação TMDB.
    Suporta tanto chave padrão v3 (api_key via query param) quanto token JWT v4 (Bearer token no header).
    """
    params = extra_params.copy() if extra_params else {}
    headers = {"Accept": "application/json"}
    
    key = settings.TMDB_API_KEY.strip()
    if key.startswith("Bearer "):
        headers["Authorization"] = key
    elif key.startswith("eyJ") or len(key) > 50:
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key

    return params, headers


async def _get_tom_hanks_id() -> int:
    """Busca o person_id de Tom Hanks na API do TMDB (com cache em memória)."""
    global _TOM_HANKS_ID
    if _TOM_HANKS_ID is not None:
        return _TOM_HANKS_ID

    params, headers = _get_auth_params_and_headers({"query": "Tom Hanks", "language": "pt-BR"})

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE}/search/person",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            raise RuntimeError("Tom Hanks não encontrado na TMDB")
        _TOM_HANKS_ID = results[0]["id"]
        return _TOM_HANKS_ID


async def get_tom_hanks_movies() -> List[Dict[str, Any]]:
    """Retorna a lista de filmes com Tom Hanks, ordenada por popularidade."""
    person_id = await _get_tom_hanks_id()

    params, headers = _get_auth_params_and_headers({"language": "pt-BR"})

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE}/person/{person_id}/movie_credits",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        credits = resp.json().get("cast", [])

    # Filtra filmes sem pôster e ordena por popularidade
    filmes = [
        {
            "id": m["id"],
            "titulo": m.get("title", ""),
            "sinopse": m.get("overview", ""),
            "poster_path": m.get("poster_path"),
            "poster_url": f"{POSTER_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            "data_lancamento": m.get("release_date", ""),
            "popularidade": m.get("popularity", 0),
        }
        for m in credits
        if m.get("poster_path")
    ]

    filmes.sort(key=lambda x: x["popularidade"], reverse=True)
    return filmes


async def get_movie_detail(movie_id: int) -> Dict[str, Any]:
    """Retorna detalhes de um filme específico pelo ID TMDB."""
    params, headers = _get_auth_params_and_headers({"language": "pt-BR"})

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE}/movie/{movie_id}",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        m = resp.json()

    return {
        "id": m["id"],
        "titulo": m.get("title", ""),
        "sinopse": m.get("overview", ""),
        "poster_path": m.get("poster_path"),
        "poster_url": f"{POSTER_BASE}{m['poster_path']}" if m.get("poster_path") else None,
        "data_lancamento": m.get("release_date", ""),
        "popularidade": m.get("popularity", 0),
    }
