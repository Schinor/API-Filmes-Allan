from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.email import send_password_reset_email
from app.repositories import usuario_repo, reset_token_repo
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.schemas.auth import (
    Token,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ValidateTokenResponse,
)

router = APIRouter(tags=["auth"])


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastro(payload: UsuarioCreate, db: Session = Depends(get_db)):
    if usuario_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    return usuario_repo.create(
        db,
        nome=payload.nome,
        email=payload.email,
        senha=payload.senha,
        role=payload.role or "usuario",
    )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_email(db, form_data.username)
    if not usuario or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    token = create_access_token(
        data={
            "sub": str(usuario.id),
            "email": usuario.email,
            "nome": usuario.nome,
            "role": usuario.role,
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": usuario,
    }


@router.get("/me", response_model=UsuarioOut)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    usuario = usuario_repo.get_by_email(db, payload.email)
    if not usuario:
        raise HTTPException(status_code=404, detail="E-mail não cadastrado no sistema.")

    reset_token = reset_token_repo.create_reset_token(db, usuario.id)

    try:
        send_password_reset_email(
            to_email=usuario.email,
            token=reset_token.token,
            user_name=usuario.nome,
        )
    except Exception:
        # Continua para não travar a experiência caso Mailtrap falhe em sandbox dev
        pass

    return {
        "message": "E-mail de recuperação enviado com sucesso. Verifique sua caixa de entrada.",
        "token": reset_token.token,
    }


@router.get("/validate-reset-token/{token}", response_model=ValidateTokenResponse)
def validate_reset_token(token: str, db: Session = Depends(get_db)):
    reset_token = reset_token_repo.get_by_token(db, token)
    if not reset_token:
        return {"valid": False, "message": "Token de recuperação inválido ou não encontrado."}

    if datetime.utcnow() >= reset_token.expira_em:
        return {"valid": False, "message": "Link de recuperação expirado (limite de 30 minutos excedido)."}

    if reset_token.usado:
        return {"valid": False, "message": "Este link de recuperação já foi utilizado."}

    usuario = usuario_repo.get_by_id(db, reset_token.usuario_id)
    return {
        "valid": True,
        "email": usuario.email if usuario else None,
        "message": "Token válido.",
    }


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 1. Checa se o token existe
    reset_token = reset_token_repo.get_by_token(db, payload.token)
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperação inválido ou inexistente.",
        )

    # 2. Checa se agora < expira_em
    if datetime.utcnow() >= reset_token.expira_em:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O link de recuperação expirou (validade de 30 minutos). Solicite uma nova recuperação.",
        )

    # 3. Checa se usado = false
    if reset_token.usado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este link de recuperação já foi utilizado anteriormente.",
        )

    if len(payload.nova_senha) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ter no mínimo 6 caracteres.",
        )

    usuario = usuario_repo.get_by_id(db, reset_token.usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário associado ao token não encontrado.",
        )

    # Troca a senha
    usuario_repo.update_password(db, usuario, payload.nova_senha)

    # Marca token como utilizado para evitar reuso
    reset_token_repo.mark_as_used(db, reset_token)

    return {"message": "Senha redefinida com sucesso! Você já pode fazer login com a nova senha."}
