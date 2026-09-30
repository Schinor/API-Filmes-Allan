from typing import Optional
from sqlalchemy.orm import Session
from app.models.perfil import Perfil


def get(db: Session, usuario_id: int) -> Optional[Perfil]:
    return db.get(Perfil, usuario_id)


def get_or_new(db: Session, usuario_id: int) -> Perfil:
    """Upsert: devolve a linha existente ou uma nova (ainda não commitada)."""
    perfil = get(db, usuario_id)
    if perfil is None:
        perfil = Perfil(usuario_id=usuario_id)
        db.add(perfil)
    return perfil


def atualizar_bio(db: Session, usuario_id: int, bio: Optional[str]) -> Perfil:
    perfil = get_or_new(db, usuario_id)
    perfil.bio = bio
    db.commit()
    db.refresh(perfil)
    return perfil


def definir_foto(db: Session, usuario_id: int, foto_key: Optional[str], foto_bytes: Optional[int]) -> Perfil:
    perfil = get_or_new(db, usuario_id)
    perfil.foto_key = foto_key
    perfil.foto_bytes = foto_bytes
    db.commit()
    db.refresh(perfil)
    return perfil
