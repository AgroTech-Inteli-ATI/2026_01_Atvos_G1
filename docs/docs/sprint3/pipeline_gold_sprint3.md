---
title: "Pipeline Gold — Sprint 3"
sidebar_position: 3
---

# Evoluções do Pipeline Gold — Sprint 3

**Sprint:** 3  
**Última atualização:** 2026-06-11  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Contexto

O pipeline Gold foi estendido na Sprint 3 com dois novos módulos e melhorias no orquestrador. A estrutura de módulos de regras permaneceu a mesma da Sprint 2 (contrato `calcular_<processo>(talhao: dict) -> dict`), mas dois novos processos foram integrados: `insumos` e `dessecacao`.

```
Sprint 2: calagem, gessagem, fosfatagem, erradicacao, janela_plantio
Sprint 3: + fosfatagem_insumo, + dessecacao
```

O pipeline passa a gerar 7 processos por talhão, resultando em 471.982 registros Gold (67.426 talhões × 7 processos).

---

## 2. Novo Módulo: `insumos.py`

O módulo `insumos.py` (registrado como `fosfatagem_insumo`) calcula a dose de insumo baseada na produtividade estimada do talhão.

### 2.1 Lógica principal

```
SE tch_estimado é nulo:
  → SEM_DADO

SE tch_estimado ≤ 0:
  → SEM_DADO (dado suspeito)

Dose de N (kg/ha) = tch_estimado × FATOR_N
Dose de K₂O (kg/ha) = tch_estimado × FATOR_K

SE tch_estimado < TCH_BAIXO:
  → orientacao: "Produtividade baixa — revisar adubação"
  → regra: "insumo_tch_baixo"

SE tch_estimado ≥ TCH_ALTO:
  → orientacao: "Alta produtividade — dose plena recomendada"
  → regra: "insumo_tch_alto"

SENAO:
  → orientacao: "Dose padrão por produtividade estimada"
  → regra: "insumo_padrao"
```

### 2.2 Campo `tchan_estimado`

A Sprint 3 integrou o script `extract_safra.py` ao fluxo do pipeline. Esse script enriquece o Silver com a coluna `tchan_estimado`, calculada a partir de médias históricas por unidade e estágio. O campo é então disponibilizado via `pipeline_gold._preparar_talhao()` sob a chave `tch_estimado`.

```bash
# Ordem de execução correta (Sprint 3 em diante):
python src/processing/run_processing.py      # Raw → Silver
python src/ingestion/extract_safra.py        # Silver + TCH estimado
python src/pipeline_gold.py                  # Silver (enriquecido) → Gold
```

Se `extract_safra.py` não for executado antes do pipeline, `tch_estimado` retorna `None` e o módulo de insumos registra `SEM_DADO` para todos os talhões.

---

## 3. Novo Módulo: Dessecação

O processo `dessecacao` avalia a necessidade de aplicação de dessecante pré-colheita com base no estágio da cana e na janela de colheita.

### 3.1 Lógica principal

```
SE man_hipot é nulo:
  → SEM_DADO

SE categoria NOT IN {"Cana Soca", "Formação"}:
  → NAO_SE_APLICA

SE man_hipot == "Tardia":
  → MONITORAR: dessecação pode ser necessária para antecipar maturação

SE man_hipot == "Média":
  → AVALIAR conforme previsão de colheita

SE man_hipot == "Precoce":
  → orientação preventiva; dessecação raramente necessária
```

---

## 4. Formato do Output Gold (Sprint 3)

O arquivo continua no formato long (uma linha por talhão × processo), com duas colunas novas em relação à Sprint 2: `insumo` e `dose_kg_ha`.

| Coluna | Tipo | Presente desde |
|---|---|---|
| `id_talhao` | str | Sprint 2 |
| `chave` | str | Sprint 2 |
| `unidade` | str | Sprint 2 |
| `safra` | str | Sprint 2 |
| `processo` | str | Sprint 2 |
| `orientacao` | str | Sprint 2 |
| `regra_acionada` | str | Sprint 2 |
| `valor_calculado` | float | Sprint 2 |
| `data_geracao` | date | Sprint 2 |
| `insumo` | str | **Sprint 3** |
| `dose_kg_ha` | float | **Sprint 3** |
| `quantidade_total_kg` | float | **Sprint 3** |

A coluna `quantidade_total_kg` é calculada como `dose_kg_ha × area_ha` do talhão, permitindo que o agrônomo veja o total de insumo necessário para cada talhão sem precisar calcular manualmente.

---

## 5. Resultados do Run de 2026-06-11

| Arquivo raw | Linhas | Colunas raw | Colunas silver |
|---|---|---|---|
| `Inventario_atvos_21_27_part_2.xlsx` | 50.000 | 74 | 75 |
| `Inventario_atvos_21_27_part_4.xlsx` | 17.426 | 74 | 75 |
| `Correcao_talhoes_para_unificacao.xlsx` | 23.599 | 8 | 8 |

**Camada Gold gerada:** `data/gold/orientacoes_2026-06-11.parquet` + `.csv`  
**Total de registros:** 471.982  
**Talhões únicos:** 67.426  
**Processos cobertos:** 7 (calagem, gessagem, fosfatagem, fosfatagem_insumo, erradicacao, janela_plantio, dessecacao)  
**Unidades industriais:** 8 (UMV, URC, USL, UAT, UCP, UCR, UEL, UAE)

### Distribuição de status

| Status | Registros | Proporção |
|---|---|---|
| `attention` | ~198.000 | ~42% — maioria é SEM_DADO por falta de dados de solo |
| `ok` | ~181.000 | ~38% |
| `monitor` | ~89.000 | ~19% |
| `urgent` | ~3.200 | ~1% — erradicações recomendadas |

---

## 6. Consultas de Validação

```python
import duckdb

# Verificar cobertura por processo
duckdb.query("""
    SELECT processo,
           COUNT(*) AS total,
           SUM(CASE WHEN regra_acionada LIKE 'dado_ausente%' THEN 1 ELSE 0 END) AS sem_dado
    FROM 'data/gold/orientacoes_2026-06-11.parquet'
    GROUP BY processo
    ORDER BY processo
""").df()

# Talhões com erradicação recomendada por unidade
duckdb.query("""
    SELECT unidade, COUNT(DISTINCT id_talhao) AS talhoes_errad
    FROM 'data/gold/orientacoes_2026-06-11.parquet'
    WHERE orientacao LIKE '%ERRADICACAO RECOMENDADA%'
    GROUP BY unidade
    ORDER BY talhoes_errad DESC
""").df()

# Dose média de insumo por unidade (apenas registros com dose preenchida)
duckdb.query("""
    SELECT unidade,
           AVG(CAST(dose_kg_ha AS DOUBLE)) AS dose_media_kg_ha
    FROM 'data/gold/orientacoes_2026-06-11.parquet'
    WHERE dose_kg_ha != '' AND processo = 'fosfatagem_insumo'
    GROUP BY unidade
    ORDER BY unidade
""").df()
```
