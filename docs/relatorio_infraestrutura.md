# Relatório de Checkup de Infraestrutura

**Projeto:** Catálogo de Filmes — Tom Hanks (API-Filmes-Allan)  
**Data:** 13/09/2026  
**Stack:** Angular 19+ | FastAPI (Python 3.14) | SQLAlchemy 2.0 | MySQL 8.0 / SQLite | Docker & Docker Compose  

---

## 1. Arquitetura Geral & Organização de Pastas

### 1.1 Visão Geral dos Serviços
O sistema adota uma arquitetura orientada a serviços dividida em 3 componentes principais:
1. **Frontend (`frontend/`):** Single Page Application em Angular (standalone components, signals, SSR/SSG build) servida diretamente via container ou estaticamente via backend FastAPI fallback.
2. **Backend / Catálogo (`backend/`):** Serviço FastAPI (porta 8000) atuando como API Gateway / BFF para o frontend. Responsável por consumir a API externa TMDB para dados de filmes, gerenciar dados de favoritos e comentários, e encaminhar requisições de autenticação para o `auth-service`.
3. **Serviço de Autenticação (`auth-service/`):** Microsserviço FastAPI (porta 8001, interno) responsável por registro, login (OAuth2 Password Flow com JWT), emissão de tokens de redefinição de senha e integração SMTP via Mailtrap.

### 1.2 Camadas e Estrutura
Ambos os serviços backend (`backend` e `auth-service`) seguem o padrão arquitetural em camadas:
- `core/`: Configurações via Pydantic Settings, gerenciamento de engine/sessão do SQLAlchemy, segurança (JWT/hashing) e envio de e-mails.
- `models/`: Modelos declarativos do SQLAlchemy (ORM).
- `schemas/`: Schemas Pydantic para validação e serialização de DTOs.
- `repositories/`: Camada de acesso a dados e queries com SQLAlchemy.
- `routes/`: Roteadores HTTP do FastAPI.
- `services/` ou `clients/`: Clientes HTTP externos (TMDB e comunicação interserviço com `auth-service`).

---

## 2. Banco de Dados: Schema, Índices e Integridade Referencial

### 2.1 Schema Atual
- **`usuarios`:** `id (PK)`, `nome`, `email (UK, index)`, `senha_hash`, `role`, `criado_em`.
- **`reset_tokens`:** `id (PK)`, `token (UK, index)`, `usuario_id (FK -> usuarios.id on delete CASCADE)`, `criado_em`, `expira_em`, `usado`.
- **`favoritos`:** `id (PK)`, `usuario_id (index)`, `tmdb_movie_id`, `titulo`, `poster_path`, `criado_em`, `UniqueConstraint(usuario_id, tmdb_movie_id)`.
- **`comentarios`:** `id (PK)`, `usuario_id (index)`, `tmdb_movie_id`, `texto`, `criado_em`.

### 2.2 Diagnóstico & Pontos de Atenção
1. **Integridade Referencial Interserviço:** As tabelas `favoritos` e `comentarios` residem na mesma base de dados MySQL em produção, mas o modelo declarativo do backend não declara explicitamente a Foreign Key para `usuarios.id` porque os modelos de usuários estão isolados no `auth-service`. Isso previne integridade forçada pelo banco no caso de exclusão de usuário.
2. **Índices:** Existem índices adequados em campos frequentemente consultados (`email`, `token`, `usuario_id`).
3. **Evolução do Schema:** O `auth-service` possui verificação manual de colunas no `main.py` (`ALTER TABLE usuarios ADD COLUMN role...`), complementando o Alembic. Recomenda-se unificar as migrações exclusivamente via scripts versionados do Alembic.

---

## 3. Segurança

### 3.1 Autenticação e Hashing de Senhas
- **Hashing:** Implementado corretamente usando `bcrypt` nativo com truncagem preventiva a 72 bytes (`plain.encode("utf-8")[:72]`), evitando erros de limite do algoritmo bcrypt.
- **JWT:** Assinatura com algoritmo HMAC-SHA256 (`HS256`) e segredo parametrizado via variável de ambiente `SECRET_KEY`.
- **Recuperação de Senha:** Tokens de redefinição únicos gerados com `secrets.token_urlsafe(32)`, com prazo de expiração estrito de 30 minutos e invalidação pós-uso (`usado = True`).

### 3.2 CORS & Exposição de Dados
- **CORS:** O middleware em ambos os serviços está configurado com `allow_origins=["*"]`. Em ambiente de produção, deve ser restrito ao domínio exato do frontend.
- **Proteção de Senhas:** O hash da senha (`senha_hash`) nunca é serializado para o cliente (`UsuarioOut` não inclui o campo).
- **Rate Limiting:** Atualmente ausente nos endpoints de `/login` e `/forgot-password`. Recomenda-se adicionar limitação de taxa (ex.: `slowapi` ou Redis rate limiter) para prevenção contra força bruta e spam de e-mails.

---

## 4. Performance & Otimizações

### 4.1 Chamadas de Rede Interserviços
- O backend atua como proxy reverso manual via `httpx.AsyncClient` para o `auth-service`. A conexão HTTP adiciona pequena sobrecarga de latência (~2-5ms local).
- Recomenda-se utilizar um pool de conexões persistente (`httpx.AsyncClient` reutilizável em lifespan/singleton) em vez de instanciar um novo client a cada request (`async with httpx.AsyncClient()`).

### 4.2 Integração TMDB & Cache
- O método `_get_tom_hanks_id` possui cache estático em memória (`_TOM_HANKS_ID`).
- As listagens de filmes (`/api/filmes`) realizam chamadas externas à API do TMDB a cada requisição. Uma camada de cache em memória (ex.: `cachetools` com TTL de 1 hora) ou Redis reduzirá o tempo de resposta de ~400ms para <5ms.

### 4.3 Consultas ao Banco de Dados
- As queries em `favorito_repo` e `comentario_repo` são simples e indexadas por `usuario_id`, não apresentando problemas de N+1 no estado atual.

---

## 5. Cobertura de Testes

- **Suíte Automatizada:** 9 testes implementados com `pytest` cobrindo o fluxo do `auth-service` (registro, login, validação de tokens, expiração, reuso de token) e proxy de permissões de comentários no `backend`.
- **Isolamento:** Execução com banco de dados SQLite em memória (`StaticPool`), garantindo testes rápidos (<10s) sem dependência externa de infraestrutura.
- **Ponto de Melhoria:** Adicionar testes de carga e testes ponta a ponta (E2E) para as novas permissões granulares de RBAC.

---

## 6. Débito Técnico Geral

1. **Duplicação de Código:** Schemas (`UsuarioOut`, `UsuarioCreate`, etc.) e configurações duplicadas entre `backend/app` e `auth-service/app`.
2. **Código Morto:** O arquivo `backend/app/core/security.py` possui funções de decodificação JWT que não eram consumidas porque o backend delegava a autenticação ao `auth_client.py`.
3. **Depreciação de `datetime.utcnow()`:** O Python 3.14 gera warnings com `datetime.utcnow()`; a migração para `datetime.now(timezone.utc)` é recomendada para modernização da base.
