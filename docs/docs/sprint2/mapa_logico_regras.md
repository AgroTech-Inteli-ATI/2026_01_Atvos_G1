# Mapa Lógico de Regras Agronômicas

**Sprint:** 2 | **Atualizado:** 2026-06-11  
**Público-alvo:** Agrônomos e técnicos agrícolas — sem necessidade de conhecimento de programação

---

> **Como ler estes fluxogramas**
>
> - Caixas **retangulares** → passos do processo  
> - Losangos (perguntas com **?**) → condições de decisão  
> - Setas **SIM / NÃO** → caminhos alternativos  
> - Caixas com borda dupla (**══**) → resultado final entregue ao agrônomo  
> - **SEM_DADO** → campo obrigatório ausente; o sistema não gera orientação e aguarda o dado  
> - **NÃO SE APLICA** → a regra não é pertinente para este tipo de talhão

---

## 1. Erradicação de Canavial

**Pergunta central:** este talhão deve ser reformado (erradicado e replantado)?

**Dados necessários:** número do corte, produtividade estimada (TCH), categoria do talhão, se reforma já está programada pela usina.

> Todos os dados vêm da planilha de inventário — **nenhuma análise de solo é necessária para esta regra.**

```
                    ┌─────────────────────────────┐
                    │    TALHÃO PARA AVALIAÇÃO     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  Categoria é "Formação"       │
                    │  ou "Muda"?                   │
                    └───────┬──────────────┬────────┘
                          SIM            NÃO
                            │              │
                            ▼              ▼
                    ╔═══════════╗   ┌──────────────────────────────┐
                    ║  NÃO SE   ║   │  Reforma já programada        │
                    ║  APLICA   ║   │  pela usina?                  │
                    ║ (canavial ║   └──────┬───────────────┬────────┘
                    ║ em form.) ║        SIM             NÃO
                    ╚═══════════╝          │               │
                                           ▼               ▼
                                  ╔═══════════════╗  ┌────────────────────────┐
                                  ║   NÃO SE      ║  │  TCH ou Nº corte       │
                                  ║   APLICA      ║  │  estão ausentes?        │
                                  ║ (usina já     ║  └───────┬────────┬────────┘
                                  ║ programou)    ║        SIM      NÃO
                                  ╚═══════════════╝          │        │
                                                             ▼        │
                                                    ╔════════════╗    │
                                                    ║  SEM_DADO  ║    │
                                                    ║ (aguardando║    │
                                                    ║   dados)   ║    │
                                                    ╚════════════╝    │
                                                                      │
                                           ┌──────────────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────────┐
                              │  Número do corte ≥ 5?       │
                              │  (canavial tardio / velho)  │
                              └─────────┬──────────┬────────┘
                                      SIM          NÃO
                                        │            │
                          ┌─────────────┘            └──────────────────┐
                          │                                              │
                          ▼                                              ▼
            ┌─────────────────────────────┐             ┌───────────────────────────┐
            │   TCH estimado              │             │  Número do corte é 3 ou 4? │
            │   (produtividade)?          │             │  (ciclo médio)             │
            └─────┬──────────┬────────┬───┘             └──────┬──────────┬──────────┘
                  │          │        │                       SIM         NÃO
              < 50 t/ha  50–70 t/ha  > 70 t/ha               │    (é 1 ou 2 = jovem)
                  │          │        │                        │           │
                  ▼          ▼        ▼                        ▼           ▼
        ╔══════════════╗ ╔═══════════════╗ ╔═══════════╗  [ver abaixo]  [ver abaixo]
        ║ ERRADICAÇÃO  ║ ║    AVALIAR    ║ ║ MONITORAR ║
        ║ RECOMENDADA  ║ ║  ERRADICAÇÃO  ║ ║ canavial  ║
        ║ alta prioridade║ ║custo-benefício║ ║ tardio    ║
        ║              ║ ║  crítico      ║ ║ produtivo ║
        ╚══════════════╝ ╚═══════════════╝ ╚═══════════╝


            CICLO MÉDIO (3º ou 4º corte)          CANAVIAL JOVEM (1º ou 2º corte)
            ────────────────────────────          ───────────────────────────────
            TCH < 40 t/ha                         TCH < 40 t/ha
               ╔════════════════════╗                ╔═══════════════════════════╗
               ║    INVESTIGAR      ║                ║    INVESTIGAR             ║
               ║ baixa produtiv.    ║                ║ falha grave de campo      ║
               ║ precoce — verificar║                ║ (replantio pode ser       ║
               ║ pragas e doenças   ║                ║ necessário)               ║
               ╚════════════════════╝                ╚═══════════════════════════╝

            40 ≤ TCH ≤ 70 t/ha                    TCH ≥ 40 t/ha
               ╔════════════════════╗                ╔═══════════════════════════╗
               ║    MONITORAR       ║                ║   NÃO RECOMENDADA         ║
               ║ reavaliar na       ║                ║ canavial jovem com bom    ║
               ║ próxima safra      ║                ║ desempenho — aguardar     ║
               ╚════════════════════╝                ╚═══════════════════════════╝

            TCH > 70 t/ha
               ╔════════════════════╗
               ║  NÃO RECOMENDADA   ║
               ║ bom desempenho     ║
               ╚════════════════════╝
```

**Limiares de referência (validar com PO Atvos):**

| Limiar | Valor atual |
|--------|-------------|
| Corte considerado "tardio" | ≥ 5º corte |
| TCH crítico (erradicação quase certa) | < 50 t/ha |
| TCH de alerta (avaliar custo-benefício) | 50 – 70 t/ha |
| TCH de investigação em canavial jovem | < 40 t/ha |

---

## 2. Janela de Plantio

**Pergunta central:** o plantio foi feito (ou está planejado) na época certa do ano?

**Dados necessários:** categoria do talhão, maturação hipotética da variedade, tipo de reforma, data de plantio (se disponível).

> Aplica-se **somente** a talhões em formação ou muda. Canaviais já estabelecidos são ignorados.

```
                    ┌─────────────────────────────┐
                    │    TALHÃO PARA AVALIAÇÃO     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  Categoria é "Formação"       │
                    │  ou "Muda"?                   │
                    └───────┬──────────────┬────────┘
                          NÃO            SIM
                            │              │
                            ▼              ▼
                    ╔═══════════╗  ┌───────────────────────────────────┐
                    ║  NÃO SE   ║  │  Tipo de Reforma tem janela        │
                    ║  APLICA   ║  │  específica definida?              │
                    ║(já colhido)║  │  ("Inverno" ou "18 Meses")        │
                    ╚═══════════╝  └──────────┬────────────────┬────────┘
                                            SIM               NÃO
                                              │                 │
                                ┌─────────────┘                 │
                                │                               ▼
                      USAR JANELA DO              ┌─────────────────────────────┐
                      TIPO DE REFORMA:            │  Maturação da variedade      │
                      ┌────────────────┐          │  (MAN_HIPOT) definida?       │
                      │ Inverno:       │          └───────┬──────────────┬────────┘
                      │ abril – julho  │                NÃO             SIM
                      ├────────────────┤                  │               │
                      │ 18 Meses:      │                  │    USAR JANELA DA MATURAÇÃO:
                      │ março – maio   │                  │    ┌──────────────────────┐
                      └───────┬────────┘                  │    │ Precoce: abril–junho │
                              │                           │    ├──────────────────────┤
                              │                           │    │ Média: junho–agosto   │
                              │                           │    ├──────────────────────┤
                              │                           │    │ Tardia: agosto–outubro│
                              │                           │    └─────────┬────────────┘
                              │                           │              │
                              │                   ┌───────┴──────┐      │
                              │                   │ MAN_HIPOT =  │      │
                              │                   │ "A Definir"? │      │
                              │                   └──────┬───────┘      │
                              │                        SIM              │
                              │                          │              │
                              │                          ▼              │
                              │                ╔══════════════════╗     │
                              │                ║ Definir maturação ║     │
                              │                ║ com o agrônomo   ║     │
                              │                ║ antes de plantar ║     │
                              │                ╚══════════════════╝     │
                              │                                         │
                              │            (ambos nulos → SEM_DADO)     │
                              │                                         │
                     ┌────────┴─────────────────────────────────────────┘
                     │
                     ▼
          ┌─────────────────────────────────┐
          │   DATA DE PLANTIO foi informada? │
          └──────────┬────────────┬──────────┘
                   SIM           NÃO
                     │             │
                     ▼             ▼
          ┌─────────────────┐  ╔══════════════════════════════╗
          │ Mês do plantio  │  ║  ORIENTAÇÃO PREVENTIVA:      ║
          │ está dentro da  │  ║  "Plante entre [mês início]  ║
          │ janela?         │  ║   e [mês fim]"               ║
          └───┬─────┬───┬───┘  ╚══════════════════════════════╝
             SIM  LIMIT. NÃO
              │     │     │
              ▼     ▼     ▼
        ╔═════════╗ ╔══════════╗ ╔══════════════════════════╗
        ║ DENTRO  ║ ║  LIMITE  ║ ║  FORA DA JANELA          ║
        ║   DA    ║ ║ DA JANELA║ ║  avaliar impacto         ║
        ║ JANELA  ║ ║ (1 mês   ║ ║  na maturação da safra   ║
        ║         ║ ║ de folga)║ ║                          ║
        ╚═════════╝ ╚══════════╝ ╚══════════════════════════╝
```

**Janelas de referência (validar com PO Atvos por unidade industrial):**

| Configuração | Meses ideais |
|---|---|
| Maturação **Precoce** | Abril a Junho |
| Maturação **Média** | Junho a Agosto |
| Maturação **Tardia** | Agosto a Outubro |
| Reforma **Inverno** | Abril a Julho |
| Reforma **18 Meses** | Março a Maio |

---

## 3. Gessagem

**Pergunta central:** o solo precisa de gesso agrícola para corrigir o excesso de alumínio no subsolo?

**Dados necessários:** saturação por Al³⁺ (análise de solo) e/ou textura do solo; CTC para calcular a dose.

> **Situação atual:** a análise de Al³⁺ ainda não está integrada ao sistema. Por enquanto, o sistema orienta com base na **textura do solo** e solicita que a análise seja feita.

```
                    ┌─────────────────────────────┐
                    │    TALHÃO PARA AVALIAÇÃO     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  Resultado de Al³⁺               │
                    │  (análise de solo) disponível?   │
                    └────────────┬────────────┬─────────┘
                               SIM           NÃO
                                 │             │
                 ┌───────────────┘             └──────────────────────┐
                 │                                                     │
                 ▼                                                     ▼
    ┌────────────────────────────┐              ┌──────────────────────────────────┐
    │  Saturação por Al³⁺        │              │  Textura do solo disponível        │
    │  acima de 20%?             │              │  (campo "Ambiente" da planilha)?  │
    └──────┬──────────┬──────────┘              └──────┬───────────────────┬────────┘
         SIM         NÃO                             SIM                  NÃO
           │           │                               │                    │
           │           ▼                               │                    ▼
           │  ╔════════════════════╗                   │           ╔════════════╗
           │  ║ GESSAGEM NÃO       ║                   │           ║  SEM_DADO  ║
           │  ║ INDICADA           ║                   │           ║ (sem textura║
           │  ║ (Al³⁺ dentro do    ║                   │           ║ nem análise)║
           │  ║ limite seguro)     ║                   │           ╚════════════╝
           │  ╚════════════════════╝                   │
           │                           ORIENTAR POR TEXTURA:
           ▼                           ┌──────────────────────────────────────────┐
    ┌─────────────────────┐            │ Solo MUITO ARGILOSO                       │
    │  CTC disponível?    │            │   → Avaliar gessagem — ALTA PRIORIDADE   │
    └────┬────────┬────────┘            │     solicitar análise de Al³⁺            │
        SIM      NÃO                   ├──────────────────────────────────────────┤
          │        │                   │ Solo ARGILOSO                             │
          ▼        ▼                   │   → Avaliar gessagem                     │
    ┌─────────┐ ╔═════════════════╗    │     solicitar análise de Al³⁺            │
    │Calcular │ ║ GESSAGEM        ║    ├──────────────────────────────────────────┤
    │ dose    │ ║ INDICADA        ║    │ Solo MÉDIO / FRANCO                       │
    │(ver     │ ║ CTC ausente:    ║    │   → Avaliar conforme resultado de Al³⁺   │
    │ tabela) │ ║ dose a calcular ║    ├──────────────────────────────────────────┤
    └────┬────┘ ╚═════════════════╝    │ Solo ARENOSO                              │
         │                            │   → Raramente indicado — confirmar        │
         ▼                            │     com análise antes de aplicar          │
   ╔══════════════════════════╗       └──────────────────────────────────────────┘
   ║ GESSAGEM RECOMENDADA:    ║
   ║ aplicar X t/ha de gesso  ║
   ║ (calculado por textura   ║
   ║  e CTC do solo)          ║
   ╚══════════════════════════╝
```

**Dose de gesso por textura (quando CTC disponível):**

| Textura do solo | Fórmula da dose | Exemplo com CTC = 60 mmolc/dm³ |
|---|---|---|
| Arenoso | 0,5 × CTC ÷ 10 | 3,0 t/ha |
| Médio / Franco | 1,0 × CTC ÷ 10 | 4,0 t/ha (limite máx.) |
| Argiloso | 1,5 × CTC ÷ 10 | 4,0 t/ha (limite máx.) |
| Muito argiloso | 2,0 × CTC ÷ 10 | 4,0 t/ha (limite máx.) |

> Dose máxima por aplicação: **4,0 t/ha** — validar com PO Atvos.

---

## 4. Calagem

**Pergunta central:** o solo precisa de calcário para corrigir a acidez?

**Dados necessários:** pH do solo, CTC, saturação de bases atual e alvo; categoria do talhão.

> **Situação atual:** análise de solo ainda não está integrada ao sistema. Esta regra retornará **SEM_DADO** até que os dados sejam fornecidos.

```
                    ┌─────────────────────────────┐
                    │    TALHÃO PARA AVALIAÇÃO     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  pH do solo, CTC e saturação     │
                    │  de bases disponíveis?           │
                    └────────────┬─────────────┬───────┘
                                NÃO           SIM
                                 │              │
                                 ▼              │
                        ╔════════════╗          │
                        ║  SEM_DADO  ║          │
                        ║ (aguardando║          │
                        ║ análise de ║          │
                        ║   solo)    ║          │
                        ╚════════════╝          │
                                                ▼
                               ┌────────────────────────────┐
                               │  pH do solo ≥ 6,0?         │
                               └──────┬──────────┬──────────┘
                                    SIM          NÃO
                                      │            │
                                      ▼            │
                           ╔══════════════════╗    │
                           ║ SEM NECESSIDADE  ║    │
                           ║ DE CALAGEM       ║    │
                           ║ pH adequado      ║    │
                           ╚══════════════════╝    │
                                                   ▼
                               ┌────────────────────────────┐
                               │  pH do solo entre          │
                               │  5,5 e 6,0?               │
                               └──────┬──────────┬──────────┘
                                    SIM          NÃO (pH < 5,5)
                                      │            │
                                      ▼            ▼
                           ╔══════════════════╗  ┌─────────────────────────────┐
                           ║ CALAGEM PREVENTIVA║  │  Categoria é "Formação"     │
                           ║ SUPERFICIAL       ║  │  ou "Muda"?                 │
                           ║ dose reduzida     ║  │  (solo será mobilizado      │
                           ║ (50% da dose      ║  │   no plantio)               │
                           ║  calculada)       ║  └──────┬────────────┬──────────┘
                           ╚══════════════════╝        SIM           NÃO
                                                         │        (Cana Soca)
                                                         ▼             │
                                              ╔══════════════════╗     ▼
                                              ║ CALAGEM           ║  ╔══════════════════╗
                                              ║ INCORPORADA       ║  ║ CALAGEM           ║
                                              ║ dose plena,       ║  ║ SUPERFICIAL       ║
                                              ║ enterrada no solo ║  ║ dose reduzida     ║
                                              ║ (solo mobilizado  ║  ║ (50% da dose      ║
                                              ║  no plantio)      ║  ║  calculada)       ║
                                              ╚══════════════════╝  ╚══════════════════╝
```

**Fórmula de dose (método da saturação de bases — Embrapa/IAC):**

```
Dose (t/ha) = [ (V_alvo − V_atual) × CTC ] ÷ (PRNT × 10)

Onde:
  V_alvo  = saturação de bases alvo (padrão Atvos: 60%)
  V_atual = saturação de bases atual medida na análise de solo
  CTC     = capacidade de troca catiônica em mmolc/dm³
  PRNT    = poder relativo de neutralização do calcário (padrão: 80%)
  Dose máxima por aplicação: 6,0 t/ha
```

---

## 5. Fosfatagem

**Pergunta central:** o solo tem fósforo suficiente, ou precisa de adubação fosfatada corretiva?

**Dados necessários:** teor de fósforo disponível no solo (análise pelo método Mehlich-1); categoria do talhão.

> **Situação atual:** análise de solo ainda não está integrada ao sistema. Esta regra retornará **SEM_DADO** até que os dados sejam fornecidos.

```
                    ┌─────────────────────────────┐
                    │    TALHÃO PARA AVALIAÇÃO     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │  Teor de P disponível (Mehlich-1) │
                    │  disponível na análise de solo?   │
                    └────────────┬─────────────┬────────┘
                                NÃO           SIM
                                 │              │
                                 ▼              │
                        ╔════════════╗          │
                        ║  SEM_DADO  ║          │
                        ║ (aguardando║          │
                        ║ análise de ║          │
                        ║   solo)    ║          │
                        ╚════════════╝          │
                                                ▼
                            ┌───────────────────────────────────────┐
                            │  CLASSIFICAR TEOR DE P               │
                            │                                       │
                            │  P ≥ 30 mg/dm³  → ALTO               │
                            │  P entre 15–29  → MÉDIO              │
                            │  P entre 8–14   → BAIXO              │
                            │  P < 8 mg/dm³   → MUITO BAIXO        │
                            └──────────────────────┬────────────────┘
                                                   │
                            ┌──────────────────────┘
                            │
              ┌─────────────┴─────────────────────────┐
              │                                        │
              ▼                                        ▼
    ┌─────────────────┐                    ┌─────────────────────────────────┐
    │  Classe = ALTO  │                    │  Classe = MÉDIO, BAIXO ou       │
    │  (P ≥ 30 mg/dm³)│                    │  MUITO BAIXO                    │
    └────────┬────────┘                    └──────────────┬──────────────────┘
             │                                            │
             ▼                                            ▼
    ╔══════════════════╗                      ┌────────────────────────────────┐
    ║ SEM NECESSIDADE  ║                      │  Categoria é "Formação"         │
    ║ DE FOSFATAGEM    ║                      │  ou "Muda"? (cana-planta)       │
    ║ nível alto de P  ║                      └─────────┬────────────┬──────────┘
    ╚══════════════════╝                              SIM           NÃO
                                                        │        (Cana Soca)
                                                        ▼             ▼
                                             ╔══════════════════╗ ╔══════════════════╗
                                             ║ FOSFATAGEM       ║ ║ FOSFATAGEM DE    ║
                                             ║ CORRETIVA        ║ ║ MANUTENÇÃO       ║
                                             ║ (dose plena —    ║ ║ (dose reduzida a ║
                                             ║ ver tabela)      ║ ║ 50% — ver tabela)║
                                             ╚══════════════════╝ ╚══════════════════╝
```

**Tabela de doses por classe de P e ciclo do canavial:**

| Classe | Teor de P | Dose cana-planta | Dose cana-soca (manutenção) |
|---|---|---|---|
| Muito Baixo | < 8 mg/dm³ | **120 kg P₂O₅/ha** | 60 kg P₂O₅/ha |
| Baixo | 8 – 14 mg/dm³ | **80 kg P₂O₅/ha** | 40 kg P₂O₅/ha |
| Médio | 15 – 29 mg/dm³ | **40 kg P₂O₅/ha** | 20 kg P₂O₅/ha |
| Alto | ≥ 30 mg/dm³ | — sem necessidade — | — |

> Doses baseadas em Embrapa/IAC. **Validar os valores com o PO Atvos** antes de usar operacionalmente.

---

## Resumo: o que cada processo produz

| Processo | Dados atuais disponíveis | Resultado hoje |
|---|---|---|
| **Erradicação** | ✅ Inventário (corte, TCH) | Recomendação gerada para todos os talhões |
| **Janela de Plantio** | ✅ Inventário (MAN_HIPOT, TP_REFORMA, DATA_PLANTIO) | Recomendação gerada para talhões em formação |
| **Gessagem** | ⚠️ Textura disponível; Al³⁺ não integrado | Orientação por textura + solicitação de análise |
| **Calagem** | ❌ Aguardando análise de solo (pH, CTC, V%) | SEM_DADO — campo será preenchido quando análise chegar |
| **Fosfatagem** | ❌ Aguardando análise de solo (P Mehlich-1) | SEM_DADO — campo será preenchido quando análise chegar |

---

## Parâmetros que precisam de validação do PO Atvos

Os valores abaixo foram definidos com referências técnicas (Embrapa/IAC) e representam **pontos de partida**. O PO Atvos deve revisar e aprovar cada um antes do uso operacional.

| Processo | Parâmetro | Valor atual | O que muda se ajustar |
|---|---|---|---|
| Erradicação | Corte "tardio" | ≥ 5º corte | Muda quando canavial é considerado velho |
| Erradicação | TCH crítico | 50 t/ha | Ponto onde erradicação é quase certa |
| Erradicação | TCH de alerta | 70 t/ha | Zona de custo-benefício crítico |
| Gessagem | Al³⁺ crítico | 20% | Limiar de toxidez por alumínio |
| Gessagem | Dose máxima | 4,0 t/ha | Limite por aplicação |
| Calagem | pH adequado | 6,0 | Acima disto, sem necessidade de calcário |
| Calagem | pH crítico | 5,5 | Abaixo disto, calagem necessária |
| Calagem | V_alvo | 60% | Saturação de bases desejada |
| Calagem | PRNT | 80% | Eficiência do calcário — depende do fornecedor |
| Calagem | Dose máxima | 6,0 t/ha | Limite por aplicação |
| Fosfatagem | P muito baixo | < 8 mg/dm³ | Threshold para dose máxima |
| Fosfatagem | P alto | ≥ 30 mg/dm³ | Acima disto, sem necessidade |
| Janela plantio | Todos os meses | Ver tabela acima | Variam por unidade industrial |
