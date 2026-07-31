import datetime as dt

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import config_do_site, exigir_permissao
from app.models import AuditLog, Case, Document, Evidence
from app.routers.casos import TIPOS_EVIDENCIA
from app.templating import contexto_base, templates

router = APIRouter()

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def data_por_extenso(momento: dt.datetime) -> str:
    return f"{momento.day} de {MESES_PT[momento.month - 1]} de {momento.year}"


@router.get("/documentos")
def listar_documentos(
    request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("documentos.ver"))
):
    documentos = db.query(Document).order_by(Document.criado_em.desc()).all()
    casos = db.query(Case).order_by(Case.titulo).all()
    contexto = contexto_base(request, db, usuario)
    contexto.update({"documentos": documentos, "casos": casos})
    return templates.TemplateResponse(request, "documentos.html", contexto)


@router.post("/documentos/gerar-inquerito")
def gerar_inquerito(
    request: Request,
    case_id: int = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("documentos.gerar")),
):
    caso = db.get(Case, case_id)
    if caso is None:
        return RedirectResponse(url="/documentos", status_code=303)

    evidencias = [e for e in caso.evidencias if not e.is_deleted]
    cfg = config_do_site(db)
    agora = dt.datetime.utcnow()

    contexto_doc = {
        "cfg": cfg,
        "caso": caso,
        "evidencias": evidencias,
        "evidencias_por_tipo": _agrupar(evidencias),
        "tipos": TIPOS_EVIDENCIA,
        "data_instaurado": data_por_extenso(evidencias[0].criado_em if evidencias else caso.criado_em),
        "data_hoje": data_por_extenso(agora),
        "gerado_por": usuario,
    }
    html = templates.get_template("documento_inquerito.html").render(**contexto_doc)

    documento = Document(
        tipo="inquerito", case_id=caso.id, titulo=f"Inquérito — {caso.titulo}", conteudo_html=html,
        gerado_por_id=usuario.id,
    )
    db.add(documento)
    db.flush()
    db.add(AuditLog(usuario_id=usuario.id, acao="gerar_inquerito", entidade="document", entidade_id=documento.id))
    db.commit()
    return RedirectResponse(url=f"/documentos/{documento.id}", status_code=303)


@router.post("/documentos/gerar-mandado")
def gerar_mandado(
    request: Request,
    case_id: int = Form(...),
    nome_individuo: str = Form(...),
    passaporte: str = Form(...),
    qualificacao: str = Form(""),
    local: str = Form(""),
    motivo: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("documentos.gerar")),
):
    caso = db.get(Case, case_id)
    if caso is None:
        return RedirectResponse(url="/documentos", status_code=303)

    cfg = config_do_site(db)
    agora = dt.datetime.utcnow()
    contexto_doc = {
        "cfg": cfg,
        "caso": caso,
        "nome_individuo": nome_individuo,
        "passaporte": passaporte,
        "qualificacao": qualificacao,
        "local": local,
        "motivo": motivo,
        "data_hoje": data_por_extenso(agora),
        "gerado_por": usuario,
    }
    html = templates.get_template("documento_mandado.html").render(**contexto_doc)

    documento = Document(
        tipo="mandado", case_id=caso.id, titulo=f"Mandado — {nome_individuo}", conteudo_html=html,
        gerado_por_id=usuario.id,
    )
    db.add(documento)
    db.flush()
    db.add(AuditLog(usuario_id=usuario.id, acao="gerar_mandado", entidade="document", entidade_id=documento.id))
    db.commit()
    return RedirectResponse(url=f"/documentos/{documento.id}", status_code=303)


@router.get("/documentos/{documento_id}")
def ver_documento(
    documento_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("documentos.ver")),
):
    documento = db.get(Document, documento_id)
    if documento is None:
        return RedirectResponse(url="/documentos", status_code=303)
    contexto = contexto_base(request, db, usuario)
    contexto.update({"documento": documento})
    return templates.TemplateResponse(request, "documento_view.html", contexto)


def _agrupar(evidencias: list[Evidence]) -> dict[str, list[Evidence]]:
    agrupadas: dict[str, list[Evidence]] = {}
    for ev in evidencias:
        agrupadas.setdefault(ev.tipo, []).append(ev)
    return agrupadas
