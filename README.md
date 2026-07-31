# ☀ Energia Solar — Site Feira de Ciências

## Estrutura de arquivos

```
energia-solar/
├── index.html       ← Página principal (edite os textos aqui!)
├── css/
│   └── style.css    ← Estilos visuais (cores, fontes, layout)
├── js/
│   └── main.js      ← Interatividade (calculadora, animações, menu)
└── README.md        ← Este arquivo
```

---

## Como editar os textos

O arquivo **`index.html`** contém comentários indicando exatamente onde editar:

```html
<!-- EDITE AQUI: Descrição do texto -->
Seu texto atual aqui...
```

Basta abrir o `index.html` em qualquer editor de texto (Bloco de Notas, VS Code, etc.)
e substituir os textos nos trechos marcados com `<!-- EDITE AQUI -->`.

---

## O que está pronto (não precisa editar)

- ✅ Navegação responsiva com menu hambúrguer no celular
- ✅ Hero com animação do sol e estatísticas animadas
- ✅ Acordeão interativo para a metodologia
- ✅ Comparação visual Protótipo × Sistema Real
- ✅ Gráfico de barras animado
- ✅ Calculadora solar interativa (totalmente funcional)
- ✅ Barras de progresso animadas
- ✅ Animações suaves de entrada (fade-in no scroll)
- ✅ Design responsivo para PC e celular

---

## O que personalizar

### Textos principais:
- **Hipótese** do projeto
- **Objetivo** geral
- **Metodologia** (etapas 1 a 5)
- **Especificações** do protótipo e do sistema real
- **Dados do gráfico** (valores das barras)
- **Resultados** e conclusões
- **Referências** bibliográficas
- **Dados do rodapé**: nome da escola, integrantes, turma, professor

### Dados das barras do gráfico:
No `index.html`, procure por `data-width` nas `<div class="bar-fill">`:
```html
<div class="bar-fill navy" data-width="45%">9,5%</div>
```
Altere o `data-width` (tamanho visual) e o texto dentro (valor exibido).

### Estatísticas do Hero (números animados):
Procure por `data-count` no index.html:
```html
<span data-count="90" data-suffix="%">0%</span>
```

---

## Como abrir o site

**Opção 1 (mais simples):** Dê duplo clique no arquivo `index.html` — ele abre direto no navegador.

**Opção 2 (recomendado para edição):** Use o VS Code com a extensão "Live Server" para ver as alterações em tempo real.

---

## Cores do projeto

| Cor           | Hex       | Uso |
|---------------|-----------|-----|
| Azul Marinho  | `#0B1D3A` | Fundo do hero, cards de destaque |
| Amarelo Solar | `#F5C400` | Destaques, botões, ícones |
| Branco        | `#FFFFFF` | Fundo das seções, cards |
| Azul Suave    | `#F8F9FD` | Fundo geral da página |

---

## Fontes utilizadas (Google Fonts — online)

- **Playfair Display** — títulos elegantes
- **Outfit** — texto corrido, limpo e legível

> As fontes são carregadas da internet. O site precisa de conexão ativa para exibi-las corretamente.
> Para uso offline, baixe e hospede as fontes localmente.

---

Bom projeto! ☀
