from pathlib import Path

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.deps import abas_visiveis, config_do_site, permissoes_do_usuario
from app.models import User

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

URL_DAS_ABAS = {
    "dashboard": "/dashboard",
    "casos": "/casos",
    "evidencias_pessoais": "/evidencias-pessoais",
    "documentos": "/documentos",
    "admin_usuarios": "/admin/usuarios",
    "admin_configuracoes": "/admin/configuracoes",
    "admin_auditoria": "/admin/auditoria",
}


def contexto_base(request, db: Session, usuario: User | None) -> dict:
    return {
        "request": request,
        "usuario": usuario,
        "cfg": config_do_site(db),
        "abas": abas_visiveis(db, usuario) if usuario else [],
        "permissoes": permissoes_do_usuario(usuario) if usuario else set(),
        "url_abas": URL_DAS_ABAS,
    }
