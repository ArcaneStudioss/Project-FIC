import datetime as dt

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import exigir_permissao
from app.models import Case
from app.templating import contexto_base, templates

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), usuario=Depends(exigir_permissao("dashboard.ver"))):
    total_casos = db.query(func.count(Case.id)).scalar() or 0
    resolvidos = db.query(func.count(Case.id)).filter(Case.status == "resolvido").scalar() or 0
    arquivados = db.query(func.count(Case.id)).filter(Case.status == "arquivado").scalar() or 0
    abertos = db.query(func.count(Case.id)).filter(Case.status.in_(["aberto", "em_andamento"])).scalar() or 0

    casos_resolvidos = (
        db.query(Case).filter(Case.status == "resolvido", Case.resolvido_em.isnot(None)).all()
    )
    if casos_resolvidos:
        duracoes = [(c.resolvido_em - c.criado_em).total_seconds() for c in casos_resolvidos]
        media_segundos = sum(duracoes) / len(duracoes)
        media_dias = round(media_segundos / 86400, 1)
    else:
        media_dias = None

    recentes = db.query(Case).order_by(Case.criado_em.desc()).limit(8).all()

    contexto = contexto_base(request, db, usuario)
    contexto.update(
        {
            "total_casos": total_casos,
            "resolvidos": resolvidos,
            "arquivados": arquivados,
            "abertos": abertos,
            "media_dias": media_dias,
            "recentes": recentes,
        }
    )
    return templates.TemplateResponse(request, "dashboard.html", contexto)
