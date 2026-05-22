# Regras Agronômicas — Motor de Decisão (Sprint 2)

> **Fonte:** Manual Prático Para o Manejo da Cana-de-Açúcar — Agroadvance (2022)
> **Objetivo:** Formalizar as regras do PDA como pseudocódigo em português antes da implementação em Python.
> **Status:** Rascunho para validação com orientador e PO ATVOS.

---

## Como ler este documento

Cada seção corresponde a um módulo de regras (`/src/rules/<processo>.py`).
Para cada processo são documentados:

- **Fonte dos dados** — quais colunas do Silver e da análise de solo são necessárias
- **Regras extraídas do manual** — citações e interpretações técnicas
- **Pseudocódigo** — lógica condicional em português antes de qualquer linha de Python
- **Mapeamento de colunas** — como os conceitos do manual se traduzem nos dados disponíveis
- **Saída esperada** — dicionário que a função Python deve retornar

---

## 1. Calagem (`calagem.py`)

### 1.1 Fonte dos dados

| Conceito agronômico | Coluna(s) disponível(is) | Tabela |
|---|---|---|
| pH do solo | `ph1`, `ph2` | `Dados_analise_solo.csv` |
| Saturação por bases atual (V%) | `V1`, `V2` | `Dados_analise_solo.csv` |
| CTC do solo | `CTC1`, `CTC2` | `Dados_analise_solo.csv` |
| Magnésio trocável | `mg1`, `mg2` | `Dados_analise_solo.csv` |
| Tipo de ciclo (cana planta / soca) | `CATEGORIA` | Silver (Inventário) |
| Número de corte | `NO_CORTE` | Silver (Inventário) |
| Chave de junção solo ↔ talhão | `FST` (solo) / `CHAVESIG` (inventário) | Ambas |

### 1.2 Regras extraídas do manual

> *"Aplicar calcário para elevar a saturação por bases a 60%, sendo pelo menos 1 t ha-¹ do tipo dolomítico se o teor de magnésio trocável for inferior a 5 mmolc dm-³."*
> — Manual, p. 6

> *"Utilize ¾ da dose de calcário antes da primeira passagem do arado e ¼ da dose antes da grade niveladora."*
> — Manual, p. 6

> *"Na cultura da cana, a melhor oportunidade para a calagem ocorre apenas a cada 5 ou 6 anos, sendo que, durante o plantio, tem-se a única oportunidade de incorporar bem o calcário."*
> — Manual, p. 10

**Interpretação técnica:**
- Meta: V% alvo = 60%
- Fórmula padrão de necessidade de calcário (NC):
  `NC (t/ha) = (V_alvo - V_atual) × CTC / 100`
- Se `mg < 5 mmolc dm-³`: usar calcário dolomítico, mínimo 1 t/ha
- A calagem incorporada só é possível na cana planta (reforma/plantio novo)
- Em cana soca: apenas aplicação superficial (sem incorporação)
- Início do processo: **150 dias antes do plantio**

### 1.3 Pseudocódigo

```
FUNÇÃO calcular_necessidade_calagem(talhao):

  # Validação de dados obrigatórios
  SE ph OU V_atual OU CTC OU mg forem nulos:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_analise_solo"
    }

  # Parâmetros fixos do manual
  V_ALVO = 60  # % de saturação por bases alvo
  MG_MINIMO = 5  # mmolc dm-³

  # Calcular necessidade de calagem
  dose_calcario = (V_ALVO - V_atual) × CTC / 100  # t/ha

  SE dose_calcario <= 0:
    RETORNAR {
      orientacao: "Solo já atingiu saturação alvo. Não há necessidade de calagem.",
      valor_calculado: 0,
      regra_acionada: "v_percent_adequado"
    }

  # Definir tipo de calcário
  SE mg < MG_MINIMO:
    tipo_calcario = "dolomítico"
    dose_calcario = MAX(dose_calcario, 1.0)  # mínimo 1 t/ha
  SENAO:
    tipo_calcario = "calcítico ou dolomítico"

  # Definir modo de aplicação por tipo de ciclo
  SE CATEGORIA == "Cana Planta":
    tipo_aplicacao = "incorporada"
    parcelamento = "3/4 antes do arado + 1/4 antes da grade niveladora"
    antecedencia_dias = 150
  SENAO:  # Cana Soca, qualquer corte > 1
    tipo_aplicacao = "superficial"
    parcelamento = "dose única em superfície"
    antecedencia_dias = 60
    dose_calcario = dose_calcario * 0.5  # eficiência reduzida sem incorporação

  RETORNAR {
    orientacao: f"Aplicar {dose_calcario:.1f} t/ha de calcário {tipo_calcario} ({tipo_aplicacao}). {parcelamento}. Aplicar {antecedencia_dias} dias antes do plantio.",
    valor_calculado: dose_calcario,
    unidade: "t/ha",
    regra_acionada: f"calagem_{tipo_aplicacao}",
    tipo_calcario: tipo_calcario
  }
```

### 1.4 Casos de borda

| Situação | Comportamento esperado |
|---|---|
| `ph` ou `V1` ausente | Retorna `SEM_DADO` com `regra_acionada: "dado_ausente_analise_solo"` |
| V% ≥ 60 (solo ok) | Retorna dose 0 com orientação "sem necessidade" |
| V% = 0 (dado suspeito) | Retorna `SEM_DADO` com `regra_acionada: "dado_suspeito_v_percent"` |
| `mg` ausente | Usa calcítico como padrão, adiciona alerta na orientação |

---

## 2. Gessagem (`gessagem.py`)

### 2.1 Fonte dos dados

| Conceito agronômico | Coluna(s) disponível(is) | Tabela |
|---|---|---|
| Cálcio no subsolo (25-50 cm) | `ca2` (segunda análise em profundidade) | `Dados_analise_solo.csv` |
| Saturação por Alumínio (m%) | Calculado: `al / (sb + al) × 100` | `Dados_analise_solo.csv` |
| Teor de argila | `DE_TP_SOLO` (descritivo) | Silver (Inventário) |
| Tipo de ciclo | `CATEGORIA` | Silver (Inventário) |

> ⚠️ **Atenção:** A saturação por Al (m%) não é uma coluna direta — precisa ser calculada a partir de `al` e `sb`. A textura/argila no Silver é textual (`DE_TP_SOLO`), não numérica — será necessário um dicionário de conversão para estimar g/kg de argila.

### 2.2 Regras extraídas do manual

> *"Com base em amostras de solo de 25-50 cm, a aplicação de gesso é recomendada quando o teor de Ca for inferior a 4 mmolc dm-³ e a saturação por Al (m%) for acima de 40%, conforme a fórmula: argila (em g/kg) × 5 = kg ha-¹ de gesso a aplicar."*
> — Manual, p. 6

> *"Realize a aplicação do gesso na etapa da grade niveladora, pois o gesso possui mobilidade no solo. Isso garante que haja uma melhor distribuição de cálcio e enxofre mais efetiva na camada de cultivo 0-60 cm."*
> — Manual, p. 6

> *"É importante parcelar a aplicação destes produtos para um melhor desempenho na correção da acidez."*
> — Manual, p. 6

**Interpretação técnica:**
- Critérios de disparo (ambos devem ser verdadeiros):
  1. `ca2 < 4 mmolc dm-³` (cálcio no subsolo insuficiente)
  2. `m% > 40%` onde `m% = al / (sb + al) × 100`
- Dose: `argila (g/kg) × 5 = kg/ha de gesso`
- Timing: 60-90 dias antes do plantio, na passagem da grade niveladora

### 2.3 Dicionário de conversão de textura → argila (g/kg)

Para converter `DE_TP_SOLO` em valor numérico de argila:

| Descrição no Silver | Argila estimada (g/kg) |
|---|---|
| Neossolo Quartzarênico / textura arenosa | 80 |
| Latossolo Vermelho / textura média | 250 |
| Latossolo Vermelho / textura argilosa | 450 |
| Latossolo Vermelho / textura muito argilosa | 600 |
| Argissolo / textura média-argilosa | 350 |
| Outros / não identificado | usar mediana = 250 + flag de incerteza |

> ⚠️ **Para validação com o PO ATVOS:** confirmar os valores de argila por tipo de solo antes de usar em produção.

### 2.4 Pseudocódigo

```
FUNÇÃO calcular_necessidade_gessagem(talhao):

  # Validação de dados obrigatórios
  SE ca2 OU al2 OU sb2 forem nulos:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_analise_subsolo"
    }

  # Calcular saturação por alumínio (m%) no subsolo
  SE (sb2 + al2) == 0:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_suspeito_sb_al_zero"
    }

  m_percent = (al2 / (sb2 + al2)) × 100

  # Verificar critérios de disparo (manual: AMBOS devem ser verdadeiros)
  criterio_ca = ca2 < 4       # Ca insuficiente no subsolo
  criterio_al = m_percent > 40  # Al tóxico no subsolo

  SE NÃO (criterio_ca E criterio_al):
    RETORNAR {
      orientacao: f"Gessagem não indicada. Ca subsolo={ca2:.1f} mmolc dm-³, m%={m_percent:.1f}%. Critérios: Ca<4 E m%>40 (ambos necessários).",
      valor_calculado: 0,
      regra_acionada: "gessagem_nao_necessaria"
    }

  # Determinar dose com base na textura do solo
  argila_g_kg = converter_textura_para_argila(DE_TP_SOLO)
  dose_gesso = argila_g_kg × 5  # kg/ha

  RETORNAR {
    orientacao: f"Aplicar {dose_gesso:.0f} kg/ha de gesso agrícola na passagem da grade niveladora (60-90 dias antes do plantio). Ca subsolo={ca2:.1f} mmolc dm-³, m%={m_percent:.1f}%.",
    valor_calculado: dose_gesso,
    unidade: "kg/ha",
    regra_acionada: "gessagem_necessaria",
    m_percent_subsolo: m_percent
  }
```

### 2.5 Casos de borda

| Situação | Comportamento esperado |
|---|---|
| `ca2` ou `al2` ausente | Retorna `SEM_DADO` |
| Apenas um dos critérios verdadeiro | Retorna "não indicada" + explica qual critério não foi atingido |
| Textura não mapeada no dicionário | Usa mediana + adiciona `flag_textura_incerta: True` |

---

## 3. Fosfatagem (`fosfatagem.py`)

### 3.1 Fonte dos dados

| Conceito agronômico | Coluna(s) disponível(is) | Tabela |
|---|---|---|
| Fósforo disponível no solo | `p1` | `Dados_analise_solo.csv` |
| Produtividade estimada (TCH) | `TCH_PROD` | Silver (Inventário) |
| Tipo de ciclo | `CATEGORIA` | Silver (Inventário) |
| Textura do solo | `DE_TP_SOLO` | Silver (Inventário) |

### 3.2 Regras extraídas do manual

> *"No pré-plantio, além da calagem e gessagem, a fosfatagem pode ser necessária."*
> — Manual, p. 10

> *"No sulco de plantio, colocamos 50 a 100% da dose total de nitrogênio e 100% da dose total de fósforo."*
> — Manual, p. 10

> *"Extração e exportação de fósforo: 11 kg P / 100 t de colmo (exportação via colmo), 8 kg P / 100 t (via folhas). Total: 19 kg P / 100 t colhida."*
> — Manual, p. 10 (Tabela Orlando F., 1983)

**Interpretação técnica:**
- O manual não especifica um limiar de P no solo explicitamente — usa a extração/exportação por tonelada
- Referência padrão do Boletim 100/IAC para cana em SP: P crítico varia por textura
  - Solo arenoso: P crítico = 12 mg/dm³
  - Solo médio: P crítico = 15 mg/dm³
  - Solo argiloso: P crítico = 18 mg/dm³
- Dose de reposição base: exportação × TCH_estimada
- Na cana planta: 100% da dose no sulco de plantio (pré-plantio + sulco)
- Na cana soca: dose de manutenção em cobertura (30-60 dias após colheita)

> ⚠️ **Para validação com PO ATVOS:** confirmar os limiares críticos de P que a ATVOS adota — o manual Agroadvance é genérico; os valores do IAC Boletim 100 são referência mas podem diferir do protocolo ATVOS.

### 3.3 Pseudocódigo

```
FUNÇÃO calcular_necessidade_fosfatagem(talhao):

  # Validação de dados obrigatórios
  SE p1 for nulo:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_fosforo_solo"
    }

  SE TCH_PROD for nulo OU TCH_PROD <= 0:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_tch_estimado"
    }

  # Definir P crítico por textura
  p_critico = definir_p_critico(DE_TP_SOLO)
  # arenoso → 12, médio → 15, argiloso → 18

  # Calcular exportação de P pela cultura (Tabela Orlando 1983)
  exportacao_p_kg = 19 × (TCH_PROD / 100)  # kg P / ha

  SE p1 >= p_critico:
    # Solo com P adequado: apenas repor exportação
    dose_fosforo = exportacao_p_kg
    regra = "fosfatagem_manutencao"
    orientacao_txt = f"Solo com P adequado ({p1:.1f} mg/dm³ ≥ {p_critico} mg/dm³). Aplicar dose de manutenção: {dose_fosforo:.1f} kg P₂O₅/ha para repor exportação estimada ({TCH_PROD:.0f} t/ha)."
  SENAO:
    # Solo deficiente: corrigir + repor exportação
    deficit_p = p_critico - p1
    dose_correcao = deficit_p × 2.5  # fator de conversão déficit → dose (referência IAC)
    dose_fosforo = dose_correcao + exportacao_p_kg
    regra = "fosfatagem_correcao"
    orientacao_txt = f"Solo com deficiência de P ({p1:.1f} mg/dm³ < {p_critico} mg/dm³). Aplicar correção + manutenção: {dose_fosforo:.1f} kg P₂O₅/ha. 100% no sulco de plantio (cana planta) ou cobertura 30-60 dias após colheita (cana soca)."

  # Definir momento de aplicação
  SE CATEGORIA == "Cana Planta":
    momento = "100% no sulco de plantio"
  SENAO:
    momento = "cobertura 30-60 dias após colheita"

  RETORNAR {
    orientacao: orientacao_txt + f" Momento: {momento}.",
    valor_calculado: dose_fosforo,
    unidade: "kg P₂O₅/ha",
    regra_acionada: regra
  }
```

---

## 4. Erradicação (`erradicacao.py`)

### 4.1 Fonte dos dados

| Conceito agronômico | Coluna(s) disponível(is) | Tabela |
|---|---|---|
| Produtividade estimada (TCH) | `TCH_PROD` | Silver (Inventário) |
| Número de corte | `NO_CORTE` | Silver (Inventário) |
| Situação do talhão | `SIT_TALHAO` | Silver (Inventário) |
| Categoria da cultura | `CATEGORIA` | Silver (Inventário) |
| Área do talhão | `AREA_HA` | Silver (Inventário) |
| Data do último corte | `ULT_CORTE` | Silver (Inventário) |

### 4.2 Regras extraídas do manual

> *"Produtividades inferiores a 55 t ha-¹ no ciclo, a reforma do canavial é uma recomendação importante."*
> — Manual, p. 15

> *"A colheita ocorre de maio a novembro e não deve ultrapassar esse período porque as novas brotações serão afetadas podendo comprometer o crescimento e desenvolvimento da planta, que chega ao inverno pouco desenvolvida e consequentemente mais suscetível aos danos por geada."*
> — Manual, p. 15

> *"Após a colheita, na renovação do canavial, é possível utilizar algumas culturas para recuperar o solo e ajudar no manejo de plantas daninhas, pragas e doenças. A rotação de culturas pode ser feita com soja precoce e amendoim cultivados de outubro a fevereiro. Para implantação de adubos verdes são recomendadas as culturas crotalária-juncea, mucuna-preta e guandu, cultivados em setembro e outubro sendo incorporados em janeiro e fevereiro."*
> — Manual, p. 15

**Interpretação técnica:**
- Limiar crítico de produtividade: TCH < 55 t/ha → reforma indicada
- Regra adicional de longevidade: cana com muitos cortes tende a decair naturalmente
  - Referência do setor: reforma comum entre o 5º e 6º corte
  - Manual não especifica número máximo de cortes, mas menciona "ciclo de 5 a 6 anos"
- Talhões com `SIT_TALHAO = "Fechado"` ou `CATEGORIA = "Cana Planta"` recém-plantados: não avaliar erradicação

### 4.3 Pseudocódigo

```
FUNÇÃO calcular_necessidade_erradicacao(talhao):

  # Validação de dados obrigatórios
  SE TCH_PROD for nulo:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_tch_prod"
    }

  # Talhões recém-plantados ou fechados não são candidatos
  SE CATEGORIA == "Cana Planta" OU SIT_TALHAO == "Fechado":
    RETORNAR {
      orientacao: "Talhão não elegível para avaliação de erradicação (cana planta ou talhão fechado).",
      valor_calculado: None,
      regra_acionada: "erradicacao_nao_aplicavel"
    }

  # Limiar principal do manual: TCH < 55 t/ha
  TCH_CRITICO = 55  # t/ha (Manual Agroadvance, p. 15)

  # Fator adicional: número de corte (longevidade)
  CORTE_LIMITE = 6  # referência do setor sucroenergético

  SE TCH_PROD < TCH_CRITICO E NO_CORTE >= CORTE_LIMITE:
    prioridade = "ALTA"
    regra = "erradicacao_tch_baixo_e_corte_alto"
    orientacao_txt = f"REFORMA INDICADA COM PRIORIDADE ALTA. TCH estimado={TCH_PROD:.1f} t/ha (abaixo de 55 t/ha) e {NO_CORTE}° corte. Considerar rotação com soja (out-fev) ou adubos verdes (crotalária, mucuna, guandu — set/out, incorporar jan/fev)."

  SENAO SE TCH_PROD < TCH_CRITICO:
    prioridade = "MÉDIA"
    regra = "erradicacao_tch_baixo"
    orientacao_txt = f"REFORMA SUGERIDA. TCH estimado={TCH_PROD:.1f} t/ha (abaixo de 55 t/ha), {NO_CORTE}° corte. Avaliar custo-benefício da reforma vs. manutenção da soqueira."

  SENAO SE NO_CORTE >= CORTE_LIMITE:
    prioridade = "BAIXA"
    regra = "erradicacao_corte_alto_tch_ok"
    orientacao_txt = f"Monitorar. TCH={TCH_PROD:.1f} t/ha ainda aceitável, mas {NO_CORTE}° corte — planejar reforma nos próximos 1-2 ciclos."

  SENAO:
    prioridade = "NENHUMA"
    regra = "erradicacao_nao_necessaria"
    orientacao_txt = f"Talhão com boa produtividade ({TCH_PROD:.1f} t/ha) e {NO_CORTE}° corte. Não há indicação de reforma."

  RETORNAR {
    orientacao: orientacao_txt,
    valor_calculado: TCH_PROD,
    unidade: "t/ha",
    regra_acionada: regra,
    prioridade_reforma: prioridade
  }
```

---

## 5. Janela de Plantio (`janela_plantio.py`)

### 5.1 Fonte dos dados

| Conceito agronômico | Coluna(s) disponível(is) | Tabela |
|---|---|---|
| Data de plantio | `DATA_PLANTIO` | Silver (Inventário) |
| Tipo de cana (sistema) | `ESTAGIO` / `CATEGORIA` | Silver (Inventário) |
| Número de corte | `NO_CORTE` | Silver (Inventário) |
| Situação do talhão | `SIT_TALHAO` | Silver (Inventário) |
| Data do último corte | `ULT_CORTE` | Silver (Inventário) |
| Data de fechamento | `DATA_FECHA` | Silver (Inventário) |
| Unidade industrial | `UNID_IND` / `DESC_EMPRESA` | Silver (Inventário) |

### 5.2 Regras extraídas do manual

> *"A escolha adequada da época de plantio é fundamental para o bom desenvolvimento da cultura da cana-de-açúcar."*
> — Manual, p. 8

> *"Para seu crescimento, a cana necessita de alta disponibilidade de água, temperaturas elevadas e alto índice de radiação solar."*
> — Manual, p. 8

**Ciclos disponíveis (tabela do manual, p. 15):**

| Tipo de cana | Duração do ciclo |
|---|---|
| Cana de ano e meio | 14 a 22 meses |
| Cana de ano | 12 meses |
| Cana soca | 12 meses |
| Cana de inverno | 12 a 16 meses |

> *"A colheita ocorre de maio a novembro e não deve ultrapassar esse período."*
> — Manual, p. 15

> *"Para iniciar a safra com o pé direito, a recomendação é: comece a preparar o solo 150 dias antes da data programada para realizar o plantio."*
> — Manual, p. 5

> *"Em decorrência da necessidade de alta disponibilidade de água, temperaturas elevadas e alto índice de radiação solar: Setembro a março, no Norte-Nordeste. Abril a novembro no Centro-Sul."*
> — Manual, p. 4

**Quantidade de mudas:**
> *"A quantidade necessária de mudas varia entre 10 e 15 toneladas por hectare. Para o plantio em épocas de estiagem é necessário dar preferência para densidade de 15 a 18 gemas por metro."*
> — Manual, p. 8

### 5.3 Pseudocódigo

```
FUNÇÃO calcular_janela_plantio(talhao):

  # Validação de dados obrigatórios
  SE DATA_PLANTIO for nulo:
    RETORNAR {
      orientacao: "SEM_DADO",
      regra_acionada: "dado_ausente_data_plantio"
    }

  # Determinar sistema e janela de colheita esperada
  SE ESTAGIO contém "ano e meio" OU "18":
    sistema = "cana_ano_e_meio"
    ciclo_min_meses = 14
    ciclo_max_meses = 22
  SENAO SE ESTAGIO contém "inverno":
    sistema = "cana_inverno"
    ciclo_min_meses = 12
    ciclo_max_meses = 16
  SENAO:
    sistema = "cana_ano"
    ciclo_min_meses = 12
    ciclo_max_meses = 12

  # Calcular janela de colheita esperada
  data_colheita_min = DATA_PLANTIO + ciclo_min_meses
  data_colheita_max = DATA_PLANTIO + ciclo_max_meses

  # Verificar se colheita cai dentro da janela ideal (maio–novembro)
  MES_COLHEITA_MIN = 5   # maio
  MES_COLHEITA_MAX = 11  # novembro

  mes_colheita_esperado = mes(data_colheita_min)

  SE mes_colheita_esperado >= MES_COLHEITA_MIN E mes_colheita_esperado <= MES_COLHEITA_MAX:
    janela_ok = True
    alerta_janela = "Colheita estimada dentro da janela ideal (mai–nov)."
  SENAO:
    janela_ok = False
    alerta_janela = f"ATENÇÃO: Colheita estimada fora da janela ideal (mai–nov). Mês esperado: {mes_colheita_esperado}. Risco de novas brotações comprometidas pelo inverno."

  # Data-limite para início do preparo de solo
  data_inicio_preparo = DATA_PLANTIO - 150 dias

  # Recomendação de mudas
  SE sistema == "cana_ano_e_meio":
    qtd_mudas_txt = "10–15 t/ha de mudas (12–18 gemas/m linear)"
  SENAO:
    qtd_mudas_txt = "10–15 t/ha de mudas (mínimo 12 gemas/m linear)"

  RETORNAR {
    orientacao: f"Sistema: {sistema}. Janela de colheita estimada: {data_colheita_min.strftime('%b/%Y')} a {data_colheita_max.strftime('%b/%Y')}. {alerta_janela} Início do preparo de solo: {data_inicio_preparo.strftime('%d/%m/%Y')} (150 dias antes do plantio). Mudas: {qtd_mudas_txt}.",
    valor_calculado: ciclo_min_meses,
    unidade: "meses_ciclo",
    regra_acionada: "janela_ok" SE janela_ok SENAO "janela_fora_do_ideal",
    data_colheita_estimada_inicio: data_colheita_min,
    data_colheita_estimada_fim: data_colheita_max,
    data_preparo_solo: data_inicio_preparo
  }
```

---

## 6. Mapeamento de Colunas Silver ↔ Análise de Solo

Para que o `pipeline_gold.py` funcione, os dois DataFrames precisam ser cruzados. A chave de junção é:

```
Silver.CHAVESIG  ←→  Solo.FST
```

**Formato de CHAVESIG:** `"110133-1-6"` (Fazenda-Setor-Talhão)
**Formato de FST:** `"320110-1-11"` (mesmo padrão: Fazenda-Setor-Talhão)

**Joins necessários:**
1. Inventário Silver (4 partes) → `pd.concat` → DataFrame unificado
2. DataFrame unificado ↔ `Dados_analise_solo.csv` via `CHAVESIG == FST`
3. Resultado: um DataFrame com dados de talhão + análise de solo para cada registro

---

## 7. Tabela Resumo: Processos × Dados Necessários

| Processo | Dado crítico | Fonte | Disponível? |
|---|---|---|---|
| Calagem | `V1`, `CTC1`, `mg1` | Solo | ✅ |
| Calagem | `CATEGORIA` | Silver | ✅ |
| Gessagem | `ca2`, `al2`, `sb2` | Solo (subsolo) | ✅ |
| Gessagem | `DE_TP_SOLO` | Silver | ✅ (textual, precisa conversão) |
| Fosfatagem | `p1` | Solo | ✅ |
| Fosfatagem | `TCH_PROD` | Silver | ✅ (imputado quando nulo) |
| Erradicação | `TCH_PROD`, `NO_CORTE` | Silver | ✅ |
| Janela de Plantio | `DATA_PLANTIO`, `ESTAGIO` | Silver | ✅ |

---

## 8. Pontos para Validação com o PO ATVOS

Antes de implementar a Task 2.3, os seguintes itens precisam de validação:

1. **Calagem:** A ATVOS usa V% alvo = 60% ou adota outro valor?
2. **Gessagem:** O dicionário de conversão textura → argila (g/kg) está correto para as condições da ATVOS?
3. **Fosfatagem:** Quais são os limiares críticos de P que a ATVOS adota por textura? O Boletim 100/IAC é a referência?
4. **Erradicação:** TCH < 55 t/ha como limiar de reforma — a ATVOS usa este valor ou tem um específico por unidade/variedade?
5. **Janela de Plantio:** A ATVOS opera exclusivamente no Centro-Sul (janela abr–nov) ou tem unidades no Norte-Nordeste?
6. **Chave de join:** Confirmar que `CHAVESIG == FST` é a chave correta e que não há variações de formatação entre os datasets.

---

*Documento gerado em: 2026-05-21 | Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022)*
