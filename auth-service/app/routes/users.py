from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories import usuario_repo
from app.schemas.usuario import UsuarioOut, UserRoleOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/role", response_model=UserRoleOut)
def get_user_role(user_id: int, db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return {"user_id": usuario.id, "role": usuario.role}


@router.get("/{user_id}", response_model=UsuarioOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario
