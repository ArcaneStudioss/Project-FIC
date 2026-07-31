import datetime as dt
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import UPLOADS_DIR, get_db
from app.deps import exigir_permissao
from app.models import AuditLog, Case, Evidence
from app.templating import contexto_base, templates

router = APIRouter()

# Mesmas categorias usadas no bot do Discord, pra manter a organização
# consistente entre os dois sistemas.
TIPOS_EVIDENCIA = {
    "indiciado": "Indiciado (Líder/Sub-Líder/Gerente)",
    "localizacao": "Perímetro/Localização",
    "produto": "Produto",
    "painel": "Painel",
    "contratacao": "Contratação",
    "bau": "Baús de Líderes e Membros",
    "suspeitos_armados": "Suspeitos Armados na Organização",
    "rota_farm": "Rota de Farm",
    "uniforme": "Uniforme (mochila)",
    "depoimento": "Depoimento",
    "cor_veiculo": "Coloração de Veículo",
    "radio": "Rádio Utilizada",
    "outro": "Outro",
}

STATUS_LABEL = {
    "aberto": "Aberto",
    "em_andamento": "Em Andamento",
    "resolvido": "Resolvido",
    "arquivado": "Arquivado",
}


@router.get("/casos")
def listar_casos(request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("casos.ver"))):
    casos = db.query(Case).order_by(Case.criado_em.desc()).all()
    contexto = contexto_base(request, db, usuario)
    contexto.update({"casos": casos, "status_label": STATUS_LABEL})
    return templates.TemplateResponse(request, "casos_lista.html", contexto)


@router.post("/casos/novo")
def criar_caso(
    request: Request,
    titulo: str = Form(...),
    descricao: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("casos.gerenciar")),
):
    caso = Case(titulo=titulo, descricao=descricao, criado_por_id=usuario.id)
    db.add(caso)
    db.flush()
    db.add(AuditLog(usuario_id=usuario.id, acao="criar_caso", entidade="case", entidade_id=caso.id, detalhes=titulo))
    db.commit()
    return RedirectResponse(url=f"/casos/{caso.id}", status_code=303)


@router.get("/casos/{caso_id}")
def ver_caso(
    caso_id: int, request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("casos.ver"))
):
    caso = db.get(Case, caso_id)
    if caso is None:
        return RedirectResponse(url="/casos", status_code=303)

    evidencias_ativas = [e for e in caso.evidencias if not e.is_deleted]
    agrupadas: dict[str, list[Evidence]] = {}
    for ev in evidencias_ativas:
        agrupadas.setdefault(ev.tipo, []).append(ev)

    contexto = contexto_base(request, db, usuario)
    contexto.update(
        {
            "caso": caso,
            "agrupadas": agrupadas,
            "tipos": TIPOS_EVIDENCIA,
            "status_label": STATUS_LABEL,
        }
    )
    return templates.TemplateResponse(request, "caso_detalhe.html", contexto)


@router.post("/casos/{caso_id}/status")
def mudar_status(
    caso_id: int,
    novo_status: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("casos.gerenciar")),
):
    caso = db.get(Case, caso_id)
    if caso is not None and novo_status in STATUS_LABEL:
        caso.status = novo_status
        if novo_status == "resolvido" and caso.resolvido_em is None:
            caso.resolvido_em = dt.datetime.utcnow()
        if novo_status == "arquivado" and caso.arquivado_em is None:
            caso.arquivado_em = dt.datetime.utcnow()
        db.add(
            AuditLog(
                usuario_id=usuario.id,
                acao="mudar_status_caso",
                entidade="case",
                entidade_id=caso.id,
                detalhes=novo_status,
            )
        )
        db.commit()
    return RedirectResponse(url=f"/casos/{caso_id}", status_code=303)


@router.post("/casos/{caso_id}/evidencia")
async def anexar_evidencia(
    caso_id: int,
    tipo: str = Form(...),
    titulo: str = Form(...),
    descricao: str = Form(""),
    arquivo: UploadFile | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("evidencias.anexar")),
):
    nome_salvo = None
    caminho_salvo = None
    if arquivo is not None and arquivo.filename:
        extensao = Path(arquivo.filename).suffix
        nome_salvo = f"{uuid.uuid4().hex}{extensao}"
        caminho_salvo = str(UPLOADS_DIR / nome_salvo)
        with open(caminho_salvo, "wb") as destino:
            shutil.copyfileobj(arquivo.file, destino)

    evidencia = Evidence(
        case_id=caso_id,
        dono_id=usuario.id,
        tipo=tipo,
        titulo=titulo,
        descricao=descricao,
        nome_arquivo=arquivo.filename if arquivo else None,
        caminho_arquivo=nome_salvo,
    )
    db.add(evidencia)
    db.flush()
    db.add(
        AuditLog(usuario_id=usuario.id, acao="anexar_evidencia", entidade="evidence", entidade_id=evidencia.id)
    )
    db.commit()
    return RedirectResponse(url=f"/casos/{caso_id}", status_code=303)


@router.post("/evidencias/{evidencia_id}/arquivar")
def arquivar_evidencia(
    evidencia_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("evidencias.arquivar")),
):
    """'Arquivar' aqui NUNCA é um delete de verdade — só marca is_deleted,
    então a evidência some da tela mas continua no banco e no log."""
    evidencia = db.get(Evidence, evidencia_id)
    caso_id = evidencia.case_id if evidencia else None
    if evidencia is not None and not evidencia.is_deleted:
        evidencia.is_deleted = True
        evidencia.deleted_at = dt.datetime.utcnow()
        evidencia.deleted_by_id = usuario.id
        db.add(
            AuditLog(usuario_id=usuario.id, acao="arquivar_evidencia", entidade="evidence", entidade_id=evidencia.id)
        )
        db.commit()
    if caso_id:
        return RedirectResponse(url=f"/casos/{caso_id}", status_code=303)
    return RedirectResponse(url="/evidencias-pessoais", status_code=303)
