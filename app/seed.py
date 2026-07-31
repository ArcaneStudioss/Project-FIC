"""Roda uma vez (automaticamente, no primeiro start) pra criar o cargo Admin,
o usuário administrador inicial, as abas padrão e as cores padrão do site.
Depois disso, tudo é editável pela interface — esse script não precisa ser
rodado de novo."""
from app.database import SessionLocal, init_db
from app.models import Role, RolePermission, SiteSetting, Tab, User
from app.security import PERMISSOES, hash_senha

CORES_PADRAO = {
    "cor_fundo": "#0b0c0e",
    "cor_painel": "#16181c",
    "cor_borda": "#2a2d33",
    "cor_texto": "#e9eaec",
    "cor_texto_fraco": "#9aa0a8",
    "cor_destaque": "#7fa3bd",
    "cor_sucesso": "#5fa87a",
    "cor_alerta": "#c9a227",
    "cor_perigo": "#c1584f",
    "nome_orgao": "Departamento de Inteligência Policial",
    "nome_cidade": "Cidade do Hype",
    "sigla": "DIP",
}

ABAS_PADRAO = [
    ("dashboard", "Dashboard", "📊", "dashboard.ver"),
    ("casos", "Casos", "🗂️", "casos.ver"),
    ("evidencias_pessoais", "Evidências Pessoais", "📎", "pessoal.usar"),
    ("documentos", "Documentos", "📑", "documentos.ver"),
    ("admin_usuarios", "Usuários e Cargos", "👤", "admin.usuarios"),
    ("admin_configuracoes", "Configurações do Site", "⚙️", "admin.configuracoes"),
    ("admin_auditoria", "Auditoria e Backups", "🛡️", "admin.auditoria"),
]


def seed(usuario_admin: str = "admin", senha_admin: str = "admin123"):
    init_db()
    db = SessionLocal()
    try:
        if not db.query(Role).filter_by(nome="Admin").first():
            cargo_admin = Role(nome="Admin", cor="#c9a227", is_admin=True, protegido=True)
            db.add(cargo_admin)
            db.flush()
            for chave in PERMISSOES:
                db.add(RolePermission(role_id=cargo_admin.id, permission_key=chave))
        else:
            cargo_admin = db.query(Role).filter_by(nome="Admin").first()

        if not db.query(User).filter_by(username=usuario_admin).first():
            db.add(
                User(
                    username=usuario_admin,
                    nome_exibicao="Administrador",
                    senha_hash=hash_senha(senha_admin),
                    role_id=cargo_admin.id,
                )
            )

        for chave, valor in CORES_PADRAO.items():
            if not db.query(SiteSetting).filter_by(chave=chave).first():
                db.add(SiteSetting(chave=chave, valor=valor))

        for i, (chave, rotulo, icone, permissao) in enumerate(ABAS_PADRAO):
            if not db.query(Tab).filter_by(chave=chave).first():
                db.add(Tab(chave=chave, rotulo=rotulo, icone=icone, ordem=i, permissao_necessaria=permissao))

        db.commit()
        print(f"Seed concluído. Login inicial -> usuário: {usuario_admin} / senha: {senha_admin}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
