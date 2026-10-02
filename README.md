# 🎬 Catálogo de Filmes — Tom Hanks (Arquitetura de Microsserviços)

Aplicação web fullstack para navegação no catálogo de filmes do ator Tom Hanks, com sistema de favoritos, comentários e microsserviço dedicado de **autenticação, controle de acesso e recuperação de senha**.

> **Disciplina:** Cloud Computing / Arquitetura de Software  
> **Professor:** [@siriani](https://github.com/siriani)

🔗 **Aplicação em produção (Portainer):** **https://marcio-mazega-isw055.lapps.studio**

### 🗂️ Atividades e onde estão neste README

| Nº | Atividade | Seções |
|---|---|---|
| 2 | Catálogo de filmes Tom Hanks (TMDB, favoritos, comentários, segregação por usuário) | [Catálogo e segregação](#-catálogo-e-segregação-por-usuário), [Evolução arquitetural](#️-evolução-arquitetural-monólito--microsserviços), [Modelo de dados](#️-modelo-de-dados-schema) |
| 3 | Microsserviço de autenticação + esqueci minha senha | [Evolução arquitetural](#️-evolução-arquitetural-monólito--microsserviços), [Recuperação de senha](#-demonstração-do-fluxo-de-recuperação-de-senha), [Docker Compose](#-docker-compose--configuração-dos-serviços) |
| 4 | RBAC | [Controle de acesso (RBAC)](#️-controle-de-acesso-baseado-em-papel-rbac) |
| 5 | Logs e auditoria | [Auditoria: log-service + Redis Streams](#-auditoria-log-service--redis-streams) |
| 6 | Upload e perfil | [Perfil de usuário e object storage (Garage)](#️-perfil-de-usuário-e-object-storage-garage) |
| Extra | Swagger/OpenAPI | [Documentação da API](#-documentação-da-api-swagger--openapi) |
| Extra | CI/CD | [CI/CD com GitHub Actions](#-cicd-com-github-actions) |
| Extra | Observabilidade | [Observabilidade](#-observabilidade-health-checks-e-métricas) |

---

## 🏛️ Evolução Arquitetural: Monólito ➔ Microsserviços

Na **Atividade 2**, o catálogo rodava em um único container monolítico (FastAPI + Angular) com regras de negócio, dados e autenticação acoplados no mesmo deploy.

Na **Atividade 3**, toda a responsabilidade de autenticação e identidade foi desacoplada para um **segundo container independente (`auth-service`)**, mantendo o catálogo como o **único ponto de entrada público**.

Na **Atividade 6**, a stack ganhou um **object storage S3 compatível (Garage)** para as fotos de perfil — ver a seção **🖼️ Perfil de usuário e object storage (Garage)** abaixo.

```
                           REDE EXTERNA (HOST)
                                   │
                                   │  HTTP :8000
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  CONTAINER 1: catalogo (Único Ponto de Entrada Público)               │
│                                                                        │
│  ┌───────────────────────┐         ┌───────────────────────────────┐   │
│  │   Angular 21 SPA      │ ──────▶ │   FastAPI (Backend Catálogo)  │   │
│  │   - Catálogo          │         │   - /api/filmes (TMDB)        │   │
│  │   - Favoritos         │         │   - /api/favoritos            │   │
│  │   - Comentários       │         │   - /api/comentarios          │   │
│  │   - Perfil (foto)     │         │   - /api/perfis + /storage/*  │   │
│  │   - Redefinição Senha │         │   - /api/auth/* (Proxy/Bridge)│   │
│  └───────────────────────┘         └───────┬──────────────┬────────┘   │
└────────────────────────────────────────────┼──────────────┼────────────┘
                                             │              │
                      REDE INTERNA DOCKER    │              │  S3 (boto3) e ponte /storage:
                     (filmes-network bridge) │              │  http://garage:3900
                                             │              ▼
                                             │   ┌─────────────────────────────┐
                                             │   │ garage (object storage S3)  │
                                             │   │ bucket catalogo-avatares    │
                                             │   │ sem porta publicada         │
                                             │   └─────────────────────────────┘
                                             │  HTTP interno:
                                             │  http://auth-service:8001
                                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│  CONTAINER 2: auth-service (Isolado na Rede Interna - Sem Porta Host) │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │   FastAPI (Microsserviço de Autenticação)                        │  │
│  │   - Cadastro e Login com JWT                                     │  │
│  │   - Gestão de papéis e permissões (RBAC)                         │  │
│  │   - Esqueci minha senha (Reset Tokens com expiração de 30 min)   │  │
│  │   - Integração SMTP Mailtrap para disparo de e-mails reais       │  │
│  └──────────────────┬─────────────────────────────┬─────────────────┘  │
└─────────────────────┼─────────────────────────────┼────────────────────┘
                      │                             │
                      ▼                             ▼
          ┌───────────────────────┐     ┌───────────────────────┐
          │   Mailtrap Sandbox    │     │   MariaDB / MySQL     │
          │   (Envio de E-mail)   │     │   (Banco Existente)   │
          └───────────────────────┘     └───────────────────────┘
```

### Principais Benefícios da Arquitetura
1. **Isolamento Real de Responsabilidades:** Regras de negócio de catálogo e autenticação rodam em processos e containers separados.
2. **Defesa em Profundidade:** O `auth-service` **não possui portas publicadas para o host**, sendo acessível apenas pela rede Docker interna (`filmes-network`).
3. **Ponto de Entrada Único:** Todas as requisições públicas (incluindo o link de troca de senha) chegam pelo Catálogo, que encaminha internamente as chamadas de autenticação.

---

## 🎞️ Catálogo e segregação por usuário

O catálogo vem da TMDB (chamada só pelo backend); o pôster é a URL `image.tmdb.org/t/p/w500{poster_path}`, sem baixar a imagem:

![Ficha do filme no catálogo com pôster, título, ano e sinopse](assets/SitePosterSinopse.png)

Favoritos são filtrados pelo `usuario_id` do JWT — nunca por um id enviado pelo cliente. A conta A tem 7 favoritos; a conta B, logada no mesmo endereço, não vê nenhum:

![Conta A: página de favoritos com 7 filmes](assets/SiteAt2UserA.png)
![Conta B: página de favoritos vazia](assets/SiteAt2UserB.png)

---

## 📸 Demonstração do Fluxo de Recuperação de Senha

### 1. Solicitação de Recuperação de Senha
O usuário informa o e-mail cadastrado na tela de login clicando em *"Esqueceu a senha?"*:

![Solicitação de Recuperação](assets/Site_Funcionando.png)

---

### 2. E-mail Real Recebido no Mailtrap Sandbox
O microsserviço `auth-service` dispara um e-mail HTML/texto via SMTP contendo o link seguro de uso único e validade de 30 minutos:

![E-mail Recebido no Mailtrap](assets/Site_Funcionando1.png)

---

### 3. Redefinição de Senha via Rota do Catálogo
Ao clicar no link do e-mail, a rota pública do catálogo (`/reset-password?token=...`) valida o token e permite a criação da nova senha com segurança:

![Redefinição de Senha](assets/Site_Funcionando2.png)

---

### 4. Link Expirado Recusado
O token é recusado se não existir, se já tiver sido usado (`usado = true` após a troca) ou se `agora >= expira_em` (30 minutos após a criação). Para testar sem esperar, basta forçar a expiração no banco (`UPDATE reset_tokens SET expira_em = NOW() - INTERVAL 1 MINUTE WHERE token = '<TOKEN>';`) e abrir o link:

![Link de recuperação expirado sendo recusado](assets/Site_Funcionando3.png)

---

## 🐳 Docker Compose — Configuração dos Serviços

Trecho do `docker-compose.yml` ilustrando os dois serviços e a rede compartilhada `filmes-network`:

```yaml
services:
  catalogo:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: catalogo-filmes
    ports:
      - "${PORT:-8000}:8000"  # Ponto de entrada público
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - TMDB_BASE_URL=${TMDB_BASE_URL:-https://api.themoviedb.org/3}
      - TMDB_API_KEY=${TMDB_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=1440
      - PORT=8000
      - AUTH_SERVICE_URL=http://auth-service:8001
      - STORAGE_ENDPOINT=http://garage:3900       # object storage (Atividade 6)
      - STORAGE_BUCKET=${STORAGE_BUCKET:-catalogo-avatares}
      - STORAGE_ACCESS_KEY=${STORAGE_ACCESS_KEY}
      - STORAGE_SECRET_KEY=${STORAGE_SECRET_KEY}
    depends_on:
      auth-service:
        condition: service_healthy
      garage:
        condition: service_healthy
    dns:
      - 8.8.8.8
      - 1.1.1.1
    networks:
      - filmes-network

  auth-service:
    build:
      context: ./auth-service
      dockerfile: Dockerfile
    container_name: auth-service
    expose:
      - "8001"                # Sem "ports:" publicado para o host
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=${ALGORITHM:-HS256}
      - ACCESS_TOKEN_EXPIRE_MINUTES=1440
      - PORT=8001
      - MAILTRAP_HOST=${MAILTRAP_HOST:-sandbox.smtp.mailtrap.io}
      - MAILTRAP_PORT=${MAILTRAP_PORT:-2525}
      - MAILTRAP_USERNAME=${MAILTRAP_USERNAME:-}
      - MAILTRAP_PASSWORD=${MAILTRAP_PASSWORD:-}
      - MAILTRAP_FROM_EMAIL=${MAILTRAP_FROM_EMAIL:-nao-responda@tomhanksfilmes.com}
      - CATALOGO_URL=${CATALOGO_URL:-http://localhost:8000}
      - RESET_TOKEN_EXPIRE_MINUTES=30
    dns:
      - 8.8.8.8
      - 1.1.1.1
    networks:
      - filmes-network

  garage:
    image: ghcr.io/schinor/garage:${IMAGE_TAG:-latest}   # dxflrs/garage:v2.3.0 + garage.toml
    command: ["/garage", "server", "--single-node", "--default-bucket"]
    environment:
      - GARAGE_RPC_SECRET=${GARAGE_RPC_SECRET}
      - GARAGE_DEFAULT_ACCESS_KEY=${STORAGE_ACCESS_KEY}
      - GARAGE_DEFAULT_SECRET_KEY=${STORAGE_SECRET_KEY}
      - GARAGE_DEFAULT_BUCKET=${STORAGE_BUCKET:-catalogo-avatares}
    volumes:
      - garage-meta:/var/lib/garage/meta
      - garage-data:/var/lib/garage/data
    expose:
      - "3900"                # Sem "ports:" — o navegador chega pela ponte /storage do catálogo
    healthcheck:
      test: ["CMD", "/garage", "status"]
    networks:
      - filmes-network

networks:
  filmes-network:
    driver: bridge

volumes:
  garage-meta:
  garage-data:
```

> Trecho resumido — o arquivo completo ([`docker-compose.yml`](docker-compose.yml)) também tem log-service, Redis, Prometheus e Grafana.

---

## ⚙️ Variáveis de Ambiente

Configure as variáveis no seu arquivo `.env` com base no [.env.example](.env.example):

```env
# Banco de Dados existente (MariaDB / MySQL compartilhado)
DATABASE_URL=mysql+pymysql://usuario:senha@host:3306/nome_do_banco

# API TMDB
TMDB_API_KEY=seu_token_tmdb
TMDB_BASE_URL=https://api.themoviedb.org/3

# Chave JWT compartilhada
SECRET_KEY=chave_secreta_jwt_longa_e_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Rede e Portas
PORT=8000
AUTH_SERVICE_URL=http://auth-service:8001

# E-mail (SMTP Mailtrap)
# DESENVOLVIMENTO — Mailtrap Sandbox: captura os e-mails numa caixa de testes,
# NÃO entrega ao destinatário real.
MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=2525
MAILTRAP_USERNAME=seu_usuario_mailtrap
MAILTRAP_PASSWORD=sua_senha_mailtrap
#
# PRODUÇÃO — Mailtrap Email Sending: entrega ao e-mail real do usuário.
# Exige domínio verificado no Mailtrap (SPF/DKIM). Troque as linhas acima por:
# MAILTRAP_HOST=live.smtp.mailtrap.io
# MAILTRAP_PORT=587
# MAILTRAP_USERNAME=apismtp@mailtrap.io   (conforme exibido no painel do domínio)
# MAILTRAP_PASSWORD=token_de_api_do_mailtrap
#
# O remetente precisa pertencer ao domínio verificado (em produção).
MAILTRAP_FROM_EMAIL=nao-responda@tomhanksfilmes.com
MAILTRAP_FROM_NAME="Catálogo Filmes Tom Hanks"

# URL PÚBLICA do catálogo (com HTTPS em produção) — usada no link do e-mail
CATALOGO_URL=http://localhost:8000

# Redefinição de senha
RESET_TOKEN_EXPIRE_MINUTES=30
# Máximo de solicitações por usuário dentro da janela (anti-abuso)
RESET_REQUEST_LIMIT=3
RESET_REQUEST_WINDOW_MINUTES=15
# Somente dev: sem credenciais SMTP, registra o link no log do auth-service
# em vez de falhar. Mantenha false em produção.
EMAIL_LOG_LINK_WITHOUT_SMTP=false

# Auditoria (log-service) — token compartilhado entre catálogo e log-service
# Gere com: openssl rand -hex 32
LOG_INTERNAL_TOKEN=token_interno_do_log_service

# Observabilidade (Grafana) e tag das imagens
GRAFANA_ADMIN_PASSWORD=senha_do_admin_do_grafana
# Senha do HTTP Basic que protege o proxy /prometheus (usuário fixo "admin") — o Prometheus
# não tem login próprio. Sem essa variável o proxy fica desabilitado (503).
PROMETHEUS_PROXY_PASSWORD=senha_do_proxy_do_prometheus
IMAGE_TAG=latest

# Object storage (Garage) — Atividade 6
# GARAGE_RPC_SECRET:  openssl rand -hex 32
# STORAGE_ACCESS_KEY: echo "GK$(openssl rand -hex 16)"   (precisa começar com GK)
# STORAGE_SECRET_KEY: openssl rand -hex 32
GARAGE_RPC_SECRET=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_BUCKET=catalogo-avatares
# Expiração da URL pré-assinada (ver seção do perfil)
STORAGE_BANDA_MINIMA_KBPS=256
STORAGE_MARGEM_USO_SEGUNDOS=600
STORAGE_EXPIRACAO_MAX_SEGUNDOS=3600
# Tamanho máximo do upload da foto (2 MB)
PERFIL_FOTO_MAX_BYTES=2097152
```

---

## 🏃 Como Executar

### 1. Execução Local com Docker Compose

```bash
docker compose up --build
```

- **Aplicação Web:** `http://localhost:8000`
- **Documentação da API (Catálogo):** `http://localhost:8000/api/docs`

> O `auth-service` não aceita conexões diretas do host (`curl http://localhost:8001` falhará propositalmente), garantindo o isolamento da rede interna.

---

### 2. Deploy no Portainer (Stack de Microsserviços)

1. Acesse o **Portainer** do servidor.
2. Vá em **Stacks** ➔ **Add Stack**.
3. Selecione **Repository**:
   - **Repository URL:** URL do seu repositório GitHub
   - **Repository reference:** `refs/heads/feature/auth-microservice` (ou a branch de entrega)
   - **Compose path:** `docker-compose.yml`
4. Na seção **Environment variables**, adicione as variáveis de ambiente necessárias:
   - `PORT`: Porta reservada atribuída ao seu usuário
   - `DATABASE_URL`: String de conexão do seu banco MariaDB existente
   - `TMDB_API_KEY`: Seu Bearer Token da TMDB
   - `SECRET_KEY`: Sua chave secreta JWT
   - `MAILTRAP_HOST`, `MAILTRAP_PORT`, `MAILTRAP_USERNAME`, `MAILTRAP_PASSWORD`: credenciais SMTP (Sandbox para testes, Email Sending para entrega real)
   - `MAILTRAP_FROM_EMAIL`: remetente do domínio verificado no Mailtrap
   - `CATALOGO_URL`: URL pública do catálogo, com `https://` (usada no link do e-mail e como base dos links do Grafana — se ficar no padrão `localhost`, o login do Grafana redireciona para `localhost:8000/grafana`)
   - `LOG_INTERNAL_TOKEN`: token compartilhado entre o catálogo e o log-service
   - `GRAFANA_ADMIN_PASSWORD`: senha do admin do Grafana
   - `PROMETHEUS_PROXY_PASSWORD`: senha do HTTP Basic que protege `/prometheus` (o Prometheus não tem login próprio)
   - `GARAGE_RPC_SECRET`, `STORAGE_ACCESS_KEY` (começa com `GK`) e `STORAGE_SECRET_KEY`: segredos do object storage (comandos de geração no [`.env.example`](.env.example)). **Não troque depois do primeiro deploy**: o Garage guarda a chave de acesso no volume `garage-meta`
   - `STORAGE_BUCKET`, `STORAGE_BANDA_MINIMA_KBPS`, `STORAGE_MARGEM_USO_SEGUNDOS`, `STORAGE_EXPIRACAO_MAX_SEGUNDOS`, `PERFIL_FOTO_MAX_BYTES` *(opcionais)*: já têm padrão no compose
   - `IMAGE_TAG` *(opcional)*: tag das imagens do GHCR (`latest` por padrão; use `sha-<commit>` para fixar uma versão)
5. Clique em **Deploy the stack**. O Portainer baixa as imagens `ghcr.io/schinor/*` (catálogo, auth-service, log-service, garage, prometheus e grafana), sobe o Redis e conecta tudo na rede privada.

**Stack em produção:** https://marcio-mazega-isw055.lapps.studio (domínio gerado pelo Portainer para a porta pública do `catalogo`, ou seja, a porta `${PORT}` mapeada no compose).
- Documentação da API: https://marcio-mazega-isw055.lapps.studio/api/docs
- Redoc: https://marcio-mazega-isw055.lapps.studio/api/redoc
- Grafana: https://marcio-mazega-isw055.lapps.studio/grafana (login `admin` / `GRAFANA_ADMIN_PASSWORD`)
- Prometheus: https://marcio-mazega-isw055.lapps.studio/prometheus (HTTP Basic `admin` / `PROMETHEUS_PROXY_PASSWORD`)

> Apenas o `catalogo` fica exposto diretamente nesse domínio (é o único serviço com `ports:` publicado — ver [Docker Compose](#-docker-compose--configuração-dos-serviços)). `auth-service`, `log-service`, `redis` e `garage` só existem na rede interna `filmes-network`. Prometheus (`9090`) e Grafana (`3000`) também ficam só na rede interna (`expose:`): o domínio público passa por um proxy (Cloudflare, no caso do Portainer/lapps.studio) que só encaminha um conjunto fixo de portas HTTP, então uma porta dedicada nunca chegaria lá — e publicá-la no host compartilhado conflita com a stack de outro aluno (`port is already allocated`) e impede o container de subir. Por isso o `catalogo` expõe **`/grafana`** e **`/prometheus`**, que encaminham internamente para `grafana:3000` e `prometheus:9090` removendo o prefixo — por isso o Grafana usa só `GF_SERVER_ROOT_URL=${CATALOGO_URL}/grafana/` (para gerar os links) **sem** `GF_SERVER_SERVE_FROM_SUB_PATH`, e o Prometheus usa `--web.external-url=/prometheus/` com `--web.route-prefix=/` (mesmo padrão *bridge* já usado em `/api/auth/*` — ver [`backend/app/routes/observability_proxy.py`](backend/app/routes/observability_proxy.py)). O Grafana continua com seu próprio login; o Prometheus não tem autenticação nativa, então o proxy exige HTTP Basic (`PROMETHEUS_PROXY_PASSWORD`) — sem essa variável definida, o proxy responde `503` de propósito.

> As imagens do GHCR nascem **privadas**. Torne os pacotes públicos ou cadastre no Portainer um registry `ghcr.io` com um Personal Access Token de escopo `read:packages` (o token fica no Portainer, nunca no repositório).
> O Prometheus, o Grafana e o Garage usam imagens próprias (`prometheus/Dockerfile`, `grafana/Dockerfile`, `garage/Dockerfile`) com a configuração (`prometheus.yml`, `grafana/provisioning`, `grafana/dashboards`, `garage/garage.toml`) já embutida na imagem — não há bind mount de caminho do repositório, então a stack sobe normalmente mesmo com um usuário não administrador no Portainer.

---

## 📄 Documentação da API (Swagger / OpenAPI)

Dois serviços documentados de ponta a ponta: **catálogo** e **auth-service**.

| Serviço | Swagger UI | Redoc |
|---|---|---|
| catalogo (produção) | **https://marcio-mazega-isw055.lapps.studio/api/docs** | https://marcio-mazega-isw055.lapps.studio/api/redoc |
| catalogo (local) | `http://localhost:8000/api/docs` | `http://localhost:8000/api/redoc` |
| auth-service | `http://localhost:8001/docs` *(só na rede interna do Docker — sem porta publicada no host)* | `http://localhost:8001/redoc` |

Cada rota, nos dois serviços, documenta:
- Método HTTP, path e parâmetros (query/path), com os tipos e validações reais (`Query(..., ge=1, le=500)` etc.).
- Corpo da requisição, via os `schemas` Pydantic (`response_model` e os `BaseModel` de entrada).
- **Todas as respostas possíveis com exemplo de payload** — sucesso e erro. Os erros (`401`, `403`, `404`, `409`, `502`, `503`, além do `400` específico de cada rota) são declarados via `responses={...}` em cada `@router` (ver [`backend/app/core/api_responses.py`](backend/app/core/api_responses.py) e [`auth-service/app/core/api_responses.py`](auth-service/app/core/api_responses.py)), com o `detail` exatamente igual ao que o código realmente devolve — não é um exemplo genérico.

Por padrão o FastAPI só documenta o código de sucesso e o `422` automático de validação; os `responses=` acima existem porque sem eles o Swagger nunca mostraria, por exemplo, que `POST /api/favoritos` pode devolver `409` (filme já favoritado) ou que qualquer rota protegida por `require_permission` pode devolver `403` (e gerar um evento `acesso_negado` na auditoria).

```bash
# Exemplo de "Try it out" via curl (equivalente ao botão no Swagger)
curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=seu-email@exemplo.com&password=sua-senha" | python3 -m json.tool
```

![Swagger UI — POST /api/auth/login com "Try it out" (senha e token ocultados)](assets/SiteSwaggerUI.png)

---

## 🧾 Auditoria: log-service + Redis Streams

Terceiro microsserviço da stack. Ele recebe eventos de auditoria do catálogo e os grava em um **Redis Stream** (`audit:events`).

```
Navegador → catalogo (:8000) ──POST /eventos──┐
                │                             ▼
                ├─ auth-service ──────►  log-service (expose 8002) ──XADD──► Redis
                │                             ▲
Admin → GET /api/logs (catalogo, exige RBAC) ─┘ GET /eventos
```

- O navegador **nunca** fala com o log-service, só com o catálogo (mesmo padrão *bridge* do `/api/auth/*`).
- O log-service é o único que fala com o Redis. Nem ele nem o Redis publicam porta no host.
- A comunicação interna usa o cabeçalho `X-Internal-Token` (`LOG_INTERNAL_TOKEN`), comparado em tempo constante.
- **Auditoria não derruba funcionalidade:** se o log-service cair, favoritar e comentar continuam funcionando (o cliente usa timeout de 1,5 s e só registra um warning).

### Por que Redis Streams?

- **Ordenação e ID nativos:** cada `XADD` gera um ID `<timestamp-ms>-<seq>` monotônico, então a ordem cronológica vem de graça, sem coluna de data nem índice.
- **Leitura dos últimos N eventos** com uma única chamada: `XREVRANGE audit:events + - COUNT N` (mais recentes primeiro).
- **Escrita append-only barata**, ideal para trilha de auditoria, com limite de tamanho (`MAXLEN ~ 100000`) para o stream não crescer sem fim.
- Persistência via AOF (`--appendonly yes`) e volume Docker `redis-data`.

### Eventos registrados

| Evento (`acao`) | Onde nasce | Campos extras |
|---|---|---|
| `login` | proxy `POST /api/auth/login` (200) | `usuario_id` |
| `login_falhou` | proxy `POST /api/auth/login` (401) | `detalhes=email:<tentado>` |
| `logout` | `POST /api/auth/logout` (chamado pelo Angular ao clicar em *Sair*) | `usuario_id` |
| `favoritar` | `POST /api/favoritos` | `recurso=filme:<id>` |
| `comentar` | `POST /api/comentarios` | `recurso=filme:<id>`, `detalhes=comentario:<id>` |
| `apagar_comentario` | `DELETE /api/comentarios/{id}` | `detalhes=autor` ou `moderacao` |
| `perfil_atualizado` | `PUT /api/perfis/{id}` (200) | `recurso=perfil:<id>` |
| `perfil_foto_atualizada` | `PUT /api/perfis/{id}/foto` (200) | `recurso=perfil:<id>`, `detalhes=<chave do objeto>` |
| `perfil_foto_removida` | `DELETE /api/perfis/{id}/foto` (204, havia foto) | `recurso=perfil:<id>` |
| `acesso_negado` | **Toda** resposta 403 do catálogo, pelo handler global de exceções (`app/main.py` → `auditar_acesso_negado`): `require_permission`, `DELETE` de comentário alheio, edição de perfil alheio e também os 403 repassados do auth-service (ex.: `GET /api/auth/users` sem `gerenciar:usuarios`, cadastro pedindo `admin`) | `recurso=<permissão>`, `comentario:<id>` ou `perfil:<id alvo>` (vazio quando o 403 vem do auth-service); `usuario_id` lido do JWT; `detalhes=<método> <rota>` |

Todo evento carrega `usuario_id` (quando há), `acao`, `origem`, `timestamp` (UTC, ISO 8601) e `ip`.

### Consulta (somente admin)

`GET /api/logs?limit=50` exige a permissão `visualizar:logs`, atribuída **somente** ao papel `admin`. Usuário comum recebe **403** (e isso gera um evento `acesso_negado`). As permissões vão dentro do JWT: depois de a permissão nova entrar no seed, o admin precisa fazer **login de novo**.

```bash
curl -s -H "Authorization: Bearer $TOKEN_ADMIN" "https://marcio-mazega-isw055.lapps.studio/api/logs?limit=20"
```

**Saída real de uma execução local** (stack de CI, do mais recente para o mais antigo):

```
login          uid=2  (admin)
logout         uid=1
acesso_negado  uid=1  visualizar:logs  GET /api/logs
comentar       uid=1  filme:13         comentario:1
favoritar      uid=1  filme:13
login          uid=1
login_falhou   -      email:naoexiste@teste.com
```

![Consulta a /api/logs autenticada como admin](assets/SiteLogsAdmin.png)

---

## 📈 Observabilidade: health checks e métricas

### `/health` com readiness real

| Serviço | Dependência testada | Falha |
|---|---|---|
| catalogo | MariaDB (`SELECT 1`), auth-service (`GET /health` = 200) e Garage (responde na `:3900`), em paralelo | `503 {"status":"unhealthy","db":"up","auth_service":"down","storage":"up"}` (o campo da dependência que caiu vem `down`) |
| auth-service | MariaDB (`SELECT 1`) | `503 {"status":"unhealthy","db":"down",...}` |
| log-service | Redis (`PING`) | `503 {"status":"unhealthy","redis":"down"}` |

Cada serviço tem `healthcheck` no compose (Python `urllib`, já que as imagens `slim` não têm `curl`), e o `depends_on` usa `condition: service_healthy`. Com o Redis parado, o log-service passa a `(unhealthy)` sozinho (~30 s no compose de produção).

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
docker stop <container-redis>       # após ~30-40 s: log-service (unhealthy)
docker start <container-redis>      # volta a (healthy)
```

> 📸 **Prints:** para `docker ps`, use a lista de **Containers** do Portainer (mostra o `Status`/`Health` de cada serviço da stack sem precisar de acesso SSH ao host) — capture com tudo `(healthy)` e, opcionalmente, pare o container do Redis pelo próprio Portainer e capture o `log-service` ficando `(unhealthy)`. Para `/metrics`, acesse https://marcio-mazega-isw055.lapps.studio/metrics; para o painel do Grafana, acesse https://marcio-mazega-isw055.lapps.studio/grafana (ver seção "Deploy no Portainer" acima).

![Containers da stack no Portainer (02/10/2026): só o catalogo publica porta (8220:8000); auth-service, log-service, garage e redis só na rede interna](assets/SitePortainerContainers.png)
![/health do catálogo em produção com as três dependências up](assets/SiteHealth.png)
![Containers da stack no Portainer, com o redis pausado](assets/SiteContainerPausado.png)
![log-service (unhealthy) após o redis parar de responder](assets/SiteLogsParado.png)

### `/metrics` (Prometheus)

Os três serviços expõem `/metrics` via `prometheus-fastapi-instrumentator` (`http_requests_total` por rota/status e `http_request_duration_seconds`). `/health` e `/metrics` ficam fora da contagem.

> ⚠️ O catálogo tem a porta pública, então `/metrics` fica acessível por ela. Em produção real, bloqueie a rota no proxy de borda e deixe só o Prometheus raspar pela rede interna.

![/metrics do catálogo em produção (contagem por rota/status)](assets/SiteMetricsGrafana.png)

### Prometheus + Grafana (bônus)

- Prometheus: `http://localhost:9090` localmente (`docker-compose.dev.yml`), ou https://marcio-mazega-isw055.lapps.studio/prometheus em produção (HTTP Basic `admin` / `PROMETHEUS_PROXY_PASSWORD` — ver [proxy](#-docker-compose--configuração-dos-serviços)). `prometheus.yml` raspa `catalogo:8000`, `auth-service:8001`, `log-service:8002`; em `/targets` os três devem estar `UP`.
- Grafana: `http://localhost:3000` localmente (`docker-compose.dev.yml`), ou https://marcio-mazega-isw055.lapps.studio/grafana em produção (usuário `admin`, senha em `GRAFANA_ADMIN_PASSWORD`). A fonte de dados e o painel **HANKS+ — Serviços** (requisições/min, erros 4xx/5xx e latência p95) já vêm provisionados em `grafana/`.

![Prometheus em produção: os três alvos UP](assets/SitePrometheusContainers.png)
![Painel HANKS+ — Serviços no Grafana: requisições/min, erros 4xx/5xx e latência p95](assets/SiteGrafanaDashboard.png)

---

## 🖼️ Perfil de usuário e object storage (Garage)

**Atividade 6.** Cada usuário tem uma página de perfil (`/perfil/:id`) com **nome, foto, bio curta (280 caracteres) e a lista de filmes favoritados**. A foto vai para um **object storage S3 compatível (Garage)**, num bucket dedicado (`catalogo-avatares`); o banco guarda **só a chave** do objeto.

| Método | Rota | O que faz | Sucesso |
|---|---|---|---|
| GET | `/api/perfis/me` | Perfil do usuário logado | 200 |
| GET | `/api/perfis/{usuario_id}` | Perfil de qualquer usuário (qualquer logado pode ver) | 200 / 404 |
| PUT | `/api/perfis/{usuario_id}` | Atualiza a bio (só o dono) | 200 |
| PUT | `/api/perfis/{usuario_id}/foto` | Upload multipart, campo `foto` (só o dono) | 200 |
| DELETE | `/api/perfis/{usuario_id}/foto` | Remove a foto (só o dono, idempotente) | 204 |

### 1. Por que a imagem não mora no banco

Guardar a foto como `BLOB` no MariaDB incha as tabelas e o backup, deixa toda leitura de perfil carregando megabytes pela conexão do banco e não escala: o banco relacional é caro para servir arquivo. O **object storage** é feito para isso — arquivos endereçados por **bucket + chave**, lidos e gravados por uma **API HTTP (S3)** com autenticação por **assinatura** em cada requisição. É a evolução natural de FTP/SFTP/SCP: em vez de um servidor de arquivos com sessão e diretórios, uma API sem estado, com permissões por chave e URLs temporárias.

No projeto, o banco guarda apenas `foto_key` (ex.: `avatares/42/9f1c….webp`) e `foto_bytes`. A URL é **montada na hora de exibir**.

### 2. Fluxo

```
UPLOAD
Navegador ──PUT /api/perfis/{id}/foto (JWT)──► catalogo
                                                 │ 1. id da rota == id do JWT?  (senão 403 + acesso_negado)
                                                 │ 2. lê em chunks até PERFIL_FOTO_MAX_BYTES (senão 413)
                                                 │ 3. Pillow: é JPEG/PNG/WEBP de verdade? (senão 415)
                                                 │ 4. re-encode → WEBP 512×512, chave avatares/<id>/<uuid>.webp
                                                 ├──PutObject (boto3)──► garage:3900  (arquivo)
                                                 └──UPDATE perfis──────► MariaDB      (só a chave)

EXIBIÇÃO
Navegador ──GET /api/perfis/{id}──► catalogo ──gera URL pré-assinada (host interno garage:3900)
          ◄── foto_url = /storage/catalogo-avatares/avatares/42/<uuid>.webp?X-Amz-...&X-Amz-Signature=...
Navegador ──<img src=foto_url>──► catalogo /storage/* (ponte, sem JWT)
                                     └── repassa caminho + query INTACTOS ──► garage:3900
                                                                   Garage valida assinatura e expiração
                                                                   (válida → 200 image/webp; adulterada/expirada → 403)
```

### 3. Por que Garage

| | **Garage** (escolhido) | MinIO (community) | OpenStack Swift |
|---|---|---|---|
| Custo / licença | Gratuito (AGPL) | Gratuito (AGPL) | Gratuito (Apache) |
| Manutenção | Ativa (v2.3.0) | Repositório community **arquivado em abr/2026**, sem imagens oficiais novas | Ativa, mas atrelada ao ecossistema OpenStack |
| Peso no compose | **1 container** leve, sem dependências | 1 container | Proxy + storage nodes + **Keystone** para autenticação |
| API S3 | Sim | Sim | Via middleware (API nativa é outra) |
| URL pré-assinada | Sim (SigV4) | Sim | Via middleware (`tempurl` na API nativa) |

O MinIO seria a escolha óbvia até 2025, mas o repositório community foi arquivado e parou de publicar imagens oficiais — subir uma imagem congelada num trabalho novo é dívida desde o primeiro dia. O Swift é desproporcional para um bucket de avatares (exige Keystone). O Garage roda em nó único com `--single-node --default-bucket`, que cria a chave de acesso e o bucket a partir das variáveis de ambiente e é idempotente no restart. Como o cliente é o **`boto3`** (API S3 genérica, nada de SDK de fornecedor), trocar para MinIO/S3/R2 é só mudar `STORAGE_ENDPOINT` e as chaves.

### 4. Requisito 3 — URL pré-assinada (e não bucket público)

| | **URL pré-assinada** (escolhida) | Bucket público |
|---|---|---|
| Bucket | Continua **privado** | Qualquer um lista/baixa se souber a chave |
| Controle | Cada URL é emitida pelo backend para quem pode ver o perfil | Nenhum — a URL é permanente |
| Revogação | Natural: a URL **expira** sozinha; trocar/remover a foto invalida a chave | Só apagando o objeto |
| Link vazado | Vale até a expiração (no máximo 1 h) | Vale para sempre |
| Cache | Pior: a query muda a cada GET, o navegador não reaproveita entre recargas | Ótimo (URL estável, CDN) |
| Garage | Suportado (SigV4) | **Não suportado**: o Garage não implementa ACL/bucket policy pública (só *website* por bucket) |

**Fórmula da expiração** ([`backend/app/services/storage.py`](backend/app/services/storage.py) → `calcular_expiracao`):

```
validade = clamp( ceil(tamanho_bytes × 8 / (BANDA_MINIMA_KBPS × 1000)) + MARGEM_USO,  mín 60 s,  máx EXPIRACAO_MAX )
```

- **Tempo de download na pior banda aceita** (`STORAGE_BANDA_MINIMA_KBPS=256`): a URL precisa durar pelo menos o tempo de baixar o arquivo numa conexão ruim.
- **Margem de uso da página** (`STORAGE_MARGEM_USO_SEGUNDOS=600`): a página fica aberta, o usuário rola, volta, o navegador rebusca a imagem.
- **Teto** (`STORAGE_EXPIRACAO_MAX_SEGUNDOS=3600`): limita a janela em que um link vazado continua válido.

Exemplo: um avatar WEBP 512×512 de 60 KB → 61 440 × 8 = 491 520 bits ÷ 256 000 bit/s ≈ 1,9 s → **2 s + 600 s = 602 s (~10 min)**. Um arquivo absurdo de 1 TB bateria no teto de **3600 s**. Se a página ficar aberta além disso, o Angular detecta o erro da `<img>` e recarrega o perfil **uma vez** para obter uma URL nova.

**Por que a ponte `/storage`.** O Garage, como o auth-service e o log-service, **não publica porta** (só `expose: 3900`) — e, no Portainer, uma porta dedicada nem passaria pelo proxy do domínio público. A URL é assinada com o host **interno** `garage:3900` e devolvida ao navegador com o prefixo `/storage` do catálogo; a rota [`backend/app/routes/storage_proxy.py`](backend/app/routes/storage_proxy.py) repassa **caminho e query byte a byte** (usa o `raw_path`, sem decodificar) para `garage:3900`. Como o host e o caminho são idênticos aos assinados, quem valida assinatura e expiração é o **próprio Garage** — a ponte não reimplementa a verificação, só confere que o bucket é o esperado (404) e que há `X-Amz-Signature` (403), e devolve o status do Garage como veio. A rota não exige JWT de propósito (`<img src>` não envia `Authorization`): a assinatura **é** a autorização. **Custo:** o tráfego das imagens passa pelo catálogo (streaming, sem carregar o arquivo inteiro em memória).

### 5. Validação do upload

- **Tamanho em streaming:** o arquivo é lido em blocos de 64 KB; passou de `PERFIL_FOTO_MAX_BYTES` (2 MB) → **413** sem ler o resto. Vazio → **400**.
- **Tipo pelo conteúdo, não pela extensão nem pelo `Content-Type`:** o Pillow abre e verifica os bytes; só `JPEG`, `PNG` e `WEBP` passam. Texto renomeado para `.png`, GIF, PNG truncado → **415** `"Envie uma imagem JPEG, PNG ou WEBP"`.
- **Decompression bomb:** `Image.MAX_IMAGE_PIXELS = 25 000 000` — uma imagem pequena em bytes e gigante em pixels é recusada (415) antes de ser expandida na memória.
- **Re-encode para WEBP 512×512 (qualidade 85):** remove **EXIF** (inclusive GPS), respeita a orientação da câmera (`exif_transpose`), neutraliza arquivos poliglotas (imagem + HTML/ZIP no mesmo arquivo) e padroniza o tamanho (~3–60 KB).
- **Chave gerada pelo servidor:** `avatares/<id>/<uuid4>.webp` — o nome original do arquivo nunca é usado.
- **Ordem das gravações:** storage primeiro (se falhar → **502**, banco intocado); depois o banco (se falhar, o objeto novo é apagado); só então a foto antiga sai do bucket. Assim o banco nunca aponta para um objeto que não existe.
- **Limite de envios:** 10 uploads por minuto por usuário (**429**). O catálogo não tinha rate limiting; o limite é em memória, por processo — suficiente para 1 réplica.

### 6. Requisito 4 — cada um só edita o próprio perfil

- A identidade vem **sempre do JWT** (`sub`). O `{usuario_id}` da rota existe **só para ser comparado** com ele (e para permitir demonstrar a tentativa com ID alheio); os schemas de entrada **não têm** campo `usuario_id` — se o cliente mandar um, é ignorado.
- **Admin não é exceção:** também recebe **403** ao tentar editar perfil alheio. É uma decisão explícita — o requisito é "cada um só edita o próprio perfil", e moderação de perfil não faz parte do escopo. (A remoção da conta inteira continua sendo do admin, em `/api/auth/users/{id}`, e leva junto o perfil e a foto.)
- A checagem acontece **antes** de ler o conteúdo do arquivo, e cada recusa gera o evento de auditoria **`acesso_negado`** com `recurso=perfil:<id alvo>`.
- O campo `pode_editar` do GET só serve para a interface esconder os botões; quem garante a regra é o backend.

**Demonstração** — [`scripts/demo_perfil.sh`](scripts/demo_perfil.sh) (bash + curl + jq; credenciais só por variável de ambiente):

```bash
USER_A_EMAIL=... USER_A_SENHA=... USER_B_EMAIL=... USER_B_SENHA=... ./scripts/demo_perfil.sh
# BASE_URL=https://marcio-mazega-isw055.lapps.studio para rodar contra produção
```

Saída real (stack de CI local, Garage de verdade):

```
== 1. Login dos usuários A e B
  ✔ A = usuário 1 (ana@demo.com) · B = usuário 2 (beto@demo.com)
== 2. A envia a própria foto
  ✔ PUT /api/perfis/1/foto (token de A) → HTTP 200
== 3. GET do perfil de A e download pela URL assinada
  foto_url: /storage/catalogo-avatares/avatares/1/eb1bd227….webp?X-Amz-Algorithm=AWS4-HMAC-SHA256&…&X-Amz-Expires=601&…&X-Amz-Signature=314cbf2c…
  ✔ GET foto_url (sem token: a assinatura é a autorização) [image/webp, 3068 bytes] → HTTP 200
== 4. A tenta editar a bio de B com o próprio token
  ✔ PUT /api/perfis/2 (token de A) — Você só pode editar o próprio perfil → HTTP 403
== 5. A tenta trocar a foto de B
  ✔ PUT /api/perfis/2/foto (token de A) — Você só pode editar o próprio perfil → HTTP 403
== 6. URL assinada com a assinatura adulterada
  ✔ GET com 1 caractere da assinatura trocado (recusado pelo Garage) → HTTP 403
== 7. O banco guarda só a chave
  chave do objeto: avatares/1/eb1bd227942b474bbc260766a42b4be6.webp
```

Para ver a expiração real, suba o catálogo com `STORAGE_MARGEM_USO_SEGUNDOS=0` e `STORAGE_EXPIRACAO_MAX_SEGUNDOS=60`, gere uma `foto_url` e tente abri-la depois de ~65 s → **403** do Garage.

### 7. Evidências

![Página de perfil em produção com a foto enviada, bio e favoritos](assets/SitePerfilFoto.png)

> 📸 **Pendente:** objeto no bucket — `docker exec garage-schinor /garage bucket info catalogo-avatares` (contagem de objetos/tamanho) ou console do Portainer.

`SELECT usuario_id, foto_key, foto_bytes FROM perfis;` no MariaDB de produção (02/10/2026), mostrando que o banco guarda só a chave:

```
usuario_id | foto_key                                           | foto_bytes
1          | avatares/1/c271d378fd4046999ed8687d7d6d201c.webp   | 15782
```

> 📸 **Pendente:** saída do `scripts/demo_perfil.sh` com os dois **403** de edição alheia.

> 📸 **Pendente:** URL adulterada/expirada recusada (403 do Garage).

> 📸 **Pendente:** persistência — a foto continua aparecendo depois de recriar a stack (`docker compose down && docker compose up -d`, sem `-v`).

---

## 🚀 CI/CD com GitHub Actions

```
git push → GitHub Actions (build + teste) → imagens no GHCR (sha-<commit> + latest) → Portainer puxa → no ar
```

Workflow: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)

1. **`test`** (em todo push e PR): roda o `pytest` (suíte completa), sobe a stack completa de [`docker-compose.ci.yml`](docker-compose.ci.yml) com Redis e SQLite descartáveis (o MySQL de produção é da infra, não roda no CI) e `--wait` (só segue se **todos** os serviços ficarem `healthy`), e então falha o pipeline se: `/health` do catálogo não responder 200, o login de um usuário inexistente não devolver 401 (prova que catálogo → auth-service → banco conversam), `/metrics` não expuser métricas ou a ponte `/storage` não recusar (403) uma URL sem assinatura. O `garage` também precisa ficar `healthy`.
2. **`publish`** (só em push para `main`, e só se `test` passou): constrói as seis imagens e publica no **GHCR** com duas tags: `sha-<7 primeiros caracteres do commit>` (rastreável até o commit) e `latest`.

| Imagem | Origem |
|---|---|
| `ghcr.io/schinor/catalogo-filmes` | `Dockerfile` (raiz) |
| `ghcr.io/schinor/auth-service` | `auth-service/Dockerfile` |
| `ghcr.io/schinor/log-service` | `log-service/Dockerfile` |
| `ghcr.io/schinor/prometheus` | `prometheus/Dockerfile` |
| `ghcr.io/schinor/grafana` | `grafana/Dockerfile` |
| `ghcr.io/schinor/garage` | `garage/Dockerfile` |

### Como os segredos são fornecidos (sem revelar valores)

- **Nada de segredo no YAML, no Dockerfile ou na imagem.**
- **No CI:** o workflow gera valores descartáveis em tempo de execução (`openssl rand`) para o JWT, o token do log-service e as chaves do Garage (`GARAGE_RPC_SECRET`, `STORAGE_ACCESS_KEY` = `GK` + 32 hex, `STORAGE_SECRET_KEY`). O login no GHCR usa o `GITHUB_TOKEN` automático.
- **Em produção:** `DATABASE_URL`, `SECRET_KEY`, `TMDB_API_KEY`, `LOG_INTERNAL_TOKEN`, credenciais do Mailtrap, `GRAFANA_ADMIN_PASSWORD` e as chaves do Garage são cadastradas como *Environment variables* da stack no **Portainer**. Localmente ficam no `.env` (fora do Git).

### Deploy

O `docker-compose.yml` referencia `ghcr.io/schinor/<serviço>:${IMAGE_TAG:-latest}`. Para o deploy automático, crie a stack no Portainer a partir do repositório e ligue *Automatic updates* (polling ou webhook). Para fixar uma versão específica, defina `IMAGE_TAG=sha-<commit>` na stack.

Execução verde de referência (commit `ebfba41`, que publicou `sha-ebfba41` + `latest`): https://github.com/Schinor/API-Filmes-Allan/actions/runs/36744055742

![Execuções do workflow CI/CD no GitHub Actions, todas com sucesso](assets/SiteCICD.png)

### Pendências

- O deploy é "puxar e recriar" pelo Portainer; se a atualização automática não estiver habilitada, o passo final é manual (*Pull and redeploy*).

---

## 🗄️ Modelo de Dados (Schema)

```sql
-- ── auth-service ────────────────────────────────────────────────────────────

-- Permissões no formato ação:recurso (ex.: apagar:comentario-de-outro)
CREATE TABLE permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  action VARCHAR(50) NOT NULL,
  resource VARCHAR(50) NOT NULL,
  description VARCHAR(255),
  UNIQUE (action, resource)
);

-- Papéis (amigo-do-wilson, preso-no-terminal, houston-temos-acesso, capitao-hanks, admin)
CREATE TABLE roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(50) UNIQUE NOT NULL,
  description VARCHAR(255)
);

-- Mapeamento papel → permissões (populado pelo seed em auth-service/app/core/rbac_seed.py)
CREATE TABLE role_permissions (
  role_id INT NOT NULL,
  permission_id INT NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- Usuários (role = slug do papel; role_id aponta para roles)
CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'amigo-do-wilson',
  role_id INT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
);

-- Ajustes individuais: concede (concedida = TRUE) ou revoga (FALSE) uma permissão em relação ao papel
CREATE TABLE user_permissions (
  usuario_id INT NOT NULL,
  permission_id INT NOT NULL,
  concedida BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (usuario_id, permission_id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- Tabela de Tokens de Recuperação de Senha
CREATE TABLE reset_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  token VARCHAR(128) UNIQUE NOT NULL,
  usuario_id INT NOT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expira_em TIMESTAMP NOT NULL,
  usado BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ── catálogo ────────────────────────────────────────────────────────────────

-- Tabela de Favoritos (isolada por usuario_id)
CREATE TABLE favoritos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  tmdb_movie_id INT NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  poster_path VARCHAR(255),
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (usuario_id, tmdb_movie_id)
);

-- Tabela de Comentários (isolada por usuario_id)
CREATE TABLE comentarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  tmdb_movie_id INT NOT NULL,
  texto TEXT NOT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Perfil "social" do usuário no catálogo (Atividade 6). Linha criada sob demanda
-- na primeira edição; sem linha = bio vazia e sem foto.
CREATE TABLE perfis (
  usuario_id    INT PRIMARY KEY,
  bio           VARCHAR(280),
  foto_key      VARCHAR(255),          -- só a CHAVE do objeto no bucket, nunca a URL
  foto_bytes    INT,                   -- tamanho, usado no cálculo da expiração da URL
  atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

> `perfis` segue o mesmo critério de `favoritos` e `comentarios`: é criada pelo `create_all` do catálogo e **não declara FK** para `usuarios`, que pertence ao auth-service (no CI cada serviço tem o próprio SQLite). A limpeza quando um usuário é removido acontece em `DELETE /api/auth/users/{id}`, que apaga favoritos, comentários, o perfil **e a foto no bucket**. No SQLAlchemy, o `ON UPDATE` vira `onupdate=func.now()` (portável para SQLite).

---

## 🛡️ Controle de Acesso Baseado em Papel (RBAC)

### 1. O que cada papel pode fazer

| Papel | Permissões / ações permitidas |
|---|---|
| **`amigo-do-wilson`** *(padrão)* | Ver e pesquisar o catálogo; ver detalhes dos filmes; listar comentários. |
| **`preso-no-terminal`** | Tudo de `amigo-do-wilson`; listar, adicionar e remover os próprios favoritos. |
| **`houston-temos-acesso`** | Tudo de `preso-no-terminal`; criar comentários e apagar os próprios comentários. |
| **`capitao-hanks`** | Tudo de `houston-temos-acesso`; acessar o catálogo premium. |
| **`admin`** | Todas as permissões anteriores; **apagar comentários de qualquer usuário**; listar e gerenciar usuários; alterar papéis; gerenciar a matriz de permissões e administrar o sistema. |

Permissões de cada papel, no formato `ação:recurso` (fonte única: [`auth-service/app/core/rbac_seed.py`](auth-service/app/core/rbac_seed.py)):

| Permissão | `amigo-do-wilson` | `preso-no-terminal` | `houston-temos-acesso` | `capitao-hanks` | `admin` |
|---|:-:|:-:|:-:|:-:|:-:|
| `assistir:catalogo` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `detalhes:filmes` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `listar:comentarios` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `listar:favoritos` | | ✔ | ✔ | ✔ | ✔ |
| `adicionar:favoritos` | | ✔ | ✔ | ✔ | ✔ |
| `remover:favoritos` | | ✔ | ✔ | ✔ | ✔ |
| `criar:comentarios` | | | ✔ | ✔ | ✔ |
| `apagar:comentario-proprio` | | | ✔ | ✔ | ✔ |
| `assistir:catalogo-premium` | | | | ✔ | ✔ |
| `apagar:comentario-de-outro` | | | | | ✔ |
| `visualizar:usuarios` | | | | | ✔ |
| `gerenciar:usuarios` | | | | | ✔ |
| `gerenciar:papeis` | | | | | ✔ |
| `gerenciar:permissoes` | | | | | ✔ |
| `visualizar:logs` | | | | | ✔ |
| `administrar:sistema` | | | | | ✔ |

No catálogo, as rotas não testam o nome do papel: `require_permission("<ação:recurso>")` ([`backend/app/dependencies.py`](backend/app/dependencies.py)) confere a permissão dentro do JWT. O `admin` passa porque recebe as permissões pelo seed (e `administrar:sistema` libera qualquer uma).

Os quatro primeiros são papéis de usuário comum disponíveis no cadastro público. O papel
`admin` não aparece no formulário e uma tentativa de enviá-lo diretamente para
`POST /api/auth/cadastro` é recusada com **HTTP 403**. Administradores devem ser
provisionados internamente ou promovidos por um administrador autorizado. A relação
completa também está registrada em [`docs/PERFIS.md`](docs/PERFIS.md).

A checagem de permissão acontece **sempre no backend**, nunca apenas na interface visual.
Qualquer requisição direta via Postman, curl ou scripts para
`DELETE /api/comentarios/{id}` de outro usuário feita por um usuário comum é recusada
com **HTTP 403 Forbidden** (`"Apenas o autor ou um administrador podem remover este comentário"`).

### 2. Padrão de Arquitetura Utilizado: Padrão A vs Padrão B

**Hoje o projeto utiliza principalmente o Padrão B (claims no JWT):** o `auth-service`
inclui `role` e `permissions` no token assinado durante o login. O catálogo valida a
assinatura e lê esses claims localmente para autorizar as rotas protegidas, sem uma
chamada de rede adicional em cada ação. Existe apenas um fallback para `GET /me` no
`auth-service` quando não é possível resolver o usuário localmente.

**O que mudaria para o Padrão A (enforcement centralizado):** o catálogo deixaria de
usar `role` e `permissions` do JWT para decidir a autorização e consultaria o
`auth-service` em cada requisição protegida. Alterações de papel teriam efeito imediato,
mas cada ação ganharia uma chamada de rede e passaria a depender da disponibilidade e
da capacidade do `auth-service`. No padrão atual, um token já emitido pode conservar as
permissões antigas até expirar (atualmente, em até 24 horas).

### 3. Demonstração prática da ação exclusiva de administrador

O teste usa comentários publicados por contas diferentes e compara os controles
disponíveis para um usuário comum e para um administrador:

1. Faça login com um papel comum que possua comentários, como `houston-temos-acesso`.
2. Envie `DELETE /api/comentarios/{id}` com o token desse usuário e registre o retorno
   **403 Forbidden**.
3. Faça login como `admin`, repita a mesma requisição e registre o retorno **200 OK**.
4. Confirme também na interface que o usuário comum não recebe o controle de exclusão
   sobre comentários alheios, enquanto o administrador recebe os controles de moderação.

#### Usuário comum

A conta comum pode visualizar os comentários da comunidade, mas não recebe o botão para
excluir comentários publicados por outras contas. Se tentar chamar o endpoint diretamente,
o backend responde com **403 Forbidden**.

![Usuário comum sem permissão para moderar comentários alheios](assets/Teste-Acesso.png)

#### Administrador

A conta administrativa recebe o indicador de moderação ativa e pode excluir comentários
de qualquer usuário. A mesma operação aceita pelo backend retorna **200 OK**.

![Administrador com controles de moderação](assets/Teste-Acesso-Admin.png)

---

## 🧪 Testes Automatizados

Executar a suíte de testes com `pytest`:

```bash
.venv/bin/pytest tests/ -v
```

Cobertura dos testes:
- Endpoint `GET /health` do `auth-service`.
- Cadastro, login e consulta de perfil `/me` com retorno de `role`.
- Consulta e isolamento dos cinco papéis RBAC.
- Bloqueio do autocadastro com papel `admin`.
- Fluxo de ponta a ponta de esqueci-senha e redefinição com validação de expiração e reuso.
- **RBAC no Catálogo (`DELETE /api/comentarios/{id}`):**
  - Usuário comum removendo o próprio comentário ➔ **200 OK**.
  - Usuário comum tentando remover comentário de outro usuário ➔ **403 Forbidden**.
  - Usuário admin removendo comentário de qualquer usuário (moderação) ➔ **200 OK**.
  - Tentativa de remoção de comentário inexistente ➔ **404 Not Found**.
- Roteamento e proteção das rotas do Catálogo.
- **Auditoria:** `log-service` (401 sem token, 202 com token, ordem do mais recente ao mais antigo, `/health` refletindo o Redis, via `fakeredis`), `/api/logs` (403 para comum, 200 para admin, 503 com log-service fora), emissão dos eventos (`login`, `login_falhou`, `logout`, `favoritar`, `comentar`, `apagar_comentario`, `acesso_negado`) e garantia de que a falha do log-service não quebra a funcionalidade.
- **Observabilidade:** `/health` (200 e 503) e `/metrics` do catálogo, do auth-service e do log-service.
- **Perfil e object storage** ([`tests/test_perfis.py`](tests/test_perfis.py), S3 simulado com `moto`):
  - `calcular_expiracao` (tempo + margem, teto, piso de 60 s) e `url_assinada` (prefixo `/storage/catalogo-avatares/avatares/`, `X-Amz-Signature`, `X-Amz-Expires`).
  - `GET /api/perfis/{id}`: 401 sem token, 404 para usuário inexistente, perfil sem linha com favoritos, `pode_editar` só para o dono.
  - `PUT` da bio: dono 200; **outro usuário 403**; **admin em perfil alheio 403**; bio > 280 → 422; `usuario_id` no corpo ignorado.
  - Upload: PNG válido → objeto WEBP 512×512 no bucket e **só a chave no banco**; EXIF removido; perfil alheio 403 sem gravar nada; > limite 413; vazio 400; texto renomeado para `.png`, GIF e PNG truncado 415; decompression bomb 415; segundo upload apaga o objeto antigo; storage fora → 502 com banco intocado; limite de 10 uploads/min → 429.
  - `DELETE` da foto: remove do banco e do bucket, repetido → 204. Remoção do usuário pelo admin apaga perfil e foto.
  - Auditoria: `perfil_atualizado`, `perfil_foto_atualizada`, `perfil_foto_removida`, `acesso_negado` com `recurso=perfil:<id>`; log-service fora não quebra o upload.
  - Ponte `/storage`: sem assinatura 403, bucket errado 404, upstream fora 502, 403 do Garage repassado e **caminho + query enviados ao upstream byte a byte iguais** aos assinados.

---

*Trabalho desenvolvido para a disciplina de Cloud — Professor [@siriani](https://github.com/siriani).*
