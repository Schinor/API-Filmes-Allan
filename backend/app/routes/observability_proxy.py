"""Proxy reverso para Grafana e Prometheus através do ponto de entrada público do catálogo.

Existe porque, em produção (Portainer), o domínio público passa por um proxy
(Cloudflare) que só encaminha um conjunto fixo de portas HTTP — as portas dedicadas
do Grafana/Prometheus (ex: 3220, 9090) nunca chegam a esse proxy. Encaminhando por
aqui, os dois ficam acessíveis pelo mesmo domínio/porta já publicados, seguindo o
mesmo padrão "bridge" usado em app.routes.auth para o auth-service.
"""

import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

router = APIRouter(tags=["observability"], include_in_schema=False)

# Headers que não devem ser repassados entre proxy e cliente (RFC 7230) — content-encoding
# e content-length também entram aqui porque o httpx já entrega o corpo descomprimido.
_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}

_security = HTTPBasic()


def _require_prometheus_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
    """O Prometheus não tem login próprio, então o proxy exige HTTP Basic (PROMETHEUS_PROXY_PASSWORD)."""
    expected_password = settings.PROMETHEUS_PROXY_PASSWORD
    if not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Proxy do Prometheus não configurado (defina PROMETHEUS_PROXY_PASSWORD)",
        )
    valid_user = secrets.compare_digest(credentials.username, "admin")
    valid_pass = secrets.compare_digest(credentials.password, expected_password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )


async def _proxy_request(request: Request, base_url: str, path: str) -> Response:
    url = f"{base_url.rstrip('/')}/{path}"
    forward_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            upstream = await client.request(
                request.method,
                url,
                params=request.query_params,
                headers=forward_headers,
                content=body,
                follow_redirects=False,
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço de observabilidade indisponível",
            )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    return Response(content=upstream.content, status_code=upstream.status_code, headers=response_headers)


@router.get("/grafana")
async def grafana_root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/grafana/")


@router.api_route("/grafana/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_grafana(path: str, request: Request) -> Response:
    """Autenticação é feita pelo próprio Grafana (usuário admin / GRAFANA_ADMIN_PASSWORD)."""
    return await _proxy_request(request, settings.GRAFANA_INTERNAL_URL, path)


@router.get("/prometheus", dependencies=[Depends(_require_prometheus_auth)])
async def prometheus_root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/prometheus/")


@router.api_route(
    "/prometheus/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(_require_prometheus_auth)],
)
async def proxy_prometheus(path: str, request: Request) -> Response:
    return await _proxy_request(request, settings.PROMETHEUS_INTERNAL_URL, path)
