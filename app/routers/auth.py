from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import config_do_site, usuario_atual
from app.models import AuditLog, User
from app.security import verificar_senha
from app.templating import templates

router = APIRouter()


@router.get("/login")
def tela_login(request: Request, db: Session = Depends(get_db)):
    if usuario_atual(request, db):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"cfg": config_do_site(db), "erro": None}
    )


@router.post("/login")
def fazer_login(
    request: Request,
    username: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = db.query(User).filter_by(username=username).first()
    if usuario is None or not usuario.ativo or not verificar_senha(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"cfg": config_do_site(db), "erro": "Usuário ou senha incorretos."},
            status_code=401,
        )

    request.session["user_id"] = usuario.id
    db.add(AuditLog(usuario_id=usuario.id, acao="login", entidade="user", entidade_id=usuario.id))
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/logout")
def fazer_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
