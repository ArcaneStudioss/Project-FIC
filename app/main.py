import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import UPLOADS_DIR, fazer_backup, init_db
from app.deps import RedirectParaLogin
from app.routers import admin, auth, casos, dashboard, documentos, evidencias
from app.seed import seed

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Sistema DIP")

# IMPORTANTE: troque essa chave antes de colocar em produção de verdade —
# ela assina o cookie de sessão. Pode (e deve) vir de uma variável de
# ambiente própria. Veja o README.
app.add_middleware(SessionMiddleware, secret_key="troque-esta-chave-antes-de-usar-em-producao")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(casos.router)
app.include_router(evidencias.router)
app.include_router(documentos.router)
app.include_router(admin.router)


@app.exception_handler(RedirectParaLogin)
async def _redirecionar_login(request: Request, exc: RedirectParaLogin):
    return RedirectResponse(url="/login", status_code=303)


async def _backup_periodico():
    """Backup automático do banco a cada 6 horas, além do botão manual na
    tela de Auditoria. Guarda tudo em data/backups/ — para uma segunda
    camada de segurança de verdade, sincronize essa pasta pra um storage
    externo (veja o README)."""
    while True:
        await asyncio.sleep(6 * 60 * 60)
        try:
            fazer_backup()
        except Exception:
            pass


@app.on_event("startup")
def _startup():
    init_db()
    seed()
    asyncio.create_task(_backup_periodico())


@app.get("/")
def raiz():
    return RedirectResponse(url="/dashboard")
