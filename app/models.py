"""Modelos do banco de dados do Sistema DIP.

Regra de ouro do projeto: NUNCA existe um DELETE físico de prova/evidência
no código da aplicação. Tudo que seria "apagado" só recebe is_deleted=True
(soft delete) — o registro continua no banco pra sempre, com log de quem e
quando arquivou. Purga física só existiria fora da aplicação, direto no
banco, e mesmo assim não é algo que o app oferece.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def agora() -> dt.datetime:
    return dt.datetime.utcnow()


# ---------------------------------------------------------------------------
# Usuários, cargos e permissões
# ---------------------------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    cor: Mapped[str] = mapped_column(String(20), default="#8fa3b0")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    protegido: Mapped[bool] = mapped_column(Boolean, default=False)  # não pode ser apagado (ex: Admin)

    usuarios: Mapped[list["User"]] = relationship(back_populates="role")
    permissoes: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    permission_key: Mapped[str] = mapped_column(String(60))

    role: Mapped[Role] = relationship(back_populates="permissoes")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    nome_exibicao: Mapped[str] = mapped_column(String(100))
    senha_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)

    role: Mapped[Role] = relationship(back_populates="usuarios")


# ---------------------------------------------------------------------------
# Configurações do site (cores, abas) — tudo editável pelo admin, sem tocar
# em arquivo. Guardado como pares chave/valor simples.
# ---------------------------------------------------------------------------
class SiteSetting(Base):
    __tablename__ = "site_settings"

    chave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[str] = mapped_column(Text)


class Tab(Base):
    """Cada aba do menu lateral. O admin pode reordenar, renomear, esconder
    e escolher qual permissão é necessária pra ver a aba."""

    __tablename__ = "tabs"

    id: Mapped[int] = mapped_column(primary_key=True)
    chave: Mapped[str] = mapped_column(String(60), unique=True)
    rotulo: Mapped[str] = mapped_column(String(60))
    icone: Mapped[str] = mapped_column(String(10), default="📄")
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    visivel: Mapped[bool] = mapped_column(Boolean, default=True)
    permissao_necessaria: Mapped[str] = mapped_column(String(60), default="")


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------
class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="aberto")  # aberto|em_andamento|resolvido|arquivado
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)
    resolvido_em: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    arquivado_em: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    criado_por: Mapped[User] = relationship()
    evidencias: Mapped[list["Evidence"]] = relationship(back_populates="caso", order_by="Evidence.criado_em")


# ---------------------------------------------------------------------------
# Evidências — tanto de caso quanto pessoais (case_id nulo = pessoal)
# ---------------------------------------------------------------------------
class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id"), nullable=True)
    dono_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # quem anexou
    tipo: Mapped[str] = mapped_column(String(40), default="outro")
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default="")
    nome_arquivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caminho_arquivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)

    # soft delete — NUNCA remova a linha do banco, só marque como arquivada
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    caso: Mapped[Case | None] = relationship(back_populates="evidencias")
    dono: Mapped[User] = relationship(foreign_keys=[dono_id])


# ---------------------------------------------------------------------------
# Chat — reaproveitado tanto pro chat de evidências pessoais quanto, no
# futuro, pra um chat por caso. "canal" identifica o contexto.
# ---------------------------------------------------------------------------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    canal: Mapped[str] = mapped_column(String(60))  # ex: "pessoal:12", "caso:5"
    autor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    conteudo: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)

    autor: Mapped[User] = relationship()


# ---------------------------------------------------------------------------
# Documentos (Inquérito / Mandado)
# ---------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30))  # inquerito|mandado
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    titulo: Mapped[str] = mapped_column(String(150))
    conteudo_html: Mapped[str] = mapped_column(Text)
    gerado_por_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)

    caso: Mapped[Case] = relationship()
    gerado_por: Mapped[User] = relationship()


# ---------------------------------------------------------------------------
# Auditoria — toda ação relevante fica registrada aqui, pra sempre.
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    acao: Mapped[str] = mapped_column(String(80))
    entidade: Mapped[str] = mapped_column(String(40))
    entidade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalhes: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime, default=agora)
