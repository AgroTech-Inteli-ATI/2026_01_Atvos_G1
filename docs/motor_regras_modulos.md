# Módulos do Motor de Regras — Arquitetura por Processo

**Sprint:** 2 | **Atualizado:** 2026-05-21  
**Caminho dos arquivos:** `src/rules/`

---

## Contrato comum a todos os módulos

Antes de entrar em cada processo, o padrão que **todos** os arquivos seguem:

```python
# Entrada
def calcular_<processo>(talhao: dict) -> dict

# Saída — sempre estas três chaves, sem exceção
{
    "orientacao":      str,         # texto para o agrônomo
    "valor_calculado": float | None, # dose calculada ou None
    "regra_acionada":  str          # código da condição disparada
}
```

Campo nulo → retorna `sem_dado("nome_do_campo")` e encerra.  
Regra inaplicável → retorna `nao_se_aplica("motivo")` e encerra.  
Nunca levanta exceção.

---

## calagem.py

**Processo:** Correção de pH do solo via aplicação de calcário.  
**Status:** 🔴 Aguarda dados de análise de solo (retorna `SEM_DADO` hoje).

### Campos de entrada

| Campo | Origem | Tipo | Unidade | Observação |
|---|---|---|---|---|
| `ph_solo` | Análise de solo | `float` | — | pH em água |
| `ctc` | Análise de solo | `float` | mmolc/dm³ | CTC a pH 7 |
| `v_atual` | Análise de solo | `float` | % | Saturação de bases atual |
| `v_alvo` | Análise de solo | `float` | % | Saturação alvo — definida pelo agrônomo Atvos |
| `categoria` | Silver | `str` | — | `"Formação"` ou `"Cana Soca"` |

### Árvore de decisão

```
SE ph_solo, ctc ou v_atual for nulo
  → SEM_DADO

SE ph_solo ≥ 6.0
  → "Sem necessidade de calagem"
  → valor_calculado = 0.0
  → regra = "ph_adequado"

SE 5.5 ≤ ph_solo < 6.0
  → dose = _calcular_dose() × 0.5   (preventiva)
  → "Calagem preventiva superficial: X t/ha"
  → regra = "ph_levemente_acido"

SE ph_solo < 5.5 E categoria em {"Formação", "Muda"}
  → dose = _calcular_dose()          (plena, incorporada)
  → "Calagem incorporada: X t/ha"
  → regra = "ph_baixo_cana_planta"

SE ph_solo < 5.5 E categoria == "Cana Soca"
  → dose = _calcular_dose() × 0.5   (reduzida, superficial)
  → "Calagem superficial: X t/ha"
  → regra = "ph_baixo_cana_soca"
```

### Fórmula de dose

```
NC (t/ha) = [(V_alvo − V_atual) × CTC] / (PRNT × 10)
```

| Parâmetro | Valor padrão | Validar com PO |
|---|---|---|
| `PRNT` | 80% | Sim — depende do fornecedor de calcário da Atvos |
| `V_ALVO_PADRAO` | 60% | Sim — pode variar por unidade industrial |
| `DOSE_MAX_T_HA` | 6.0 t/ha | Sim — limite de segurança por aplicação |
| `PH_ADEQUADO` | 6.0 | Sim |
| `PH_CRITICO` | 5.5 | Sim |

---

## gessagem.py

**Processo:** Aplicação de gesso agrícola para corrigir toxidez por alumínio em subsolo.  
**Status:** ⚠️ Parcial — funciona com textura do solo (Silver); retorna `SEM_DADO` sem saturação de Al³⁺.

### Campos de entrada

| Campo | Origem | Tipo | Unidade | Observação |
|---|---|---|---|---|
| `saturacao_al` | Análise de solo | `float` | % | Saturação por Al³⁺ |
| `ctc` | Análise de solo | `float` | mmolc/dm³ | Necessário para calcular dose |
| `desc_ambiente` | Silver | `str` | — | `"Argiloso"`, `"Arenoso"`, etc. |

### Árvore de decisão

```
SE saturacao_al disponível:
  SE Al³⁺ > 20%
    SE ctc disponível
      → dose = fator_textura × CTC / 10   (máx. 4 t/ha)
      → "Gessagem recomendada: X t/ha"
      → regra = "al_alto_gessagem_indicada"
    SE ctc indisponível
      → "Gessagem indicada — CTC ausente, dose a calcular"
      → regra = "al_alto_ctc_ausente"
  SE Al³⁺ ≤ 20%
    → "Gessagem não indicada"
    → valor_calculado = 0.0
    → regra = "al_dentro_limite"

SE saturacao_al indisponível (situação atual):
  SE desc_ambiente reconhecido
    → orienta por textura + solicita análise
    → valor_calculado = None
    → regra = "textura_{classe}_sem_analise_al"
  SE desc_ambiente nulo
    → SEM_DADO
```

### Fórmula de dose

```
dose (t/ha) = fator_textura × CTC / 10   (máx. 4 t/ha)
```

| Textura | Fator | Dose com CTC=80 mmolc/dm³ |
|---|---|---|
| Arenoso | 0.5 | 4.0 t/ha (limitado ao máx.) |
| Médio | 1.0 | 4.0 t/ha (limitado ao máx.) |
| Argiloso | 1.5 | 4.0 t/ha (limitado ao máx.) |
| Muito Argiloso | 2.0 | 4.0 t/ha (limitado ao máx.) |

| Parâmetro | Valor padrão | Validar com PO |
|---|---|---|
| `SAT_AL_CRITICA` | 20% | Sim |
| `DOSE_MAX_T_HA` | 4.0 t/ha | Sim |

---

## fosfatagem.py

**Processo:** Adubação fosfatada corretiva para elevar P disponível no solo.  
**Status:** 🔴 Aguarda dados de análise de solo (retorna `SEM_DADO` hoje).

### Campos de entrada

| Campo | Origem | Tipo | Unidade | Observação |
|---|---|---|---|---|
| `p_disponivel` | Análise de solo | `float` | mg/dm³ | P pelo método Mehlich-1 |
| `categoria` | Silver | `str` | — | Define se é cana-planta ou cana-soca |

### Árvore de decisão

```
SE p_disponivel for nulo
  → SEM_DADO

Classificar P pelo teor:
  P < 8 mg/dm³   → classe "muito_baixo"
  P < 15 mg/dm³  → classe "baixo"
  P < 30 mg/dm³  → classe "medio"
  P ≥ 30 mg/dm³  → classe "alto"

SE classe == "alto"
  → "Fosfatagem não necessária"
  → valor_calculado = 0.0

SE classe != "alto" E categoria == "cana_planta"
  → dose = dose_base (tabela abaixo)
  → "Fosfatagem corretiva (cana-planta): X kg P₂O₅/ha"

SE classe != "alto" E categoria == "cana_soca"
  → dose = dose_base × 0.5   (manutenção, não corretiva)
  → "Fosfatagem de manutenção (cana-soca): X kg P₂O₅/ha"
```

### Tabela de doses

| Classe | Faixa P (mg/dm³) | Dose cana-planta | Dose cana-soca |
|---|---|---|---|
| Muito Baixo | < 8 | 120 kg P₂O₅/ha | 60 kg P₂O₅/ha |
| Baixo | 8 – 14 | 80 kg P₂O₅/ha | 40 kg P₂O₅/ha |
| Médio | 15 – 29 | 40 kg P₂O₅/ha | 20 kg P₂O₅/ha |
| Alto | ≥ 30 | — | — |

| Parâmetro | Valor padrão | Validar com PO |
|---|---|---|
| `P_MUITO_BAIXO` | 8 mg/dm³ | Sim — Embrapa/IAC, pode variar por região |
| `P_BAIXO` | 15 mg/dm³ | Sim |
| `P_MEDIO` | 30 mg/dm³ | Sim |
| `DOSE_MUITO_BAIXO_KG` | 120 kg/ha | Sim |
| `FATOR_CANA_SOCA` | 0.5 | Sim |

---

## erradicacao.py

**Processo:** Decisão de reforma/substituição do canavial com base em produtividade e idade.  
**Status:** ✅ 100% implementado com dados da Silver.

### Campos de entrada

| Campo | Origem | Tipo | Unidade | Observação |
|---|---|---|---|---|
| `no_corte` | Silver (`NO_CORTE`) | `int` | — | 0 = formação, 1 = 1º socamento... |
| `tch_prod` | Silver (`TCH_PROD`) | `float` | t/ha | Produtividade estimada |
| `categoria` | Silver (`CATEGORIA`) | `str` | — | `"Formação"`, `"Cana Soca"`, `"Muda"` |
| `reforma` | Silver (`Reforma`) | `str` | — | `"S"` ou `"N"` |

### Árvore de decisão

```
SE categoria em {"Formação", "Muda"}  → NAO_SE_APLICA
SE reforma == "S"                     → NAO_SE_APLICA (já programada pela usina)
SE tch_prod nulo                      → SEM_DADO
SE no_corte nulo                      → SEM_DADO

━━ Canavial tardio: NO_CORTE ≥ 5 ━━━━━━━━━━━━━━━━━━━━━━━
  TCH < 50 t/ha    → ERRADICAÇÃO RECOMENDADA — alta prioridade
                     regra = "tardio_tch_critico"

  50 ≤ TCH ≤ 70    → AVALIAR ERRADICAÇÃO — custo-benefício crítico
                     regra = "tardio_tch_alerta"

  TCH > 70 t/ha    → MONITORAR — canavial tardio mas produtivo
                     regra = "tardio_tch_adequado"

━━ Ciclo médio: NO_CORTE 3 ou 4 ━━━━━━━━━━━━━━━━━━━━━━━━
  TCH < 40 t/ha    → INVESTIGAR — baixa produtividade precoce
                     regra = "medio_tch_investigar"

  40 ≤ TCH ≤ 70    → MONITORAR — reavaliar na próxima safra
                     regra = "medio_tch_monitorar"

  TCH > 70 t/ha    → NÃO RECOMENDADA — bom desempenho
                     regra = "medio_tch_adequado"

━━ Canavial jovem: NO_CORTE 1 ou 2 ━━━━━━━━━━━━━━━━━━━━━
  TCH < 40 t/ha    → INVESTIGAR — falha grave de campo
                     regra = "jovem_tch_investigar"

  TCH ≥ 40 t/ha    → NÃO RECOMENDADA — canavial jovem
                     regra = "jovem_tch_adequado"
```

| Parâmetro | Valor padrão | Validar com PO |
|---|---|---|
| `CORTE_TARDIO` | 5 | Sim — limiar de "canavial velho" |
| `TCH_CRITICO` | 50 t/ha | Sim |
| `TCH_ALERTA` | 70 t/ha | Sim |
| `TCH_INVESTIGACAO` | 40 t/ha | Sim |

---

## janela_plantio.py

**Processo:** Avaliação da época de plantio em relação à janela ideal para a variedade e tipo de reforma.  
**Status:** ✅ Implementado com dados da Silver.

### Campos de entrada

| Campo | Origem | Tipo | Unidade | Observação |
|---|---|---|---|---|
| `data_plantio` | Silver (`DATA_PLANTIO`) | `datetime` | — | Pode ser nulo |
| `man_hipot` | Silver (`MAN_HIPOT`) | `str` | — | `"Precoce"`, `"Média"`, `"Tardia"`, `"A Definir"` |
| `tp_reforma` | Silver (`TP_REFORMA`) | `str` | — | `"Convencional"`, `"Inverno"`, `"18 Meses"` |
| `categoria` | Silver (`CATEGORIA`) | `str` | — | Filtro — aplica só em `"Formação"` ou `"Muda"` |

### Árvore de decisão

```
SE categoria NOT IN {"Formação", "Muda"}
  → NAO_SE_APLICA

Determinar janela vigente (prioridade: TP_REFORMA > MAN_HIPOT):
  TP_REFORMA == "Inverno"   → janela = abril – julho
  TP_REFORMA == "18 Meses"  → janela = março – maio
  MAN_HIPOT == "Precoce"    → janela = abril – junho
  MAN_HIPOT == "Média"      → janela = junho – agosto
  MAN_HIPOT == "Tardia"     → janela = agosto – outubro
  MAN_HIPOT == "A Definir"  → orientar a definir com agrônomo
  Nenhum disponível         → SEM_DADO

SE data_plantio informada:
  mês ∈ janela        → DENTRO DA JANELA
  mês adjacente       → LIMITE DA JANELA
  mês fora            → FORA DA JANELA — avaliar impacto na maturação

SE data_plantio nula:
  → retorna orientação com a janela recomendada (sem avaliação de real vs. ideal)
```

### Janelas por configuração

| Configuração | Meses ideais | Meses (número) |
|---|---|---|
| MAN_HIPOT Precoce | Abril – Junho | 4 a 6 |
| MAN_HIPOT Média | Junho – Agosto | 6 a 8 |
| MAN_HIPOT Tardia | Agosto – Outubro | 8 a 10 |
| TP_REFORMA Inverno | Abril – Julho | 4 a 7 |
| TP_REFORMA 18 Meses | Março – Maio | 3 a 5 |

> **Atenção:** os meses acima são referência para o Centro-Oeste/SP. Validar com o PO Atvos para cada unidade industrial (UMV, URC, UEL).

---

## Resumo dos parâmetros a validar com o PO Atvos

| Módulo | Parâmetro | Valor atual | Por que validar |
|---|---|---|---|
| calagem | `PH_CRITICO` | 5.5 | Define quando calagem é obrigatória |
| calagem | `V_ALVO_PADRAO` | 60% | Pode variar por unidade industrial |
| calagem | `PRNT_PADRAO` | 80% | Depende do fornecedor de calcário contratado |
| calagem | `DOSE_MAX_T_HA` | 6.0 t/ha | Limite operacional da Atvos |
| gessagem | `SAT_AL_CRITICA` | 20% | Limiar de toxidez por Al³⁺ |
| gessagem | `DOSE_MAX_T_HA` | 4.0 t/ha | Limite operacional |
| fosfatagem | Todos os limiares de P | Ver tabela | Podem variar por análise IAC vs. Embrapa |
| fosfatagem | Todas as doses | Ver tabela | Dependem do histórico de adubação de cada área |
| erradicacao | `CORTE_TARDIO` | 5 | Pode ser 4 em áreas de alta pressão de praga |
| erradicacao | `TCH_CRITICO` | 50 t/ha | Ponto de corte econômico — varia com o preço da cana |
| janela_plantio | Todos os meses | Ver tabela | Variam por unidade industrial e safra |
