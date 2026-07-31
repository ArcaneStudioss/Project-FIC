import datetime as dt
import shutil
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models import Base

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sistema.db"
BACKUPS_DIR = DATA_DIR / "backups"
UPLOADS_DIR = DATA_DIR / "uploads"

DATA_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _ativar_wal(conexao_dbapi, _):
    """WAL = Write-Ahead Logging. Deixa o SQLite bem mais resistente a
    corrupção em caso de queda de energia/processo no meio de uma escrita —
    é a mesma técnica usada por bancos de dados 'de verdade' pra durabilidade."""
    cursor = conexao_dbapi.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fazer_backup() -> Path:
    """Copia o arquivo do banco pra data/backups/ com timestamp no nome.
    Chamado automaticamente (ver app/backup_scheduler.py) e também disponível
    pro admin rodar manualmente pela interface."""
    if not DB_PATH.exists():
        raise FileNotFoundError("Banco de dados ainda não existe")
    agora = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    destino = BACKUPS_DIR / f"sistema-{agora}.db"
    shutil.copy2(DB_PATH, destino)
    return destino


def listar_backups() -> list[Path]:
    return sorted(BACKUPS_DIR.glob("sistema-*.db"), reverse=True)
