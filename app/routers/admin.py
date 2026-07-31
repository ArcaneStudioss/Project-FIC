from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import fazer_backup, get_db, listar_backups
from app.deps import exigir_permissao
from app.models import AuditLog, Role, RolePermission, SiteSetting, Tab, User
from app.security import PERMISSOES, hash_senha
from app.templating import contexto_base, templates

router = APIRouter(prefix="/admin")


# ---------------------------------------------------------------------------
# Usuários e cargos
# ---------------------------------------------------------------------------
@router.get("/usuarios")
def usuarios(request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.usuarios"))):
    contexto = contexto_base(request, db, usuario)
    contexto.update(
        {
            "usuarios": db.query(User).order_by(User.username).all(),
            "cargos": db.query(Role).order_by(Role.nome).all(),
            "catalogo_permissoes": PERMISSOES,
        }
    )
    return templates.TemplateResponse(request, "admin_usuarios.html", contexto)


@router.post("/usuarios/novo")
def criar_usuario(
    username: str = Form(...),
    nome_exibicao: str = Form(...),
    senha: str = Form(...),
    role_id: int = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("admin.usuarios")),
):
    if not db.query(User).filter_by(username=username).first():
        novo = User(username=username, nome_exibicao=nome_exibicao, senha_hash=hash_senha(senha), role_id=role_id)
        db.add(novo)
        db.flush()
        db.add(AuditLog(usuario_id=usuario.id, acao="criar_usuario", entidade="user", entidade_id=novo.id))
        db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{alvo_id}/cargo")
def mudar_cargo(
    alvo_id: int,
    role_id: int = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("admin.usuarios")),
):
    alvo = db.get(User, alvo_id)
    if alvo is not None:
        alvo.role_id = role_id
        db.add(AuditLog(usuario_id=usuario.id, acao="mudar_cargo_usuario", entidade="user", entidade_id=alvo.id))
        db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{alvo_id}/alternar-ativo")
def alternar_ativo(
    alvo_id: int, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.usuarios"))
):
    alvo = db.get(User, alvo_id)
    if alvo is not None:
        alvo.ativo = not alvo.ativo
        db.add(
            AuditLog(
                usuario_id=usuario.id,
                acao="ativar_usuario" if alvo.ativo else "desativar_usuario",
                entidade="user",
                entidade_id=alvo.id,
            )
        )
        db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/cargos/novo")
def criar_cargo(
    nome: str = Form(...),
    cor: str = Form("#7fa3bd"),
    permissoes: list[str] = Form([]),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("admin.usuarios")),
):
    if not db.query(Role).filter_by(nome=nome).first():
        cargo = Role(nome=nome, cor=cor)
        db.add(cargo)
        db.flush()
        for chave in permissoes:
            if chave in PERMISSOES:
                db.add(RolePermission(role_id=cargo.id, permission_key=chave))
        db.add(AuditLog(usuario_id=usuario.id, acao="criar_cargo", entidade="role", entidade_id=cargo.id, detalhes=nome))
        db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/cargos/{cargo_id}/permissoes")
def atualizar_permissoes_cargo(
    cargo_id: int,
    permissoes: list[str] = Form([]),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("admin.usuarios")),
):
    cargo = db.get(Role, cargo_id)
    if cargo is not None and not cargo.is_admin:
        db.query(RolePermission).filter_by(role_id=cargo.id).delete()
        for chave in permissoes:
            if chave in PERMISSOES:
                db.add(RolePermission(role_id=cargo.id, permission_key=chave))
        db.add(
            AuditLog(usuario_id=usuario.id, acao="editar_permissoes_cargo", entidade="role", entidade_id=cargo.id)
        )
        db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


# ---------------------------------------------------------------------------
# Configurações do site: cores e abas
# ---------------------------------------------------------------------------
@router.get("/configuracoes")
def configuracoes(
    request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.configuracoes"))
):
    contexto = contexto_base(request, db, usuario)
    contexto["todas_abas"] = db.query(Tab).order_by(Tab.ordem).all()
    return templates.TemplateResponse(request, "admin_configuracoes.html", contexto)


@router.post("/configuracoes/cores")
async def salvar_cores(
    request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.configuracoes"))
):
    form = await request.form()
    for chave, valor in form.items():
        linha = db.get(SiteSetting, chave)
        if linha is not None:
            linha.valor = valor
        else:
            db.add(SiteSetting(chave=chave, valor=valor))
    db.add(AuditLog(usuario_id=usuario.id, acao="editar_configuracoes_site", entidade="site_setting"))
    db.commit()
    return RedirectResponse(url="/admin/configuracoes", status_code=303)


@router.post("/abas/{aba_id}")
def atualizar_aba(
    aba_id: int,
    rotulo: str = Form(...),
    icone: str = Form(...),
    ordem: int = Form(0),
    visivel: bool = Form(False),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("admin.configuracoes")),
):
    aba = db.get(Tab, aba_id)
    if aba is not None:
        aba.rotulo = rotulo
        aba.icone = icone
        aba.ordem = ordem
        aba.visivel = visivel
        db.add(AuditLog(usuario_id=usuario.id, acao="editar_aba", entidade="tab", entidade_id=aba.id))
        db.commit()
    return RedirectResponse(url="/admin/configuracoes", status_code=303)


# ---------------------------------------------------------------------------
# Auditoria e backups
# ---------------------------------------------------------------------------
@router.get("/auditoria")
def auditoria(
    request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.auditoria"))
):
    logs = db.query(AuditLog).order_by(AuditLog.criado_em.desc()).limit(300).all()
    contexto = contexto_base(request, db, usuario)
    contexto.update({"logs": logs, "backups": listar_backups()})
    return templates.TemplateResponse(request, "admin_auditoria.html", contexto)


@router.post("/auditoria/backup-agora")
def backup_agora(db: Session = Depends(get_db), usuario=Depends(exigir_permissao("admin.auditoria"))):
    fazer_backup()
    db.add(AuditLog(usuario_id=usuario.id, acao="backup_manual", entidade="system"))
    db.commit()
    return RedirectResponse(url="/admin/auditoria", status_code=303)
