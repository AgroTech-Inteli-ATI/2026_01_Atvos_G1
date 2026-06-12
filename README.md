# Agrotech 2026 — Atvos G1

Projeto de engenharia de dados e visualização agrônomica desenvolvido para a Atvos ao longo de quatro sprints. O sistema ingere inventários de talhões, aplica um motor de regras agronômicas e entrega orientações de intervenção por meio de uma interface web interativa.

## Visão Geral do Projeto

O pipeline segue a arquitetura medallion em três camadas:

```
Raw (Excel)  →  Silver (Parquet limpo)  →  Gold (orientações por talhão)  →  Web (frontend + API)
```

A camada Gold produz uma linha por combinação de talhão e processo agronomico (calagem, gessagem, fosfatagem, erradicação, janela de plantio, etc.), com orientação, insumo recomendado, dose calculada e status de alerta.

## Estrutura do Projeto

```
.
├── data/
│   ├── raw/                        # Dados brutos — nunca alterar
│   │   ├── Inventario_atvos_21_27_part_2.xlsx
│   │   ├── Inventario_atvos_21_27_part_4.xlsx
│   │   └── Correcao_talhoes_para_unificacao.xlsx
│   ├── processed/                  # Camada Silver — gerada pelo pipeline
│   │   ├── Inventario_atvos_21_27_part_2_silver.parquet
│   │   ├── Inventario_atvos_21_27_part_4_silver.parquet
│   │   ├── Correcao_talhoes_para_unificacao_silver.parquet
│   │   └── silver_com_safra.parquet
│   └── gold/                       # Camada Gold — gerada pelo pipeline
│       ├── orientacoes_YYYY-MM-DD.parquet
│       └── orientacoes_YYYY-MM-DD.csv
├── src/
│   ├── ingestion/
│   │   ├── load_files.py           # Leitura com logging de arquivos raw
│   │   ├── run_ingestion.py        # Executa ingestão de todos os arquivos
│   │   ├── extract_local.py        # Alternativa local ao BigQuery/GCS
│   │   └── extract_safra.py        # Integração de estimativas de safra (TCH)
│   ├── processing/
│   │   ├── clean_data.py           # Pipeline Raw → Silver
│   │   └── run_processing.py       # Executa limpeza em todos os arquivos
│   ├── rules/
│   │   ├── _base.py                # Classe base e utilitários das regras
│   │   ├── calagem.py              # Regras de calagem (pH, CTC, saturação)
│   │   ├── gessagem.py             # Regras de gessagem (Al, textura)
│   │   ├── fosfatagem.py           # Regras de fosfatagem (P Mehlich-1)
│   │   ├── erradicacao.py          # Regras de erradicação (corte, TCH)
│   │   ├── janela_plantio.py       # Regras de janela de plantio
│   │   └── insumos.py              # Cálculo de doses e insumos
│   ├── pipeline_gold.py            # Orquestra Silver → Gold
│   └── api/
│       └── server.py               # Servidor HTTP — API JSON para o frontend
├── frontend/
│   ├── index.html                  # SPA com três telas (Dashboard, Talhões, Relatórios)
│   ├── styles.css                  # Design system inspirado no Figma Componentes Web
│   └── script.js                   # Lógica de navegação, filtros, paginação e modais
├── tests/
│   ├── test_calagem.py
│   ├── test_gessagem.py
│   ├── test_insumos.py
│   └── test_pipeline_gold.py
├── docs/
│   └── docs/
│       ├── sprint1/
│       │   ├── dicionario_dados.md
│       │   ├── mapeamento_fontes.md
│       │   └── regras_limpeza.md
│       └── sprint2/
│           ├── arquitetura_motor_regras.md
│           ├── regras_agronomicas.md
│           └── relatorio_amostra_gold.md
├── requirements.txt
└── venv/
```

## Como Executar

### 1. Ativar o ambiente virtual

No Windows com PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

No Windows com CMD:

```cmd
venv\Scripts\activate.bat
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Executar o pipeline completo

Se ainda não existir o arquivo Gold, rode os passos abaixo na ordem:

```bash
python src/processing/run_processing.py
python src/ingestion/extract_safra.py
python src/pipeline_gold.py
```

Se o Gold já existir em `data/gold/`, pule direto para o passo 4.

### 4. Iniciar o servidor da API

```bash
python src/api/server.py
```

O terminal exibirá uma linha confirmando o endereço:

```
[HH:MM:SS]  Monitor Agronomico API  →  http://localhost:8000
```

O carregamento dos 471 mil registros leva alguns segundos na primeira requisição.

### 5. Abrir o frontend

Acesse **http://localhost:8000** em qualquer navegador moderno.

Para usar uma porta diferente passe o número como argumento:

```bash
python src/api/server.py 5000
```

O frontend detecta automaticamente se a API está offline e entra em modo de demonstração com dados estáticos.

## Telas da Aplicação

### Dashboard

Tela inicial com quatro cartões de KPI (total de talhões, intervenções urgentes, atenção necessária, processos cobertos) e a tabela de orientações por talhão. Aceita filtros de unidade, processo, status e busca textual, com paginação de 20 registros por página. O botão "Exportar CSV" baixa os registros filtrados diretamente da API.

### Talhões

Visão consolidada por talhão — uma linha por ID com o pior status dentre todos os processos avaliados e a lista de processos em alerta. O botão "Ver processos" abre um modal com todas as orientações daquele talhão. Aceita filtros de unidade, status geral e busca por ID ou chave.

### Relatórios

Tela analítica com três tabelas: distribuição de registros por processo agronomico (com contagem por status e sem-dado), distribuição por unidade industrial e as quinze regras mais acionadas com barra de proporção visual.

## Endpoints da API

Todos os endpoints aceitam CORS e retornam JSON UTF-8.

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/stats` | Indicadores globais para os KPIs |
| `GET /api/data` | Orientações paginadas com filtros |
| `GET /api/export` | Download CSV com os filtros ativos |
| `GET /api/talhoes` | Talhões agregados com filtros e paginação |
| `GET /api/talhao?id=...` | Todos os processos de um talhão específico |
| `GET /api/relatorio` | Resumos por processo, unidade e regras |

Parâmetros de filtro aceitos por `/api/data` e `/api/talhoes`: `unit`, `processo`, `status`, `search`, `page`, `per_page`.

## Pipeline de Dados

```
data/raw/ (Excel)
    │
    ├── src/ingestion/extract_local.py     lê com logging
    │
    ▼
src/processing/clean_data.py               Raw → Silver
    │
    ├── [1] Remove colunas 100% nulas e índice de exportação
    ├── [2] Flags booleanas para nulos com significado de negócio
    ├── [3] Imputação por mediana dentro de UNID_IND
    ├── [4] Correção de double-encoding latin-1/UTF-8
    ├── [5] Normalização de texto e datas
    └── [6] Unificação com tabela de correção de talhões
    │
    ▼
data/processed/ (Parquet Silver)
    │
    ├── src/ingestion/extract_safra.py     enriquece com TCH estimado
    │
    ▼
src/pipeline_gold.py + src/rules/          Silver → Gold
    │
    ├── calagem          (pH, CTC, V%)
    ├── gessagem         (Al³⁺, textura)
    ├── fosfatagem       (P Mehlich-1)
    ├── erradicação      (corte, TCH)
    └── janela_plantio   (maturidade, safra)
    │
    ▼
data/gold/ (Parquet + CSV)
    │
    ▼
src/api/server.py                          serve JSON via HTTP
    │
    ▼
frontend/ (HTML + CSS + JS)                interface web
```

## Testes

```bash
pytest
```

Os testes cobrem os módulos de calagem, gessagem, insumos e o pipeline gold completo.

## Documentação por Sprint

### Sprint 1 — Ingestão e Limpeza de Dados

Foco na estrutura de ingestão dos arquivos Excel brutos e na definição das regras de limpeza para a camada Silver. Os principais entregáveis foram o mapeamento de fontes, o dicionário de dados Silver e o pipeline de limpeza com imputação por mediana.

Documentos em `docs/docs/sprint1/`:

- `mapeamento_fontes.md` — colunas, chaves e granularidade de cada fonte
- `regras_limpeza.md` — decisões de limpeza aprovadas antes do código
- `dicionario_dados.md` — dicionário completo da camada Silver

### Sprint 2 — Motor de Regras Agronômicas

Implementação do motor de regras que transforma a camada Silver em orientações agronômicas estruturadas (camada Gold). Cada módulo de regra cobre um processo: calagem, gessagem, fosfatagem, erradicação e janela de plantio. O pipeline gera uma linha por talhão por processo com orientação textual, insumo recomendado e dose calculada.

Documentos em `docs/docs/sprint2/`:

- `arquitetura_motor_regras.md` — desenho da arquitetura e fluxo de dados
- `regras_agronomicas.md` — especificação técnica das regras por módulo
- `relatorio_amostra_gold.md` — validação da amostra Gold gerada

### Sprint 3 — Backend e API REST

Criação do servidor HTTP em Python puro (`src/api/server.py`) que carrega a camada Gold na memória e expõe endpoints JSON para o frontend. O servidor pré-computa os agregados por talhão e os resumos por processo e unidade na inicialização, eliminando latência nas consultas. Não requer dependências externas além das já listadas no `requirements.txt`.

Melhorias no pipeline: integração do estimador de safra (`extract_safra.py`) que enriquece o Silver com o campo `tchan_estimado`, habilitando as regras de insumos baseadas em produtividade estimada.

### Sprint 4 — Frontend e Integração

Desenvolvimento da interface web como SPA (Single Page Application) em HTML, CSS e JavaScript puro, sem frameworks. O design segue o sistema visual do Figma "Componentes Web" com adaptação para a identidade Atvos (verde primário, badges de risco coloridos, cards KPI).

Três telas completas com navegação por hash:

- **Dashboard** — KPIs e tabela de orientações com filtros e exportação CSV
- **Talhões** — inventário consolidado com status geral e modal de processos
- **Relatórios** — tabelas analíticas de distribuição por processo, unidade e regras

O frontend opera em modo de demonstração quando a API está offline, usando dados estáticos representativos.

## Resultados do Processamento

| Arquivo raw | Linhas | Colunas raw | Colunas silver |
|-------------|--------|-------------|----------------|
| `Inventario_atvos_21_27_part_2.xlsx` | 50.000 | 74 | 75 |
| `Inventario_atvos_21_27_part_4.xlsx` | 17.426 | 74 | 75 |
| `Correcao_talhoes_para_unificacao.xlsx` | 23.599 | 8 | 8 |

Camada Gold (run 2026-06-11): **471.982 registros** — 67.426 talhões únicos × 7 processos.

## Alternativas ao GCP

O projeto não utiliza Google Cloud Platform. As alternativas adotadas foram sistema de arquivos local em `data/` para substituir o GCS, e o servidor HTTP embutido do Python para substituir o Cloud Run ou App Engine.

Para consultas SQL sobre os Parquets, o DuckDB pode ser usado sem necessidade de servidor:

```python
import duckdb
df = duckdb.query("""
    SELECT unidade, processo, COUNT(*) AS n, AVG(CAST(dose_kg_ha AS DOUBLE)) AS dose_media
    FROM 'data/gold/orientacoes_2026-06-11.parquet'
    WHERE dose_kg_ha != ''
    GROUP BY unidade, processo
    ORDER BY unidade, n DESC
""").df()
```
