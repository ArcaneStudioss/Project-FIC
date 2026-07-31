import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import UPLOADS_DIR, get_db
from app.deps import exigir_permissao
from app.models import AuditLog, ChatMessage, Evidence
from app.routers.casos import TIPOS_EVIDENCIA
from app.templating import contexto_base, templates

router = APIRouter()


@router.get("/evidencias-pessoais")
def evidencias_pessoais(
    request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("pessoal.usar"))
):
    evidencias = (
        db.query(Evidence)
        .filter(Evidence.dono_id == usuario.id, Evidence.case_id.is_(None), Evidence.is_deleted.is_(False))
        .order_by(Evidence.criado_em.desc())
        .all()
    )
    canal = f"pessoal:{usuario.id}"
    mensagens = (
        db.query(ChatMessage).filter(ChatMessage.canal == canal).order_by(ChatMessage.criado_em.asc()).all()
    )

    contexto = contexto_base(request, db, usuario)
    contexto.update({"evidencias": evidencias, "tipos": TIPOS_EVIDENCIA, "mensagens": mensagens})
    return templates.TemplateResponse(request, "evidencias_pessoais.html", contexto)


@router.post("/evidencias-pessoais/nova")
async def nova_evidencia_pessoal(
    tipo: str = Form(...),
    titulo: str = Form(...),
    descricao: str = Form(""),
    arquivo: UploadFile | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("pessoal.usar")),
):
    nome_salvo = None
    if arquivo is not None and arquivo.filename:
        extensao = Path(arquivo.filename).suffix
        nome_salvo = f"{uuid.uuid4().hex}{extensao}"
        with open(UPLOADS_DIR / nome_salvo, "wb") as destino:
            shutil.copyfileobj(arquivo.file, destino)

    evidencia = Evidence(
        case_id=None,
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
        AuditLog(
            usuario_id=usuario.id, acao="anexar_evidencia_pessoal", entidade="evidence", entidade_id=evidencia.id
        )
    )
    db.commit()
    return RedirectResponse(url="/evidencias-pessoais", status_code=303)


@router.post("/evidencias-pessoais/chat")
def enviar_mensagem(
    conteudo: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(exigir_permissao("pessoal.usar")),
):
    if conteudo.strip():
        db.add(ChatMessage(canal=f"pessoal:{usuario.id}", autor_id=usuario.id, conteudo=conteudo.strip()))
        db.commit()
    return RedirectResponse(url="/evidencias-pessoais", status_code=303)
