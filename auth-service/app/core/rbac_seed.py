from sqlalchemy.orm import Session
from app.models.permissao import Permissao
from app.models.papel import Papel
from app.models.usuario import Usuario

PERMISSOES_DEFINICAO = [
    {"action": "assistir", "resource": "catalogo", "description": "Visualizar e buscar filmes no catálogo"},
    {"action": "detalhes", "resource": "filmes", "description": "Visualizar detalhes e ficha técnica de filmes"},
    {"action": "assistir", "resource": "catalogo-premium", "description": "Acesso a conteúdos 4K, bastidores e edições exclusivas"},
    {"action": "listar", "resource": "favoritos", "description": "Visualizar a lista de filmes favoritos"},
    {"action": "adicionar", "resource": "favoritos", "description": "Adicionar filmes à lista de favoritos"},
    {"action": "remover", "resource": "favoritos", "description": "Remover filmes da lista de favoritos"},
    {"action": "listar", "resource": "comentarios", "description": "Visualizar comentários da comunidade"},
    {"action": "criar", "resource": "comentarios", "description": "Publicar novos comentários em filmes"},
    {"action": "apagar", "resource": "comentario-proprio", "description": "Excluir os próprios comentários"},
    {"action": "apagar", "resource": "comentario-de-outro", "description": "Moderação: excluir comentários de outros usuários"},
    {"action": "visualizar", "resource": "usuarios", "description": "Listar usuários cadastrados no sistema"},
    {"action": "gerenciar", "resource": "usuarios", "description": "Alterar dados e papéis de usuários"},
    {"action": "gerenciar", "resource": "papeis", "description": "Criar, alterar e listar papéis do sistema"},
    {"action": "gerenciar", "resource": "permissoes", "description": "Gerenciar matriz de permissões"},
    {"action": "administrar", "resource": "sistema", "description": "Permissão exclusiva de administração do sistema"},
]

PAPEIS_DEFINICAO = [
    {
        "name": "Amigo do Wilson (Náufrago)",
        "slug": "amigo-do-wilson",
        "description": "Catálogo e permissões bem limitados — isolado, poucas ações liberadas",
        "permissoes": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
        ],
    },
    {
        "name": "Preso no Terminal (O Terminal)",
        "slug": "preso-no-terminal",
        "description": "Acesso a várias áreas, mas ainda não circula livremente por tudo",
        "permissoes": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
            "listar:favoritos",
            "adicionar:favoritos",
            "remover:favoritos",
        ],
    },
    {
        "name": "Houston, Temos Acesso (Apollo 13)",
        "slug": "houston-temos-acesso",
        "description": "Quase sem restrições — favoritos e comentários liberados",
        "permissoes": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
            "listar:favoritos",
            "adicionar:favoritos",
            "remover:favoritos",
            "criar:comentarios",
            "apagar:comentario-proprio",
        ],
    },
    {
        "name": "Capitão Hanks (Capitão Phillips)",
        "slug": "capitao-hanks",
        "description": "Máximo de permissões dentre os planos de usuário comum — acervo premium",
        "permissoes": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
            "listar:favoritos",
            "adicionar:favoritos",
            "remover:favoritos",
            "criar:comentarios",
            "apagar:comentario-proprio",
            "assistir:catalogo-premium",
        ],
    },
    {
        "name": "Admin",
        "slug": "admin",
        "description": "Administrador do sistema com controle total e permissão exclusiva de administração",
        "permissoes": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
            "listar:favoritos",
            "adicionar:favoritos",
            "remover:favoritos",
            "criar:comentarios",
            "apagar:comentario-proprio",
            "assistir:catalogo-premium",
            "apagar:comentario-de-outro",
            "visualizar:usuarios",
            "gerenciar:usuarios",
            "gerenciar:papeis",
            "gerenciar:permissoes",
            "administrar:sistema",
        ],
    },
]

LEGACY_ROLE_MAP = {
    "usuario": "amigo-do-wilson",
    "admin": "admin",
}


def seed_rbac(db: Session) -> None:
    # 1. Cria ou atualiza as permissões
    perm_dict = {}
    for p_data in PERMISSOES_DEFINICAO:
        perm = db.query(Permissao).filter(
            Permissao.action == p_data["action"],
            Permissao.resource == p_data["resource"],
        ).first()
        if not perm:
            perm = Permissao(
                action=p_data["action"],
                resource=p_data["resource"],
                description=p_data["description"],
            )
            db.add(perm)
            db.flush()
        perm_dict[f"{perm.action}:{perm.resource}"] = perm

    # 2. Cria ou atualiza os papéis e associa as permissões
    roles_dict = {}
    for r_data in PAPEIS_DEFINICAO:
        role = db.query(Papel).filter(Papel.slug == r_data["slug"]).first()
        if not role:
            role = Papel(
                name=r_data["name"],
                slug=r_data["slug"],
                description=r_data["description"],
            )
            db.add(role)
            db.flush()
        else:
            role.name = r_data["name"]
            role.description = r_data["description"]

        # Atualiza a lista de permissões do papel
        role.permissoes = [
            perm_dict[p_slug] for p_slug in r_data["permissoes"] if p_slug in perm_dict
        ]
        roles_dict[role.slug] = role

    # 3. Sincroniza usuários existentes (garante que role_id esteja associado ao papel correto)
    usuarios = db.query(Usuario).all()
    for user in usuarios:
        target_slug = LEGACY_ROLE_MAP.get(user.role, user.role)
        if target_slug in roles_dict:
            user.role_id = roles_dict[target_slug].id
            user.role = target_slug
        elif "amigo-do-wilson" in roles_dict:
            user.role_id = roles_dict["amigo-do-wilson"].id
            user.role = "amigo-do-wilson"

    db.commit()
