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
   - `MAILTRAP_USERNAME`: Usuário do Mailtrap Sandbox
   - `MAILTRAP_PASSWORD`: Senha do Mailtrap Sandbox
5. Clique em **Deploy the stack**. O Portainer fará o build do `catalogo` e do `auth-service` e subirá a stack conectada na rede privada.

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

Use o mesmo comentário, pertencente a outro usuário, nos dois testes abaixo:

1. Faça login com um papel comum que possua comentários, como `houston-temos-acesso`.
2. Envie `DELETE /api/comentarios/{id}` com o token desse usuário e registre o retorno
   **403 Forbidden**.
3. Faça login como `admin`, repita a mesma requisição e registre o retorno **200 OK**.
4. Salve as capturas nos caminhos abaixo; os links já estão preparados para inclusão.

<!-- Depois de capturar o caso 403, remova os espaços ao redor de ! para exibir a imagem:
! [Usuário comum recebe 403](assets/rbac-usuario-403.png)
-->

<!-- Depois de capturar o caso 200, remova os espaços ao redor de ! para exibir a imagem:
! [Administrador executa a moderação](assets/rbac-admin-200.png)
-->

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

---

*Trabalho desenvolvido para a disciplina de Cloud — Professor [@siriani](https://github.com/siriani).*
