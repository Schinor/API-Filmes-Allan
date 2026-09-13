# Relatório de Mapeamento de Duplicidades e Código Desnecessário

**Projeto:** Catálogo de Filmes — Tom Hanks (API-Filmes-Allan)  
**Data:** 13/09/2026  

---

## 1. Endpoints com Funcionalidade Duplicada ou Sobreposta

1. **Proxy Manual de Autenticação (`backend/app/routes/auth.py` vs `auth-service/app/routes/auth.py`):**
   - **Descrição:** O `backend` expõe rotas `/api/auth/*` (`/cadastro`, `/login`, `/me`, `/forgot-password`, `/validate-reset-token/{token}`, `/reset-password`, `/users/{user_id}/role`) cuja única função é repassar (fazer forward via `httpx`) para o `auth-service`.
   - **Impacto:** Qualquer modificação em contratos DTO precisa ser replicada em duplicidade nos schemas do backend e do auth-service.
   - **Sugestão de Consolidação:** Manter o gateway para isolar a rede interna, mas utilizar um cliente/SDK centralizado ou contrato de schemas compartilhado (`shared/schemas`).

2. **Endpoints de Consulta de Papel/Usuário (`/users/{user_id}/role` e `/users/{user_id}`):**
   - **Descrição:** No `auth-service`, `/users/{user_id}/role` retorna apenas `{"user_id": ..., "role": ...}`, enquanto `/users/{user_id}` já retorna o objeto completo com a role.
   - **Impacto:** Endpoints redundantes para a mesma entidade.
   - **Sugestão de Consolidação:** Unificar as consultas em `/users/{user_id}` ou utilizar `/me` para o usuário logado e `/admin/users` para a listagem/gestão administrativa.

---

## 2. Código Morto e Não Referenciado

1. **Módulo de Segurança Inutilizado no Backend (`backend/app/core/security.py`):**
   - **Descrição:** `backend/app/core/security.py` define `CurrentUser`, `decode_token` e `get_current_user`. No entanto, as rotas de backend importam `current_user` de `backend/app/dependencies.py`, que por sua vez chama `auth_client.get_authenticated_user` via HTTP para o `auth-service`.
   - **Impacto:** Confusão de manutenção (dois caminhos de resolução de token: decodificação local vs chamada HTTP ao auth-service).
   - **Sugestão:** Utilizar a decodificação local do JWT no backend para validação rápida de roles/permissões ou padronizar a dependência unificada `require_permission`.

2. **Migrações e Configurações Duplicadas de Alembic:**
   - **Descrição:** Existem pastas de migração e arquivos `alembic.ini` tanto em `backend/` quanto em `auth-service/`, sendo que `001_add_role_and_reset_tokens.py` está duplicado em ambos os diretórios.
   - **Impacto:** Divergência potencial no versionamento das tabelas do banco de dados compartilhado.
   - **Sugestão:** Centralizar o gerenciamento de migrações no serviço proprietário das tabelas (`auth-service` para RBAC/usuários e `backend` para catálogo/interações, ou migração unificada na raiz).

---

## 3. Lógica de Autorização Espalhada de Forma Inconsistente

1. **Checagem Ad-hoc Inline em `comentarios.py`:**
   - **Código atual:**
     ```python
     e_dono = comentario.usuario_id == user["id"]
     e_admin = user.get("role") == "admin"
     if not (e_dono or e_admin):
         raise HTTPException(status_code=403, detail="Apenas o autor ou um administrador podem remover este comentário")
     ```
   - **Problema:** As regras de autorização estão acopladas diretamente no handler da rota, com comparações literais de strings (`role == "admin"`), tornando impossível a extensão para novos papéis ou permissões granulares dinâmicas.
   - **Sugestão:** Substituir por dependência granular declarativa `require_permission("apagar:comentario-proprio")` combinada com a permissão administrativa `apagar:comentario-de-outro`.

2. **Autorização Baseada em Role Hardcoded no Frontend:**
   - **Código atual no Angular:**
     ```html
     @if (auth.isAdmin()) { ... }
     @if (auth.user()?.role === 'admin') { ... }
     ```
   - **Problema:** O frontend verifica strings fixas de roles em vez de consultar as permissões ativas do usuário.
   - **Sugestão:** Implementar a diretiva estrutural `*hasPermission="'acao:recurso'"` e o serviço `hasPermission(permission: string): boolean`.

---

## 4. Matriz de Consolidação Recomendada

| Item | Localização | Ação Recomendada | Justificativa |
|---|---|---|---|
| `backend/app/core/security.py` | Backend | Refatorar para conter a validação de permissões RBAC | Evitar código órfão e fornecer validação local rápida e segura |
| Checagens `e_admin` manuais | `comentarios.py` | Substituir por `require_permission` | Padronizar autorização granular em todas as camadas |
| Migrações Alembic duplicadas | `backend/migrations` vs `auth-service/migrations` | Definir domínio claro de tabelas para cada serviço | Garantir consistência transacional do schema |
| Validação de role no frontend | Angular templates & services | Migrar para checagem por permissão (`hasPermission`) | Permitir flexibilidade total na concessão de privilégios aos planos |
