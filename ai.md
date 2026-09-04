# Atividade 4 — RBAC de verdade

> ISW055 · Controle de acesso por papel · entrega 04/09/2026
> Continuação direta da Atividade 3 (microsserviço `auth-service`).
> Nada de schema novo — o `role` que já existe em `usuarios` passa a decidir
> algo de verdade, e a checagem acontece no servidor, nunca no Angular.

---

## 1. As quatro peças do RBAC, mapeadas no que já existe

| Peça | Onde já está |
|---|---|
| Usuário | linha em `usuarios` (existe desde a Atividade 3) |
| Papel | coluna `usuarios.role`, hoje `'usuario'` ou `'admin'` (existe, não fazia nada) |
| Atribuição | o próprio valor de `usuarios.role` — 1 usuário, 1 papel, sem tabela extra |
| **Permissão** | **é a peça que falta — o que esta atividade constrói** |

Não precisa de tabela `roles`/`permissions`/`role_permissions` pra dois papéis
fixos — isso seria RBAC genérico demais pro tamanho do projeto. A permissão
vai morar como lógica explícita nas rotas (§4), documentada antes de
implementada (§2), como o enunciado pede.

---

## 2. Permissões por papel (documentar antes de codar)

### `usuario` (papel padrão, atribuído no cadastro)

| Recurso | Pode |
|---|---|
| Filmes | ver catálogo, ver detalhes |
| Favoritos | criar, listar e remover **os próprios** |
| Comentários | criar; remover **apenas os que ele mesmo escreveu** |
| Conta | ver o próprio perfil (`/auth/me`), redefinir a própria senha |

### `admin` (tudo que `usuario` pode, mais)

| Recurso | Pode a mais |
|---|---|
| Comentários | **remover comentário de qualquer usuário** (moderação) ← ação exclusiva desta entrega |

A tabela fica curta de propósito: a atividade pede **uma** ação exclusiva de
admin implementada de verdade, não um painel administrativo inteiro. Escolhi
"apagar comentário de qualquer usuário" (a sugestão principal do enunciado)
em vez da alternativa de promover/rebaixar papel, porque a ação de moderação
já usa uma tabela e uma rota que o projeto já tem (`comentarios`,
`DELETE /api/comentarios/{id}`) — dá pra encaixar sem inventar rota nova.

---

## 3. Onde a checagem acontece — Padrão A, e por quê

O enunciado descreve dois padrões e pergunta qual o projeto já usa. A
resposta está na própria arquitetura da Atividade 3: o `catalogo` é o único
ponto de entrada público, e as chamadas de autenticação já atravessam a rede
interna até o `auth-service` (`AUTH_SERVICE_URL=http://auth-service:8001`,
citado no `docker-compose.yml` e na seção "Proxy/Bridge" do README). Isso é
**Padrão A — enforcement centralizado**: o `catalogo` não decide sozinho quem
é quem, ele pergunta pro `auth-service`.

Vale notar: hoje o `catalogo` e o `auth-service` até compartilham o mesmo
`DATABASE_URL` (mesmo banco físico). Seria tecnicamente possível o `catalogo`
consultar `usuarios.role` direto por SQL, sem passar pelo `auth-service`. Não
faço isso de propósito — o enunciado pede explicitamente "o catálogo,
**consultando** o auth-service", e isso preserva o limite de
responsabilidade que a Atividade 3 já desenhou: quem é dono da lógica de
identidade/permissão é o `auth-service`, o `catalogo` não deveria ler a
tabela de usuários por baixo do pano só porque o banco é compartilhado hoje.

---

## 4. Implementação

### 4.1 `auth-service` — nada novo, só confirmar o contrato

O endpoint `GET /auth/me` já existe (Atividade 3, tabela de testes do
README). Confirmar que o retorno inclui `role`:

```python
# auth-service/app/routes/auth.py
@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome,
            "email": current_user.email, "role": current_user.role}
```

Se hoje não devolve `role`, é o único ajuste necessário no `auth-service`
pra esta atividade — o resto do trabalho é no `catalogo`.

### 4.2 `catalogo` — cliente interno pro `auth-service`

```python
# catalogo/app/clients/auth_client.py
import httpx
from fastapi import HTTPException

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

async def get_authenticated_user(authorization: str | None) -> dict:
    if not authorization:
        raise HTTPException(401, "Token não enviado")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": authorization},
            )
    except httpx.RequestError:
        raise HTTPException(503, "Serviço de autenticação indisponível")

    if resp.status_code != 200:
        raise HTTPException(401, "Token inválido ou expirado")
    return resp.json()  # {"id": ..., "nome": ..., "email": ..., "role": ...}
```

Isso é o Padrão A na prática: cada ação sensível do `catalogo` custa uma
ida-e-volta de rede interna até o `auth-service` — aceitável aqui porque é
rede Docker interna (`filmes-network`), não internet.

### 4.3 `catalogo` — dependency reutilizável

```python
# catalogo/app/dependencies.py
from fastapi import Header, Depends
from .clients.auth_client import get_authenticated_user

async def current_user(authorization: str | None = Header(default=None)) -> dict:
    return await get_authenticated_user(authorization)
```

### 4.4 `catalogo` — a rota que muda de verdade

```python
# catalogo/app/routes/comentarios.py
@router.delete("/comentarios/{comentario_id}")
async def deletar_comentario(
    comentario_id: int,
    user: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    if not comentario:
        raise HTTPException(404, "Comentário não encontrado")

    e_dono = comentario.usuario_id == user["id"]
    e_admin = user["role"] == "admin"

    if not (e_dono or e_admin):
        raise HTTPException(403, "Apenas o autor ou um administrador podem remover este comentário")

    db.delete(comentario)
    db.commit()
    return {"detail": "Comentário removido"}
```

Três casos cobertos com a mesma rota, sem endpoint duplicado:
- dono removendo o próprio comentário → **200** (comportamento que já existia)
- `admin` removendo comentário de outra pessoa → **200** (novo — a ação exclusiva)
- `usuario` comum tentando remover comentário de outra pessoa → **403**

Isso já satisfaz o requisito 3 do enunciado: a recusa acontece no backend,
então chamar a rota direto pelo Postman/curl sem passar pela interface dá o
mesmo 403 — não existe caminho que contorne a checagem.

---

## 5. Demonstração prática (requisito 4)

Roteiro pra tirar os dois prints pedidos:

1. **Login como usuário comum** → `POST /auth/login` → guardar o `access_token`.
2. Descobrir um `comentario_id` que **não** pertence a esse usuário (`GET /api/comentarios?filme_id=...`).
3. `DELETE /api/comentarios/{id}` com `Authorization: Bearer <token do usuario>`
   → esperado **403**, corpo: `"Apenas o autor ou um administrador podem remover este comentário"`.
   **Print 1: esse 403.**
4. **Login como admin** (o admin promovido/seedado na Atividade 3 ou via SQL
   manual `UPDATE usuarios SET role='admin' WHERE email=...`) → guardar o token.
5. `DELETE /api/comentarios/{id}` (mesmo id do passo 3) com o token do admin
   → esperado **200**.
   **Print 2: esse 200**, mostrando que o mesmo comentário que o usuário
   comum não conseguiu apagar, o admin apaga.

Os dois prints lado a lado, com o `id` do comentário visível nos dois, deixam
claro que é a *mesma* ação, só muda quem está pedindo — é exatamente o que o
requisito 4 pede.

---

## 6. Resposta ao requisito 5 — Padrão A ou B?

> Texto pronto pra colar no README:

**Hoje o projeto usa o Padrão A (enforcement centralizado).** O `catalogo`
não decodifica o token sozinho: a cada ação sensível, ele chama
`GET /auth/me` no `auth-service` pela rede interna e só então decide
liberar ou recusar. Isso é consistente com a arquitetura desenhada na
Atividade 3, em que o `auth-service` é o dono exclusivo da lógica de
identidade e o `catalogo` é só o ponto de entrada público.

**O que mudaria pro Padrão B (claims no JWT):** o `catalogo` pararia de
chamar `/auth/me` e passaria a decodificar o token localmente, usando o
`SECRET_KEY`/`ALGORITHM` que os dois serviços já compartilham no
`docker-compose.yml`, lendo o claim `role` direto do payload assinado. A
troca é puramente de latência por atraso de revogação: no Padrão A, mudar o
papel de alguém em `admin` tem efeito imediato na próxima chamada; no
Padrão B, o `catalogo` só "descobriria" a mudança quando o usuário fizesse
login de novo e recebesse um token novo — e como
`ACCESS_TOKEN_EXPIRE_MINUTES=1440` (24h), um rebaixamento de admin pra
usuario comum ficaria até 24h sem efeito prático nas rotas do catálogo.

---

## 7. Trecho de README pronto (requisitos 1 e 5)

```markdown
## Controle de acesso (RBAC)

### O que cada papel pode fazer

**usuario** (papel padrão no cadastro)
- ver catálogo e detalhes de filmes
- criar, listar e remover os próprios favoritos
- criar comentários; remover apenas os próprios comentários

**admin** (tudo que usuario pode, mais)
- remover comentário de qualquer usuário (moderação)

A checagem acontece sempre no backend (`catalogo`, consultando o
`auth-service`) — nunca só na interface. Chamar a rota direto pelo
Postman/curl, sem passar pelo Angular, recebe a mesma recusa.

### Padrão de arquitetura usado

Ver seção 6 deste plano — cola direto aqui.
```

---

## 8. Checklist de entrega

- [ ] `GET /auth/me` no `auth-service` devolve `role` no corpo
- [ ] `catalogo` ganha `auth_client.py` consultando `/auth/me`
- [ ] `dependencies.py` com `current_user` reutilizável nas rotas protegidas
- [ ] `DELETE /api/comentarios/{id}` com a checagem dono-ou-admin (§4.4)
- [ ] Testar via curl/Postman direto, sem passar pelo Angular, os dois casos
- [ ] Print do 403 (usuario comum) e do 200 (admin) no mesmo comentário
- [ ] README atualizado: tabela de permissões (§2) + resposta Padrão A/B (§6)
- [ ] Menção ao `@siriani` mantida no README
- [ ] Commit no mesmo repositório das Atividades 2 e 3 (sem repo novo)