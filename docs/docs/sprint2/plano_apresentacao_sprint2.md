# Plano de Apresentação — Sprint 2: Motor de Regras Agronômicas
**Atvos G1 | Sprint 2 | 2026**

> Documento para validação antes da implementação no Canva.
> Cada slide segue a estrutura: **Título · Texto do slide · Notas do apresentador · Indicação visual**

---

## CAPA

**Título principal:** Motor de Regras Agronômicas
**Subtítulo:** Sprint 2 — Geração da Camada Gold
**Rodapé:** Atvos G1 | Sprint 2 | 2026

*Notas:* Slide de abertura. Contextualiza o tema sem entrar em detalhes técnicos.

*Visual sugerido:* Fundo escuro com fotografia aérea de canavial (estilo da paleta verde já usada no template).

---

## AGENDA (slide já pronto — referência)

7 tópicos conforme imagem compartilhada. Não requer alteração de conteúdo.

---

## SLIDE 01 — Unificação dos Dados

**Título:** 01 · Unificação dos Dados

**Corpo do slide:**
- Inventário Silver dividido em 4 arquivos de origem
- Concat → **167.426 talhões** consolidados
- Base única para todas as etapas seguintes

*Notas do apresentador:* A fragmentação original é um dado do contexto operacional — cada arquivo corresponde a uma parte da coleta de campo. O concat é a primeira operação do pipeline; sem ela nenhuma análise em escala seria possível.

*Visual sugerido:* Diagrama horizontal simples mostrando 4 caixas (Inventário 1, 2, 3, 4) convergindo para uma única caixa "167.426 talhões". Estilo seta → merge → resultado. Pode ser feito direto no Canva com shapes.

---

## SLIDE 02 — Aplicação de Correção de Talhões

**Título:** 02 · Correção de Talhões

**Corpo do slide:**
- Talhões reformados mudam de CHAVE ao longo do tempo
- Sem correção: **18.353 talhões** sem par de solo no join
- Tabela `Correcao_talhoes` remapeia a CHAVE antiga → nova
- Passo **crítico** para a integridade da base Gold

*Notas do apresentador:* Este foi um dos achados mais importantes do sprint. Os talhões que passaram por reforma têm uma CHAVE diferente no inventário versus no registro de análise de solo — se não aplicarmos a correção, perdemos dados de solo de mais de 18 mil talhões. O resultado direto seria orientações piores para quase 11% da base.

*Visual sugerido:* Duas colunas lado a lado — "Sem Correção" (vermelho: X talhões sem match) vs "Com Correção" (verde: talhões recuperados). Ou um "before / after" estilizado. Destaque numérico em 18.353.

---

## SLIDE 03 — JOIN com Dados de Solo

**Título:** 03 · JOIN com Dados de Solo

**Corpo do slide:**
- Left join: `CHAVE` (inventário) = `FST` (análise de solo)
- **74.768 talhões** com análise de solo (44,7%)
- **92.658 talhões** sem análise de solo (55,3%)
- Talhões sem solo: orientações agronômicas limitadas

*Notas do apresentador:* O join é left para garantir que todo talhão do inventário apareça na base Gold — mesmo sem dado de solo. Para esses 55,3%, a orientação retornada é `dado_ausente_analise_solo`, que serve como alerta para priorizar coleta de campo.

*Visual sugerido:* Gráfico de pizza ou rosca (donut) com dois segmentos: 44,7% verde (com solo) e 55,3% cinza (sem solo). Simples e direto. Alternativa: dois grandes números lado a lado com ícone de check e X.

---

## SLIDE 04 — Regras Geradas

**Título:** 04 · Regras Geradas

**Corpo do slide (tabela ou cards):**

| Regra | O que avalia |
|---|---|
| Calagem | Necessidade de correção de pH (V% e CTC) |
| Gessagem | Alumínio tóxico e Ca no subsolo |
| Fosfatagem | Dose de manutenção de fósforo por produtividade |
| Erradicação | Reforma do canavial (TCH baixo + corte alto) |
| Janela de Plantio | Colheita estimada dentro de mai–nov |

*Notas do apresentador:* Cinco módulos independentes, cada um recebendo os dados do talhão e retornando uma orientação + parâmetros calculados. A lógica está encapsulada por arquivo — o pipeline apenas orquestra a execução.

*Visual sugerido:* 5 cards horizontais ou verticais, um por regra, com ícone simples (planta, solo, calendário, etc.). Paleta verde do template. Evitar texto corrido — os cards já comunicam a estrutura modular.

---

## SLIDE 05 — Considerações sobre as Regras

**Título:** 05 · Considerações sobre as Regras

**Corpo do slide:**
- Regras baseadas no **Manual Agroadvance 2022** + TAP AgroTech ATVOS
- Parâmetros provisórios marcados com `flag_aguardando_validacao_po`
- **6 pontos** aguardam confirmação do PO ATVOS antes de produção:
  1. V% alvo para calagem (implementado: 60%)
  2. Tabela argila × textura para gessagem
  3. Limiares de P crítico para fosfatagem (dose de correção)
  4. Limiar de TCH e número de corte para erradicação (55 t/ha, 6° corte)
  5. Matriz de Aptidão mensal para janela de plantio
  6. TCH\_PROD: substituir imputação por modelos de estimativa (Sprint 3)

*Notas do apresentador:* O flag permite ao PO distinguir imediatamente o que é definitivo do que é provisório. Nenhuma orientação marcada com esse flag deve ser usada operacionalmente sem validação.

*Visual sugerido:* Lista numerada limpa (pode ser visual de checklist com ícones de "relógio/pendente" em amarelo ao lado de cada item). Ou: um ícone de alerta amarelo grande no canto com "6 parâmetros pendentes" em destaque, e a lista em texto menor ao lado.

---

## SLIDE 06 — Resultados das Regras

**Título:** 06 · Resultados das Regras

**Corpo do slide (foco nos números principais):**

- **573 talhões** com indicação de reforma prioritária *(TCH baixo + corte alto)*
- **20.264 talhões** com necessidade de calagem *(4.452 incorporada + 15.812 superficial)*
- **1.135 talhões** com indicação de gessagem
- **127.150 talhões** com dose de fosfatagem calculada
- **68.312 talhões** sem análise de solo → aguardam coleta de campo

*Notas do apresentador:* Os 573 talhões com erradicação de prioridade ALTA são o resultado operacional mais imediato do sprint — é uma lista acionável hoje. O dado de 68 mil talhões sem solo é o maior gap de qualidade da base e orienta o próximo ciclo de coleta de campo.

*Visual sugerido:* Layout de "destaques em números grandes" — 5 métricas em cards ou blocos com o número em fonte grande (estilo KPI dashboard). Destaque especial (cor diferente ou borda) para os 573 de erradicação prioritária. Evitar gráfico de barras aqui — os números por si já comunicam.

---

## SLIDE 07 — Estrutura do Projeto

**Título:** 07 · Estrutura do Projeto

**Corpo do slide:**

```
Bronze  →  Silver  →  Gold
```

- **Bronze:** dados brutos de campo e laboratório
- **Silver:** dados limpos, padronizados e enriquecidos (167k talhões)
- **Gold:** orientações agronômicas por talhão — 1 linha, 1 talhão, 5 processos

Pipeline: `src/pipeline_gold.py` + `src/rules/` (5 módulos)
Saída: `.parquet` + `.csv` em `data/gold/`

*Notas do apresentador:* A arquitetura medallion garante que cada camada seja auditável e reprocessável de forma independente. O Gold gerado neste sprint já está em formato wide — pronto para consumo por agrônomos, dashboards ou APIs.

*Visual sugerido:* Diagrama de três camadas (Bronze → Silver → Gold) com setas e ícones de banco de dados. Abaixo, o fluxo do pipeline gold: "4 Inventários Silver → Concat → Correção Talhões → JOIN Solo → Motor de Regras → Gold". Pode ser um flowchart simples horizontal feito no Canva.

---

## SLIDE FINAL (opcional — encerramento)

**Título:** Próximos Passos

**Corpo:**
- Review dos 6 parâmetros com PO ATVOS
- Rodar pipeline em toda a base (`--todos`)
- Sprint 3: substituir TCH imputado pelos modelos de estimativa ATVOS

*Visual sugerido:* Timeline horizontal com 3 etapas ou simples lista de bullets com ícone de seta.

---

## Notas Gerais de Design

- **Paleta:** Manter o verde escuro (#1a5c2a ou similar) e branco do template já definido
- **Texto nos slides:** O mínimo necessário — os números falam por si. Evitar parágrafos. Preferir cards, tabelas simples e destaques numéricos.
- **Fontes:** Títulos grandes e limpos; corpo em fonte menor mas legível
- **Rodapé fixo:** "Atvos G1 | Sprint 2 | 2026" em todos os slides (já presente no template)
- **Total de slides:** Capa + Agenda + 7 conteúdo + 1 encerramento = **~10 slides**
