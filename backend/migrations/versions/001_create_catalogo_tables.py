"""Cria tabelas de favoritos e comentarios do catalogo

Revision ID: 001_catalogo_tables
Revises: 
Create Date: 2026-09-13 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = "001_catalogo_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if "favoritos" not in tables:
        op.create_table(
            "favoritos",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("usuario_id", sa.Integer(), nullable=False, index=True),
            sa.Column("tmdb_movie_id", sa.Integer(), nullable=False),
            sa.Column("titulo", sa.String(length=255), nullable=False),
            sa.Column("poster_path", sa.String(length=255), nullable=True),
            sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("usuario_id", "tmdb_movie_id", name="uq_usuario_filme"),
        )

    if "comentarios" not in tables:
        op.create_table(
            "comentarios",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("usuario_id", sa.Integer(), nullable=False, index=True),
            sa.Column("tmdb_movie_id", sa.Integer(), nullable=False),
            sa.Column("texto", sa.Text(), nullable=False),
            sa.Column("criado_em", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if "comentarios" in tables:
        op.drop_table("comentarios")

    if "favoritos" in tables:
        op.drop_table("favoritos")
