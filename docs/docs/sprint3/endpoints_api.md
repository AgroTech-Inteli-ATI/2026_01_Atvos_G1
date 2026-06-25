---
title: "Endpoints da API"
sidebar_position: 2
---

# Endpoints da API REST — Sprint 3

**Sprint:** 3  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

> Todos os endpoints aceitam CORS (`Access-Control-Allow-Origin: *`) e retornam JSON em UTF-8. O servidor responde às requisições OPTIONS automaticamente para suportar preflight.

---

## Resumo dos Endpoints

| Método | Caminho | Descrição |
|--------|---------|-----------|
| `GET` | `/api/stats` | Indicadores globais para os KPIs do dashboard |
| `GET` | `/api/data` | Orientações paginadas com filtros |
| `GET` | `/api/export` | Download do CSV filtrado |
| `GET` | `/api/talhoes` | Talhões agregados com filtros e paginação |
| `GET` | `/api/talhao` | Todos os processos de um talhão específico |
| `GET` | `/api/relatorio` | Resumos analíticos por processo, unidade e regras |
| `GET` | `/` | Serve `frontend/index.html` |
| `GET` | `/styles.css` | Serve `frontend/styles.css` |
| `GET` | `/script.js` | Serve `frontend/script.js` |

---

## GET /api/stats

Retorna os indicadores globais calculados na inicialização. Usado pelos cartões KPI do dashboard.

**Sem parâmetros.**

**Resposta:**

```json
{
  "total_registros": 471982,
  "total_talhoes": 67426,
  "urgent": 3241,
  "attention": 198540,
  "monitor": 89301,
  "ok": 180900,
  "unidades": ["UAE", "UAT", "UCP", "UCR", "UEL", "UMV", "URC", "USL"],
  "processos": ["calagem", "dessecacao", "erradicacao", "fosfatagem",
                "fosfatagem_insumo", "gessagem", "janela_plantio"],
  "carregado_em": "11/06/2026 14:32"
}
```

---

## GET /api/data

Retorna as orientações paginadas com suporte a filtros. Usado pela tabela do dashboard.

**Parâmetros de query:**

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `unit` | `all` | Filtra pela unidade industrial (ex: `UMV`) |
| `processo` | `all` | Filtra pelo processo agronômico (ex: `calagem`) |
| `status` | `all` | Filtra pelo status calculado (`urgent`, `attention`, `monitor`, `ok`) |
| `search` | `""` | Busca textual em `id_talhao`, `chave`, `unidade`, `processo`, `orientacao`, `regra_acionada`, `insumo` |
| `page` | `1` | Página atual (base 1) |
| `per_page` | `20` | Registros por página (máximo: 500) |

**Resposta:**

```json
{
  "records": [
    {
      "id_talhao": "410149",
      "chave": "410149-1-8",
      "unidade": "UMV",
      "safra": "22223",
      "processo": "erradicacao",
      "orientacao": "ERRADICAÇÃO RECOMENDADA: TCH=42.1 t/ha, 6° corte",
      "regra_acionada": "tardio_tch_critico",
      "insumo": "",
      "dose_kg_ha": "",
      "quantidade_total_kg": "",
      "data_geracao": "2026-06-11",
      "status": "urgent"
    }
  ],
  "total": 3241,
  "page": 1,
  "per_page": 20,
  "total_pages": 163
}
```

---

## GET /api/export

Retorna um arquivo CSV com os mesmos filtros de `/api/data`, sem paginação. O nome do arquivo inclui a data atual.

**Parâmetros de query:** os mesmos de `/api/data` (`unit`, `processo`, `status`, `search`). Os parâmetros `page` e `per_page` são ignorados.

**Cabeçalhos da resposta:**

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="orientacoes_atvos_2026-06-11.csv"
```

O CSV inclui um BOM UTF-8 (`﻿`) para compatibilidade com Excel no Windows.

**Colunas do CSV:**

```
id_talhao, chave, unidade, safra, processo, orientacao,
regra_acionada, insumo, dose_kg_ha, quantidade_total_kg,
data_geracao, status
```

---

## GET /api/talhoes

Retorna os talhões agregados com paginação. Cada registro representa um talhão com o pior status entre todos os seus processos.

**Parâmetros de query:**

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `unit` | `all` | Filtra pela unidade industrial |
| `status` | `all` | Filtra pelo `status_geral` do talhão |
| `search` | `""` | Busca em `id_talhao`, `chave` e `unidade` |
| `page` | `1` | Página atual |
| `per_page` | `20` | Registros por página (máximo: 500) |

**Resposta:**

```json
{
  "records": [
    {
      "id_talhao": "410149",
      "chave": "410149-1-8",
      "unidade": "UMV",
      "safra": "22223",
      "status_geral": "urgent",
      "alertas": ["erradicacao", "calagem"],
      "total_alertas": 3
    }
  ],
  "total": 67426,
  "page": 1,
  "per_page": 20,
  "total_pages": 3372
}
```

---

## GET /api/talhao

Retorna todos os registros de processos de um único talhão, buscados em O(1) via `_INDEX`.

**Parâmetros de query:**

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `id` | Sim | O `id_talhao` exato (ex: `410149`) |

**Resposta:**

```json
{
  "records": [
    {
      "id_talhao": "410149",
      "chave": "410149-1-8",
      "unidade": "UMV",
      "safra": "22223",
      "processo": "erradicacao",
      "orientacao": "ERRADICAÇÃO RECOMENDADA: ...",
      "regra_acionada": "tardio_tch_critico",
      "insumo": "",
      "dose_kg_ha": "",
      "quantidade_total_kg": "",
      "data_geracao": "2026-06-11",
      "status": "urgent"
    },
    {
      "processo": "calagem",
      "orientacao": "SEM_DADO",
      "regra_acionada": "dado_ausente_ph_solo",
      "status": "attention"
    }
  ]
}
```

Se o `id` não existir no índice, retorna `{"records": []}`.

---

## GET /api/relatorio

Retorna os dados analíticos pré-computados para a tela de Relatórios. Contém três seções.

**Sem parâmetros.**

**Resposta:**

```json
{
  "por_processo": [
    {
      "processo": "calagem",
      "label": "Calagem",
      "total": 67426,
      "urgent": 0,
      "attention": 67200,
      "monitor": 0,
      "ok": 226,
      "sem_dado": 67200
    }
  ],
  "por_unidade": [
    {
      "unidade": "UMV",
      "total_talhoes": 12430,
      "urgent": 541,
      "attention": 8200,
      "monitor": 1830,
      "ok": 1859
    }
  ],
  "top_regras": [
    {
      "regra": "dado_ausente_ph_solo",
      "total": 67200,
      "pct": 14.2
    }
  ]
}
```

**Detalhes de cada seção:**

| Seção | Conteúdo |
|---|---|
| `por_processo` | Uma entrada por processo; o campo `sem_dado` conta registros cuja `regra_acionada` começa com `dado_ausente` |
| `por_unidade` | Uma entrada por unidade; `total_talhoes` é a contagem de `id_talhao` distintos |
| `top_regras` | As 15 regras mais acionadas em todo o Gold; `pct` é relativo ao total de registros |

---

## Paginação

A paginação é consistente em todos os endpoints que a suportam:

```
page     = max(1, int(page_param))
per_page = min(500, max(1, int(per_page_param)))
pages    = ceil(total / per_page)
page     = min(page, pages)   # evita página além do fim
```

Se o total de registros filtrados for zero, `total_pages` retorna `1` e `records` retorna `[]`.

---

## Códigos de Status HTTP

| Código | Situação |
|--------|---------|
| `200` | Requisição bem-sucedida |
| `204` | OPTIONS preflight (sem corpo) |
| `404` | Arquivo estático não encontrado |
| `500` | Exceção não tratada no servidor (detalhes no JSON de resposta) |
