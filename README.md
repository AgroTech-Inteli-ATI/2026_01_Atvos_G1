# Agrotech 2026 — Atvos G1

Projeto de análise de dados agrícolas da Atvos — Sprint 1: ingestão e limpeza de dados.

---

## Estrutura do Projeto

```
.
├── data/
│   ├── raw/                  # Dados brutos — nunca alterar
│   │   ├── Correcao_talhoes_para_unificacao.xlsx
│   │   ├── Inventario_atvos_21_27_part_2.xlsx
│   │   └── Inventario_atvos_21_27_part_4.xlsx
│   └── processed/            # Dados Silver — gerados pelo pipeline
│       ├── Correcao_talhoes_para_unificacao_silver.parquet
│       ├── Inventario_atvos_21_27_part_2_silver.parquet
│       └── Inventario_atvos_21_27_part_4_silver.parquet
├── src/
│   ├── ingestion/
│   │   ├── load_files.py          # Funções utilitárias de leitura (CSV/Excel)
│   │   ├── run_ingestion.py       # Carrega todos os arquivos de data/raw/
│   │   └── extract_local.py      # Alternativa local ao BigQuery/GCS
│   └── processing/
│       ├── clean_data.py          # Pipeline Raw -> Silver (funções + CLI)
│       └── run_processing.py     # Executa limpeza em todos os arquivos
├── docs/
│   ├── regras_limpeza.md         # Regras de limpeza aprovadas (Task 1.4)
│   ├── mapeamento_fontes.md      # Mapeamento das fontes de dados (Task 1.2)
│   └── dicionario_dados.md       # Dicionário de dados Silver (Task 1.6)
├── requirements.txt
└── venv/
```

---

## Como Executar

### 1. Ativar o ambiente virtual

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Ingestão (Raw)

Carrega todos os arquivos de `data/raw/` e exibe um log de leitura:

```bash
python src/ingestion/run_ingestion.py
```

### 4. Limpeza (Raw → Silver)

Processa todos os arquivos e salva Parquets em `data/processed/`:

```bash
python src/processing/run_processing.py
```

Para processar um único arquivo:

```bash
python src/processing/clean_data.py Inventario_atvos_21_27_part_2.xlsx
```

---

## Pipeline de Dados

```
data/raw/  (Excel)
    │
    ├─ src/ingestion/extract_local.py    ← lê arquivos com logging
    │
    ▼
src/processing/clean_data.py             ← aplica as regras abaixo
    │
    ├─ [1] Drop: Unnamed:0 + colunas 100% nulas
    ├─ [2] Flag: nulos com significado de negócio → bool flags
    ├─ [3] Imputar: mediana por UNID_IND (AREA_PROD, TCH_PROD, TON_ESTIM)
    ├─ [4] Encoding: corrige double-encoding latin-1/UTF-8
    ├─ [5] Texto: str.strip() em todas as colunas object
    └─ [6] Datas: converte colunas data/dt_/date para datetime64
    │
    ▼
data/processed/  (Parquet)
```

---

## Regras de Limpeza de Nulos (resumo)

| Tipo | Critério | Ação |
|------|----------|------|
| 100% nulos | Coluna inteiramente nula | Deletar coluna |
| Nulo = negócio | Null tem significado (ausência esperada) | Flag bool + manter nulo |
| Nulo = faltante | Dado deveria existir | Imputar mediana por `UNID_IND` |
| Nulo = geo | Coordenada sem cobertura | Manter, cruzar com shapefile depois |
| Poucos nulos | Sem critério claro + baixo % | Manter como está |

Detalhes completos: [`docs/regras_limpeza.md`](docs/regras_limpeza.md)

---

## Resultados do Processamento (Silver)

| Arquivo raw | Linhas | Colunas raw | Colunas silver | Alterações |
|-------------|--------|-------------|----------------|-----------|
| `Correcao_talhoes_para_unificacao.xlsx` | 23.599 | 8 | 8 | Encoding + texto |
| `Inventario_atvos_21_27_part_2.xlsx` | 50.000 | 74 | 75 | -7 drop, +8 flags, 14.210 imputações |
| `Inventario_atvos_21_27_part_4.xlsx` | 17.426 | 74 | 75 | -7 drop, +8 flags, 4.900 imputações |

Colunas deletadas nos Inventarios:
- `Unnamed: 0` (índice de exportação)
- `AREA_REEST2`, `TCH_REEST2`, `TON_REEST2`, `AREA_REEST3`, `TCH_REEST3`, `TON_REEST3` (100% nulos)

---

## Alternativas ao GCP

O projeto não utiliza Google Cloud Platform. As alternativas adotadas:

| Original | Alternativa | Script |
|----------|-------------|--------|
| BigQuery | **DuckDB** (`pip install duckdb`) — SQL in-process sobre Parquet | — |
| GCS (arquivos) | **Sistema de arquivos local** em `data/raw/` | `src/ingestion/extract_local.py` |

**Exemplo DuckDB (substitui query BigQuery):**
```python
import duckdb
df = duckdb.query("""
    SELECT UNID_IND, AVG(TCH_PROD) as tch_medio, COUNT(*) as n_talhoes
    FROM 'data/processed/Inventario_atvos_21_27_part_2_silver.parquet'
    GROUP BY UNID_IND
    ORDER BY tch_medio DESC
""").df()
```

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [`docs/mapeamento_fontes.md`](docs/mapeamento_fontes.md) | Todas as fontes: colunas, chaves, granularidade (Task 1.2) |
| [`docs/regras_limpeza.md`](docs/regras_limpeza.md) | Regras de limpeza aprovadas antes do código (Task 1.4) |
| [`docs/dicionario_dados.md`](docs/dicionario_dados.md) | Dicionário completo das colunas Silver (Task 1.6) |

---

## Status Sprint 1

| Entregavel | Status | Criterio de aceite |
|------------|--------|--------------------|
| Ambiente configurado | Feito | venv + requirements.txt |
| Mapeamento das fontes | Feito | `docs/mapeamento_fontes.md` |
| Script de ingestão Bronze | Feito | `src/ingestion/` — log gerado |
| Regras de limpeza documentadas | Feito | `docs/regras_limpeza.md` |
| Script de limpeza Silver | Feito | `data/processed/` populado |
| Dicionário de Dados Silver | Feito | `docs/dicionario_dados.md` |
