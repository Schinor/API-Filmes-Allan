# 🎬 Catálogo de Filmes — Tom Hanks (Arquitetura de Microsserviços)

Aplicação web fullstack para navegação no catálogo de filmes do ator Tom Hanks, com sistema de favoritos, comentários e microsserviço dedicado de **autenticação, controle de acesso e recuperação de senha**.

> **Disciplina:** Cloud Computing / Arquitetura de Software  
> **Professor:** [@siriani](https://github.com/siriani)

🔗 **Aplicação em produção (Portainer):** **https://marcio-mazega-isw055.lapps.studio**

---

## 🏛️ Evolução Arquitetural: Monólito ➔ Microsserviços

Na **Atividade 2**, o catálogo rodava em um único container monolítico (FastAPI + Angular) com regras de negócio, dados e autenticação acoplados no mesmo deploy.

Na **Atividade 3**, toda a responsabilidade de autenticação e identidade foi desacoplada para um **segundo container independente (`auth-service`)**, mantendo o catálogo como o **único ponto de entrada público**.

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
│  │   - Redefinição Senha │         │   - /api/auth/* (Proxy/Bridge)│   │
│  └───────────────────────┘         └──────────────┬────────────────┘   │
└───────────────────────────────────────────────────┼────────────────────┘
                                                    │
                      REDE INTERNA DOCKER           │  HTTP interno:
                     (filmes-network bridge)        │  http://auth-service:8001
                                                    │
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
    depends_on:
      - auth-service
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

networks:
  filmes-network:
    driver: bridge
```

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
   - `CATALOGO_URL`: URL pública do catálogo (usada no link do e-mail)
   - `LOG_INTERNAL_TOKEN`: token compartilhado entre o catálogo e o log-service
   - `GRAFANA_ADMIN_PASSWORD`: senha do admin do Grafana
   - `PROMETHEUS_PROXY_PASSWORD`: senha do HTTP Basic que protege `/prometheus` (o Prometheus não tem login próprio)
   - `IMAGE_TAG` *(opcional)*: tag das imagens do GHCR (`latest` por padrão; use `sha-<commit>` para fixar uma versão)
   - `GRAFANA_PORT` / `PROMETHEUS_PORT` *(opcional)*: portas do host, se as padrões (3000 e 9090) estiverem ocupadas
5. Clique em **Deploy the stack**. O Portainer baixa as imagens `ghcr.io/schinor/*` (catálogo, auth-service, log-service, prometheus e grafana), sobe o Redis e conecta tudo na rede privada.

**Stack em produção:** https://marcio-mazega-isw055.lapps.studio (domínio gerado pelo Portainer para a porta pública do `catalogo`, ou seja, a porta `${PORT}` mapeada no compose).
- Documentação da API: https://marcio-mazega-isw055.lapps.studio/api/docs
- Redoc: https://marcio-mazega-isw055.lapps.studio/api/redoc
- Grafana: https://marcio-mazega-isw055.lapps.studio/grafana (login `admin` / `GRAFANA_ADMIN_PASSWORD`)
- Prometheus: https://marcio-mazega-isw055.lapps.studio/prometheus (HTTP Basic `admin` / `PROMETHEUS_PROXY_PASSWORD`)

> Apenas o `catalogo` fica exposto diretamente nesse domínio (é o único serviço com `ports:` publicado — ver [Docker Compose](#-docker-compose--configuração-dos-serviços)). `auth-service`, `log-service` e `redis` só existem na rede interna `filmes-network`. Prometheus (`9090`) e Grafana (`3000`) têm porta própria no compose, mas o domínio público passa por um proxy (Cloudflare, no caso do Portainer/lapps.studio) que só encaminha um conjunto fixo de portas HTTP — as portas dedicadas nunca chegam lá. Por isso o `catalogo` também expõe **`/grafana`** e **`/prometheus`**, que encaminham internamente para `grafana:3000` e `prometheus:9090` (mesmo padrão *bridge* já usado em `/api/auth/*` — ver [`backend/app/routes/observability_proxy.py`](backend/app/routes/observability_proxy.py)). O Grafana continua com seu próprio login; o Prometheus não tem autenticação nativa, então o proxy exige HTTP Basic (`PROMETHEUS_PROXY_PASSWORD`) — sem essa variável definida, o proxy responde `503` de propósito.

> As imagens do GHCR nascem **privadas**. Torne os pacotes públicos ou cadastre no Portainer um registry `ghcr.io` com um Personal Access Token de escopo `read:packages` (o token fica no Portainer, nunca no repositório).
> O Prometheus e o Grafana usam imagens próprias (`prometheus/Dockerfile`, `grafana/Dockerfile`) com a configuração (`prometheus.yml`, `grafana/provisioning`, `grafana/dashboards`) já embutida na imagem — não há bind mount de caminho do repositório, então a stack sobe normalmente mesmo com um usuário não administrador no Portainer.

---

## 📄 Documentação da API (Swagger / OpenAPI)

Dois serviços documentados de ponta a ponta: **catálogo** e **auth-service**.

| Serviço | Swagger UI | Redoc |
|---|---|---|
| catalogo | `http://localhost:8000/api/docs` | `http://localhost:8000/api/redoc` |
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

> 📸 **Print do Swagger UI:** abra https://marcio-mazega-isw055.lapps.studio/api/docs, expanda um endpoint (ex: `POST /api/auth/login`), rode "Try it out" com um caso real e anexe aqui (pasta `assets/`).
> ⚠️ O print já enviado (`assets/SiteSwaggerUI.png`) expõe a senha real em texto puro e um `access_token` JWT válido no corpo da resposta — **não usar assim**. Troque a senha dessa conta e refaça o print com um usuário de teste antes de anexar, ou corte/borre o `curl -d "..."` e o campo `access_token` do JSON de resposta.

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
| `acesso_negado` | `require_permission` e ramo 403 do `DELETE` de comentário | `recurso=<permissão>`, `detalhes=<método> <rota>` |

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
| catalogo | MariaDB (`SELECT 1`) | `503 {"status":"unhealthy","db":"down"}` |
| auth-service | MariaDB (`SELECT 1`) | `503 {"status":"unhealthy","db":"down",...}` |
| log-service | Redis (`PING`) | `503 {"status":"unhealthy","redis":"down"}` |

Cada serviço tem `healthcheck` no compose (Python `urllib`, já que as imagens `slim` não têm `curl`), e o `depends_on` usa `condition: service_healthy`. Com o Redis parado, o log-service passa a `(unhealthy)` sozinho (~30 s no compose de produção).

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
docker stop <container-redis>       # após ~30-40 s: log-service (unhealthy)
docker start <container-redis>      # volta a (healthy)
```

> 📸 **Prints:** para `docker ps`, use a lista de **Containers** do Portainer (mostra o `Status`/`Health` de cada serviço da stack sem precisar de acesso SSH ao host) — capture com tudo `(healthy)` e, opcionalmente, pare o container do Redis pelo próprio Portainer e capture o `log-service` ficando `(unhealthy)`. Para `/metrics`, acesse https://marcio-mazega-isw055.lapps.studio/metrics; para o painel do Grafana, acesse https://marcio-mazega-isw055.lapps.studio/grafana (ver seção "Deploy no Portainer" acima).

![Containers da stack no Portainer, com o redis pausado](assets/SiteContainerPausado.png)
![log-service (unhealthy) após o redis parar de responder](assets/SiteLogsParado.png)

### `/metrics` (Prometheus)

Os três serviços expõem `/metrics` via `prometheus-fastapi-instrumentator` (`http_requests_total` por rota/status e `http_request_duration_seconds`). `/health` e `/metrics` ficam fora da contagem.

> ⚠️ O catálogo tem a porta pública, então `/metrics` fica acessível por ela. Em produção real, bloqueie a rota no proxy de borda e deixe só o Prometheus raspar pela rede interna.

### Prometheus + Grafana (bônus)

- Prometheus: `http://localhost:9090` localmente, ou https://marcio-mazega-isw055.lapps.studio/prometheus em produção (HTTP Basic `admin` / `PROMETHEUS_PROXY_PASSWORD` — ver [proxy](#-docker-compose--configuração-dos-serviços)). `prometheus.yml` raspa `catalogo:8000`, `auth-service:8001`, `log-service:8002`; em `/targets` os três devem estar `UP`.
- Grafana: `http://localhost:3000` localmente, ou https://marcio-mazega-isw055.lapps.studio/grafana em produção (usuário `admin`, senha em `GRAFANA_ADMIN_PASSWORD`). A fonte de dados e o painel **HANKS+ — Serviços** (requisições/min, erros 4xx/5xx e latência p95) já vêm provisionados em `grafana/`.

---

## 🚀 CI/CD com GitHub Actions

```
git push → GitHub Actions (build + teste) → imagens no GHCR (sha-<commit> + latest) → Portainer puxa → no ar
```

Workflow: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)

1. **`test`** (em todo push e PR): roda o `pytest` (suíte completa), sobe a stack completa de [`docker-compose.ci.yml`](docker-compose.ci.yml) com Redis e SQLite descartáveis (o MySQL de produção é da infra, não roda no CI) e `--wait` (só segue se **todos** os serviços ficarem `healthy`), e então falha o pipeline se: `/health` do catálogo não responder 200, o login de um usuário inexistente não devolver 401 (prova que catálogo → auth-service → banco conversam) ou `/metrics` não expuser métricas.
2. **`publish`** (só em push para `main`, e só se `test` passou): constrói as cinco imagens e publica no **GHCR** com duas tags: `sha-<7 primeiros caracteres do commit>` (rastreável até o commit) e `latest`.

| Imagem | Origem |
|---|---|
| `ghcr.io/schinor/catalogo-filmes` | `Dockerfile` (raiz) |
| `ghcr.io/schinor/auth-service` | `auth-service/Dockerfile` |
| `ghcr.io/schinor/log-service` | `log-service/Dockerfile` |
| `ghcr.io/schinor/prometheus` | `prometheus/Dockerfile` |
| `ghcr.io/schinor/grafana` | `grafana/Dockerfile` |

### Como os segredos são fornecidos (sem revelar valores)

- **Nada de segredo no YAML, no Dockerfile ou na imagem.**
- **No CI:** o workflow gera valores descartáveis em tempo de execução (`openssl rand`) para o JWT e o token do log-service. O login no GHCR usa o `GITHUB_TOKEN` automático.
- **Em produção:** `DATABASE_URL`, `SECRET_KEY`, `TMDB_API_KEY`, `LOG_INTERNAL_TOKEN`, credenciais do Mailtrap e `GRAFANA_ADMIN_PASSWORD` são cadastradas como *Environment variables* da stack no **Portainer**. Localmente ficam no `.env` (fora do Git).

### Deploy

O `docker-compose.yml` referencia `ghcr.io/schinor/<serviço>:${IMAGE_TAG:-latest}`. Para o deploy automático, crie a stack no Portainer a partir do repositório e ligue *Automatic updates* (polling ou webhook). Para fixar uma versão específica, defina `IMAGE_TAG=sha-<commit>` na stack.

![Execuções do workflow CI/CD no GitHub Actions, todas com sucesso](assets/SiteCICD.png)

### Pendências

- O deploy é "puxar e recriar" pelo Portainer; se a atualização automática não estiver habilitada, o passo final é manual (*Pull and redeploy*).

---

## 🗄️ Modelo de Dados (Schema)

```sql
-- Tabela de Usuários (com coluna role)
CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'usuario',
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
```

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

---

*Trabalho desenvolvido para a disciplina de Cloud — Professor [@siriani](https://github.com/siriani).*
