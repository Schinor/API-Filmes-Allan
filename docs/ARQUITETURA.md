# Arquitetura do Sistema — Catálogo Tom Hanks (HANKS+)

Documento que descreve a arquitetura **atual** do projeto, com base no código-fonte
(`frontend/`, `backend/`, `auth-service/`, `docker-compose*.yml`, `Dockerfile`).

## 1. Visão geral

O sistema é uma aplicação web para navegar pelo catálogo de filmes de Tom Hanks
(dados do TMDB), com favoritos, comentários e controle de acesso por papéis (RBAC).
Está dividido em **dois containers** (microsserviços) que compartilham o mesmo banco
MariaDB/MySQL e a mesma `SECRET_KEY` de JWT:

| Componente | Tecnologia | Responsabilidade |
|---|---|---|
| **catalogo** | FastAPI (Python 3.12) + SPA Angular 21 servida como estáticos | Único ponto de entrada público (porta 8000). Filmes (TMDB), favoritos, comentários e *bridge* para autenticação |
| **auth-service** | FastAPI (Python 3.12) | Cadastro, login (JWT), RBAC, usuários, recuperação de senha. Só acessível pela rede interna Docker (`expose 8001`) |
| **Banco de dados** | MariaDB / MySQL externo | Tabelas de ambos os serviços |
| **TMDB API** | Externa | Fonte dos filmes |
| **Mailtrap** | SMTP sandbox externo | Envio do e-mail de redefinição de senha |

## 2. Diagrama de contexto e implantação

```mermaid
flowchart TB
    user(["Usuário no navegador"])

    subgraph host["Host Docker"]
        subgraph net["Rede interna: filmes-network (bridge)"]
            subgraph cat["Container catalogo — porta pública 8000"]
                spa["SPA Angular 21<br/>arquivos estáticos em /static"]
                cat_api["FastAPI Catálogo<br/>/api/filmes · /api/favoritos<br/>/api/comentarios · /api/auth/*"]
            end
            subgraph auth["Container auth-service — expose 8001, sem porta no host"]
                auth_api["FastAPI Auth<br/>login · cadastro · RBAC<br/>usuários · reset de senha"]
            end
        end
    end

    db[("MariaDB / MySQL<br/>banco compartilhado")]
    tmdb["TMDB API<br/>api.themoviedb.org"]
    mail["Mailtrap SMTP<br/>sandbox"]

    user -- "HTTP :8000" --> cat
    spa -. "servida por" .-> cat_api
    cat_api -- "HTTP interno<br/>AUTH_SERVICE_URL" --> auth_api
    cat_api -- "SQLAlchemy<br/>favoritos, comentarios" --> db
    auth_api -- "SQLAlchemy<br/>usuarios, roles, permissions,<br/>role_permissions, reset_tokens" --> db
    cat_api -- "httpx, server-side" --> tmdb
    auth_api -- "SMTP STARTTLS :2525" --> mail
    mail -. "e-mail com link<br/>/reset-password?token=..." .-> user
```

Pontos-chave:

- O navegador **nunca** fala com o `auth-service` nem com o TMDB diretamente; tudo passa pelo catálogo.
- O link de redefinição enviado por e-mail aponta para o catálogo (`CATALOGO_URL/reset-password?token=...`), mantendo o `auth-service` isolado.
- Os dois serviços usam a mesma `DATABASE_URL`, `SECRET_KEY` e `ALGORITHM`.

## 3. Build e empacotamento

```mermaid
flowchart LR
    subgraph build["Dockerfile raiz — multi-stage"]
        s1["Stage 1: node:22-alpine<br/>npm ci + ng build --configuration production"]
        s2["Stage 2: python:3.12-slim<br/>pip install backend/requirements.txt<br/>COPY backend/"]
        s1 -- "dist/frontend/browser → /app/static" --> s2
    end
    s2 --> img1["Imagem catalogo-filmes"]

    subgraph build2["auth-service/Dockerfile"]
        a1["python:3.12-slim<br/>pip install requirements.txt<br/>COPY auth-service/"]
    end
    a1 --> img2["Imagem auth-service"]

    img1 --> compose["docker-compose.yml<br/>imagens do Docker Hub"]
    img2 --> compose
    img1 --> dev["docker-compose.dev.yml<br/>build local, rede filmes-network-dev"]
    img2 --> dev
```

Em desenvolvimento sem Docker, o Angular usa `frontend/proxy.conf.json` para
encaminhar `/api` para `http://127.0.0.1:8000`.

## 4. Frontend (Angular 21, standalone + signals)

```mermaid
flowchart TB
    subgraph routes["Rotas — app.routes.ts, lazy loading"]
        r_landing["/ e /planos → LandingComponent"]
        r_login["/login → LoginComponent<br/>guestGuard"]
        r_reset["/reset-password → ResetPasswordComponent"]
        r_cat["/catalogo → CatalogoComponent<br/>authGuard"]
        r_fav["/favoritos → FavoritosComponent<br/>authGuard + permissionGuard listar:favoritos"]
        r_com["/comentarios → ComentariosComponent<br/>authGuard + permissionGuard listar:comentarios"]
    end

    subgraph shared["Componentes e utilitários"]
        navbar["NavbarComponent"]
        card["MovieCardComponent"]
        modal["MovieModalComponent"]
        dir["HasPermissionDirective<br/>*hasPermission"]
    end

    subgraph guards["Guards e interceptor"]
        ag["authGuard / guestGuard"]
        pg["permissionGuard"]
        ic["authInterceptor<br/>injeta Bearer, trata 401 → logout"]
    end

    subgraph services["Services — camada HTTP"]
        s_auth["AuthService<br/>signals: token, user, permissions<br/>localStorage: tomhanks_token / tomhanks_user"]
        s_fil["FilmesService"]
        s_fav["FavoritosService"]
        s_com["ComentariosService"]
    end

    routes --> guards
    routes --> shared
    guards --> s_auth
    dir --> s_auth
    routes --> services
    services --> ic
    ic -- "HTTP /api/*" --> backend["Backend Catálogo"]
```

`AuthService.hasPermission()` considera `administrar:sistema` como coringa, espelhando a regra do backend.

## 5. Backend Catálogo — camadas

```mermaid
flowchart TB
    main["main.py<br/>CORS, create_all, routers,<br/>fallback SPA para index.html"]

    subgraph routes["routes/"]
        rt_fil["filmes.py<br/>GET /api/filmes, /api/filmes/id<br/>público"]
        rt_fav["favoritos.py<br/>GET, POST, DELETE"]
        rt_com["comentarios.py<br/>GET, POST, DELETE"]
        rt_auth["auth.py<br/>proxy /api/auth/*"]
    end

    subgraph deps["dependencies.py"]
        cu["current_user<br/>1. decodifica JWT localmente<br/>2. fallback: GET /me no auth-service"]
        rp["require_permission<br/>403 sem perm ou administrar:sistema"]
    end

    subgraph data["Acesso a dados"]
        repo_fav["repositories/favorito_repo"]
        repo_com["repositories/comentario_repo"]
        m_fav["models/Favorito<br/>UNIQUE usuario_id + tmdb_movie_id"]
        m_com["models/Comentario"]
        dbcore["core/database.py<br/>engine + SessionLocal + get_db"]
    end

    subgraph ext["Integrações externas"]
        tmdb_s["services/tmdb_service.py<br/>cache em memória do person_id"]
        auth_c["clients/auth_client.py<br/>httpx → auth-service"]
    end

    sec["core/security.py<br/>decode_token JWT"]
    cfg["core/config.py<br/>pydantic-settings"]

    main --> routes
    rt_fav --> rp
    rt_com --> rp
    rt_com --> cu
    rp --> cu
    cu --> sec
    cu --> auth_c
    rt_auth --> auth_c
    rt_fil --> tmdb_s
    rt_fav --> repo_fav --> m_fav --> dbcore
    rt_com --> repo_com --> m_com --> dbcore
    sec --> cfg
    tmdb_s --> cfg
    auth_c --> cfg
```

### Endpoints e permissões exigidas

| Método | Rota | Permissão |
|---|---|---|
| GET | `/api/filmes`, `/api/filmes/{id}` | pública |
| GET | `/api/favoritos` | `listar:favoritos` |
| POST | `/api/favoritos` | `adicionar:favoritos` |
| DELETE | `/api/favoritos/{tmdb_movie_id}` | `remover:favoritos` |
| GET | `/api/comentarios`, `/api/comentarios/{tmdb_movie_id}` | `listar:comentarios` |
| POST | `/api/comentarios` | `criar:comentarios` |
| DELETE | `/api/comentarios/{id}` | autor com `apagar:comentario-proprio`, ou `apagar:comentario-de-outro` / `administrar:sistema` / papel `admin` |
| `*` | `/api/auth/*` | repassado ao auth-service (que aplica suas próprias permissões) |

## 6. Auth-service — camadas

```mermaid
flowchart TB
    amain["main.py<br/>init_db: create_all + ALTER TABLE legado + seed_rbac<br/>GET /health"]

    subgraph aroutes["routes/"]
        ar_auth["auth.py<br/>cadastro · login · me<br/>forgot-password · validate-reset-token · reset-password"]
        ar_users["users.py<br/>users · roles · permissions · admin/status"]
    end

    subgraph acore["core/"]
        asec["security.py<br/>bcrypt, create_access_token,<br/>get_current_user, require_permission"]
        seed["rbac_seed.py<br/>permissões e papéis padrão<br/>sincroniza usuários existentes"]
        mailer["email.py<br/>SMTP Mailtrap, template HTML"]
        acfg["config.py + database.py"]
    end

    subgraph arepo["repositories/"]
        ur["usuario_repo"]
        rr["reset_token_repo"]
    end

    subgraph amodels["models/ — tabelas"]
        t_user["Usuario → usuarios"]
        t_role["Papel → roles"]
        t_perm["Permissao → permissions"]
        t_rp["role_permissions"]
        t_rt["ResetToken → reset_tokens"]
    end

    amain --> aroutes
    amain --> seed
    aroutes --> asec
    ar_auth --> mailer
    aroutes --> arepo --> amodels
    seed --> amodels
    asec --> amodels
```

## 7. Modelo de dados (tabelas compartilhadas no mesmo banco)

```mermaid
erDiagram
    usuarios }o--o| roles : "role_id (SET NULL)"
    roles ||--o{ role_permissions : ""
    permissions ||--o{ role_permissions : ""
    usuarios ||--o{ reset_tokens : "usuario_id"
    usuarios ||..o{ favoritos : "usuario_id (sem FK)"
    usuarios ||..o{ comentarios : "usuario_id (sem FK)"

    usuarios {
        int id PK
        string nome
        string email UK
        string senha_hash
        string role "slug legado, espelha o papel"
        int role_id FK
        datetime criado_em
    }
    roles {
        int id PK
        string name
        string slug UK
        string description
    }
    permissions {
        int id PK
        string action
        string resource "UNIQUE action + resource"
        string description
    }
    role_permissions {
        int role_id PK
        int permission_id PK
    }
    reset_tokens {
        int id PK
        string token UK
        int usuario_id FK
        datetime expira_em
        bool usado
    }
    favoritos {
        int id PK
        int usuario_id
        int tmdb_movie_id "UNIQUE com usuario_id"
        string titulo
        string poster_path
    }
    comentarios {
        int id PK
        int usuario_id
        int tmdb_movie_id
        text texto
        datetime criado_em
    }
```

As tabelas `favoritos` e `comentarios` pertencem ao **catálogo**; as demais, ao **auth-service**.
A ligação entre os dois domínios é apenas lógica (`usuario_id` sem chave estrangeira).

## 8. RBAC — papéis e permissões

Permissões seguem o formato `acao:recurso`. `administrar:sistema` funciona como coringa
no frontend, no catálogo e no auth-service.

```mermaid
flowchart LR
    A["amigo-do-wilson<br/>assistir:catalogo<br/>detalhes:filmes<br/>listar:comentarios"]
    B["preso-no-terminal<br/>+ listar / adicionar / remover:favoritos"]
    C["houston-temos-acesso<br/>+ criar:comentarios<br/>+ apagar:comentario-proprio"]
    D["capitao-hanks<br/>+ assistir:catalogo-premium"]
    E["admin<br/>+ apagar:comentario-de-outro<br/>+ visualizar / gerenciar:usuarios<br/>+ gerenciar:papeis / permissoes<br/>+ administrar:sistema"]

    A -- "herda" --> B -- "herda" --> C -- "herda" --> D -- "herda" --> E
```

O cadastro público aceita apenas os quatro primeiros papéis; pedir `admin` retorna HTTP 403.
Detalhes em [`PERFIS.md`](PERFIS.md).

## 9. Fluxos principais

### 9.1 Login e uso de rota protegida

O JWT é assinado pelo auth-service e contém `sub`, `email`, `nome`, `role` e `permissions`.
Como o catálogo compartilha a `SECRET_KEY`, ele valida o token **localmente**, sem chamada de rede.

```mermaid
sequenceDiagram
    actor U as Usuário
    participant FE as SPA Angular
    participant CAT as Catálogo FastAPI
    participant AUTH as auth-service
    participant DB as MariaDB

    U->>FE: e-mail e senha
    FE->>CAT: POST /api/auth/login (form-urlencoded)
    CAT->>AUTH: POST /login
    AUTH->>DB: busca usuário + papel + permissões
    AUTH->>AUTH: bcrypt.checkpw e gera JWT
    AUTH-->>CAT: access_token + user
    CAT-->>FE: access_token + user
    FE->>FE: guarda token e user em localStorage

    U->>FE: acessa /favoritos
    FE->>FE: authGuard e permissionGuard listar:favoritos
    FE->>CAT: GET /api/favoritos (Bearer JWT via interceptor)
    CAT->>CAT: current_user decodifica JWT e require_permission
    alt JWT inválido no decode local
        CAT->>AUTH: GET /me (fallback remoto)
        AUTH-->>CAT: usuário e permissões
    end
    CAT->>DB: SELECT favoritos WHERE usuario_id
    DB-->>CAT: linhas
    CAT-->>FE: 200 lista de favoritos
```

### 9.2 Consulta de filmes

```mermaid
sequenceDiagram
    participant FE as SPA Angular
    participant CAT as Catálogo FastAPI
    participant TMDB as TMDB API

    FE->>CAT: GET /api/filmes
    opt person_id ainda não em cache
        CAT->>TMDB: GET /search/person?query=Tom Hanks
        TMDB-->>CAT: person_id
    end
    CAT->>TMDB: GET /person/id/movie_credits
    TMDB-->>CAT: cast
    CAT->>CAT: remove filmes sem pôster e ordena por popularidade
    CAT-->>FE: lista de filmes
```

### 9.3 Recuperação de senha

```mermaid
sequenceDiagram
    actor U as Usuário
    participant FE as SPA Angular
    participant CAT as Catálogo FastAPI
    participant AUTH as auth-service
    participant DB as MariaDB
    participant MAIL as Mailtrap SMTP

    U->>FE: informa o e-mail em "Esqueceu a senha?"
    FE->>CAT: POST /api/auth/forgot-password
    CAT->>AUTH: POST /forgot-password
    AUTH->>DB: cria reset_token (expira em 30 min)
    AUTH->>MAIL: envia e-mail com CATALOGO_URL/reset-password?token=...
    AUTH-->>CAT: mensagem de sucesso
    CAT-->>FE: mensagem de sucesso

    U->>FE: abre o link do e-mail
    FE->>CAT: GET /api/auth/validate-reset-token/token
    CAT->>AUTH: GET /validate-reset-token/token
    AUTH->>DB: confere existência, expiração e uso
    AUTH-->>FE: valid true ou false

    U->>FE: define a nova senha
    FE->>CAT: POST /api/auth/reset-password
    CAT->>AUTH: POST /reset-password
    AUTH->>DB: atualiza senha_hash e marca token como usado
    AUTH-->>FE: senha redefinida
```

### 9.4 Remoção de comentário com moderação

```mermaid
flowchart TD
    start(["DELETE /api/comentarios/id"]) --> jwt{"JWT válido?"}
    jwt -- "não" --> e401["401"]
    jwt -- "sim" --> exists{"Comentário existe?"}
    exists -- "não" --> e404["404"]
    exists -- "sim" --> mod{"Tem apagar:comentario-de-outro,<br/>administrar:sistema ou papel admin?"}
    mod -- "sim" --> ok["Remove e retorna 200"]
    mod -- "não" --> own{"É o autor e tem<br/>apagar:comentario-proprio?"}
    own -- "sim" --> ok
    own -- "não" --> e403["403"]
```

## 10. Configuração por variáveis de ambiente

| Variável | Usada por | Função |
|---|---|---|
| `DATABASE_URL` | catálogo, auth | Conexão SQLAlchemy (`mysql+pymysql://...`) |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | catálogo, auth | Assinatura e validação do JWT (chave compartilhada) |
| `TMDB_API_KEY`, `TMDB_BASE_URL` | catálogo | Acesso ao TMDB (v3 `api_key` ou token v4 Bearer) |
| `AUTH_SERVICE_URL` | catálogo | URL interna do auth-service (`http://auth-service:8001`) |
| `MAILTRAP_*`, `RESET_TOKEN_EXPIRE_MINUTES`, `RESET_REQUEST_*`, `EMAIL_LOG_LINK_WITHOUT_SMTP` | auth | SMTP, validade do token de reset, limite de solicitações e modo dev sem SMTP |
| `CATALOGO_URL` | auth | Base pública usada no link do e-mail |
| `PORT` | ambos | Porta do uvicorn (8000 e 8001) |

## 11. Testes

`tests/` usa `pytest` com SQLite em memória e `TestClient` do FastAPI:

- `test_auth_service.py`: health, cadastro/login, matriz de papéis, bloqueio de `admin` no cadastro, fluxo de reset de senha (incluindo token reutilizado, expirado e inexistente).
- `test_backend_proxy.py`: estrutura do app do catálogo, RBAC de favoritos/comentários e moderação de comentários.

## 12. Observações sobre o estado atual

Pontos observados no código que vale ter em mente ao evoluir a arquitetura:

- **Banco compartilhado:** os dois serviços gravam no mesmo schema, então o desacoplamento é de processo, não de dados.
- **JWT com permissões embutidas:** mudar o papel de um usuário só vale para o catálogo após o token expirar (padrão 1440 min) ou novo login, pois o catálogo confia nas permissões do token.
- **`POST /forgot-password`** responde sempre com mensagem neutra (sem `token` e sem revelar se o e-mail existe), limita solicitações por usuário (`RESET_REQUEST_LIMIT` por `RESET_REQUEST_WINDOW_MINUTES`) e registra falhas de envio em log. Sem credenciais SMTP o envio falha, salvo com `EMAIL_LOG_LINK_WITHOUT_SMTP=true` (dev).
- **`GET /api/auth/users/{id}/role`** e `GET /api/auth/roles` não exigem autenticação no auth-service.
- **CORS** está com `allow_origins=["*"]` nos dois serviços.
- **`docker-compose.yml`** usa imagens publicadas (`schinor/...`) e **`docker-compose.dev.yml`** faz build local.
- O auth-service tem migrações Alembic (`migrations/versions/001`, `002`), mas `init_db()` também roda `create_all` e `ALTER TABLE` automáticos na inicialização.
