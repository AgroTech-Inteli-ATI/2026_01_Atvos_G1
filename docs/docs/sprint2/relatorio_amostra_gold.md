# Relatório — Amostra Gold | Sprint 2
**Data:** 22/05/2026 | **Amostra:** 270 talhões (30 por unidade industrial, com análise de solo)

---

## Contexto da Amostra

| Item | Valor |
|---|---|
| Total de talhões na base | 167.426 |
| Talhões com análise de solo | 74.768 (44,7%) |
| Talhões sem análise de solo | 92.658 (55,3%) |
| Talhões na amostra | 270 (30 por unidade) |
| Unidades industriais cobertas | 9 (UCP, URC, USL, e demais) |

> A amostra cobre apenas talhões **com** análise de solo. Os 92.658 talhões restantes já retornam `SEM_DADO` para calagem e gessagem — indicam necessidade de coleta de solo antes de qualquer recomendação.

---

## Resultados por Processo

### Calagem

| Resultado | Talhões |
|---|---|
| **Precisa calagem — incorporada** (cana planta, 150 dias antes) | **23** |
| **Precisa calagem — superficial** (cana soca, 60 dias antes) | **55** |
| Solo com V% adequado (≥ 60%) — sem necessidade | 129 |
| Categoria inapta (em reforma, pousio, etc.) | 63 |

Dose média nos talhões que precisam: **3,2 t/ha** (min 0,1 — max 9,1 t/ha)

> ⚠️ Parâmetro pendente de validação: V% alvo = 60% (padrão do setor).

---

### Gessagem

| Resultado | Talhões |
|---|---|
| **Precisa gessagem** (Ca subsolo < 4 e m% > 40%) | **11** |
| Não indicada | 259 |

> A gessagem tem critério duplo — ambas as condições precisam ser verdadeiras simultaneamente. Baixa incidência na amostra é esperada.
> ⚠️ Tabela argila × textura pendente de validação PO.

---

### Fosfatagem (dose de manutenção)

| Resultado | Talhões |
|---|---|
| **Com dose calculada — cana soca** | **163** |
| **Com dose calculada — cana planta** | **44** |
| Categoria inapta | 63 |

Dose média: **31,7 kg P₂O₅/ha** (min 4,8 — max 64,0 kg P₂O₅/ha)

> ⚠️ Implementação atual cobre apenas dose de manutenção (exportação × TCH). Dose de correção por deficiência de P no solo aguarda validação dos limiares críticos pela ATVOS.

---

### Erradicação de Soqueira

| Prioridade | Talhões |
|---|---|
| **MÉDIA** — TCH < 55 t/ha | **3** |
| **BAIXA** — corte ≥ 6°, TCH ok (monitorar) | **4** |
| Sem indicação | 16 |
| Não elegível (cana planta, em reforma, etc.) | 247 |

> ⚠️ Limiar TCH < 55 t/ha e corte limite ≥ 6° pendentes de validação pela ATVOS. Na amostra restrita a talhões com solo, a maioria são cana planta (não elegíveis para erradicação).

---

### Janela de Plantio

| Resultado | Talhões |
|---|---|
| **Dentro da janela ideal** (colheita mai–nov) | **135** |
| **Fora da janela ideal** ⚠️ | **107** |
| Categoria inapta | 28 |

> 107 de 242 talhões elegíveis (44%) têm colheita estimada fora de mai–nov — risco de brotações comprometidas no inverno. Este número merece atenção no planejamento.
> ⚠️ Regra atual usa janela mai–nov (Centro-Sul). Matriz de Aptidão por mês (mencionada no TAP) aguarda detalhamento pela ATVOS.

---

## Pendências para Validação com a ATVOS

| # | Processo | Parâmetro | Status |
|---|---|---|---|
| 1 | Calagem | V% alvo = 60% | ⏳ Aguarda confirmação |
| 2 | Gessagem | Tabela argila (g/kg) por textura | ⏳ Aguarda confirmação |
| 3 | Fosfatagem | Dose de correção por deficiência de P | ⏳ Aguarda limiares críticos |
| 4 | Erradicação | TCH crítico (55 t/ha) e corte limite (6°) | ⏳ Aguarda confirmação |
| 5 | Janela de plantio | Matriz de Aptidão por mês | ⏳ Aguarda estrutura da matriz |
| 6 | Pipeline | TCH_PROD virá dos modelos ATVOS (Sprint 3) | 🔜 Sprint 3 |

---

*Gerado em: 22/05/2026 | Pipeline: `src/pipeline_gold.py` | Dados: `data/gold/amostra_gold_2026-05-22.parquet`*
