# HANKS+ — Guia de Estilo Visual

> Sua assinatura, seu papel na história.

Guia de estilo do streamer pessoal de filmes (Angular + FastAPI/SQLAlchemy + MySQL). Os planos de assinatura e papéis de acesso tomam emprestado nomes de personagens do Tom Hanks, do sobrevivente ao capitão — a identidade visual precisa carregar essa personalidade sem virar bagunça.

---

## 1. Princípios visuais

1. **Tela escura, luz onde importa.** Fundos quase pretos (`surface-100`/`surface-200`) para o pôster do filme ser sempre o elemento mais vivo da tela. Dourado e vermelho aparecem só em CTAs, selos e destaques pontuais — nunca em blocos grandes de fundo.
2. **Hierarquia de marquise.** Títulos grandes usam Bebas Neue, lembrando letreiro de cinema. O corpo do texto fica em Inter, discreto, para não competir com pôsteres nem títulos.
3. **Um selo, uma jornada.** Cada plano (e o papel Admin) tem uma cor fixa amarrada ao filme que o nomeia. Essa cor nunca é reaproveitada em outro contexto — o dourado do plano Capitão Hanks, por exemplo, não vira um aviso genérico do sistema.

---

## 2. Cor

Paleta de "sala escura": carvão e marrom-café nas superfícies, dourado como acento de marca, vermelho como acento secundário (ação/urgência/exclusividade), e cinco cores adicionais — uma por selo de plano/papel.

Contraste de texto verificado sobre `surface-100`/`surface-200`: `ink` ≈ 17:1, `ink-muted` ≈ 9:1, `gold` ≈ 7,5:1 — todos acima do mínimo de 4.5:1 (WCAG AA). Os selos usam sempre a cor cheia do plano sobre o fundo `-soft` correspondente, nunca o inverso.

### 2.1 Superfícies e texto

| Token | Valor | Uso |
| --- | --- | --- |
| `surface-100` | `#100c0a` | Fundo da página; ambiente de sala de cinema escura |
| `surface-200` | `#1a1410` | Superfície de cards e painéis elevados |
| `surface-300` | `#251d17` | Hover e estados elevados sobre `surface-200` |
| `surface-400` | `#332822` | Inputs e controles em repouso |
| `border` | `#3d2f27` | Bordas de cards, divisores, contornos de controles |
| `border-strong` | `#5a4438` | Bordas em foco/hover e contornos de destaque |
| `ink` | `#f6ede1` | Texto principal sobre fundos escuros |
| `ink-muted` | `#b9a999` | Texto secundário: sinopses, metadados, legendas |
| `ink-faint` | `#8a7a6c` | Texto terciário: timestamps, contadores, placeholders |

### 2.2 Marca e estado

| Token | Valor | Uso |
| --- | --- | --- |
| `gold` | `#d1a441` | Cor de marca; CTAs primários, links ativos, ícones de destaque |
| `gold-hover` | `#e6bd5f` | Hover/active sobre elementos dourados |
| `gold-soft` | `#3a2c14` | Fundo suave para badges e destaques dourados |
| `red` | `#b6323a` | Cor secundária de marca; exclusividade e indicadores "ao vivo" |
| `red-hover` | `#cf3d46` | Hover/active sobre elementos vermelhos |
| `red-soft` | `#3a1416` | Fundo suave para badges e alertas vermelhos |
| `success` | `#4f9d6e` | Confirmações e acesso liberado |
| `warning` | `#d99a3d` | Avisos: limite de plano, aviso de expiração |
| `danger` | `#e5484d` | Erros e ações destrutivas (cancelar assinatura, remover perfil) |
| `focus-ring` | `#e6bd5f` (= `gold-hover`) | Anel de foco visível em todos os elementos interativos |

### 2.3 Selos de plano/papel (RBAC temático)

| Token | Valor | Selo | Filme de referência |
| --- | --- | --- | --- |
| `tier-wilson` / `tier-wilson-soft` | `#8f7a52` / `#241f16` | Amigo do Wilson | Náufrago (gratuito/básico) |
| `tier-terminal` / `tier-terminal-soft` | `#5c7f92` / `#14232a` | Preso no Terminal | O Terminal (intermediário) |
| `tier-apollo` / `tier-apollo-soft` | `#8fa0b3` / `#1b232b` | Houston, Temos Acesso | Apollo 13 (avançado) |
| `tier-phillips` / `tier-phillips-soft` | `#d1a441` (= `gold`) / `#3a2c14` (= `gold-soft`) | Capitão Hanks | Capitão Phillips (supremo) |
| `tier-admin` / `tier-admin-soft` | `#a480d6` / `#241a30` | Admin | — (acesso administrativo, exclusivo) |

### 2.4 Variáveis CSS (copiar direto no projeto)

```css
:root {
  /* Superfícies e texto */
  --surface-100: #100c0a;
  --surface-200: #1a1410;
  --surface-300: #251d17;
  --surface-400: #332822;
  --border: #3d2f27;
  --border-strong: #5a4438;
  --ink: #f6ede1;
  --ink-muted: #b9a999;
  --ink-faint: #8a7a6c;

  /* Marca e estado */
  --gold: #d1a441;
  --gold-hover: #e6bd5f;
  --gold-soft: #3a2c14;
  --red: #b6323a;
  --red-hover: #cf3d46;
  --red-soft: #3a1416;
  --success: #4f9d6e;
  --warning: #d99a3d;
  --danger: #e5484d;
  --focus-ring: var(--gold-hover);

  /* Selos de plano/papel */
  --tier-wilson: #8f7a52;
  --tier-wilson-soft: #241f16;
  --tier-terminal: #5c7f92;
  --tier-terminal-soft: #14232a;
  --tier-apollo: #8fa0b3;
  --tier-apollo-soft: #1b232b;
  --tier-phillips: var(--gold);
  --tier-phillips-soft: var(--gold-soft);
  --tier-admin: #a480d6;
  --tier-admin-soft: #241a30;

  /* Tipografia */
  --font-display: "Bebas Neue", "Arial Narrow", sans-serif;
  --font-sans: "Inter", system-ui, sans-serif;

  /* Espaçamento */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;

  /* Raio */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 18px;
  --radius-full: 999px;

  /* Sombra */
  --shadow-card: 0 8px 24px rgba(0, 0, 0, 0.45);
  --shadow-gold-glow: 0 0 0 1px rgba(209, 164, 65, 0.4), 0 8px 28px rgba(209, 164, 65, 0.25);
}
```

---

## 3. Tipografia

- **Display — Bebas Neue** (Google Fonts): nome da marca, títulos de seção, título do filme no pôster. Sempre em maiúsculas; nunca para parágrafos ou texto corrido.
- **Texto — Inter** (Google Fonts): interface, sinopses, formulários. `label` (caixa alta, peso 600) é reservado para botões e selos; `caption` para metadados pequenos como duração e ano.

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap">
```

| Estilo | Família | Tamanho | Altura de linha | Peso | Uso |
| --- | --- | --- | --- | --- | --- |
| `display-xl` | Display | 64px | 60px | 400 | Nome da marca e títulos hero |
| `display-lg` | Display | 40px | 40px | 400 | Títulos de seção e nome do plano em destaque |
| `display-md` | Display | 28px | 30px | 400 | Título do filme no pôster do card |
| `body-lg` | Texto | 18px | 28px | 400 | Sinopses longas e texto de destaque |
| `body` | Texto | 15px | 24px | 400 | Texto padrão de interface |
| `body-sm` | Texto | 13px | 20px | 400 | Texto secundário: metadados, sinopse curta em cards |
| `label` | Texto | 12px | 16px | 600 | Botões e selos, sempre em caixa alta |
| `caption` | Texto | 11px | 14px | 500 | Timestamps, contadores e legendas pequenas |

---

## 4. Espaçamento e forma

Grade de 4px, de `space-1` (4px) a `space-16` (64px). Cantos generosos e crescentes: `radius-sm` em controles pequenos, `radius-md` em botões, `radius-lg` em pôsteres e cards grandes, `radius-full` em selos e avatares. É uma vitrine de filmes, não um formulário — a forma reforça isso.

---

## 5. Componentes

### 5.1 Button

Ação clicável em quatro níveis de ênfase.

- **Primary (dourado)**: a única ação principal de uma tela — assistir, confirmar assinatura, avançar de plano.
- **Secondary**: ações de apoio — adicionar à lista, editar perfil.
- **Ghost**: ações terciárias e navegação leve — ver detalhes, fechar um modal.
- **Danger**: ações destrutivas — cancelar assinatura, remover perfil. Sempre exigir confirmação antes de executar.

Tokens: `gold`, `gold-hover`, `surface-100`, `ink`, `ink-muted`, `border-strong`, `danger`, `radius-md`, `space-3`, estilo `label`.

Diretrizes: nunca mais de um botão `primary` visível ao mesmo tempo; texto sempre em caixa alta, curto e direto (2–3 palavras); estado desabilitado usa opacidade 40%, nunca uma cor própria.

```css
.btn {
  border: none;
  cursor: pointer;
  border-radius: var(--radius-md);
  padding: 10px 20px;
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.4px;
  text-transform: uppercase;
}
.btn-primary { background: var(--gold); color: var(--surface-100); }
.btn-primary:hover { background: var(--gold-hover); }
.btn-secondary { background: transparent; color: var(--ink); border: 1px solid var(--border-strong); }
.btn-secondary:hover { border-color: var(--gold); color: var(--gold); }
.btn-ghost { background: transparent; color: var(--ink-muted); }
.btn-ghost:hover { color: var(--ink); }
.btn-danger { background: var(--danger); color: #1a0505; }
.btn[disabled] { opacity: 0.4; cursor: not-allowed; }
```

### 5.2 TierBadge

Selo compacto que identifica o plano de assinatura ou o papel do usuário.

Diretrizes: sempre o ponto (`dot`) + o nome do plano em `label` — a cor nunca aparece sozinha, sem texto; um usuário exibe um único selo de plano por vez (`Admin` pode aparecer ao lado quando a conta também tem papel administrativo); fundo sempre no token `-soft` correspondente, nunca a cor cheia.

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px 6px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.dot { width: 8px; height: 8px; border-radius: 999px; flex: none; }

.badge.wilson   { background: var(--tier-wilson-soft);   color: var(--tier-wilson); }
.badge.terminal { background: var(--tier-terminal-soft); color: var(--tier-terminal); }
.badge.apollo   { background: var(--tier-apollo-soft);   color: var(--tier-apollo); }
.badge.phillips { background: var(--tier-phillips-soft); color: var(--tier-phillips); }
.badge.admin    { background: var(--tier-admin-soft);    color: var(--tier-admin); }
.badge .dot { background: currentColor; }
```

### 5.3 MovieCard

Card de pôster usado nas prateleiras do catálogo e na página de detalhes.

- **Anatomia**: pôster com imagem de fundo (troque por arte real do filme) e título em `display-md`; corpo com ano/gênero, selo de nível de acesso (reaproveitado do TierBadge) e sinopse curta em `body-sm`.
- **Padrão**: borda `border`, sombra `shadow-card`.
- **Em destaque** (ex.: filme exclusivo do plano Capitão Hanks): borda `gold` e sombra `shadow-gold-glow`.

Diretrizes: selo de nível sempre com as mesmas cores do TierBadge; sinopse limitada a duas linhas (truncar com reticências); no máximo um card "em destaque" por fileira.

```css
.card {
  width: 220px;
  background: var(--surface-200);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.card.featured { border-color: var(--gold); box-shadow: var(--shadow-gold-glow); }
.card .poster {
  height: 280px;
  background: linear-gradient(160deg, var(--surface-400), var(--surface-300));
  display: flex;
  align-items: flex-end;
  padding: 12px;
}
.card .poster .title {
  font-family: var(--font-display);
  color: var(--ink);
  font-size: 28px;
  line-height: 0.95;
}
.card .body { padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.card .synopsis { color: var(--ink-muted); font-size: 13px; line-height: 20px; }
```

---

## 6. Planos e papéis (RBAC temático)

| Selo | Filme de referência | Nível de acesso |
| --- | --- | --- |
| Amigo do Wilson | Náufrago | Gratuito / básico |
| Preso no Terminal | O Terminal | Intermediário |
| Houston, Temos Acesso | Apollo 13 | Avançado |
| Capitão Hanks | Capitão Phillips | Supremo |
| Admin | — | Acesso administrativo, exclusivo |

---

## 7. Ícones e logotipo

Nenhum ícone ou logotipo foi fornecido ainda. Por enquanto a marca se apoia só na tipografia (o nome "HANKS+" em Bebas Neue) e na paleta de cor. Adicione uma marca própria (wordmark ou símbolo) antes de publicar o produto para fora do círculo pessoal.
