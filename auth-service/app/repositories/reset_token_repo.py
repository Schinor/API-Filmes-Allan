import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.reset_token import ResetToken
from app.core.config import settings


def create_reset_token(db: Session, usuario_id: int) -> ResetToken:
    token_str = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expira_em = now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

    reset_token = ResetToken(
        token=token_str,
        usuario_id=usuario_id,
        criado_em=now,
        expira_em=expira_em,
        usado=False,
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_by_token(db: Session, token: str) -> Optional[ResetToken]:
    return db.query(ResetToken).filter(ResetToken.token == token.strip()).first()


def mark_as_used(db: Session, reset_token: ResetToken) -> None:
    reset_token.usado = True
    db.commit()
