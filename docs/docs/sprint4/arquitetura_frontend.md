---
title: "Arquitetura do Frontend"
sidebar_position: 1
---

# Arquitetura do Frontend — Sprint 4

**Sprint:** 4  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Visão Geral

O frontend é uma SPA (Single Page Application) implementada em HTML, CSS e JavaScript puro, sem frameworks. A navegação entre as três telas é feita via hash de URL, sem nenhuma recarga de página.

```
frontend/
├── index.html    ← estrutura HTML das três telas + componentes reutilizáveis
├── styles.css    ← design system e layout responsivo
└── script.js     ← roteamento, filtros, paginação, modais e chamadas à API
```

Os três arquivos são servidos como estáticos pelo mesmo servidor Python que hospeda a API (`src/api/server.py`).

---

## 2. Roteamento por Hash

A navegação usa `window.location.hash` para identificar a tela ativa. Isso permite que o usuário use os botões de voltar/avançar do navegador e compartilhe URLs com tela específica já aberta.

```javascript
const VIEWS = ["dashboard", "talhoes", "relatorios"];
const VIEWS_WITH_SIDEBAR = ["dashboard", "talhoes"];

function navigate(view) {
  // 1. Atualiza link ativo na navbar
  document.querySelectorAll(".nav-link").forEach(a => {
    a.classList.toggle("active", a.dataset.view === view);
  });

  // 2. Alterna visibilidade das views
  VIEWS.forEach(v => {
    document.getElementById("view-" + v).hidden = (v !== view);
  });

  // 3. Alterna painel da sidebar
  ["dashboard", "talhoes"].forEach(v => {
    document.getElementById("sidebar-" + v).hidden = (v !== view);
  });

  // 4. Sidebar: visível no Dashboard e Talhões, oculta em Relatórios
  document.getElementById("layout").classList.toggle(
    "no-sidebar", !VIEWS_WITH_SIDEBAR.includes(view)
  );

  // 5. Lazy-load: carrega dados apenas na primeira visita a cada tela
  if (view === "talhoes" && !talhoesState.loaded) loadTalhoes();
  if (view === "relatorios" && !relatorioLoaded)  loadRelatorio();

  currentView = view;
  window.location.hash = view;
}

window.addEventListener("hashchange", () => navigate(location.hash.slice(1) || "dashboard"));
navigate(location.hash.slice(1) || "dashboard");   // inicialização
```

---

## 3. Estrutura HTML

O layout é dividido em três regiões principais:

```html
<nav class="navbar">              <!-- barra de navegação fixa -->
<div class="layout" id="layout"> <!-- container flex: sidebar + main -->
  <aside class="sidebar">
    <div id="sidebar-dashboard">  <!-- filtros da tela Dashboard -->
    <div id="sidebar-talhoes">    <!-- filtros da tela Talhões -->
  </aside>
  <main class="main-content">
    <div id="view-dashboard">     <!-- KPIs + tabela de orientações -->
    <div id="view-talhoes">       <!-- tabela de talhões consolidados -->
    <div id="view-relatorios">    <!-- três tabelas analíticas -->
  </main>
</div>
<div id="modal">                  <!-- modal de detalhes do talhão -->
<div id="toast">                  <!-- notificação temporária -->
```

A classe `.no-sidebar` no `#layout` remove a sidebar e expande o `main-content` para largura total, usada na tela de Relatórios.

---

## 4. Estado da Aplicação

Cada tela tem um objeto de estado independente:

```javascript
const dashState = {
  page: 1,
  total: 0,
  total_pages: 1,
  filters: { unit: "all", processo: "all", status: "all", search: "" }
};

const talhoesState = {
  page: 1,
  total: 0,
  total_pages: 1,
  filters: { unit: "all", status: "all", search: "" },
  loaded: false      // flag de lazy-load
};

let relatorioLoaded = false;   // flag de lazy-load
```

Os filtros são aplicados no servidor (parâmetros de query na chamada à API). O estado local armazena apenas a página atual e os valores de filtro selecionados.

---

## 5. Ciclo de Atualização (Dashboard)

```
Usuário clica em "Aplicar filtros"
     │
     ├── dashState.page = 1
     ├── dashState.filters = { valores dos selects/input }
     └── refreshDash()
           │
           ├── fetch("/api/data?unit=...&processo=...&status=...&search=...&page=1&per_page=20")
           │     ├── Sucesso → renderTable(data.records)
           │     │            renderPagination(data.total_pages)
           │     │            renderChips(dashState.filters)
           │     └── Falha (API offline) → isDemo = true
           │                               renderTable(demoPage(demoFilter(DEMO_RECS)))
           │
           └── fetch("/api/stats")
                 ├── Sucesso → renderKPIs(data)
                 └── Falha   → renderKPIs(DEMO_STATS)
```

---

## 6. Modo de Demonstração

O frontend detecta automaticamente quando a API está indisponível usando `AbortSignal.timeout()`. Quando a primeira requisição falha, a variável global `isDemo` é definida como `true` e todas as chamadas subsequentes usam os dados locais.

```javascript
let isDemo = false;

async function apiFetch(url) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(res.status);
    return await res.json();
  } catch {
    isDemo = true;
    return null;
  }
}
```

Os dados de demonstração (`DEMO_RECS`, `DEMO_TALHOES`, `DEMO_RELATORIO`) são objetos JavaScript definidos no início de `script.js` com 10 registros representativos cobrindo todos os status e processos.

Um banner amarelo é exibido na navbar quando `isDemo === true`:

```html
<span id="navbar-safra" class="demo-badge">MODO DEMONSTRAÇÃO</span>
```

---

## 7. Segurança — HTML Escaping

Todos os valores de dados inseridos no DOM passam pela função `esc()` para prevenir XSS:

```javascript
function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
```

Nenhum dado da API é inserido via `innerHTML` sem passar por `esc()`.

---

## 8. Dependências

O frontend não possui dependências externas. Nenhum `npm`, `node_modules` ou CDN é necessário. O arquivo `index.html` não carrega nenhum script ou estilo externo.

| Recurso | Abordagem |
|---|---|
| Ícones | Caracteres Unicode e CSS puro |
| Fontes | Fonte do sistema (`system-ui, -apple-system, sans-serif`) |
| Gráficos | Mini-barras proporcionais via CSS (`.mini-bar`) |
| Animações | CSS `@keyframes` puro |
| Modais | Elemento `<div>` posicionado por CSS |
