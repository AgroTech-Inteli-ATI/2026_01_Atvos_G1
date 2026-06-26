---
title: "Regras de Limpeza"
sidebar_position: 2
---

# Regras de Limpeza — Camada Silver

**Documento aprovado em:** 2026-05-07  
**Responsável:** Módulo 10 — Atvos G1  
**Desbloqueia:** Task 1.5 (script de limpeza)

---

## 1. Resumo das Regras

| Tipo | Critério | Acao |
|------|----------|------|
| **100% nulos** | Coluna inteiramente nula | Deletar coluna |
| **Nulo = negócio** | Null tem significado (ausência é esperada) | Criar flag `flag_*` (True/False) + manter nulo |
| **Nulo = faltante** | Dado deveria existir mas não foi coletado | Imputar mediana por `UNID_IND` |
| **Nulo = geo** | Coordenada ou zona sem cobertura de sensor/mapeamento | Manter nulo, cruzar com outro dataset |
| **Poucos nulos** | Sem critério de negócio claro e < ~6% | Manter como está |

---

## 2. Colunas Deletadas

### 2a. Índice de exportação (sem valor de negócio)

| Coluna | Arquivo | Motivo |
|--------|---------|--------|
| `Unnamed: 0` | Inventario parts 2 e 4 | Índice gerado por exportação anterior do pandas |

### 2b. 100% nulos (detectados dinamicamente)

| Coluna | Arquivo | Motivo |
|--------|---------|--------|
| `AREA_REEST2` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |
| `TCH_REEST2` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |
| `TON_REEST2` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |
| `AREA_REEST3` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |
| `TCH_REEST3` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |
| `TON_REEST3` | Inventario parts 2 e 4 | 100% nulo — coluna reservada não utilizada |

---

## 3. Flags de Negócio (Nulo = Significado)

Flag é `True` quando **todas** as colunas do grupo são nulas simultaneamente.  
As colunas originais são **mantidas** com seus nulos intactos.

| Flag Criada | Colunas Gatilho | % True (part 2) | % True (part 4) | Interpretação |
|-------------|-----------------|-----------------|-----------------|---------------|
| `flag_bloco_ausente` | `BLOCO` | 23,5% | 23,5% | Talhão não atribuído a nenhum bloco de colheita |
| `flag_caract_ausente` | `DT_CARACT`, `CARACT` | 99,8% | 99,8% | Sem evento de caracterização registrado no período |
| `flag_cana_ent_ausente` | `CANA_ENT` | 98,9% | 98,9% | Talhão não entregou cana nessa safra |
| `flag_tp_reforma_ausente` | `TP_REFORMA` | 69,3% | 69,6% | Talhão não passou por reforma (`Reforma = 'N'`) |
| `flag_reestimativa_ausente` | `AREA_REEST`, `TCH_REEST`, `TON_REEST` | 56,2% | 55,5% | Sem reestimativa de produção registrada |
| `flag_muda_ausente` | `AREA_MUDA`, `TCH_MUDA`, `TON_MUDA` | 94,0% | 94,4% | Talhão não é destinado a muda/formação |
| `flag_colheita_ausente` | `AREA_COLHIDA` | 38,6% | 38,2% | Talhão ainda não foi colhido na safra |
| `flag_talhao_aberto` | `DATA_FECHA` | 35,5% | 35,1% | Talhão ainda aberto (ciclo não encerrado) |

---

## 4. Imputação de Produção (Nulo = Faltante)

As três colunas têm relação física: **TON_ESTIM = AREA_PROD × TCH_PROD**.  
A imputação ocorre em dois passos sequenciais (função `imputar_producao()`):

### Passo 1 — Derivação matemática (sem estimativa estatística)

Quando dois dos três campos estão presentes, o terceiro é calculado exatamente pela relação física.  
Isso mantém consistência interna sem introduzir viés estatístico.

| Caso | Cálculo |
|------|---------|
| `AREA_PROD` ausente | `AREA_PROD = TON_ESTIM / TCH_PROD` (requer TCH_PROD > 0) |
| `TCH_PROD` ausente | `TCH_PROD = TON_ESTIM / AREA_PROD` (requer AREA_PROD > 0) |
| `TON_ESTIM` ausente | `TON_ESTIM = AREA_PROD × TCH_PROD` |

### Passo 2 — Mediana estratificada em hierarquia de 4 níveis

Para casos onde nenhuma derivação é possível (todos os três campos ausentes), aplica-se mediana por grupo em ordem decrescente de especificidade:

| Nível | Agrupamento | Ativa quando |
|-------|------------|--------------|
| 1 | `UNID_IND + CATEGORIA + faixa_corte` | Grupo com ≥ 5 amostras válidas |
| 2 | `UNID_IND + CATEGORIA` | Grupo do nível 1 muito pequeno |
| 3 | `UNID_IND` | Grupo do nível 2 muito pequeno |
| 4 | Mediana global | Garante completude — sem nulos residuais |

**Justificativa do nível 1 vs. mediana simples por UNID_IND:**  
TCH_PROD varia ~25% entre cana-planta (NO_CORTE ≤ 1) e soca tardia (NO_CORTE ≥ 7), conforme curva de senescência documentada pela Embrapa Agroenergia. Usar a mediana da unidade sem estratificação mistura esses perfis e introduz viés sistemático na variável mais importante do modelo de erradicação.

**Faixas de corte (função `_faixa_corte()`):**

| Faixa | NO_CORTE | Perfil |
|-------|----------|--------|
| `plantio` | ≤ 1 | Cana-planta — TCH máximo |
| `soca_nova` | 2–3 | Curva descendente inicial |
| `soca_media` | 4–6 | Produtividade intermediária |
| `soca_tardia` | ≥ 7 | Candidatos a erradicação |

| Coluna | Part 2: nulos imputados | Part 4: nulos imputados | Justificativa |
|--------|------------------------|------------------------|---------------|
| `AREA_PROD` | 14.210 | 4.900 | Todo talhão ativo deveria ter área de produção |
| `TCH_PROD` | 14.210 | 4.900 | Todo talhão ativo deveria ter TCH estimado |
| `TON_ESTIM` | 14.210 | 4.900 | Derivado de AREA_PROD × TCH_PROD |

---

## 5. Colunas Geográficas (Manter para Cruzamento Posterior)

| Coluna | % Nulo (part 2) | % Nulo (part 4) | Dataset sugerido para cruzamento |
|--------|-----------------|-----------------|----------------------------------|
| `LATITUDE` | 18,8% | 18,5% | Shapefile de talhões / IBGE |
| `LONGITUDE` | 18,8% | 18,5% | Shapefile de talhões / IBGE |
| `ZONA_AGRO_ECOLOGICA` | 17,7% | 18,3% | Zoneamento agrícola MAPA |
| `DESC_ZONA` | 17,7% | 18,3% | Par com ZONA_AGRO_ECOLOGICA |
| `DESC_AMBIENTE` | 36,1% | 35,5% | Dataset de análise de solo |

---

## 6. Poucos Nulos (Manter como Está)

| Coluna | % Nulo | Decisão |
|--------|---------|---------|
| `AREA_DANO` | ~0,1% | Manter |
| `TIPO_CONTRATO` | ~0,1% | Manter |
| `FORNEC` | ~0,1% | Manter |
| `OBJETIVO` | ~0,5% | Manter |
| `SISTEMA_COL` | ~0,6% | Manter |
| `MAN_HIPOT` | ~2,8% | Manter (categórica, "A Definir" é valor válido) |
| `SIST_PLANT` | ~2,8% | Manter |
| `ULT_CORTE` | ~5,5% | Manter (data — talhões sem corte anterior) |
| `DATA_PLANTIO` | ~10,3% | Manter (data — talhões em reforma podem não ter data) |

---

## 7. Outras Transformações Aplicadas

| Transformação | Função | Detalhe |
|---------------|--------|---------|
| Correção de encoding | `corrigir_encoding()` | Corrige double-encoding latin-1/UTF-8 em colunas texto |
| Padronização de texto | `padronizar_texto()` | `str.strip()` em todas as colunas object |
| Padronização de datas | `padronizar_datas()` | Converte colunas com `data`/`date`/`dt_` no nome para `datetime64` |
| Formato de saída | `salvar_silver()` | Parquet em `data/processed/` |
