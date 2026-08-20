from typing import Optional
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.core.security import hash_password


def get_by_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email).first()


def get_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def create(db: Session, nome: str, email: str, senha: str) -> Usuario:
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
