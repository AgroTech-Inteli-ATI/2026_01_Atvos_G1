---
title: "Arquitetura da API"
sidebar_position: 1
---

# Servidor HTTP e Arquitetura da API — Sprint 3

**Sprint:** 3  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Visão Geral

A Sprint 3 entregou o servidor HTTP que expõe os dados da camada Gold para o frontend. O servidor foi implementado usando apenas a biblioteca padrão do Python (`http.server`), sem dependências externas adicionais.

```
data/gold/orientacoes_YYYY-MM-DD.csv
     ↓  src/api/server.py  (inicialização)
Pré-cômputo de agregados na memória
     ↓  http://localhost:8000
frontend/ (Dashboard · Talhões · Relatórios)
```

O servidor carrega todos os 471.982 registros na inicialização e pré-computa as estruturas de dados necessárias para cada tipo de consulta. As requisições subsequentes são servidas a partir da memória sem nenhuma I/O adicional.

---

## 2. Estrutura de Arquivos

```
src/
└── api/
    └── server.py     ← servidor completo (único arquivo)

frontend/
├── index.html        ← SPA servida como arquivo estático
├── styles.css        ← estilos servidos como arquivo estático
└── script.js         ← lógica do cliente servida como arquivo estático
```

O servidor serve os arquivos estáticos do frontend na raiz (`/`) e expõe os endpoints da API sob o prefixo `/api/`.

---

## 3. Estruturas de Dados em Memória

Na inicialização, cinco estruturas globais são preenchidas a partir do CSV Gold mais recente:

| Variável | Tipo | Descrição |
|---|---|---|
| `_RECORDS` | `list[dict]` | Todos os 471.982 registros flat com campo `status` calculado |
| `_META` | `dict` | Agregados globais: totais por status, listas de unidades e processos |
| `_TALHOES` | `list[dict]` | 67.426 talhões com pior status e lista de processos em alerta |
| `_RELATORIO` | `dict` | Distribuição por processo, por unidade e top 15 regras acionadas |
| `_INDEX` | `dict[str, list]` | Índice `id_talhao → [records]` para busca O(1) por talhão |

### 3.1 Campos de cada registro (`_RECORDS`)

| Campo | Tipo | Origem |
|---|---|---|
| `id_talhao` | str | Coluna `id_talhao` do CSV Gold |
| `chave` | str | Coluna `chave` |
| `unidade` | str | Coluna `unidade` |
| `safra` | str | Coluna `safra` |
| `processo` | str | Coluna `processo` |
| `orientacao` | str | Coluna `orientacao` |
| `regra_acionada` | str | Coluna `regra_acionada` |
| `insumo` | str | Coluna `insumo` (vazio quando não aplicável) |
| `dose_kg_ha` | str | Coluna `dose_kg_ha` (vazio quando não aplicável) |
| `quantidade_total_kg` | str | Coluna `quantidade_total_kg` |
| `data_geracao` | str | Coluna `data_geracao` |
| `status` | str | **Calculado**: `urgent` / `attention` / `monitor` / `ok` |

### 3.2 Classificação de status

A função `_classify(row)` determina o status de cada registro com a seguinte lógica:

```python
def _classify(row: dict) -> str:
    regra = row.get("regra_acionada", "")
    ori   = row.get("orientacao", "").upper()
    if "dado_ausente" in regra or "SEM_DADO" in ori:
        return "attention"
    if "ERRADICACAO" in ori and "RECOMENDADA" in ori:
        return "urgent"
    if "MONITORAR" in ori or "monitorar" in regra:
        return "monitor"
    return "ok"
```

| Status | Cor | Condição |
|---|---|---|
| `urgent` | Vermelho | Orientação contém "ERRADICACAO RECOMENDADA" |
| `attention` | Âmbar | Regra contém "dado_ausente" ou orientação contém "SEM_DADO" |
| `monitor` | Azul | Orientação ou regra contém "MONITORAR" |
| `ok` | Verde | Todos os outros casos |

### 3.3 Estrutura de talhão (`_TALHOES`)

```python
{
    "id_talhao":     "410149",
    "chave":         "410149-1-8",
    "unidade":       "UMV",
    "safra":         "22223",
    "status_geral":  "urgent",      # pior status dentre todos os processos
    "alertas":       ["erradicacao", "calagem"],  # processos não-ok, sem duplicatas
    "total_alertas": 5              # total de registros não-ok
}
```

O `status_geral` é determinado pelo status de maior prioridade entre todos os processos do talhão, segundo a ordem `urgent > attention > monitor > ok`.

---

## 4. Fluxo de Inicialização

```
python src/api/server.py
     │
     ├── 1. Localiza CSV Gold mais recente em data/gold/orientacoes_*.csv
     ├── 2. Lê todos os registros com csv.DictReader (UTF-8 BOM)
     ├── 3. Calcula _classify() para cada registro → campo "status"
     ├── 4. _compute_meta() → contagens por status, listas de unidades/processos
     ├── 5. _compute_talhoes() → agrupa por id_talhao, define status_geral
     ├── 6. _compute_relatorio() → Counter por processo, unidade e regra
     ├── 7. _compute_index() → dict id_talhao → [records]
     └── 8. HTTPServer.serve_forever() em localhost:PORT
```

O carregamento dos 471 mil registros leva entre 3 e 8 segundos na primeira requisição, dependendo do disco. Após esse passo, todas as consultas são servidas a partir da memória.

---

## 5. Tratamento de Erros

| Situação | Comportamento |
|---|---|
| Nenhum CSV em `data/gold/` | Levanta `FileNotFoundError` com instrução de execução do pipeline |
| Exceção em qualquer endpoint | Retorna JSON `{"error": "mensagem"}` com HTTP 500 e imprime traceback no terminal |
| Arquivo estático não encontrado | Retorna JSON `{"error": "not found"}` com HTTP 404 |
| Parâmetro de paginação inválido | `int()` com fallback: valores negativos são ajustados para 1, valores acima do máximo são truncados |

---

## 6. Como Executar

```bash
# Na raiz do projeto, com o ambiente virtual ativado:
python src/api/server.py

# Porta alternativa:
python src/api/server.py 5000
```

O servidor muda o diretório de trabalho para a raiz do projeto automaticamente via `os.chdir()`, portanto pode ser executado de qualquer diretório.

### Pré-requisito

O arquivo Gold precisa existir em `data/gold/`. Se ainda não foi gerado:

```bash
python src/processing/run_processing.py
python src/ingestion/extract_safra.py
python src/pipeline_gold.py
```

---

## 7. Decisões de Design

| Decisão | Motivo |
|---|---|
| `http.server` da stdlib em vez de Flask/FastAPI | Sem dependências externas; o projeto já tinha `requirements.txt` fechado |
| Pré-cômputo de todos os agregados na inicialização | Elimina latência por requisição; 471k registros cabem confortavelmente na RAM |
| CSV em vez de Parquet como fonte do servidor | O `csv.DictReader` é stdlib; leitura de Parquet exigiria pandas/pyarrow |
| Servir frontend como arquivos estáticos pelo mesmo servidor | Evita problemas de CORS em desenvolvimento local; única porta para abrir |
| `_INDEX` separado de `_TALHOES` | `_TALHOES` tem apenas o resumo por talhão; o detalhe por processo é buscado sob demanda em `_INDEX` |
