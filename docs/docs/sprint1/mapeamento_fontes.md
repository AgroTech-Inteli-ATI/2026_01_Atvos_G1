---
title: "Mapeamento de Fontes"
sidebar_position: 1
---

# Mapeamento de Fontes de Dados — Sprint 1

**Última atualização:** 2026-05-07  
**Responsável:** Módulo 10 — Atvos G1

> **Infraestrutura:** O projeto não utiliza Google Cloud Platform.
> Alternativas locais documentadas na seção final.

---

## Fontes Disponíveis

### Fonte 1 — Correção Talhões para Unificação

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Correcao_talhoes_para_unificacao.xlsx` |
| **Silver** | `data/processed/Correcao_talhoes_para_unificacao_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas** | 23.599 |
| **Colunas** | 8 |
| **Granularidade** | 1 linha = 1 par (talhão origem → talhão destino) |
| **Chave de junção** | `Faz_Origem` + `Setor_Origem` + `Talhao_Origem` |
| **Frequência de atualização** | Snapshot manual (atualização por demanda) |
| **Nulos** | Nenhum |

**Colunas:**

| Coluna | Tipo | Descrição | Chave? |
|--------|------|-----------|--------|
| `Safra_Origem` | int | Safra do talhão de origem (formato AASSSS) | Parte da chave |
| `Faz_Origem` | int | Código da fazenda de origem | Parte da chave |
| `Setor_Origem` | int | Setor da fazenda de origem | Parte da chave |
| `Talhao_Origem` | int | Número do talhão de origem | Parte da chave |
| `Faz_Destino` | int | Código da fazenda de destino | — |
| `Setor_Destino` | int | Setor da fazenda de destino | — |
| `Talhao_Destino` | int | Número do talhão de destino | — |
| `Motivo` | str | Motivo da correção (ex: "1-Reforma", "2-Unificação") | — |

---

### Fonte 2 — Inventário Atvos 2021-2027 (Parte 2)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_2.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_2_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 50.000 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2021–2022 (SAFRA 22122) |
| **Data de geração** | 2026-04-23 |

---

### Fonte 3 — Inventário Atvos 2021-2027 (Parte 4)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_4.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_4_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 17.426 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2022–2023 (SAFRA 22223) |
| **Data de geração** | 2026-04-23 |

---

## Colunas do Inventário (Partes 2 e 4 — estrutura idêntica)

| Coluna | Tipo | Descrição | Chave? | Nulos |
|--------|------|-----------|--------|-------|
| `CHAVESIG` | int | Identificador único do talhão no SIG | PK | 0% |
| `CHAVE` | str | Chave legível (formato: NUM-SETOR-TALHAO) | — | 0% |
| `SAFRA` | int | Código da safra (formato AASSSS) | — | 0% |
| `EMPRESA` | int | Código numérico da empresa/unidade | FK | 0% |
| `DESC_EMPRESA` | str | Sigla da unidade industrial | — | 0% |
| `UndGerencial` | str | Unidade gerencial (igual DESC_EMPRESA) | — | 0% |
| `BLOCO` | float | Bloco de colheita | — | 23,5% |
| `NUM` | int | Código numérico da fazenda | FK | 0% |
| `FAZENDA` | str | Nome da fazenda | — | 0% |
| `SETOR` | int | Número do setor dentro da fazenda | FK | 0% |
| `TALHAO` | int | Número do talhão dentro do setor | FK | 0% |
| `DE_OCUP` | str | Descrição da ocupação (ex: "Cana de Açúcar") | — | 0% |
| `FG_OCORREN` | str | Flag de ocorrência (S/F) | — | 0% |
| `DT_OCORREN` | datetime | Data da ocorrência | — | 0% |
| `AREA_HA` | float | Área total do talhão em hectares | — | 0% |
| `AREA_DANO` | float | Área danificada em hectares | — | ~0,1% |
| `VARIED` | str | Variedade de cana plantada | — | 0% |
| `MAN_HIPOT` | str | Manejo hipotético (Precoce/Média/Tardia) | — | ~2,8% |
| `TIPO_PROP` | str | Tipo de propriedade (PARC, FORNSUPAR etc.) | — | 0% |
| `TIPO_CONTRATO` | str | Tipo de contrato com o fornecedor | — | ~0,1% |
| `ESTAGIO` | str | Estágio da cana (ex: "3º Corte", "Formação 18m") | — | 0% |
| `NO_CORTE` | int | Número do corte | — | 0% |
| `CATEGORIA` | str | Categoria (Cana Soca, Formação, Muda) | — | 0% |
| `DATA_PLANTIO` | datetime | Data do plantio | — | ~10,3% |
| `FRENTE` | int | Código da frente de colheita | — | 0% |
| `ZONA_AGRO_ECOLOGICA` | float | Código da zona agroecológica | — | ~18% (geo) |
| `DESC_ZONA` | str | Descrição da zona agroecológica | — | ~18% (geo) |
| `DT_CARACT` | datetime | Data do evento de caracterização | — | ~99,8% (negócio) |
| `CARACT` | str | Tipo de caracterização | — | ~99,8% (negócio) |
| `EXPANSAO` | str | Flag de expansão (S/N) | — | 0% |
| `Devolucao` | str | Flag de devolução (S/N) | — | 0% |
| `Reforma` | str | Flag de reforma (S/N) | — | 0% |
| `TP_REFORMA` | str | Tipo de reforma | — | ~69% (negócio) |
| `SIST_PLANT` | str | Sistema de plantio | — | ~2,8% |
| `TP_IRRIGA` | str | Tipo de irrigação | — | 0% |
| `Vinhaca_E` | str | Aplicação de vinhaça (S/N) | — | 0% |
| `TORTA` | str | Aplicação de torta de filtro (S/N) | — | 0% |
| `SISTEMA_COL` | float | Sistema de colheita | — | ~0,6% |
| `DIST_TERRA` | float | Distância por estrada de terra (km) | — | 0% |
| `DIST_ASFALTO` | float | Distância por asfalto (km) | — | 0% |
| `DIST_HIDR` | int | Distância hidroviária (km) | — | 0% |
| `UNID_IND` | int | Código da unidade industrial | FK | 0% |
| `AMBIENTE` | str | Código do ambiente de produção | — | 0% |
| `DESC_AMBIENTE` | str | Descrição do ambiente (tipo de solo) | — | ~36% (geo) |
| `DE_TP_SOLO` | str | Descrição do tipo de solo | — | 0% |
| `ESPAC` | str | Espaçamento de plantio | — | 0% |
| `AREA_PROD` | float | Área de produção (ha) — **imputada** | — | 0% após silver |
| `TCH_PROD` | float | Toneladas de cana por hectare estimadas — **imputada** | — | 0% após silver |
| `TON_ESTIM` | float | Toneladas estimadas de produção — **imputada** | — | 0% após silver |
| `AREA_REEST` | float | Área de reestimativa (ha) | — | ~56% (negócio) |
| `TCH_REEST` | float | TCH reestimado | — | ~56% (negócio) |
| `TON_REEST` | float | Toneladas reestimadas | — | ~56% (negócio) |
| `AREA_MUDA` | float | Área de muda (ha) | — | ~94% (negócio) |
| `TCH_MUDA` | float | TCH de muda | — | ~94% (negócio) |
| `TON_MUDA` | float | Toneladas de muda | — | ~94% (negócio) |
| `AREA_COLHIDA` | float | Área efetivamente colhida (ha) | — | ~38% (negócio) |
| `OBJETIVO` | str | Objetivo do talhão (Safra, Muda) | — | ~0,5% |
| `SIT_TALHAO` | str | Situação atual do talhão | — | 0% |
| `DATA_FECHA` | datetime | Data de fechamento do ciclo | — | ~35% (negócio) |
| `CANA_ENT` | float | Cana entregue na usina (ton) | — | ~99% (negócio) |
| `ADMIN` | str | Tipo de administração (CANA PROPRIA, FORNECEDOR) | — | 0% |
| `CD_FORNEC` | int | Código do fornecedor | FK | 0% |
| `FORNEC` | str | Nome do fornecedor | — | ~0,1% |
| `ULT_CORTE` | datetime | Data do último corte | — | ~5,5% |
| `LATITUDE` | str | Latitude do centróide do talhão | — | ~18,5% (geo) |
| `LONGITUDE` | str | Longitude do centróide do talhão | — | ~18,5% (geo) |
| `Data_Geracao_Planilha` | datetime | Timestamp de geração do arquivo | — | 0% |

**Flags adicionadas na camada Silver (não existem no raw):**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `flag_bloco_ausente` | bool | True quando BLOCO é nulo |
| `flag_caract_ausente` | bool | True quando DT_CARACT e CARACT são nulos |
| `flag_cana_ent_ausente` | bool | True quando CANA_ENT é nulo |
| `flag_tp_reforma_ausente` | bool | True quando TP_REFORMA é nulo |
| `flag_reestimativa_ausente` | bool | True quando AREA_REEST, TCH_REEST e TON_REEST são nulos |
| `flag_muda_ausente` | bool | True quando AREA_MUDA, TCH_MUDA e TON_MUDA são nulos |
| `flag_colheita_ausente` | bool | True quando AREA_COLHIDA é nulo |
| `flag_talhao_aberto` | bool | True quando DATA_FECHA é nulo |

---

## Relações entre Fontes

```
Inventario_part_2 (safras 21-22)  ─┐
                                    ├─ Unir por CHAVESIG → Inventario Completo
Inventario_part_4 (safras 22-23)  ─┘
                        │
                        └─── Cruzar com Correcao_talhoes via:
                             Faz_Origem = NUM, Setor_Origem = SETOR,
                             Talhao_Origem = TALHAO
```

---

## Alternativas ao GCP (sem BigQuery / sem GCS)

| Necessidade original | Solução adotada |
|---------------------|----------------|
| BigQuery (SQL em escala) | **DuckDB** (`pip install duckdb`) — SQL in-process sobre Parquet/DataFrames locais |
| GCS (armazenamento de arquivos) | **Sistema de arquivos local** — `data/raw/` e `data/processed/` |
| Script `extract_bigquery.py` | `src/ingestion/extract_local.py` — lê CSV/Excel/Parquet com logging |
| Script `extract_gcs.py` | Mesmo `extract_local.py` — função `extract_all_raw()` |

**Exemplo DuckDB (equivalente ao BigQuery):**
```python
import duckdb
df = duckdb.query("""
    SELECT UNID_IND, AVG(TCH_PROD) as tch_medio
    FROM 'data/processed/Inventario_atvos_21_27_part_2_silver.parquet'
    GROUP BY UNID_IND
""").df()
```
