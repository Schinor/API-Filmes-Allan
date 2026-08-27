from typing import Optional
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.core.security import hash_password


def get_by_id(db: Session, user_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == user_id).first()


def get_by_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()


def create(db: Session, nome: str, email: str, senha: str, role: str = "usuario") -> Usuario:
    normalized_role = role.strip().lower() if role else "usuario"
    if normalized_role not in ("usuario", "admin"):
        normalized_role = "usuario"

    user = Usuario(
        nome=nome.strip(),
        email=email.strip().lower(),
        senha_hash=hash_password(senha),
        role=normalized_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: Usuario, nova_senha: str) -> Usuario:
    user.senha_hash = hash_password(nova_senha)
    db.commit()
    db.refresh(user)
    return user
