# 🎬 Catálogo de Filmes — Tom Hanks (Arquitetura de Microsserviços)

Aplicação web fullstack para navegar no catálogo de filmes estrelados por Tom Hanks, com sistema de favoritos, comentários e microsserviço dedicado de **autenticação e gerenciamento de identidade**.

> **Disciplina de Cloud Computing**
> **Professor:** [@siriani](https://github.com/siriani)

---

## 🏛️ Evolução Arquitetural: Do Monólito aos Microsserviços

Na Atividade 2, a aplicação rodava em um único container monolítico contendo a interface Angular, a API do Catálogo e a lógica de autenticação e acesso ao banco de dados no mesmo deploy.

Na **Atividade 3**, a responsabilidade de autenticação e identidade de usuários foi extraída para um **microsserviço independente (`auth-service`)**.

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

### Por que desacoplar a autenticação?
1. **Isolamento de Responsabilidade:** O catálogo foca em regras de negócio de filmes, favoritos e comentários, enquanto o `auth-service` gerencia credenciais, sessões, tokens e segurança.
2. **Segurança Aumentada (Defesa em Profundidade):** O `auth-service` não expõe portas para o host (`ports:` omitido no Compose) e é acessível **apenas** internamente pela rede Docker `filmes-network`.
3. **Escalabilidade e Manutenibilidade:** O serviço de autenticação pode evoluir ou ser reutilizado por outros serviços sem impacto no catálogo.

---

## 🚀 Funcionalidades

- **Catálogo de Filmes em Tempo Real:** Conexão direta com a API TMDB para exibição de filmes, pôsteres e sinopses.
- **Autenticação via Microsserviço:** Cadastro e login com JWT assinado e validação de sessão.
- **Papéis de Usuário (Roles):** Suporte nativo a papéis `usuario` e `admin`, com identificação na interface e endpoints de consulta (`GET /users/{id}/role`).
- **Fluxo Completo de "Esqueci Minha Senha":**
  - Solicitação de link informando e-mail.
  - Geração de token único gravado na tabela `reset_tokens`.
  - Disparo de e-mail formatado via SMTP (Mailtrap) com link direcionado para a rota do Catálogo.
  - Validação estrita: link expira em **30 minutos** e é de **uso único** (`usado = true`).
  - Troca da senha com hash bcrypt seguro.
- **Favoritos e Comentários Isolados:** Cada usuário gerencia seus próprios dados de forma independente.

---

## 🐳 Docker Compose — Configuração dos Serviços

Trecho do `docker-compose.yml` ilustrando os dois serviços na rede compartilhada `filmes-network`:

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
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=1440
      - PORT=8001
      - MAILTRAP_HOST=${MAILTRAP_HOST:-sandbox.smtp.mailtrap.io}
      - MAILTRAP_PORT=${MAILTRAP_PORT:-2525}
      - MAILTRAP_USERNAME=${MAILTRAP_USERNAME:-}
      - MAILTRAP_PASSWORD=${MAILTRAP_PASSWORD:-}
      - MAILTRAP_FROM_EMAIL=${MAILTRAP_FROM_EMAIL:-nao-responda@tomhanksfilmes.com}
      - CATALOGO_URL=${CATALOGO_URL:-http://localhost:8000}
      - RESET_TOKEN_EXPIRE_MINUTES=30
    networks:
      - filmes-network

networks:
  filmes-network:
    driver: bridge
```

---

## ⚙️ Variáveis de Ambiente

Crie ou configure o arquivo `.env` a partir do modelo [.env.example](.env.example):

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

### 1. Subir toda a stack com Docker Compose

```bash
docker compose up --build
```

O catálogo estará disponível no seu navegador em:
- **Aplicação:** `http://localhost:8000`
- **Docs da API (Catálogo):** `http://localhost:8000/api/docs`

> Note que tentar acessar o `auth-service` diretamente a partir do host (`curl http://localhost:8001`) irá falhar intencionalmente, pois o container não expõe portas públicas.

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

O projeto inclui uma suíte completa de testes automatizados com `pytest`:

```bash
pytest tests/ -v
```

Casos cobertos:
- Verificação do endpoint `GET /health` do `auth-service`.
- Cadastro, login e consulta de dados do usuário autenticado.
- Validação e retorno de papéis (`usuario`, `admin`).
- Fluxo de ponta a ponta de "Esqueci Minha Senha" e redefinição com troca de credenciais.
- **Teste Negativo (Expiração):** Rejeição automática de tokens após 30 minutos.
- **Teste Negativo (Reuso):** Rejeição automática de tentativa de reuso de token já utilizado.
- **Teste Negativo (Token Inválido):** Rejeição de tokens inexistentes ou corrompidos.
- Rotas protegidas do backend Catálogo integradas.

---

*Projeto desenvolvido para a disciplina de Cloud — Professor [@siriani](https://github.com/siriani).*
