from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SiteSetting, Tab, User


def usuario_atual(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    usuario = db.get(User, user_id)
    if usuario is None or not usuario.ativo:
        return None
    return usuario


def exigir_login(request: Request, db: Session = Depends(get_db)) -> User:
    usuario = usuario_atual(request, db)
    if usuario is None:
        raise RedirectParaLogin()
    return usuario


class RedirectParaLogin(Exception):
    pass


def permissoes_do_usuario(usuario: User) -> set[str]:
    if usuario.role.is_admin:
        from app.security import PERMISSOES

        return set(PERMISSOES.keys())
    return {rp.permission_key for rp in usuario.role.permissoes}


def tem_permissao(usuario: User, chave: str) -> bool:
    if not chave:
        return True
    return chave in permissoes_do_usuario(usuario)


def exigir_permissao(chave: str):
    def _dep(request: Request, db: Session = Depends(get_db)) -> User:
        usuario = usuario_atual(request, db)
        if usuario is None:
            raise RedirectParaLogin()
        if not tem_permissao(usuario, chave):
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar isso.")
        return usuario

    return _dep


def config_do_site(db: Session) -> dict:
    linhas = db.query(SiteSetting).all()
    return {linha.chave: linha.valor for linha in linhas}


def abas_visiveis(db: Session, usuario: User) -> list[Tab]:
    abas = db.query(Tab).order_by(Tab.ordem).all()
    return [aba for aba in abas if aba.visivel and tem_permissao(usuario, aba.permissao_necessaria)]
