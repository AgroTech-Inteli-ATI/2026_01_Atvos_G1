# Agrotech 2026 — Atvos G1

Projeto de engenharia de dados e visualização agronômica desenvolvido para a Atvos ao longo de quatro sprints. O sistema ingere inventários de talhões, aplica um motor de regras agronômicas paralelo e entrega orientações de intervenção por meio de uma interface web interativa.

## Visão Geral

```
Raw (Excel)  →  Silver (Parquet limpo)  →  Gold (orientações por talhão)  →  Web (frontend + API)
```

A camada Gold produz uma linha por combinação de talhão × processo agronômico (calagem, gessagem, fosfatagem, erradicação, janela de plantio, fosfatagem por insumo e dessecação), com orientação textual, insumo recomendado, dose calculada, quantidade total em kg e status de alerta.

## Estrutura do Projeto

```
.
├── data/
│   ├── raw/                             # Dados brutos — nunca alterar
│   ├── processed/                       # Camada Silver (Parquet)
│   └── gold/                            # Camada Gold (Parquet + CSV)
├── src/
│   ├── ingestion/
│   │   ├── extract_local.py             # Leitura com logging dos arquivos raw
│   │   ├── extract_safra.py             # Enriquece Silver com TCH estimado
│   │   └── run_ingestion.py
│   ├── processing/
│   │   ├── clean_data.py                # Pipeline Raw → Silver
│   │   └── run_processing.py
│   ├── rules/
│   │   ├── _base.py                     # Contrato de interface + sem_dado / nao_se_aplica / dado_suspeito
│   │   ├── calagem.py                   # pH + CTC + saturação de bases (Embrapa/IAC)
│   │   ├── gessagem.py                  # Saturação de Al³⁺ + textura (Malavolta)
│   │   ├── fosfatagem.py                # P Mehlich-1 (IAC Boletim 100)
│   │   ├── erradicacao.py               # NO_CORTE + TCH_PROD
│   │   ├── janela_plantio.py            # Maturidade + janela de colheita
│   │   └── insumos.py                   # Dose por extração (MAP) + Glifosato 480 SL
│   ├── pipeline/                        # Pacote modular do pipeline Silver → Gold
│   │   ├── loader.py                    # Leitura do Silver
│   │   ├── transformer.py               # Transformação paralela (ThreadPoolExecutor)
│   │   ├── saver.py                     # Persistência em Parquet + CSV
│   │   ├── reporter.py                  # Relatório de validação no console
│   │   └── utils.py                     # Log compartilhado
│   ├── pipeline_gold.py                 # Orquestrador (usa src/pipeline/)
│   └── api/
│       └── server.py                    # API HTTP — JSON para o frontend
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── tests/
│   ├── conftest.py
│   ├── helpers.py                       # assert_resultado_valido / assert_sem_dado / assert_dado_suspeito
│   ├── test_calagem.py
│   ├── test_erradicacao.py
│   ├── test_gessagem.py
│   ├── test_insumos.py
│   └── test_pipeline_gold.py
├── docs/                                # Site Docusaurus com documentação por sprint
├── requirements.txt
└── venv/
```

## Como Executar

### 1. Ativar o ambiente virtual

```powershell
# Windows — PowerShell
venv\Scripts\Activate.ps1

# Windows — CMD
venv\Scripts\activate.bat
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Executar o pipeline completo

```bash
python src/processing/run_processing.py   # Raw → Silver
python src/ingestion/extract_safra.py     # Silver + TCH estimado (habilita insumos)
python src/pipeline_gold.py               # Silver → Gold (paralelo, ~8 workers)
```

Se o Gold já existir em `data/gold/`, pule direto para o passo 4.

### 4. Iniciar o servidor da API

```bash
python src/api/server.py
```

O terminal exibirá:

```
[HH:MM:SS]  Monitor Agronomico API  →  http://localhost:8000
```

### 5. Abrir o frontend

Acesse **http://localhost:8000** em qualquer navegador moderno.

Para usar uma porta diferente:

```bash
python src/api/server.py 5000
```

O frontend entra em modo de demonstração com dados estáticos quando a API está offline.

## Motor de Regras Agronômicas

O motor segue um contrato estrito: toda função de regra recebe `talhao: dict` e retorna exatamente:

```python
{
    "orientacao":       str,          # recomendação textual ou código de estado
    "valor_calculado":  float | None, # dose ou índice numérico
    "regra_acionada":   str,          # código machine-readable da condição
}
```

### 4 estados de retorno

| Estado | `orientacao` | Quando |
|---|---|---|
| Resultado válido | `<regra>` | Campo presente e plausível |
| `SEM_DADO` | `"SEM_DADO"` | Campo ausente, None ou NaN |
| `NAO_SE_APLICA` | `"NAO_SE_APLICA"` | Regra não pertinente ao perfil |
| `DADO_SUSPEITO` | `"DADO_SUSPEITO: <motivo>"` | Valor presente mas fisicamente impossível |

### Detecção de outliers

Cada módulo valida os limites físicos dos campos antes de calcular:

| Módulo | Campo | Limites |
|---|---|---|
| Erradicação | TCH_PROD | [0, 300] t/ha |
| Erradicação | NO_CORTE | [0, 20] cortes |
| Calagem | pH | [0, 14] |
| Calagem | V_ATUAL | [0%, 100%] |
| Gessagem | sat_al | [0%, 100%] |
| Fosfatagem | P | [0, 1000] mg/dm³ |
| Insumos | tchan | (0, 300] t/ha |

## Paralelismo da Pipeline

O módulo `src/pipeline/transformer.py` processa cada talhão de forma independente usando `ThreadPoolExecutor`:

```python
with ThreadPoolExecutor(max_workers=N_WORKERS) as executor:
    futures = [executor.submit(_processar_talhao, row, hoje) for row in rows]
    for future in as_completed(futures):
        todos_registros.extend(future.result())
```

Como as funções de regra são puras (sem estado compartilhado), o paralelismo é seguro sem locks. Com 8 workers em produção, o tempo de processamento de 67 mil talhões × 7 processos reduz proporcionalmente ao número de núcleos disponíveis.

## Endpoints da API

| Endpoint | Descrição |
|---|---|
| `GET /api/stats` | KPIs globais: totais e área por status |
| `GET /api/data` | Orientações paginadas com filtros |
| `GET /api/export` | Download CSV com filtros ativos |
| `GET /api/talhoes` | Talhões agregados (pior status entre processos) |
| `GET /api/talhao?id=...` | Todos os processos de um talhão |
| `GET /api/relatorio` | Distribuição por processo, unidade e regras (% área) |

Parâmetros aceitos por `/api/data` e `/api/talhoes`: `unit`, `processo`, `status`, `search`, `page`, `per_page`.

## Testes

```bash
pytest
```

**170 testes** em 5 arquivos, organizados em 5 camadas de robustez por módulo:

1. **SEM_DADO** — entradas nulas, NaN, tipo errado
2. **NAO_SE_APLICA** — categorias de talhão incompatíveis
3. **Outliers (DADO_SUSPEITO)** — valores fora do intervalo físico, testados nos limites exatos
4. **Lógica agronômica** — monotonicidade de doses, fronteiras exatas de decisão
5. **Contrato de interface** — parametrizado com todas as fixtures; nunca levanta exceção

```
tests/test_erradicacao.py     34 testes
tests/test_calagem.py         31 testes
tests/test_gessagem.py        26 testes
tests/test_insumos.py         45 testes
tests/test_pipeline_gold.py   34 testes
```

## Pipeline de Dados

```
data/raw/ (Excel)
    │
    ├── src/ingestion/extract_local.py     lê com logging
    ▼
src/processing/clean_data.py               Raw → Silver
    ├── Remove colunas 100% nulas
    ├── Flags booleanas para nulos de negócio
    ├── Imputação por mediana dentro de UNID_IND
    ├── Correção de double-encoding latin-1/UTF-8
    ├── Normalização de texto e datas
    └── Unificação com tabela de correção de talhões
    ▼
data/processed/ (Parquet Silver)
    │
    ├── src/ingestion/extract_safra.py     enriquece com tchan_estimado
    ▼
src/pipeline_gold.py                       orquestrador
    ├── src/pipeline/loader.py             carrega Silver
    ├── src/pipeline/transformer.py        aplica regras (paralelo)
    │   ├── calagem          (pH, CTC, V%)
    │   ├── gessagem         (Al³⁺, textura)
    │   ├── fosfatagem       (P Mehlich-1)
    │   ├── erradicacao      (NO_CORTE, TCH)
    │   ├── janela_plantio   (maturidade)
    │   ├── fosfatagem_insumo (extração por TCH)
    │   └── dessecacao       (Glifosato 480 SL)
    ├── src/pipeline/reporter.py           relatório de validação
    └── src/pipeline/saver.py              salva Parquet + CSV
    ▼
data/gold/ (Parquet + CSV)
    ▼
src/api/server.py                          API HTTP
    ▼
frontend/ (HTML + CSS + JS)                interface web
```

## Resultados do Processamento

| Arquivo raw | Linhas | Colunas silver |
|---|---|---|
| `Inventario_atvos_21_27_part_2.xlsx` | 50.000 | 75 |
| `Inventario_atvos_21_27_part_4.xlsx` | 17.426 | 75 |
| `Correcao_talhoes_para_unificacao.xlsx` | 23.599 | 8 |

**Camada Gold (2026-06-11):** 471.982 registros — 67.426 talhões × 7 processos.

## Alternativas ao GCP

O projeto não usa Google Cloud Platform. Alternativas locais adotadas:

- `data/` no sistema de arquivos local substitui GCS
- Servidor HTTP embutido do Python substitui Cloud Run
- DuckDB para consultas SQL sobre Parquet sem servidor:

```python
import duckdb
df = duckdb.query("""
    SELECT unidade, processo, COUNT(*) AS n
    FROM 'data/gold/orientacoes_2026-06-11.parquet'
    GROUP BY unidade, processo
    ORDER BY unidade, n DESC
""").df()
```

## Documentação por Sprint

- **Sprint 1** (`docs/docs/sprint1/`) — Ingestão, limpeza e dicionário de dados Silver
- **Sprint 2** (`docs/docs/sprint2/`) — Motor de regras agronômicas e camada Gold
- **Sprint 3** (`docs/docs/sprint3/`) — API REST, modularização e plano de escalabilidade
- **Sprint 4** (`docs/docs/sprint4/`) — Frontend SPA e análise de custo
