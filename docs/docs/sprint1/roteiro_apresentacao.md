---
title: "Roteiro da Apresentação"
sidebar_position: 4
---

# Roteiro — Apresentação Sprint 1

**Arquivo:** `apresentacao_sprint1_v3.pptx` (6 slides)  
**Duração:** 5–6 min (normal) | 4 min (rápido) | 8–10 min (detalhado)

---

## Slides e Roteiro

### Slide 1 — Capa

> "Bom dia / Boa tarde. Somos o Grupo 1 do Módulo 10, parceiros da Atvos. Nessa Sprint 1 entregamos a fundação de dados do projeto: ingestão, limpeza e documentação de 167 mil registros de inventário de talhões."

---

### Slide 2 — Contexto e Fontes

> "Trabalhamos com cinco fontes de dados locais — sem GCP. O coração são quatro partes do inventário de talhões cobrindo o ciclo 2021-2027, com 74 colunas cada. A quinta fonte é uma tabela de correção de talhões para cruzamentos futuros."

**Pontos a mencionar:**
- 191.025 linhas no total (50k + 50k + 50k + 17k + 23k)
- Granularidade: 1 linha = 1 talhão × 1 safra
- Chave primária: `CHAVESIG`
- Infraestrutura: sistema de arquivos local + DuckDB como alternativa ao BigQuery

---

### Slide 3 — Pipeline e Scripts

> "O pipeline tem dois estágios: Bronze (ingestão) e Silver (limpeza). Os scripts em `src/` são modulares — cada função tem responsabilidade única."

**Fluxo:**
```
data/raw/ (Excel)  →  src/ingestion/  →  src/processing/  →  data/processed/ (Parquet)
```

**Scripts entregues:**
- `extract_local.py` — lê CSV/Excel/Parquet com logging
- `clean_data.py` — pipeline Raw -> Silver (6 funções)
- `run_processing.py` — executa limpeza em lote

---

### Slide 4 — Regras de Limpeza

> "Classificamos cada coluna em 5 categorias antes de escrever uma linha de código. Isso evita decisões arbitrárias durante o processamento."

**As 5 regras:**

| Tipo | Critério | Ação |
|------|----------|------|
| 100% nulos | Coluna inteiramente nula | Deletar |
| Nulo = negócio | Ausência tem significado | Flag bool + manter nulo |
| Nulo = faltante | Dado deveria existir | Imputar mediana por `UNID_IND` |
| Nulo = geo | Sem cobertura de mapeamento | Manter, cruzar depois |
| Poucos nulos | Sem critério claro, < 6% | Manter como está |

**Exemplo de flag de negócio:** `flag_cana_ent_ausente = True` significa que o talhão não entregou cana nessa safra — não é dado faltante, é informação de negócio.

---

### Slide 5 — Resultados e Próximos Passos

> "Os três arquivos Silver estão gerados e documentados. Os inventários cresceram de 74 para 75 colunas com as flags de negócio."

**Resultados:**

| Arquivo | Linhas | Colunas raw | Colunas silver | Alterações |
|---------|--------|-------------|----------------|-----------|
| Correcao_talhoes | 23.599 | 8 | 8 | Encoding + texto |
| Inventario part 1 | 50.000 | 74 | 75 | -7 drop, +8 flags, 14.322 imputações |
| Inventario part 2 | 50.000 | 74 | 75 | -7 drop, +8 flags, 14.210 imputações |
| Inventario part 3 | 50.000 | 74 | 75 | -7 drop, +8 flags, 14.246 imputações |
| Inventario part 4 | 17.426 | 74 | 75 | -7 drop, +8 flags, 4.900 imputações |

**Próximos passos (Sprint 2):**
- União dos inventários (parts 1, 2, 3 e 4) por `CHAVESIG`
- Cruzamento com `Correcao_talhoes` via `NUM + SETOR + TALHAO`
- Enriquecimento geográfico com shapefile / IBGE para preencher coordenadas ausentes
- Análises exploratórias: distribuição de TCH por unidade industrial, safra e variedade

---

### Slide 6 — Encerramento

> "Toda a documentação está disponível no Docusaurus do projeto: mapeamento de fontes, regras de limpeza e dicionário de dados Silver. Ficamos à disposição para perguntas."

---

## Modos de Apresentação

| Modo | Duração | Slides | Como adaptar |
|------|---------|--------|--------------|
| **Rápido** | ~4 min | 1, 4, 5, 6 | Pule slides 2 e 3; mencione pipeline em uma frase no slide 5 |
| **Normal** | ~5–6 min | Todos | Siga o roteiro acima sem aprofundar exemplos |
| **Detalhado** | ~8–10 min | Todos | Expanda slide 4 com exemplos de flag; slide 3 com trecho de código |

---

## FAQ — Perguntas Antecipadas

| Pergunta | Resposta |
|----------|----------|
| Por que não usar GCP? | Decisão de infraestrutura do projeto — DuckDB sobre Parquet local cobre os casos de uso de SQL analítico sem dependência de nuvem |
| Por que mediana e não média para imputação? | A média é sensível a outliers de produção; a mediana por `UNID_IND` preserva diferenças regionais entre usinas |
| O que são as flags de negócio? | Colunas booleanas que registram ausências com significado (ex: talhão sem entrega de cana), preservando o nulo original para análise futura |
| Os dados são atualizados? | São snapshots gerados em 2026-04-23; a frequência de atualização depende do processo da Atvos |
| O que acontece com as coordenadas ausentes (~18%)? | Mantidas como nulo na Silver; o plano é cruzar com shapefile de talhões na Sprint 2 |
