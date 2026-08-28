# 🎬 Catálogo de Filmes — Tom Hanks (Arquitetura de Microsserviços)

Aplicação web fullstack para navegação no catálogo de filmes do ator Tom Hanks, com sistema de favoritos, comentários e microsserviço dedicado de **autenticação, controle de acesso e recuperação de senha**.

> **Disciplina:** Cloud Computing / Arquitetura de Software  
> **Professor:** [@siriani](https://github.com/siriani)

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
│  │   - Gestão de Roles (usuario, admin)                             │  │
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

## 📸 Demonstração e Telas de Recuperação de Senha

### 1. Solicitação de Recuperação de Senha
O usuário informa o e-mail cadastrado na tela de login clicando em *"Esqueceu a senha?"*:

![Solicitação de Recuperação](docs/screenshots/01-solicitacao-recuperacao.png)

---

### 2. E-mail Real Recebido no Mailtrap Sandbox
O microsserviço dispara um e-mail HTML/texto via SMTP contendo o link seguro de uso único:

![E-mail Recebido no Mailtrap](docs/screenshots/02-email-mailtrap.png)

---

### 3. Redefinição de Senha
Ao clicar no link do e-mail, a rota pública do catálogo (`/reset-password?token=...`) valida o token e permite a criação da nova senha:

![Redefinição de Senha](docs/screenshots/03-redefinicao-senha.png)

---

### 4. Validação de Segurança (Link Expirado ou Já Utilizado)
Caso o link tenha mais de 30 minutos ou já tenha sido usado, o sistema recusa a troca e exige uma nova solicitação:

![Tentativa Recusada](docs/screenshots/04-link-expirado-recusado.png)

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
CATALOGO_URL=http://localhost:8000

# Mailtrap (SMTP Sandbox)
MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=2525
MAILTRAP_USERNAME=seu_usuario_mailtrap
MAILTRAP_PASSWORD=sua_senha_mailtrap
MAILTRAP_FROM_EMAIL=nao-responda@tomhanksfilmes.com
MAILTRAP_FROM_NAME="Catálogo Filmes Tom Hanks"
RESET_TOKEN_EXPIRE_MINUTES=30
```

---

## 🏃 Como Executar

### 1. Subir toda a aplicação

```bash
docker compose up --build
```

- **Aplicação Web:** `http://localhost:8000`
- **Documentação da API (Catálogo):** `http://localhost:8000/api/docs`

> O `auth-service` não aceita conexões diretas do host (`curl http://localhost:8001` falhará propositalmente), garantindo o isolamento da rede interna.

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

## 🧪 Testes Automatizados

Executar a suíte de testes com `pytest`:

```bash
.venv/bin/pytest tests/ -v
```

Cobertura dos testes:
- Endpoint `GET /health` do `auth-service`.
- Cadastro, login e consulta de perfil `/me`.
- Consulta de papéis (`usuario`, `admin`).
- Fluxo de ponta a ponta de esqueci-senha e redefinição.
- **Teste Negativo (Expiração):** Recusa de tokens após 30 minutos.
- **Teste Negativo (Reuso):** Recusa de tokens já marcados como `usado = true`.
- **Teste Negativo (Token Inválido):** Recusa de tokens inexistentes.
- Roteamento e proteção das rotas do Catálogo.

---

*Trabalho desenvolvido para a disciplina de Cloud — Professor [@siriani](https://github.com/siriani).*
