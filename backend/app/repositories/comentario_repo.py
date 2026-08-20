from typing import List
from sqlalchemy.orm import Session
from app.models.comentario import Comentario


def list_by_user_and_movie(db: Session, usuario_id: int, tmdb_movie_id: int) -> List[Comentario]:
    return (
        db.query(Comentario)
        .filter(Comentario.usuario_id == usuario_id, Comentario.tmdb_movie_id == tmdb_movie_id)
        .order_by(Comentario.criado_em.desc())
        .all()
    )


def list_by_user(db: Session, usuario_id: int) -> List[Comentario]:
    return (
        db.query(Comentario)
        .filter(Comentario.usuario_id == usuario_id)
        .order_by(Comentario.criado_em.desc())
        .all()
    )


def create(db: Session, usuario_id: int, tmdb_movie_id: int, texto: str) -> Comentario:
    comentario = Comentario(
        usuario_id=usuario_id,
        tmdb_movie_id=tmdb_movie_id,
        texto=texto,
    )
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario


def delete(db: Session, comentario_id: int, usuario_id: int) -> bool:
    comentario = (
        db.query(Comentario)
        .filter(Comentario.id == comentario_id, Comentario.usuario_id == usuario_id)
        .first()
    )
    if comentario:
        db.delete(comentario)
        db.commit()
        return True
    return False
