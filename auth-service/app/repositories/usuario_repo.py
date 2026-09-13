from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.papel import Papel
from app.core.security import hash_password

LEGACY_ROLE_MAP = {
    "usuario": "amigo-do-wilson",
    "admin": "admin",
}


def get_by_id(db: Session, user_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == user_id).first()


def get_by_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()


def list_all(db: Session) -> List[Usuario]:
    return db.query(Usuario).order_by(Usuario.id.asc()).all()


def create(db: Session, nome: str, email: str, senha: str, role: str = "amigo-do-wilson") -> Usuario:
    raw_role = role.strip().lower() if role else "amigo-do-wilson"
    slug = LEGACY_ROLE_MAP.get(raw_role, raw_role)

    # Localiza o papel no banco
    papel = db.query(Papel).filter(Papel.slug == slug).first()
    if not papel:
        # Fallback para amigo-do-wilson
        papel = db.query(Papel).filter(Papel.slug == "amigo-do-wilson").first()
        slug = papel.slug if papel else "amigo-do-wilson"

    user = Usuario(
        nome=nome.strip(),
        email=email.strip().lower(),
        senha_hash=hash_password(senha),
        role=slug,
        role_id=papel.id if papel else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_role(db: Session, user: Usuario, role_slug: str) -> Usuario:
    slug = LEGACY_ROLE_MAP.get(role_slug.strip().lower(), role_slug.strip().lower())
    papel = db.query(Papel).filter(Papel.slug == slug).first()
    if papel:
        user.role_id = papel.id
        user.role = papel.slug
    else:
        user.role = slug
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: Usuario, nova_senha: str) -> Usuario:
    user.senha_hash = hash_password(nova_senha)
    db.commit()
    db.refresh(user)
    return user
