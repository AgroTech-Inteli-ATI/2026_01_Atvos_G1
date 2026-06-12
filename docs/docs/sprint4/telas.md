---
title: "Telas da Aplicação"
sidebar_position: 2
---

# Telas da Aplicação — Sprint 4

**Sprint:** 4  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Estrutura de Navegação

A aplicação tem três telas acessíveis pela navbar superior. A URL muda com cada tela via hash, permitindo compartilhamento de links e uso dos botões de navegação do navegador.

| Tela | Hash | Sidebar | Endpoint principal |
|------|------|---------|-------------------|
| Dashboard | `#dashboard` | Sim | `GET /api/data` |
| Talhões | `#talhoes` | Sim | `GET /api/talhoes` |
| Relatórios | `#relatorios` | Não | `GET /api/relatorio` |

---

## 2. Dashboard

Tela inicial carregada automaticamente ao abrir `http://localhost:8000`.

### 2.1 Cartões KPI

Quatro cartões no topo da tela, alimentados por `GET /api/stats`:

| Cartão | Campo da API | Descrição |
|--------|-------------|-----------|
| Total de talhões | `total_talhoes` | Talhões únicos no Gold |
| Urgentes | `urgent` | Registros com status `urgent` |
| Atenção | `attention` | Registros com SEM_DADO ou atenção |
| Processos | `processos.length` | Quantidade de processos cobertos |

Cada cartão tem um ícone circular colorido e um subtexto descritivo.

### 2.2 Tabela de Orientações

Exibe os registros da camada Gold com paginação de 20 por página.

**Colunas:**

| Coluna | Descrição |
|--------|-----------|
| ID Talhão | `id_talhao` — identificador único |
| Unidade | Sigla da unidade industrial (UMV, URC, etc.) |
| Processo | Nome do processo agronômico |
| Orientação | Texto descritivo da recomendação |
| Insumo | Nome do insumo quando aplicável |
| Dose (kg/ha) | Dose calculada quando aplicável |
| Status | Badge colorido com o status classificado |

A coluna de status usa badges visuais:

```
■ Urgente    — fundo vermelho claro, texto vermelho escuro
■ Atenção    — fundo âmbar claro, texto âmbar escuro
■ Monitorar  — fundo azul claro, texto azul escuro
■ OK         — fundo verde claro, texto verde escuro
```

### 2.3 Filtros (Sidebar)

| Filtro | Tipo | Valores |
|--------|------|---------|
| Unidade | Select | Todas + lista das 8 unidades da API |
| Processo | Select | Todos + 7 processos |
| Status | Select | Todos / Urgente / Atenção / Monitorar / OK |
| Busca | Input texto | Busca em todos os campos de texto |

O botão "Aplicar filtros" dispara a requisição. O botão "Limpar" restaura todos os filtros para o padrão.

Os filtros ativos são exibidos como chips abaixo do título da tela, com botão de remoção individual em cada chip.

### 2.4 Exportação CSV

O botão "Exportar CSV" chama `GET /api/export` com os filtros ativos e inicia o download do arquivo diretamente. O CSV exportado respeita todos os filtros selecionados na sidebar.

### 2.5 Paginação

Exibida abaixo da tabela com botões de página anterior, próxima e indicador "Página X de Y". O total de registros filtrados é exibido como "Mostrando X–Y de Z registros".

---

## 3. Talhões

Tela com visão consolidada por talhão — uma linha por `id_talhao`, independente da quantidade de processos avaliados.

### 3.1 Tabela de Talhões

**Colunas:**

| Coluna | Descrição |
|--------|-----------|
| ID Talhão | Identificador único |
| Chave | Chave legível (formato NUM-SETOR-TALHAO) |
| Unidade | Sigla da unidade industrial |
| Safra | Código da safra |
| Status Geral | Pior status dentre todos os processos do talhão |
| Alertas | Pills coloridas com os processos em alerta |
| Ações | Botão "Ver processos" |

Os alertas são exibidos como pills horizontais com cor correspondente ao status de cada processo. Se um talhão tiver muitos alertas, os pills ficam em wrap.

### 3.2 Modal de Detalhes do Talhão

O botão "Ver processos" abre um modal com:

- **Cabeçalho:** ID do talhão, unidade e safra
- **Lista de processos:** uma entrada por processo com:
  - Nome do processo (legível, ex: "Calagem")
  - Badge de status
  - Texto da orientação
  - Regra acionada
  - Insumo e dose (quando presentes)

Os dados do modal são carregados sob demanda via `GET /api/talhao?id=...`.

### 3.3 Filtros (Sidebar)

| Filtro | Tipo | Valores |
|--------|------|---------|
| Unidade | Select | Todas + lista das 8 unidades |
| Status Geral | Select | Todos / Urgente / Atenção / Monitorar / OK |
| Busca | Input texto | Busca em `id_talhao`, `chave` e `unidade` |

Os dados da tela de Talhões são carregados apenas na primeira visita (lazy-load). Visitas subsequentes reutilizam o estado.

---

## 4. Relatórios

Tela analítica sem sidebar, com três tabelas de resumo. Os dados são carregados via `GET /api/relatorio` na primeira visita.

Durante o carregamento, um spinner animado é exibido no centro da tela.

### 4.1 Distribuição por Processo

Tabela com uma linha por processo agronômico. Indica quantos registros estão em cada status e quantos retornam SEM_DADO por falta de dados de solo.

**Colunas:** Processo / Total / Urgente / Atenção / Monitorar / OK / Sem Dado

Os valores de contagem são coloridos de acordo com o status correspondente.

### 4.2 Distribuição por Unidade

Tabela com uma linha por unidade industrial. A coluna "Talhões" conta talhões únicos (não registros totais).

**Colunas:** Unidade / Talhões / Urgente / Atenção / Monitorar / OK

### 4.3 Top 15 Regras Acionadas

Tabela com as 15 regras mais frequentes em todo o Gold. Cada linha tem uma mini-barra de proporção visual.

**Colunas:** Regra / Total / % / Barra

A barra é uma `<div>` com largura proporcional à porcentagem, renderizada em CSS puro:

```css
.mini-bar-wrap { width: 120px; background: #e5e7eb; border-radius: 4px; }
.mini-bar      { height: 8px; background: #16a34a; border-radius: 4px; }
```

---

## 5. Componentes Globais

### 5.1 Modal

Um único elemento `<div id="modal">` é reutilizado para todos os modais da aplicação. O conteúdo é gerado dinamicamente em JavaScript a cada abertura. O modal fecha ao clicar no botão X ou ao clicar fora da área de conteúdo.

### 5.2 Toast de Notificação

O elemento `<div id="toast">` exibe mensagens temporárias (3 segundos) para confirmar ações como exportação CSV. O toast usa `opacity` e `transition` CSS para aparecer e desaparecer suavemente.

### 5.3 Indicador de Modo Demo

Quando a API está offline, um badge âmbar aparece na navbar com o texto "MODO DEMONSTRAÇÃO". Todos os dados exibidos passam a vir dos objetos `DEMO_RECS`, `DEMO_TALHOES` e `DEMO_RELATORIO` definidos em `script.js`.
