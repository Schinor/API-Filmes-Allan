# 🎬 Catálogo de Filmes — Tom Hanks

Aplicação web fullstack para navegar filmes com Tom Hanks, com sistema de favoritos e comentários **isolados por usuário**.

> Disciplina de Cloud — Professor: @siriani

---

## 🚀 Funcionalidades

- **Cadastro e login** com JWT (sessão segura por usuário)
- **Catálogo de filmes** via API TMDB — pôster, título e sinopse sempre ao vivo
- **Favoritar filmes** — persiste no banco de dados isolado por conta
- **Comentar filmes** — cada usuário só vê seus próprios comentários
- **Isolamento total** — nenhum dado de um usuário é visível para outro

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│  Container Docker (porta reservada do aluno)             │
│                                                          │
│  ┌──────────────┐    ┌───────────────────────────────┐  │
│  │  Angular SPA  │───▶│  FastAPI (Backend)            │  │
│  │  (estático)   │    │  /api/auth   /api/filmes      │  │
│  └──────────────┘    │  /api/favoritos  /api/comentarios │
│                       └────────┬──────────────────────┘  │
│                                │                          │
│                    ┌───────────┴──────────┐               │
│                    │   TMDB API (externa) │               │
│                    └──────────────────────┘               │
│                                │                          │
│                    ┌───────────┴──────────┐               │
│                    │  MariaDB (banco aluno)│               │
│                    │  usuarios/favoritos/ │               │
│                    │  comentarios         │               │
│                    └──────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## 🔒 Segurança — Credenciais

**Nenhuma chave ou senha está no código.** Todas as credenciais são passadas via variáveis de ambiente no Portainer.

Copie `.env.example` → `.env` e preencha os valores reais (`.env` está no `.gitignore`).

## ⚙️ Variáveis de Ambiente

```env
DATABASE_URL=mysql+pymysql://usuario:senha@host:3306/nome_do_banco
TMDB_API_KEY=seu_bearer_token_da_tmdb
TMDB_BASE_URL=https://api.themoviedb.org/3
SECRET_KEY=chave_secreta_jwt_longa
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PORT=8000  # porta reservada do aluno
```

## 🐳 Deploy com Docker

### Build e execução local

```bash
docker build -t catalogo-tomhanks .
docker run -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://..." \
  -e TMDB_API_KEY="..." \
  -e TMDB_BASE_URL="https://api.themoviedb.org/3" \
  -e SECRET_KEY="..." \
  catalogo-tomhanks
```

### Deploy no Portainer

1. Clone o repositório no servidor
2. No Portainer → "Add Stack" → referencie o `Dockerfile`
3. Configure as variáveis de ambiente no campo **Env**
4. Certifique-se de usar a **porta reservada do seu usuário**

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Angular 21 (standalone components, signals) |
| Backend | FastAPI + Python 3.12 |
| Banco | MariaDB / MySQL (SQLAlchemy + Alembic) |
| Auth | JWT (python-jose + bcrypt) |
| API externa | TMDB (The Movie Database) |
| Container | Docker multi-stage |

## 📁 Estrutura do Projeto

```
.
├── Dockerfile              # Build multi-stage (Angular + FastAPI)
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example        # Template de variáveis (sem valores reais)
│   ├── alembic.ini
│   ├── migrations/
│   └── app/
│       ├── main.py         # Entry point FastAPI
│       ├── core/           # config, database, security
│       ├── models/         # SQLAlchemy models
│       ├── repositories/   # Queries isoladas por usuario_id
│       ├── routes/         # auth, filmes, favoritos, comentarios
│       ├── schemas/        # Pydantic schemas
│       └── services/       # tmdb_service.py
└── frontend/
    └── src/
        └── app/
            ├── pages/      # login, catalogo, favoritos, comentarios
            ├── components/ # navbar, movie-card, movie-modal
            ├── services/   # auth, filmes, favoritos, comentarios
            ├── guards/     # authGuard, guestGuard
            └── interceptors/ # JWT header automático
```

## 🗄️ Schema do Banco

```sql
CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE favoritos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  tmdb_movie_id INT NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  poster_path VARCHAR(255),
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
  UNIQUE (usuario_id, tmdb_movie_id)
);

CREATE TABLE comentarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  tmdb_movie_id INT NOT NULL,
  texto TEXT NOT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

---

*Projeto desenvolvido como exercício acadêmico — disciplina fechando o ciclo de infraestrutura e isolamento de dados entre usuários.*
