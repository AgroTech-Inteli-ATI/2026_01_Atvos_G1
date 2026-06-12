# Motor de Regras Agronômicas — Arquitetura e Handoff

**Sprint:** 2  
**Última atualização:** 2026-05-21  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Visão Geral

O Motor de Regras é a **Camada Gold** do pipeline de dados Atvos. Ele lê os dados limpos da Camada Silver (`data/processed/`), aplica heurísticas agronômicas do PDA (Plano de Desenvolvimento Agrícola) para cada talhão, e gera um arquivo com orientações operacionais (`data/gold/`).

```
data/raw/          ←  arquivos Excel originais (Atvos)
     ↓  src/processing/run_processing.py
data/processed/    ←  Camada Silver (Parquet limpo)
     ↓  src/pipeline_gold.py
data/gold/         ←  Camada Gold (orientações por talhão)
```

---

## 2. Estrutura de Arquivos

```
src/
├── rules/
│   ├── _base.py           ← contrato de interface + helpers compartilhados
│   ├── __init__.py        ← exporta o dict REGRAS {processo → função}
│   ├── calagem.py         ← correção de pH do solo
│   ├── gessagem.py        ← aplicação de gesso agrícola
│   ├── fosfatagem.py      ← adubação fosfatada corretiva
│   ├── erradicacao.py     ← decisão de reforma/substituição do canavial
│   └── janela_plantio.py  ← adequação da época de plantio
└── pipeline_gold.py       ← orquestrador: lê Silver, aplica regras, salva Gold

data/
├── processed/             ← Silver (entrada do pipeline Gold)
└── gold/                  ← Gold (saída: orientacoes_YYYY-MM-DD.parquet + .csv)
```

---

## 3. Contrato de Interface (lei para todos os módulos)

Cada módulo expõe **uma única função principal** com a assinatura:

```python
def calcular_<processo>(talhao: dict) -> dict
```

### Entrada

Um `dict` gerado automaticamente por `pipeline_gold._preparar_talhao()` a partir de uma linha do DataFrame Silver. Os campos disponíveis estão documentados na seção 6.

### Saída

Sempre um `dict` com **exatamente estas três chaves**:

| Chave | Tipo | Descrição |
|---|---|---|
| `orientacao` | `str` | Texto descritivo da recomendação para o agrônomo |
| `valor_calculado` | `float \| None` | Dose ou índice numérico, quando calculável |
| `regra_acionada` | `str` | Código snake_case que identifica qual condição disparou |

### Regras de ouro

- **Nunca levantar exceção.** Campo ausente → chamar `sem_dado("nome_do_campo")`.
- **Nunca retornar estrutura diferente.** O pipeline depende das três chaves acima.
- **Nunca acessar arquivos ou banco de dados diretamente.** Tudo chega via `talhao: dict`.

### Valores reservados de `regra_acionada`

| Prefixo | Significado |
|---|---|
| `dado_ausente_*` | Campo obrigatório nulo ou faltante |
| `categoria_*` | Regra não se aplica a esta categoria de talhão |
| `reforma_ja_programada` | A usina já agendou reforma — regra ignorada |
| `erro_execucao` | Exceção capturada pelo pipeline (nunca deve ocorrer) |

---

## 4. Helpers em `_base.py`

Importe daqui para não duplicar lógica entre módulos:

```python
from rules._base import sem_dado, nao_se_aplica, resultado, numerico, texto

# Retorna SEM_DADO padronizado quando campo obrigatório é nulo
sem_dado("ph_solo")
# → {"orientacao": "SEM_DADO", "valor_calculado": None, "regra_acionada": "dado_ausente_ph_solo"}

# Retorna NAO_SE_APLICA quando a regra não é válida para este talhão
nao_se_aplica("categoria_formacao_ou_muda")
# → {"orientacao": "NAO_SE_APLICA", "valor_calculado": None, "regra_acionada": "categoria_formacao_ou_muda"}

# Constrói resultado válido (arredonda valor a 2 casas)
resultado("Aplicar 2.5 t/ha de calcário", 2.5, "ph_baixo_cana_planta")

# Valida se um campo numérico é utilizável (não None, não NaN, não inf)
numerico(talhao.get("tch_prod"))  # True / False

# Valida se uma string não está vazia
texto(talhao.get("categoria"))    # True / False
```

Também disponível em `_base.py`:

```python
classificar_textura(desc_ambiente)
# "Argiloso" → "argiloso" | "Arenoso" → "arenoso" | None se não reconhecido

ciclo_do_talhao(categoria)
# "Formação" → "cana_planta" | "Cana Soca" → "cana_soca" | None
```

---

## 5. Status dos Módulos

| Módulo | Dados necessários | Fonte | Status |
|---|---|---|---|
| `erradicacao.py` | `NO_CORTE`, `TCH_PROD`, `CATEGORIA`, `Reforma` | **Silver (disponível)** | ✅ Implementado e funcional |
| `janela_plantio.py` | `MAN_HIPOT`, `DATA_PLANTIO`, `TP_REFORMA`, `CATEGORIA` | **Silver (disponível)** | ✅ Implementado e funcional |
| `gessagem.py` | `saturacao_al`, `ctc` (análise solo) + `DESC_AMBIENTE` (Silver) | **Misto** | ⚠️ Parcial — funciona por textura; retorna SEM_DADO sem análise de Al³⁺ |
| `calagem.py` | `ph_solo`, `ctc`, `v_atual`, `v_alvo` | **Análise de solo (não integrada)** | 🔴 SEM_DADO — aguarda fonte de dados de solo |
| `fosfatagem.py` | `p_disponivel` (P Mehlich-1) | **Análise de solo (não integrada)** | 🔴 SEM_DADO — aguarda fonte de dados de solo |

---

## 6. Campos do Dicionário `talhao`

O dict de entrada contém **dois grupos de campos**:

### 6.1 Campos disponíveis agora (da Silver)

| Chave no dict | Coluna Silver | Tipo | Exemplo |
|---|---|---|---|
| `id_talhao` | `CHAVESIG` | `int` | `410149` |
| `chave` | `CHAVE` | `str` | `"410149-1-8"` |
| `unidade` | `DESC_EMPRESA` | `str` | `"UMV"` |
| `unid_ind` | `UNID_IND` | `int` | `21` |
| `safra` | `SAFRA` | `int` | `22223` |
| `no_corte` | `NO_CORTE` | `int` | `4` |
| `categoria` | `CATEGORIA` | `str` | `"Cana Soca"` |
| `man_hipot` | `MAN_HIPOT` | `str` | `"Precoce"` |
| `data_plantio` | `DATA_PLANTIO` | `datetime` | `2024-05-10` |
| `tp_reforma` | `TP_REFORMA` | `str` | `"Convencional"` |
| `reforma` | `Reforma` | `str` | `"S"` ou `"N"` |
| `tch_prod` | `TCH_PROD` | `float` | `72.5` |
| `area_prod` | `AREA_PROD` | `float` | `48.3` |
| `ton_estim` | `TON_ESTIM` | `float` | `3500.0` |
| `area_ha` | `AREA_HA` | `float` | `50.0` |
| `desc_ambiente` | `DESC_AMBIENTE` | `str` | `"Argiloso"` |
| `de_tp_solo` | `DE_TP_SOLO` | `str` | `"Latossolo Vermelho"` |
| `ambiente` | `AMBIENTE` | `str` | `"B"` |

### 6.2 Campos ainda não integrados (retornam `None` hoje)

Quando a fonte de análise de solo for integrada, o mapeamento deve ser feito **somente em `pipeline_gold._preparar_talhao()`**. Os módulos de regra não precisam mudar.

| Chave no dict | Campo agronômico | Unidade | Usado por |
|---|---|---|---|
| `ph_solo` | pH em água | — | `calagem.py` |
| `ctc` | Capacidade de Troca Catiônica | mmolc/dm³ | `calagem.py`, `gessagem.py` |
| `v_atual` | Saturação de bases atual | % | `calagem.py` |
| `v_alvo` | Saturação de bases alvo | % | `calagem.py` |
| `p_disponivel` | P disponível Mehlich-1 | mg/dm³ | `fosfatagem.py` |
| `saturacao_al` | Saturação por Al³⁺ | % | `gessagem.py` |
| `ca_cmolc` | Cálcio | cmolc/dm³ | (reservado) |
| `mg_cmolc` | Magnésio | cmolc/dm³ | (reservado) |

---

## 7. Lógica de Cada Módulo

### 7.1 `erradicacao.py` — ✅ Funcional

**Pergunta:** este canavial deve ser erradicado e reformado?

```
SE categoria == "Formação" ou "Muda"    → NAO_SE_APLICA
SE reforma == "S"                       → NAO_SE_APLICA (já programada)
SE tch_prod é nulo                      → SEM_DADO
SE no_corte é nulo                      → SEM_DADO

━━ Canavial tardio (NO_CORTE ≥ 5) ━━
  TCH < 50 t/ha    → ERRADICAÇÃO RECOMENDADA  (alta prioridade)
  TCH 50–70 t/ha   → AVALIAR ERRADICAÇÃO      (custo-benefício crítico)
  TCH > 70 t/ha    → MONITORAR                (ainda produtivo)

━━ Ciclo médio (NO_CORTE 3 ou 4) ━━
  TCH < 40 t/ha    → INVESTIGAR               (baixa produtividade precoce)
  TCH 40–70 t/ha   → MONITORAR
  TCH > 70 t/ha    → NÃO RECOMENDADA

━━ Canavial jovem (NO_CORTE 1 ou 2) ━━
  TCH < 40 t/ha    → INVESTIGAR               (falha grave de campo)
  TCH ≥ 40 t/ha    → NÃO RECOMENDADA
```

**Limiares a validar com PO Atvos:** `CORTE_TARDIO = 5`, `TCH_CRITICO = 50`, `TCH_ALERTA = 70`, `TCH_INVESTIGACAO = 40`

---

### 7.2 `janela_plantio.py` — ✅ Funcional

**Pergunta:** o plantio está dentro da janela ideal para a maturação e tipo de reforma?

```
SE categoria NOT IN {"Formação", "Muda"}  → NAO_SE_APLICA
SE man_hipot == "A Definir"               → orientar a definir com agrônomo

Janelas por MAN_HIPOT (meses ideais):
  "Precoce"  → abril – junho
  "Média"    → junho – agosto
  "Tardia"   → agosto – outubro

Janelas por TP_REFORMA (sobrescreve MAN_HIPOT quando definido):
  "Inverno"   → abril – julho
  "18 Meses"  → março – maio

Com DATA_PLANTIO informada:
  → compara mês real com janela → DENTRO / LIMITE / FORA DA JANELA

Sem DATA_PLANTIO:
  → retorna orientação preventiva com a janela recomendada
```

**Meses a validar com PO Atvos** — variam por unidade industrial (UMV, URC, UEL) e microrregião.

---

### 7.3 `gessagem.py` — ⚠️ Parcial

**Pergunta:** o solo precisa de gesso agrícola para corrigir toxidez por Al³⁺?

```
SE saturacao_al disponível:
  SE Al³⁺ > 20%   → dose = _calcular_dose_gesso(ctc, textura)  → RECOMENDADA
  SE Al³⁺ ≤ 20%   → sem necessidade

SE saturacao_al indisponível (situação atual):
  Usa apenas DESC_AMBIENTE:
  "muito_argiloso" → "Avaliar — alta prioridade, solicitar análise"
  "argiloso"       → "Avaliar — solicitar análise de Al³⁺"
  "medio"          → "Avaliar conforme resultado de Al³⁺"
  "arenoso"        → "Raramente indicado — confirmar com análise"
  nulo             → SEM_DADO

Dose de gesso (Embrapa):
  dose (t/ha) = fator_textura × CTC / 10   (máx. 4 t/ha)
  fator: arenoso=0.5 | médio=1.0 | argiloso=1.5 | muito argiloso=2.0
```

---

### 7.4 `calagem.py` — 🔴 Aguarda dados de solo

**Pergunta:** o solo precisa de calcário para elevar o pH?

```
SE ph_solo é nulo  → SEM_DADO  (situação atual — dados não integrados)
SE ctc é nulo      → SEM_DADO
SE v_atual é nulo  → SEM_DADO

SE ph_solo ≥ 6.0   → sem necessidade
SE 5.5 ≤ pH < 6.0  → dose preventiva × 0.5, superficial
SE pH < 5.5 E cana-planta → dose plena, incorporada
SE pH < 5.5 E cana-soca   → dose × 0.5, superficial

Fórmula de dose (método saturação de bases — Embrapa/IAC):
  NC (t/ha) = [(V_alvo − V_atual) × CTC] / (PRNT × 10)
  CTC em mmolc/dm³ | PRNT = 80% (confirmar com PO) | máx. 6 t/ha
```

---

### 7.5 `fosfatagem.py` — 🔴 Aguarda dados de solo

**Pergunta:** o solo precisa de adubação fosfatada corretiva?

```
SE p_disponivel é nulo → SEM_DADO  (situação atual — dados não integrados)

Tabela de interpretação (P Mehlich-1):
  P < 8 mg/dm³   → Muito Baixo → 120 kg P₂O₅/ha (cana-planta)
  P < 15 mg/dm³  → Baixo      →  80 kg P₂O₅/ha
  P < 30 mg/dm³  → Médio      →  40 kg P₂O₅/ha
  P ≥ 30 mg/dm³  → Alto       →  sem necessidade

Cana-soca: dose × 0.5 (manutenção, não corretiva)
```

---

## 8. Como Adicionar uma Nova Fonte de Dados de Solo

Quando os dados de análise química chegarem, a mudança é **em um único lugar**:

**`src/pipeline_gold.py`, função `_preparar_talhao()`**

```python
# Antes (retorna None — campo não existe na Silver):
"ph_solo": safe("ph_solo"),

# Depois (mapeia coluna do novo dataset integrado ao Silver):
"ph_solo": safe("PH_AGUA"),   # nome exato da coluna no DataFrame Silver estendido
```

Os módulos de regra (`calagem.py`, etc.) **não precisam de nenhuma alteração**. Eles simplesmente deixarão de retornar `SEM_DADO` quando o campo passar a ter valor.

---

## 9. Como Adicionar uma Nova Regra

1. Crie `src/rules/nova_regra.py` seguindo o template:

```python
from ._base import sem_dado, nao_se_aplica, resultado, numerico, texto

def calcular_nova_regra(talhao: dict) -> dict:
    """
    Descrição do processo agronômico.

    Parameters
    ----------
    talhao : dict
        campo_x (tipo) descrição, unidade, ex: valor

    Returns
    -------
    dict com orientacao, valor_calculado, regra_acionada
    """
    campo = talhao.get("campo_x")
    if not numerico(campo):
        return sem_dado("campo_x")

    # ... lógica da regra ...

    return resultado("Descrição da ação", valor_float, "codigo_da_regra")
```

2. Registre em `src/rules/__init__.py`:

```python
from .nova_regra import calcular_nova_regra

REGRAS = {
    ...
    "nova_regra": calcular_nova_regra,   # adicionar aqui
}
```

O pipeline passa a incluir o novo processo automaticamente para todos os talhões.

---

## 10. Como Rodar o Pipeline

```bash
# Gera data/gold/orientacoes_YYYY-MM-DD.parquet + .csv
python src/pipeline_gold.py

# Mostra o relatório sem salvar (para testes)
python src/pipeline_gold.py --dry-run

# Testar um módulo individualmente
python -m src.rules.erradicacao
python -m src.rules.janela_plantio
```

### Pré-requisito

Os arquivos Silver precisam existir em `data/processed/`. Se não existirem:

```bash
python src/processing/run_processing.py
```

---

## 11. Formato do Output Gold

Arquivo: `data/gold/orientacoes_YYYY-MM-DD.parquet` (e `.csv` idêntico)

**Formato long:** uma linha por combinação (talhão × processo).

| Coluna | Tipo | Exemplo |
|---|---|---|
| `id_talhao` | int | `410149` |
| `chave` | str | `"410149-1-8"` |
| `unidade` | str | `"UMV"` |
| `safra` | int | `22223` |
| `processo` | str | `"erradicacao"` |
| `orientacao` | str | `"ERRADICAÇÃO RECOMENDADA: ..."` |
| `valor_calculado` | float | `45.0` |
| `regra_acionada` | str | `"tardio_tch_critico"` |
| `data_geracao` | date | `2026-05-21` |

Com 5 processos e N talhões, o Gold terá `N × 5` linhas.

---

## 12. Validação Rápida do Output

```python
import pandas as pd

df = pd.read_parquet("data/gold/orientacoes_2026-05-21.parquet")

# Verificar cobertura por processo
df.groupby("processo")["regra_acionada"].value_counts()

# Talhões com erradicação recomendada
df[(df["processo"] == "erradicacao") &
   (df["regra_acionada"] == "tardio_tch_critico")][["chave", "unidade", "valor_calculado"]]

# Proporção de SEM_DADO por processo (mede cobertura dos dados)
df["sem_dado"] = df["regra_acionada"].str.startswith("dado_ausente")
df.groupby("processo")["sem_dado"].mean().mul(100).round(1).rename("% SEM_DADO")
```

---

## 13. Decisões de Design Relevantes

| Decisão | Motivo |
|---|---|
| Uma função por módulo, não uma classe | Facilita testar isoladamente e paralelizar entre devs |
| `sem_dado()` em vez de exceção | O pipeline nunca deve travar por um campo nulo em um talhão |
| Formato long no Gold (talhão × processo) | Facilita filtros por processo no BI/dashboard |
| Limiares como constantes no topo do arquivo | O PO pode revisar sem ler o código da função |
| `_preparar_talhao()` como único ponto de mapeamento | Isola a mudança quando novas fontes de dados chegarem |
