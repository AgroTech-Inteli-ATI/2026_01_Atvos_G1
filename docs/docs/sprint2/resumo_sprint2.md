# Sprint 2 — Motor de Regras Agronômicas
**Status:** Concluída (22/05/2026) | **Próxima validação:** Review com PO ATVOS

---

## O que foi entregue

### Pipeline Gold (`src/pipeline_gold.py`)
Pipeline de 4 passos que transforma os dados Silver em orientações operacionais por talhão:

1. **Unificar** — concat das 4 partes do inventário Silver (167.426 talhões)
2. **Corrigir** — aplica `Correcao_talhoes` remapeando 18.353 CHAVEs reformadas (passo crítico para o join funcionar)
3. **Enriquecer** — left join `CHAVE == FST` com `Dados_analise_solo.csv` (44,7% dos talhões casam)
4. **Gerar Gold** — aplica os 5 módulos de regra, salva em formato wide (uma linha por talhão, colunas por processo)

Arquivos gerados em `data/gold/`: `amostra_gold_YYYY-MM-DD.parquet` e `.csv`

```
4 × Inventario_*_silver.parquet
        ↓  pd.concat
inventario_silver_unificado.parquet       (167.426 talhões)

        ↓  Correcao_talhoes (18.353 CHAVEs remapeadas)
inventario_silver_corrigido.parquet

        ↓  left join CHAVE == FST
inventario_silver_enriquecido.parquet
  ├── Com análise de solo:  74.768 talhões (44,7%)
  └── Sem análise de solo:  92.658 talhões (55,3%)

        ↓  Motor de Regras (5 módulos × talhões com solo)
amostra_gold_YYYY-MM-DD.parquet/.csv     (formato wide — 1 linha por talhão)
```

> A tabela `Correcao_talhoes` é **crítica** para o join: sem ela, 18.353 CHAVEs reformadas não casariam com os registros de solo correspondentes.

---

### Módulos de Regras (`src/rules/`)

| Arquivo | Função principal | Dado crítico | Parâmetro pendente PO |
|---|---|---|---|
| `calagem.py` | `calcular_calagem()` | V1, CTC1, mg1 | V% alvo = 60% |
| `gessagem.py` | `calcular_gessagem()` | ca2, al2, sb2 | Tabela argila × textura |
| `fosfatagem.py` | `calcular_fosfatagem()` | TCH_PROD | Limiares P crítico (dose de correção) |
| `erradicacao.py` | `calcular_erradicacao()` | TCH_PROD, NO_CORTE | TCH < 55 t/ha e corte ≥ 6 |
| `janela_plantio.py` | `calcular_janela_plantio()` | ULT_CORTE (soca) / DATA_PLANTIO (demais) | Matriz de Aptidão por mês |

Cada função recebe um dicionário com os dados do talhão e retorna `orientacao`, `valor_calculado`, `regra_acionada` e `flag_aguardando_validacao_po`.

---

### Dados necessários por processo

| Processo | Dado crítico | Fonte | Disponível? |
|---|---|---|---|
| Calagem | `V1`, `CTC1`, `mg1`, `CATEGORIA` | Solo + Silver | ✅ |
| Gessagem | `ca2`, `al2`, `sb2`, `DE_TP_SOLO` | Solo + Silver | ✅ (textura por keyword matching) |
| Fosfatagem | `TCH_PROD`, `CATEGORIA` | Silver | ✅ (imputado por mediana quando nulo) |
| Erradicação | `TCH_PROD`, `NO_CORTE`, `CATEGORIA` | Silver | ✅ |
| Janela de Plantio | `ULT_CORTE` (soca) / `DATA_PLANTIO` (demais), `ESTAGIO` | Silver | ✅ |

Duas colunas derivadas são calculadas internamente pelos módulos antes de aplicar as regras:

| Coluna derivada | Cálculo | Usada em |
|---|---|---|
| `argila_g_kg` | keyword matching em `DE_TP_SOLO` | Gessagem (dose) |
| `m_percent_subsolo` | `al2 / (sb2 + al2) × 100` | Gessagem (critério de disparo) |

> `m_percent_subsolo` usa fórmula padrão Embrapa/IAC — não consta no Manual Agroadvance, foi adicionada como conhecimento técnico complementar.

---

### Documentação gerada

| Arquivo | Conteúdo |
|---|---|
| `docs/sprint2/regras_agronomicas.md` | Pseudocódigo de todas as regras, fontes do manual, interpretação técnica por processo |
| `docs/sprint2/relatorio_amostra_gold.md` | Análise dos 270 talhões da amostra com números por processo |
| `docs/sprint2/resumo_sprint2.md` | Este arquivo |

---

## Números da Amostra (270 talhões, 30 por unidade)

| Processo | Destaque |
|---|---|
| Calagem | 78 talhões com necessidade (23 incorporada + 55 superficial); dose média 3,2 t/ha |
| Gessagem | 11 talhões com indicação (Ca subsolo < 4 e m% > 40%) |
| Fosfatagem | 207 talhões com dose calculada; média 31,7 kg P₂O₅/ha |
| Erradicação | 7 talhões com algum nível de indicação (3 MÉDIA + 4 BAIXA) |
| Janela de plantio | A ser reprocessada — ver nota abaixo |

> **Nota sobre janela de plantio:** os números anteriores da amostra (44% fora da janela) foram gerados com uma versão que usava `DATA_PLANTIO` para soca, quando o correto é `ULT_CORTE`. O módulo foi corrigido; os números serão atualizados na próxima execução do pipeline.

---

## Resultados do Pipeline Completo (base Silver, execução em 22/05/2026)

> ⚠️ Números de janela de plantio abaixo são da versão anterior do módulo (antes da correção ULT_CORTE). Serão reprocessados.

| Processo | Regra acionada | Qtd talhões |
|---|---|---|
| Calagem | `calagem_incorporada` | 4.452 |
| Calagem | `calagem_superficial` | 15.812 |
| Calagem | `v_percent_adequado` (solo ok) | 38.574 |
| Calagem | `dado_ausente_analise_solo` | 68.312 |
| Calagem | `calagem_nao_aplicavel` | 40.276 |
| Gessagem | `gessagem_necessaria` | 1.135 |
| Gessagem | `gessagem_nao_necessaria` | 73.633 |
| Gessagem | `dado_ausente_analise_subsolo` | 92.658 |
| Fosfatagem | `fosfatagem_manutencao_cana_planta` | 24.567 |
| Fosfatagem | `fosfatagem_manutencao_soca` | 102.583 |
| Fosfatagem | `fosfatagem_nao_aplicavel` | 40.276 |
| Erradicação | `erradicacao_tch_baixo_e_corte_alto` (**prioridade ALTA**) | **573** |
| Erradicação | `erradicacao_tch_baixo` (prioridade MÉDIA) | 3.126 |
| Erradicação | `erradicacao_corte_alto_tch_ok` (monitorar) | 2.454 |
| Erradicação | `erradicacao_nao_necessaria` | 9.625 |
| Janela de Plantio | `janela_dentro_do_ideal` | 84.912 ⚠️ |
| Janela de Plantio | `janela_fora_do_ideal` | 63.757 ⚠️ |
| Janela de Plantio | `dado_ausente_data_plantio` | 227 ⚠️ |

Destaques: 68.312 talhões sem análise de solo (precisam de coleta de campo); 573 talhões com indicação de reforma prioritária (TCH baixo + corte alto).

---

## Decisões de Arquitetura

- **Formato wide** — uma linha por talhão com colunas por processo (ex: `calagem_orientacao`, `calagem_dose_t_ha`), mais legível para agrônomos e para exportação tabular
- **Amostra por padrão** — pipeline roda com 30 talhões por unidade até as regras serem validadas pelo PO; flag `--todos` disponível para produção
- **Lógica nos módulos** — cada `regra.py` tem a lógica completa; o pipeline só orquestra (`apply()` por linha)
- **`flag_aguardando_validacao_po`** — todas as orientações com parâmetros incertos são marcadas, permitindo filtrar o que é provisório

---

## Pendências para Validação com o PO ATVOS

Os itens abaixo estão implementados com parâmetros provisórios (`flag_aguardando_validacao_po = True`) e precisam ser confirmados antes de uso em produção:

1. **Calagem — V% alvo:** implementado com 60% (padrão do setor). A ATVOS adota esse valor ou tem um específico por unidade/ambiente?

2. **Gessagem — Tabela argila × textura:** o matching por palavras-chave (`"muito argilosa"` → 500 g/kg, `"argilosa"` → 350 g/kg, etc.) está correto para os solos da ATVOS?

3. **Fosfatagem — Dose de correção:** a implementação atual cobre apenas a dose de **manutenção** (exportação × TCH). A dose de **correção** por deficiência de P depende dos limiares críticos por textura que a ATVOS adota (Boletim 100/IAC ou protocolo próprio).

4. **Erradicação — Limiares:** TCH < 55 t/ha e 6° corte como limiar de reforma — a ATVOS usa esses valores ou tem parâmetros específicos por unidade industrial ou variedade?

5. **Janela de Plantio — Matriz de Aptidão:** o TAP menciona uma "Matriz de Aptidão por mês" para priorização de plantio, mais granular que a regra mai–nov implementada. Como é estruturada essa matriz?

6. **TCH como insumo:** o TAP especifica que os modelos de estimativa de safra da própria ATVOS devem alimentar o `TCH_PROD` do pipeline (Sprint 3). Atualmente estamos usando os valores imputados do Silver.

---

## O que precisa acontecer antes da Sprint 3

1. **Review com PO ATVOS** — validar os 6 parâmetros listados na seção "Pendências" acima
2. **Rodar em toda a base** — `python src/pipeline_gold.py --todos` após validação das regras
3. **TCH_PROD** — Sprint 3 substituirá o valor imputado pelos modelos de estimativa da própria ATVOS

---

*Fonte das regras: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022) + TAP AgroTech ATVOS*
*Atualizado em: 22/05/2026*
