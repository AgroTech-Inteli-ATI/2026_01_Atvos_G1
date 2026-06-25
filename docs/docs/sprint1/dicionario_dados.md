---
title: "Dicionário de Dados"
sidebar_position: 3
---

# Dicionário de Dados — Camada Silver

**Última atualização:** 2026-05-07  
**Responsável:** Módulo 10 — Atvos G1  
**Critério de pronto:** todas as colunas dos DataFrames Silver documentadas

---

## Dataset: Correcao_talhoes_para_unificacao_silver

**Arquivo:** `data/processed/Correcao_talhoes_para_unificacao_silver.parquet`  
**Linhas:** 23.599 | **Colunas:** 8

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `Safra_Origem` | Safra do talhão de origem | int64 | — | Ex.: 22324 | Correcao_talhoes_para_unificacao.xlsx |
| `Faz_Origem` | Código numérico da fazenda de origem | int64 | — | Ex.: 110001 | Correcao_talhoes_para_unificacao.xlsx |
| `Setor_Origem` | Setor da fazenda de origem | int64 | — | >= 1 | Correcao_talhoes_para_unificacao.xlsx |
| `Talhao_Origem` | Número do talhão de origem | int64 | — | >= 1 | Correcao_talhoes_para_unificacao.xlsx |
| `Faz_Destino` | Código numérico da fazenda de destino | int64 | — | Ex.: 117001 | Correcao_talhoes_para_unificacao.xlsx |
| `Setor_Destino` | Setor da fazenda de destino | int64 | — | >= 1 | Correcao_talhoes_para_unificacao.xlsx |
| `Talhao_Destino` | Número do talhão de destino | int64 | — | >= 1 | Correcao_talhoes_para_unificacao.xlsx |
| `Motivo` | Motivo da correção de talhão | str | — | Ex.: "1-Reforma" | Correcao_talhoes_para_unificacao.xlsx |

---

## Dataset: Inventario_atvos_silver (partes 1, 2, 3 e 4 — estrutura idêntica)

**Arquivos:** 
- `data/processed/Inventario_atvos_21_27_part_1_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_2_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_3_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_4_silver.parquet` — 17.426 linhas, 75 colunas

### Identificadores e Chaves

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `CHAVESIG` | Identificador único do talhão no SIG | int64 | — | Único por linha | Inventario_atvos_21_27_part_*.xlsx |
| `CHAVE` | Chave legível no formato NUM-SETOR-TALHAO | str | — | Ex.: "410149-1-8" | Inventario_atvos_21_27_part_*.xlsx |
| `SAFRA` | Código da safra agrícola | int64 | — | Ex.: 22122, 22223 | Inventario_atvos_21_27_part_*.xlsx |
| `EMPRESA` | Código numérico da unidade industrial | int64 | — | Ex.: 21, 31, 41 | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_EMPRESA` | Sigla da unidade industrial | str | — | Ex.: "UMV", "URC", "UEL" | Inventario_atvos_21_27_part_*.xlsx |
| `UndGerencial` | Unidade gerencial, equivalente a `DESC_EMPRESA` | str | — | Ex.: "UMV" | Inventario_atvos_21_27_part_*.xlsx |
| `NUM` | Código numérico da fazenda | int64 | — | Ex.: 410149 | Inventario_atvos_21_27_part_*.xlsx |
| `SETOR` | Número do setor dentro da fazenda | int64 | — | >= 1 | Inventario_atvos_21_27_part_*.xlsx |
| `TALHAO` | Número do talhão dentro do setor | int64 | — | >= 1 | Inventario_atvos_21_27_part_*.xlsx |
| `UNID_IND` | Código da unidade industrial, equivalente a `EMPRESA` | int64 | — | Ex.: 21, 31, 41 | Inventario_atvos_21_27_part_*.xlsx |
| `CD_FORNEC` | Código do fornecedor | int64 | — | Ex.: 1031551 | Inventario_atvos_21_27_part_*.xlsx |

### Localização e Propriedade

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `FAZENDA` | Nome da fazenda | str | — | Texto livre | Inventario_atvos_21_27_part_*.xlsx |
| `TIPO_PROP` | Tipo de propriedade | str | — | PARC, FORNSUPAR, etc. | Inventario_atvos_21_27_part_*.xlsx |
| `TIPO_CONTRATO` | Tipo de contrato com o fornecedor | str | — | PARCERIA, SPOT, etc. | Inventario_atvos_21_27_part_*.xlsx |
| `ADMIN` | Tipo de administração da área | str | — | "CANA PROPRIA", "FORNECEDOR" | Inventario_atvos_21_27_part_*.xlsx |
| `FORNEC` | Nome do fornecedor | str | — | Texto livre | Inventario_atvos_21_27_part_*.xlsx |

### Características do Talhão

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `AREA_HA` | Área total do talhão | float64 | ha | > 0 | Inventario_atvos_21_27_part_*.xlsx |
| `AREA_DANO` | Área danificada | float64 | ha | >= 0 e <= AREA_HA | Inventario_atvos_21_27_part_*.xlsx |
| `DE_OCUP` | Descrição da ocupação | str | — | "Cana de Açúcar" | Inventario_atvos_21_27_part_*.xlsx |
| `DE_TP_SOLO` | Tipo de solo | str | — | Texto livre, ex.: "Latossolo..." | Inventario_atvos_21_27_part_*.xlsx |
| `AMBIENTE` | Código do ambiente de produção | str | — | Letra única: A-G | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_AMBIENTE` | Descrição do ambiente de produção | str | — | "Arenoso", "Argiloso", etc. | Inventario_atvos_21_27_part_*.xlsx |
| `ESPAC` | Espaçamento de plantio | str | — | Ex.: "1,5 Mts", "0,90x1,50m" | Inventario_atvos_21_27_part_*.xlsx |
| `LATITUDE` | Latitude do centroide do talhão | str | graus decimais | -33 a +5 (Brasil) | Inventario_atvos_21_27_part_*.xlsx |
| `LONGITUDE` | Longitude do centroide do talhão | str | graus decimais | -74 a -32 (Brasil) | Inventario_atvos_21_27_part_*.xlsx |
| `BLOCO` | Bloco de colheita | float64 | — | >= 1 (inteiros) | Inventario_atvos_21_27_part_*.xlsx |
| `ZONA_AGRO_ECOLOGICA` | Código da zona agroecológica | float64 | — | Ex.: 1.0, 2.0, 99.0 | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_ZONA` | Descrição da zona agroecológica | str | — | Ex.: "Bonsucro - NAO" | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_TERRA` | Distância do talhão à usina por estrada de terra | float64 | km | >= 0 | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_ASFALTO` | Distância do talhão à usina por asfalto | float64 | km | >= 0 | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_HIDR` | Distância hidroviária | int64 | km | >= 0 | Inventario_atvos_21_27_part_*.xlsx |

### Cultura e Manejo

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `VARIED` | Variedade de cana plantada | str | — | Ex.: "RB867515", "RB92579" | Inventario_atvos_21_27_part_*.xlsx |
| `CATEGORIA` | Categoria do talhão | str | — | "Cana Soca", "Formação", "Muda" | Inventario_atvos_21_27_part_*.xlsx |
| `ESTAGIO` | Estágio do ciclo da cana | str | — | Ex.: "3º Corte", "Formação 18m" | Inventario_atvos_21_27_part_*.xlsx |
| `NO_CORTE` | Número do corte | int64 | — | 0 (formação) a aprox. 8 | Inventario_atvos_21_27_part_*.xlsx |
| `DATA_PLANTIO` | Data do plantio da cana | datetime64 | — | >= 2010 | Inventario_atvos_21_27_part_*.xlsx |
| `MAN_HIPOT` | Manejo hipotético de maturação | str | — | "Precoce", "Média", "Tardia", "A Definir" | Inventario_atvos_21_27_part_*.xlsx |
| `SIST_PLANT` | Sistema de plantio | str | — | "Mecanizado", "Plan.Meiosi Viv.Sec." | Inventario_atvos_21_27_part_*.xlsx |
| `TP_IRRIGA` | Tipo de irrigação | str | — | "S/Info", "Hidroroll", etc. | Inventario_atvos_21_27_part_*.xlsx |
| `Vinhaca_E` | Aplicação de vinhaça (S/N) | str | — | "S", "N" | Inventario_atvos_21_27_part_*.xlsx |
| `TORTA` | Aplicação de torta de filtro (S/N) | str | — | "S", "N" | Inventario_atvos_21_27_part_*.xlsx |
| `SISTEMA_COL` | Código do sistema de colheita | float64 | — | Ex.: 4.0 | Inventario_atvos_21_27_part_*.xlsx |
| `FRENTE` | Código da frente de colheita | int64 | — | >= 1; 99 = sem frente | Inventario_atvos_21_27_part_*.xlsx |

### Reforma

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `EXPANSAO` | Flag de expansão de área | str | — | "S", "N" | Inventario_atvos_21_27_part_*.xlsx |
| `Devolucao` | Flag de devolução de área | str | — | "S", "N" | Inventario_atvos_21_27_part_*.xlsx |
| `Reforma` | Flag de reforma do talhão | str | — | "S", "N" | Inventario_atvos_21_27_part_*.xlsx |
| `TP_REFORMA` | Tipo de reforma | str | — | "Convencional", "Inverno", "18 Meses" | Inventario_atvos_21_27_part_*.xlsx |

### Produção Estimada (valores imputados na Silver quando faltantes)

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `AREA_PROD` | Área de produção estimada | float64 | ha | > 0 e <= AREA_HA | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_PROD` | Toneladas de cana por hectare estimadas | float64 | t/ha | 20-150 | Inventario_atvos_21_27_part_*.xlsx |
| `TON_ESTIM` | Toneladas totais estimadas (`AREA_PROD` x `TCH_PROD`) | float64 | t | > 0 | Inventario_atvos_21_27_part_*.xlsx |

### Reestimativa de Produção

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `AREA_REEST` | Área considerada na reestimativa de produção | float64 | ha | > 0 | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_REEST` | TCH reestimado | float64 | t/ha | 20-150 | Inventario_atvos_21_27_part_*.xlsx |
| `TON_REEST` | Toneladas reestimadas | float64 | t | > 0 | Inventario_atvos_21_27_part_*.xlsx |

### Muda e Formação

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `AREA_MUDA` | Área destinada a muda | float64 | ha | > 0 | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_MUDA` | TCH de muda | float64 | t/ha | 20-100 | Inventario_atvos_21_27_part_*.xlsx |
| `TON_MUDA` | Toneladas de muda | float64 | t | > 0 | Inventario_atvos_21_27_part_*.xlsx |

### Colheita e Encerramento

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `AREA_COLHIDA` | Área efetivamente colhida | float64 | ha | > 0 e <= AREA_HA | Inventario_atvos_21_27_part_*.xlsx |
| `OBJETIVO` | Objetivo do talhão na safra | str | — | "Safra", "Muda", "Sem Objetivo" | Inventario_atvos_21_27_part_*.xlsx |
| `SIT_TALHAO` | Situação atual do talhão | str | — | "Fechado", "Cana Planta", etc. | Inventario_atvos_21_27_part_*.xlsx |
| `DATA_FECHA` | Data de fechamento do ciclo | datetime64 | — | >= 2018 | Inventario_atvos_21_27_part_*.xlsx |
| `CANA_ENT` | Cana entregue na usina | float64 | t | > 0 | Inventario_atvos_21_27_part_*.xlsx |
| `ULT_CORTE` | Data do último corte registrado | datetime64 | — | >= 2010 | Inventario_atvos_21_27_part_*.xlsx |

### Ocorrências e Caracterizações

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `FG_OCORREN` | Flag de ocorrência (S = sim, F = fim) | str | — | "S", "F" | Inventario_atvos_21_27_part_*.xlsx |
| `DT_OCORREN` | Data da ocorrência registrada | datetime64 | — | >= 2020 | Inventario_atvos_21_27_part_*.xlsx |
| `DT_CARACT` | Data do evento de caracterização | datetime64 | — | >= 2025 | Inventario_atvos_21_27_part_*.xlsx |
| `CARACT` | Tipo de caracterização | str | — | "TRANSF. AREA FORNECEDOR", etc. | Inventario_atvos_21_27_part_*.xlsx |
| `Data_Geracao_Planilha` | Timestamp de geração do arquivo | datetime64 | — | 2026-04-23 | Inventario_atvos_21_27_part_*.xlsx |

### Flags de Negócio (adicionadas na Silver)

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Fonte original |
|--------|-----------|------|---------|----------------|----------------|
| `flag_bloco_ausente` | `True` quando `BLOCO` é nulo, indicando talhão sem bloco de colheita | bool | — | True/False | Derivada |
| `flag_caract_ausente` | `True` quando `DT_CARACT` e `CARACT` são nulos | bool | — | True/False | Derivada |
| `flag_cana_ent_ausente` | `True` quando `CANA_ENT` é nulo, indicando ausência de entrega registrada | bool | — | True/False | Derivada |
| `flag_tp_reforma_ausente` | `True` quando `TP_REFORMA` é nulo, indicando ausência de tipo de reforma informado | bool | — | True/False | Derivada |
| `flag_reestimativa_ausente` | `True` quando `AREA_REEST`, `TCH_REEST` e `TON_REEST` são nulos | bool | — | True/False | Derivada |
| `flag_muda_ausente` | `True` quando `AREA_MUDA`, `TCH_MUDA` e `TON_MUDA` são nulos | bool | — | True/False | Derivada |
| `flag_colheita_ausente` | `True` quando `AREA_COLHIDA` é nulo | bool | — | True/False | Derivada |
| `flag_talhao_aberto` | `True` quando `DATA_FECHA` é nulo, indicando ciclo ainda não encerrado | bool | — | True/False | Derivada |
