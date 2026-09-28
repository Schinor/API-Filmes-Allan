from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="amigo-do-wilson")
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    papel = relationship("Papel", back_populates="usuarios", lazy="joined")
    reset_tokens = relationship("ResetToken", back_populates="usuario", cascade="all, delete-orphan")
    ajustes_permissao = relationship(
        "UsuarioPermissao", back_populates="usuario", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def permissions(self) -> list[str]:
        """Permissões efetivas: as do papel, mais as concedidas e menos as revogadas individualmente."""
        base = [f"{p.action}:{p.resource}" for p in self.papel.permissoes] if self.papel else []
        concedidas = [a.permissao.slug for a in self.ajustes_permissao if a.concedida]
        revogadas = {a.permissao.slug for a in self.ajustes_permissao if not a.concedida}
        efetivas = [p for p in base if p not in revogadas]
        return efetivas + [p for p in concedidas if p not in efetivas]

    @property
    def permissions_list(self) -> list[str]:
        return self.permissions
