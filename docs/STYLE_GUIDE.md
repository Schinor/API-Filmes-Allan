# 🎬 Rota de Fuga — Guia de Estilo Visual

> Referência completa de design system para atualização do frontend.  
> Tema: **Arquivos Cinematográficos Vintage** — escuro, editorial, cinematográfico.

---

## 1. Identidade Visual

### Conceito
O site evoca **fichas técnicas de cinema clássico**, **bilhetes de passagem vintage** e **arquivos confidenciais**. A linguagem visual combina tipografia display expressiva (Bebas Neue) com serifa elegante (Fraunces) sobre fundo escuro quase-preto com detalhes em dourado/âmbar.

### Nome e Branding
```
ROTA DE FUGA          ← display, maiúsculas, tracking largo
CATÁLOGO TOM HANKS    ← subtitle, 0.65rem, accent color, tracking
```

---

## 2. Paleta de Cores (CSS Custom Properties)

### Cores Globais (`styles.css`)

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#0E120F` | Fundo principal (quase-preto esverdeado) |
| `--bg-panel` | `#171B16` | Painéis, cards, barras |
| `--bg-card` | `#171B16` | Cards de conteúdo |
| `--bg-modal` | `#1D221C` | Fundo de modais |
| `--paper` | `#EDE6D3` | Texto principal (creme envelhecido) |
| `--paper-muted` | `rgba(237,230,211,0.72)` | Texto secundário |
| `--paper-faint` | `rgba(237,230,211,0.12)` | Bordas finas, hover states |
| `--accent` | `#B08650` | Dourado âmbar — cor de ênfase padrão |
| `--accent-light` | `#C89F6B` | Dourado mais claro (hover) |
| `--accent-glow` | `rgba(176,134,80,0.25)` | Glow de botões primários |
| `--border` | `rgba(237,230,211,0.12)` | Bordas sutis |
| `--border-strong` | `rgba(237,230,211,0.24)` | Bordas mais visíveis |
| `--success` | `#46d369` | Verde de sucesso |
| `--primary` | `#e50914` | Vermelho Netflix (legado, evitar) |

### Acentos por Plano

| Token | Valor | Plano |
|---|---|---|
| `--accent-ilha` | `#C8965A` | Ilha (Náufrago) — laranja areia |
| `--accent-terminal` | `#8A9199` | Terminal — cinza azulado |
| `--accent-orbita` | `#5C8AA0` | Órbita — azul NASA |
| `--accent-capitao` | `#C9A227` | Capitão — dourado premium |

### Acentos por Role (Badges)

| Classe | Background | Uso |
|---|---|---|
| `.badge-admin` | `#e50914` (vermelho) | Admin |
| `.badge-capitao` | `#c9a227` (dourado) | Capitão Hanks |
| `.badge-houston` | `#3b82f6` (azul) | Houston, Temos Acesso |
| `.badge-terminal` | `#8b5cf6` (roxo) | Preso no Terminal |
| `.badge-wilson` | `#4b5563` (cinza) | Amigo do Wilson |

---

## 3. Tipografia

### Fontes

| Variável | Fonte | Fallback | Uso |
|---|---|---|---|
| `--font-display` | Bebas Neue | Impact, sans-serif | Títulos, badges, labels uppercase, CTAs |
| `--font-serif` | Fraunces | Georgia, serif | Subtítulos, citações, descrições, itálico |
| `--font` | Inter | -apple-system, sans-serif | Corpo de texto, inputs, elementos de UI |

### Escala Tipográfica

```css
/* Títulos principais (display) */
h1: clamp(3.2rem, 6.5vw, 5.2rem)  — letter-spacing: 2px, line-height: 0.92
h2: clamp(2.5rem, 5vw, 4rem)       — letter-spacing: 2px, text-transform: uppercase
h3: 2.2rem                          — letter-spacing: 1.5px (plano nos cards)

/* Kicker / Overline */
.kicker: font-display, 0.95rem, letter-spacing: 2px, cor: --accent

/* Corpo */
p grande: font-serif, 1.15rem, line-height: 1.65
p normal: 0.9rem, line-height: 1.5
p pequeno: 0.82rem, line-height: 1.45

/* Labels uppercase */
label: 0.65–0.88rem, letter-spacing: 1.5–2px, --paper-muted

/* Monospace (seriais, barcodes) */
serial: font mono, 0.68–0.75rem, --paper-muted ou --accent
```

---

## 4. Layout e Grid

### Container
```css
max-width: 1280px;
margin: 0 auto;
padding: 0 1.5rem;
```

### Grids Principais

| Contexto | Grid |
|---|---|
| Cards de planos | `repeat(4, 1fr)` → `repeat(2, 1fr)` (≤1024px) → `1fr` (≤640px) |
| Destaque assimétrico | `460px 1fr` → `1fr` (≤1024px) |
| Stats/Laurels | `repeat(4, 1fr)` → `repeat(2, 1fr)` → `1fr` |
| Footer links | `repeat(3, 1fr)` → `1fr` |

### Espaçamentos
```css
/* Seções */
padding: 5rem 1.5rem — seção padrão
padding: 6rem 1.5rem 7.5rem — seção de planos

/* Cards */
padding: 1.75rem 1.4rem — card padrão

/* Gaps */
gap: 1.5rem — cards em grid
gap: 1.25rem — itens internos de card
gap: 2.5rem — seções de destaque
```

---

## 5. Componentes

### 5.1 Navbar (Usuário Logado)

```
[🎬 Tom Hanks — Catálogo]  [Planos] [Catálogo] [⭐ Favoritos] [💬 Comentários]  [Nome] [BADGE] [Sair]
```

- `height: 60px`, `background: #0a0a0a`, `border-bottom: 1px solid #222`
- `position: sticky; top: 0; z-index: 100`
- Links: `#b3b3b3` → `#fff` no hover/active
- Botão Sair: border `#555`, hover → `#e50914`

### 5.2 Card de Plano (`.elenco-card`)

```
┌─ [accent bar 3px] ──────────────────┐
│ [BADGE ESSENCIAL]      #TH-2000-... │  ← header
│                                      │
│ PAPEL ATRIBUÍDO                      │  ← role block
│ "Chuck Noland as O Sobrevivente"     │
│ Náufrago (Cast Away, 2000)           │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ ILHA                                 │  ← price block
│ R$ 19,90 / mês                       │
│ Descrição curta...                   │
│                                      │
│ RECURSOS DO PASSE:                   │  ← features
│ ✦ Item 1                             │
│ ✦ Item 2                             │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ [        ASSINAR ILHA »            ] │  ← CTA button
└──────────────────────────────────────┘
```

**Estados:**
- Default: `border: 1px solid --border`, `background: --bg-panel`
- Hover: `border-color: --card-accent`, botão fica sólido na cor do plano
- Offset escalonado no desktop: cards alternados em `translateY(0/32/12/44px)`

### 5.3 Kicker Tag (Overline)

```html
<div class="kicker-tag">
  <span class="kicker-dot"></span>
  <span>TEXTO EM CAPS</span>
</div>
```

- Fonte display, 0.95rem, letter-spacing 2px, cor `--accent`
- Dot: 6px círculo, mesma cor, `box-shadow: 0 0 8px var(--accent)`

### 5.4 Botões

| Classe | Estilo | Uso |
|---|---|---|
| `.btn-hero-primary` | Fundo `--accent`, cor `--bg`, display font | CTA principal |
| `.btn-hero-secondary` | Transparente, border `--border-strong` | CTA secundário |
| `.btn-nav-primary` | Border `--accent`, cor `--accent`, fundo `--bg-panel` | Nav/header |
| `.btn-card-cta` | Transparente, largura total, hover → sólido accent do plano | Card de plano |
| `.btn-confirm-plan` | Fundo `--modal-accent`, largura total | Modal de confirmação |
| `.btn-logout` | Transparente, border `#555`, hover vermelho | Navbar |

**Padrão de botão:**
```css
font-family: --font-display;
letter-spacing: 1.5–2px;
text-transform: uppercase;
border-radius: 2–3px;
transition: all 0.2s ease;
```

### 5.5 Modal (Ticket)

```
┌─ SALVO-CONDUTO AUTORIZADO  #TH-... ─┐
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│ [BADGE]                              │
│ PLANO CAPITÃO                        │
│ "Miller & Phillips as O Comandante"  │
│ ┃ R$ 79,90 / mês                     │
│ Descrição do plano...                │
│ ┌────────────────────────────────┐   │
│ │ BENEFÍCIOS INCLUSOS:           │   │
│ │ ✦ Item                         │   │
│ └────────────────────────────────┘   │
│ [   CRIAR CONTA & ATIVAR CAPITÃO »  ]│
│   Garantia de 7 dias · Cancele...    │
└──────────────────────────────────────┘
```

- Overlay: `rgba(8,10,8,0.85)` com `backdrop-filter: blur(8px)`
- Ticket: `background: #171C17`, border 2px sólida na cor do plano
- `max-width: 520px`

### 5.6 Input Fields (Login/Forms)

```css
background: #141414;
border: 1px solid #333;
border-radius: 8px;
color: #fff;
padding: 0.75rem 1rem;
/* focus → border-color: --primary (#e50914) */
```

### 5.7 Alerts

```css
/* Error */
background: rgba(229,9,20,0.15);
color: #ff6b6b;
border: 1px solid rgba(229,9,20,0.3);

/* Success */
background: rgba(70,211,105,0.15);
color: #46d369;
border: 1px solid rgba(70,211,105,0.3);
```

### 5.8 Divisores e Ornamentos

```
✦   — ornamento de seção / item de lista (cor accent do contexto)
»   — seta de CTA (botões primários)
★   — estrela de destaque / mini-selo
←   — voltar
─ ─ — linha tracejada (separador interno de card/modal)
```

---

## 6. Inconsistências Atuais a Corrigir

> Estas são divergências identificadas que devem ser padronizadas na atualização.

### 6.1 Navbar — fundo diferente da paleta global
A navbar usa `background: #0a0a0a` hardcoded, em vez do token `--bg` (`#0E120F`) ou `--bg-panel`. Deve usar variável.

### 6.2 Login page — fora do sistema visual
A página de login usa um card `#1f1f1f` com bordas `border-radius: 12px` e gradiente `#1a0505` que não segue o estilo cinematográfico do resto do site. Deve ser refatorada para usar:
- `background: var(--bg)`
- Card com `var(--bg-panel)`, `border: 1px solid var(--border)`, `border-radius: 4px`
- Tipografia com `--font-display` nos títulos
- Botão com padrão do design system (sem `border-radius: 6px` arredondado)

### 6.3 Páginas internas (catálogo, favoritos, comentários) — sem estilo cinematográfico
As páginas internas usam estilos genéricos que não seguem o design system da landing. Devem adotar:
- Headers com `.kicker-tag` + título display
- Cards seguindo o padrão `--bg-panel` + `border: 1px solid --border`
- Botões com `--font-display` e `letter-spacing`

### 6.4 Navbar — estilo desconectado
A navbar usa `#0a0a0a` + `#e50914` (Netflix red) enquanto o design system usa `--bg` + `--accent` (dourado). Deve ser alinhada.

---

## 7. Padrões de Animação

```css
/* Entrada de elementos */
animation: heroEntrance 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards;
@keyframes heroEntrance {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Transições de hover */
transition: all 0.2s ease;
transition: border-color 0.25s ease, box-shadow 0.25s ease;

/* Modal */
@keyframes modalFadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

---

## 8. Responsividade

| Breakpoint | Comportamento |
|---|---|
| `> 1024px` | Layout completo, grid 4 colunas, offsets escalonados |
| `≤ 1024px` | Grid 2 colunas, layouts single-column |
| `≤ 640px` | Grid 1 coluna, nav simplificada, footer empilhado |

---

## 9. Roadmap de Atualização do Frontend

### Prioridade Alta
- [ ] **Navbar** — adotar `--bg` e `--accent` (dourado), remover `#e50914` do branding
- [ ] **Página de Login** — refatorar para design system cinematográfico
- [ ] **Catálogo** — header com kicker tag, search estilizado, spinner no estilo

### Prioridade Média
- [ ] **Favoritos** — header cinematográfico, cards de filme no estilo
- [ ] **Comentários** — header, formulário e lista no estilo
- [ ] **Movie Card** — bordas e hover alinhados ao design system
- [ ] **Movie Modal** — já parcialmente correto; padronizar botões internos

### Prioridade Baixa
- [ ] **Reset Password** — estilo consistente com login reformulado
- [ ] **Página 404** — criar página não encontrada no estilo

---

## 10. Checklist de Implementação por Componente

Ao atualizar um componente, verifique:

- [ ] Usa `var(--bg)` e `var(--bg-panel)` em vez de cores hardcoded
- [ ] Usa `var(--paper)` e `var(--paper-muted)` para texto
- [ ] Usa `var(--accent)` para destaques (não `#e50914`)
- [ ] Usa `var(--border)` e `var(--border-strong)` para bordas
- [ ] Títulos usam `font-family: var(--font-display)` com `text-transform: uppercase`
- [ ] `letter-spacing` presente em todos os textos display (mínimo 1.5px)
- [ ] `border-radius` é pequeno: `2–4px` (não `12px`)
- [ ] Botões usam `--font-display` e `letter-spacing: 1.5–2px`
- [ ] Hover transitions: `0.2s ease`
- [ ] Separadores usam `border: 1px solid var(--border)` ou `1px dashed var(--border)`
