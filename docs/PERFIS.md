# Perfis e permissões (RBAC)

Os usuários comuns são divididos em quatro papéis. O cadastro público permite
escolher somente esses papéis; `admin` não pode ser escolhido durante o cadastro.

## `amigo-do-wilson` — Amigo do Wilson

- Visualizar e pesquisar o catálogo.
- Visualizar detalhes dos filmes.
- Listar comentários.

## `preso-no-terminal` — Preso no Terminal

Inclui tudo de `amigo-do-wilson` e também:

- Listar favoritos.
- Adicionar filmes aos próprios favoritos.
- Remover filmes dos próprios favoritos.

## `houston-temos-acesso` — Houston, Temos Acesso

Inclui tudo de `preso-no-terminal` e também:

- Criar comentários.
- Apagar os próprios comentários.

## `capitao-hanks` — Capitão Hanks

Inclui tudo de `houston-temos-acesso` e também:

- Acessar o catálogo premium.

## `admin` — Administrador

Inclui todas as permissões dos usuários comuns e também:

- Apagar comentários de qualquer usuário (moderação).
- Listar e gerenciar usuários, incluindo promoção e rebaixamento de papéis.
- Gerenciar papéis e a matriz de permissões.
- Administrar o sistema.

O papel `admin` deve ser provisionado internamente ou atribuído por outro
administrador autorizado. A API recusa com HTTP 403 qualquer tentativa de criar
uma conta administrativa pelo endpoint público de cadastro.
