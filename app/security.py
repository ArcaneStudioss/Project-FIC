import bcrypt


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


# Catálogo fixo de permissões que existem no sistema. O admin não cria
# permissões novas (isso exigiria mexer no código em algum lugar), mas cria
# quantos CARGOS quiser e escolhe livremente quais dessas permissões cada
# cargo tem — isso sim, tudo pela interface.
PERMISSOES = {
    "dashboard.ver": "Ver o dashboard",
    "casos.ver": "Ver casos",
    "casos.gerenciar": "Criar, editar e arquivar casos",
    "evidencias.ver": "Ver evidências de casos",
    "evidencias.anexar": "Anexar evidências",
    "evidencias.arquivar": "Arquivar (remover da visualização) uma evidência",
    "pessoal.usar": "Usar a aba de Evidências Pessoais e o chat",
    "documentos.gerar": "Gerar Inquéritos e Mandados",
    "documentos.ver": "Ver documentos já gerados",
    "admin.usuarios": "Gerenciar usuários e cargos",
    "admin.configuracoes": "Editar cores, abas e permissões do site",
    "admin.auditoria": "Ver o log de auditoria e backups",
}
