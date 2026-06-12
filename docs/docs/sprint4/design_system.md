---
title: "Design System"
sidebar_position: 3
---

# Design System — Sprint 4

**Sprint:** 4  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

> O design foi adaptado a partir do sistema visual "Componentes Web — G04" (Figma), com paleta e componentes ajustados para a identidade da Atvos e ao contexto de monitoramento agronômico.

---

## 1. Tokens de Cor

Todas as cores são definidas como variáveis CSS em `:root`, permitindo alteração centralizada.

```css
:root {
  /* Primária — verde Atvos */
  --green:       #16a34a;
  --green-dark:  #15803d;
  --green-bg:    #dcfce7;
  --green-text:  #166534;

  /* Status urgente */
  --red:         #ef4444;
  --red-bg:      #fee2e2;
  --red-text:    #991b1b;

  /* Status atenção */
  --amber:       #f59e0b;
  --amber-bg:    #fef3c7;
  --amber-text:  #92400e;

  /* Status monitorar */
  --blue:        #3b82f6;
  --blue-bg:     #dbeafe;
  --blue-text:   #1d4ed8;

  /* Superfície e bordas */
  --bg:          #f9fafb;
  --surface:     #ffffff;
  --border:      #e5e7eb;
  --text:        #111827;
  --text-muted:  #6b7280;
}
```

---

## 2. Tipografia

A aplicação usa a fonte do sistema operacional para garantir a melhor legibilidade em cada plataforma sem carregamento externo:

```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
             Roboto, Oxygen, Ubuntu, sans-serif;
```

| Uso | Tamanho | Peso |
|-----|---------|------|
| Título de seção | `1.25rem` | 600 |
| Label de filtro | `0.875rem` | 500 |
| Célula de tabela | `0.875rem` | 400 |
| Texto auxiliar | `0.75rem` | 400 |
| Valor KPI | `2rem` | 700 |

---

## 3. Componentes

### 3.1 Navbar

Barra superior fixa com fundo branco e borda inferior sutil. Contém logotipo, links de navegação e indicador de safra/demo.

```
┌────────────────────────────────────────────────────┐
│  🌿 Monitor Agronomico    Dashboard  Talhões  Relatórios  │  Safra 2026
└────────────────────────────────────────────────────┘
```

O link ativo recebe `border-bottom: 2px solid var(--green)` e cor `var(--green)`.

### 3.2 Cartões KPI

Grade de quatro cartões com fundo branco, borda arredondada e sombra leve.

```
┌─────────────────────┐
│  ● 67.426           │
│  Total de Talhões   │
└─────────────────────┘
```

O círculo colorido é gerado em CSS com `border-radius: 50%` e cor correspondente ao tipo do indicador (verde para total, vermelho para urgentes, etc.).

```css
.kpi-card   { background: var(--surface); border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.kpi-icon   { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.kpi-value  { font-size: 2rem; font-weight: 700; }
.kpi-label  { font-size: .875rem; color: var(--text-muted); }
```

### 3.3 Badges de Status

Usados nas colunas de status das tabelas e nos pills de alerta na tela de Talhões.

```css
.badge          { padding: 2px 10px; border-radius: 9999px; font-size: .75rem; font-weight: 600; }
.badge-urgent   { background: var(--red-bg);   color: var(--red-text);   }
.badge-attention{ background: var(--amber-bg); color: var(--amber-text); }
.badge-monitor  { background: var(--blue-bg);  color: var(--blue-text);  }
.badge-ok       { background: var(--green-bg); color: var(--green-text); }
```

### 3.4 Pills de Alerta (Talhões)

Exibidos na coluna "Alertas" da tabela de talhões. Cada pill indica um processo com problema.

```css
.alert-pill      { padding: 2px 8px; border-radius: 9999px; font-size: .7rem; font-weight: 500; }
.pill-urgent     { background: var(--red-bg);   color: var(--red-text);   }
.pill-attention  { background: var(--amber-bg); color: var(--amber-text); }
.pill-monitor    { background: var(--blue-bg);  color: var(--blue-text);  }
```

### 3.5 Sidebar de Filtros

Painel lateral esquerdo com largura fixa de 260px, separado do conteúdo principal por uma borda direita.

```css
.sidebar        { width: 260px; border-right: 1px solid var(--border); padding: 1.5rem 1rem; }
.layout         { display: flex; gap: 0; }
.layout.no-sidebar .sidebar { display: none; }
.main-content   { flex: 1; min-width: 0; padding: 1.5rem; }
```

O botão "Aplicar filtros" usa a cor primária verde. O botão "Limpar" usa estilo outline.

### 3.6 Tabelas

Todas as tabelas seguem o mesmo padrão visual:

```css
.data-table           { width: 100%; border-collapse: collapse; }
.data-table th        { text-align: left; font-size: .75rem; font-weight: 600;
                        text-transform: uppercase; color: var(--text-muted);
                        padding: .75rem 1rem; border-bottom: 1px solid var(--border); }
.data-table td        { padding: .75rem 1rem; border-bottom: 1px solid var(--border);
                        font-size: .875rem; vertical-align: top; }
.data-table tr:hover  { background: #f9fafb; }
```

Células numéricas nos relatórios recebem `text-align: right` e cor correspondente ao status.

### 3.7 Modal

Overlay escurecido com cartão centralizado. Fecha ao clicar fora do cartão.

```css
.modal-overlay  { position: fixed; inset: 0; background: rgba(0,0,0,.4);
                  display: flex; align-items: center; justify-content: center; z-index: 50; }
.modal-card     { background: white; border-radius: 12px; width: min(700px, 95vw);
                  max-height: 85vh; overflow-y: auto; padding: 1.5rem; }
```

O cabeçalho do modal de talhão usa uma grade de três colunas para exibir ID, unidade e safra lado a lado.

### 3.8 Spinner de Carregamento

Usado na tela de Relatórios enquanto os dados são buscados:

```css
.spinner { width: 40px; height: 40px; border: 4px solid var(--border);
           border-top-color: var(--green); border-radius: 50%;
           animation: spin .8s linear infinite; }

@keyframes spin { to { transform: rotate(360deg); } }
```

---

## 4. Chips de Filtros Ativos

Os filtros aplicados são exibidos como chips removíveis abaixo do título da tela. Um chip aparece apenas quando o filtro tem valor diferente de "todos/vazio".

```
[ Unidade: UMV  ×  ]  [ Status: urgent  ×  ]
```

Clicar no `×` de um chip remove aquele filtro e reaplicar a consulta.

---

## 5. Layout Responsivo

O layout usa `flexbox` para a divisão sidebar/conteúdo. Em telas menores (abaixo de 768px), a sidebar colapsa automaticamente:

```css
@media (max-width: 768px) {
  .sidebar         { display: none; }
  .main-content    { padding: 1rem; }
  .kpi-grid        { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .kpi-grid        { grid-template-columns: 1fr; }
}
```

---

## 6. Adaptações do Figma Original

O design de referência era o sistema "Componentes Web — G04" (aplicativo SIAS de assistência social). As adaptações realizadas para o contexto agronômico foram:

| Elemento original | Adaptação |
|---|---|
| Paleta azul institucional | Verde primário `#16a34a` (identidade agrícola) |
| Cards de beneficiário | Cards de talhão com ID, chave e unidade |
| Status de atendimento | Status agronômico (urgent/attention/monitor/ok) |
| Tabela de histórico | Tabela de orientações por processo |
| Formulário de cadastro | Sidebar de filtros com selects e busca textual |
| Modal de perfil | Modal de processos do talhão com cards por processo |
