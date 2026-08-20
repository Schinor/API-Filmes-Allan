from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.repositories import usuario_repo
from app.schemas.usuario import UsuarioCreate, UsuarioOut, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastro(payload: UsuarioCreate, db: Session = Depends(get_db)):
    if usuario_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    return usuario_repo.create(db, payload.nome, payload.email, payload.senha)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_email(db, form_data.username)
    if not usuario or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    token = create_access_token(data={"sub": str(usuario.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioOut)
def me(current_user=Depends(get_current_user)):
    return current_user
