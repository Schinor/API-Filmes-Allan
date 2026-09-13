# Implementação de Sistema de Roles & Permissões — Streamer de Filmes

## Contexto do projeto
- **Stack:** Angular (frontend) + Python FastAPI + SQLAlchemy (backend) + MySQL
- **Estado atual:** já existe a **atribuição** usuário ↔ papel (campo `role` no cadastro), mas falta o modelo de **permissão** granular (ação sobre recurso).
- **Modelo conceitual a seguir:**
  - **Permissão** = uma ação sobre um recurso. Ex.: `apagar:comentario-de-outro`, `assistir:catalogo-premium`, `gerenciar:usuarios`.
  - **Papel (Role)** = um conjunto de permissões.
  - **Atribuição** = vínculo usuário ↔ papel (já existe, deve ser preservado/adaptado, não recriado do zero).

## Objetivo geral
Implementar um RBAC completo (permissão granular por ação:recurso), aplicá-lo em todo o backend (exceto endpoints públicos) e no frontend, e entregar dois relatórios: um checkup de infraestrutura e um mapeamento de duplicidades/código desnecessário.

---

## 1. Modelo de dados

Criar (via Alembic ou equivalente já usado no projeto):

- **`permissions`**: `id`, `action`, `resource`, `description`. Constraint única em `(action, resource)`.
- **`roles`**: `id`, `name`, `slug`, `description`.
- **`role_permissions`** (N:N): `role_id`, `permission_id`.
- Adaptar a tabela de usuários para referenciar `roles` (manter compatibilidade com o campo `role` atual durante a transição — não quebrar usuários já cadastrados).

## 2. Papéis a criar

| Nome do papel | Slug sugerido | Nível | Descrição |
|---|---|---|---|
| Amigo do Wilson (Náufrago) | `amigo-do-wilson` | Gratuito/básico | Catálogo e permissões bem limitados — isolado, poucas ações liberadas |
| Preso no Terminal (O Terminal) | `preso-no-terminal` | Intermediário | Acesso a várias áreas, mas ainda não circula livremente por tudo |
| Houston, Temos Acesso (Apollo 13) | `houston-temos-acesso` | Avançado | Quase sem restrições |
| Capitão Hanks (Capitão Phillips) | `capitao-hanks` | Supremo | Máximo de permissões dentre os planos de usuário comum |
| Admin | `admin` | Administrativo | Deve ter pelo menos **uma permissão exclusiva** que nenhum outro papel possui (ex.: `administrar:sistema`) |

**Importante:** antes de aplicar a matriz de permissões definitiva, o Antigravity deve varrer o código para levantar todos os recursos/ações existentes e **propor** uma matriz papel × permissão para validação humana antes de aplicar em produção.

## 3. Backend — aplicação nos endpoints

1. Criar uma dependency/decorator FastAPI, ex. `require_permission("acao:recurso")`, para proteger rotas.
2. Mapear **todos** os endpoints existentes, separando:
   - **Públicos** (login, registro, catálogo público, health-check, etc.) — não tocar.
   - **Privados** — cada um deve receber a permissão adequada.
3. Aplicar a dependency em cada endpoint privado.
4. Criar endpoint(s) administrativos de CRUD de roles/permissions, protegidos pela permissão exclusiva do Admin.
5. Cobrir com testes automatizados: usuário sem permissão → 403; usuário com permissão → sucesso.

## 4. Frontend — aplicação no Angular

1. Serviço para carregar as permissões do usuário logado (via claims do token ou endpoint `/me`).
2. Guard de rota baseado em permissão.
3. Diretiva estrutural (ex.: `*hasPermission`) para ocultar/desabilitar elementos de UI conforme permissão.
4. Aplicar guards nas rotas correspondentes e a diretiva nos componentes com ações restritas.

## 5. Checkup de infraestrutura (relatório separado)

Pedir um relatório cobrindo:
- Arquitetura atual (serviços, camadas, organização de pastas).
- Banco de dados: schema, índices, integridade referencial.
- Segurança: autenticação, hashing de senha, exposição de dados sensíveis, CORS, rate limiting.
- Performance: queries N+1, endpoints lentos, uso (ou ausência) de cache.
- Cobertura de testes.
- Débito técnico geral.

## 6. Mapeamento de duplicidade / código desnecessário (relatório separado)

- Endpoints com funcionalidade duplicada ou sobreposta.
- Código morto (funções/classes/rotas não referenciadas em lugar nenhum).
- Lógica de autorização espalhada de forma inconsistente pelo código.
- Sugestão de consolidação ou remoção, com justificativa para cada item.

---

## Entregáveis esperados

1. Migration + models de `Permission`, `Role`, `RolePermission`.
2. Seed dos 5 papéis + matriz de permissões proposta (para validação antes de aplicar).
3. Dependency/middleware de autorização aplicado em todos os endpoints privados do backend.
4. Guards + diretiva de permissão aplicados no Angular.
5. Relatório de infraestrutura (`.md`).
6. Relatório de duplicidade/código desnecessário (`.md`).

## Restrições

- Não alterar nem restringir endpoints públicos — listar quais são considerados públicos **antes** de começar a aplicação.
- Manter compatibilidade com o campo `role` existente durante a migração.
- Validar a matriz permissão × papel com o desenvolvedor antes de aplicar em produção.