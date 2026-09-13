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

    @property
    def permissions(self) -> list[str]:
        if self.papel and self.papel.permissoes:
            return [f"{p.action}:{p.resource}" for p in self.papel.permissoes]
        return []

    @property
    def permissions_list(self) -> list[str]:
        return self.permissions
