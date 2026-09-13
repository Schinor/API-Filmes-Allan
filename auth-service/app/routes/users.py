from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.permissao import Permissao
from app.models.papel import Papel
from app.repositories import usuario_repo
from app.schemas.usuario import (
    UsuarioOut,
    UserRoleOut,
    UserRoleUpdate,
    PapelOut,
    PapelCreate,
    PermissaoOut,
)

router = APIRouter(prefix="", tags=["users & rbac"])


@router.get("/users", response_model=List[UsuarioOut])
def list_users(
    db: Session = Depends(get_db),
    _user=Depends(require_permission("gerenciar:usuarios")),
):
    return usuario_repo.list_all(db)


@router.get("/users/{user_id}/role", response_model=UserRoleOut)
def get_user_role(user_id: int, db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return {
        "user_id": usuario.id,
        "role": usuario.role,
        "role_id": usuario.role_id,
        "permissions": usuario.permissions,
    }


@router.put("/users/{user_id}/role", response_model=UsuarioOut)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("gerenciar:usuarios")),
):
    usuario = usuario_repo.get_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario_repo.update_role(db, usuario, payload.role)


@router.get("/users/{user_id}", response_model=UsuarioOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario


@router.get("/roles", response_model=List[PapelOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Papel).all()


@router.post("/roles", response_model=PapelOut, status_code=status.HTTP_201_CREATED)
def create_or_update_role(
    payload: PapelCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("gerenciar:papeis")),
):
    role = db.query(Papel).filter(Papel.slug == payload.slug).first()
    if not role:
        role = Papel(name=payload.name, slug=payload.slug, description=payload.description)
        db.add(role)
    else:
        role.name = payload.name
        role.description = payload.description

    if payload.permission_ids:
        perms = db.query(Permissao).filter(Permissao.id.in_(payload.permission_ids)).all()
        role.permissoes = perms

    db.commit()
    db.refresh(role)
    return role


@router.get("/permissions", response_model=List[PermissaoOut])
def list_permissions(
    db: Session = Depends(get_db),
    _user=Depends(require_permission("gerenciar:permissoes")),
):
    return db.query(Permissao).all()


@router.get("/admin/status")
def admin_status(
    _user=Depends(require_permission("administrar:sistema")),
):
    return {
        "status": "online",
        "admin_access": True,
        "message": "Painel de controle administrativo autorizado.",
    }
