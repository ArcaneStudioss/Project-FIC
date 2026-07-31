# Sistema COI/DIP

Sistema web de gestão de casos, evidências e documentos — login com cargos e
permissões 100% configuráveis pela própria interface (cores, abas visíveis,
cargos e o que cada um pode fazer), sem precisar tocar em nenhum arquivo depois
de instalado.

## O que tem

- **Login** com usuários, cargos e permissões granulares (o cargo Admin tem
  acesso total; os outros cargos você define exatamente o que cada um pode
  fazer).
- **Dashboard**: casos resolvidos, arquivados, em aberto e tempo médio por caso.
- **Casos**: funciona parecido com os canais de caso do Discord, mas as
  evidências ficam organizadas por categoria (Indiciado, Perímetro, Produto,
  etc.) em vez de em ordem cronológica solta.
- **Evidências Pessoais**: cada agente tem seu próprio espaço pra anexar
  provas + um chat particular (só ele vê).
- **Documentos**: gera Inquérito (junta automaticamente todas as evidências do
  caso escolhido, organizadas por categoria) e Mandado, com botão de
  Imprimir/Salvar como PDF direto do navegador.
- **Configurações** (aba só do Admin): cores do site, nome do órgão/cidade,
  quais abas aparecem e em que ordem — tudo salvo no banco, aplicado na hora.
- **Auditoria e Backups**: toda ação relevante fica registrada (quem, o quê,
  quando); backup do banco automático a cada 6h + botão manual.

## Sobre a segurança das provas — leia isto

O código **nunca** apaga uma evidência de verdade. O botão "Arquivar" só marca
a linha como `is_deleted=True` no banco — ela some da tela, mas continua lá
pra sempre, junto com um registro de quem arquivou e quando (aba Auditoria).
Não existe, em lugar nenhum do código, um comando que apague uma evidência do
banco de dados.

Isso cobre erro humano e bug de aplicação. **Não cobre**, sozinho, falha de
hardware/hospedagem — pra isso, o backup automático (`data/backups/`) precisa
ser sincronizado pra um lugar fora do próprio servidor (um bucket S3, Google
Drive, outro servidor). Isso depende de onde você hospedar — veja a seção de
Deploy.

## Como rodar (teste local)

```bash
pip install -r requirements.txt
python run.py
```

Acesse `http://localhost:8000`. Login inicial: **admin / admin123** — troque
essa senha assim que entrar (crie um novo usuário Admin e desative/apague o
padrão, ou adicione uma tela de troca de senha — ainda não tem uma pronta).

## Antes de usar de verdade (checklist de produção)

1. **Troque a `secret_key`** em `app/main.py` (linha do `SessionMiddleware`) —
   idealmente lendo de uma variável de ambiente, não deixando fixa no código.
2. **Troque a senha do admin** assim que logar pela primeira vez.
3. Configure o **backup externo** (item acima).
4. Rode atrás de HTTPS (a maioria das hospedagens já faz isso automaticamente).

## Hospedagem

Esse projeto **não roda na Discloud** (ela é feita pra bots de Discord, não
pra sites). Opções de hospedagem que funcionam bem com FastAPI + SQLite:

- **Railway** ou **Render** — mais simples, tem plano gratuito limitado, você
  só conecta o repositório e ele sobe sozinho.
- Uma **VPS** (Hetzner, DigitalOcean, etc.) — mais controle, precisa configurar
  você mesmo (ou eu te ajudo a montar o passo a passo).

Em qualquer uma dessas, o comando de start é:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Estrutura do projeto

```
app/
  main.py            # ponto de entrada
  models.py           # tabelas do banco
  database.py         # conexão SQLite + backup
  security.py         # senha (bcrypt) + catálogo de permissões
  deps.py              # login/permissão exigidos em cada rota
  seed.py               # cria o Admin e as configs padrão na 1ª vez
  routers/              # uma rota por área (casos, evidências, documentos, admin...)
  templates/            # HTML (Jinja2)
  static/                # CSS, JS, logo
data/
  sistema.db            # banco (criado automaticamente)
  uploads/               # arquivos anexados
  backups/                # cópias do banco
```

## Próximos passos que vale a pena pedir pra eu adicionar

- Tela de troca de senha pelo próprio usuário.
- Chat também dentro de cada Caso (hoje só tem no espaço pessoal).
- Fotos/evidências embutidas dentro do PDF do Inquérito de forma mais rica
  (hoje já entra, mas dá pra caprichar no layout).
- Exportar backup direto pra um serviço externo (S3, Google Drive) automaticamente.
