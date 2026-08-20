from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.favoritos import Favorito


def list_by_user(db: Session, usuario_id: int) -> List[Favorito]:
    return (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario_id)
        .order_by(Favorito.criado_em.desc())
        .all()
    )


def get_by_user_and_movie(db: Session, usuario_id: int, tmdb_movie_id: int) -> Optional[Favorito]:
    return (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario_id, Favorito.tmdb_movie_id == tmdb_movie_id)
        .first()
    )


def create(db: Session, usuario_id: int, tmdb_movie_id: int, titulo: str, poster_path: Optional[str]) -> Optional[Favorito]:
    fav = Favorito(
        usuario_id=usuario_id,
        tmdb_movie_id=tmdb_movie_id,
        titulo=titulo,
        poster_path=poster_path,
    )
    db.add(fav)
    try:
        db.commit()
        db.refresh(fav)
        return fav
    except IntegrityError:
        db.rollback()
        return None


def delete(db: Session, usuario_id: int, tmdb_movie_id: int) -> bool:
    fav = get_by_user_and_movie(db, usuario_id, tmdb_movie_id)
    if fav:
        db.delete(fav)
        db.commit()
        return True
    return False
