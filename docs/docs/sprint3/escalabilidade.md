---
title: "Plano de Escalabilidade"
sidebar_position: 4
---

# Plano de Escalabilidade — Pipeline Agronômica

**Sprint:** 3  
**Última atualização:** 2026-06-25  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Contexto

A pipeline Silver → Gold processa **67.426 talhões × 7 processos = 471.982 chamadas de função** a cada execução. Na versão sequencial original, esse loop era o gargalo principal:

```python
# Versão original (sequencial)
for _, row in df.iterrows():           # 67.426 iterações
    for processo, func in REGRAS.items():  # × 7 funções
        resultado = func(talhao)
```

Com a modularização do Sprint 3, o transformer foi reescrito para paralelismo por talhão.

---

## 2. Por que os Talhões São Paralelizáveis

As funções de regra têm três propriedades que tornam o paralelismo trivialmente seguro:

1. **Puras** — recebem `talhao: dict` e retornam `dict`; sem efeitos colaterais
2. **Sem estado compartilhado** — não leem nem escrevem em variáveis globais
3. **Determinísticas** — mesma entrada → mesma saída sempre

Portanto, qualquer talhão pode ser processado em qualquer ordem, por qualquer thread, sem locks.

---

## 3. Implementação Atual — ThreadPoolExecutor

```python
# src/pipeline/transformer.py
from concurrent.futures import ThreadPoolExecutor, as_completed

N_WORKERS = min(os.cpu_count() or 4, 8)

def aplicar_regras(df, hoje, n_workers=N_WORKERS):
    rows = df.to_dict("records")          # ~10× mais rápido que iterrows()

    todos_registros = []
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_processar_talhao, row, hoje) for row in rows]
        for future in as_completed(futures):
            todos_registros.extend(future.result())

    return pd.DataFrame(todos_registros, columns=COLUNAS_GOLD)
```

**Ganho esperado com 8 workers** (máquina com 8 núcleos):

| Cenário | Talhões | Tempo sequencial (est.) | Tempo paralelo (est.) |
|---|---|---|---|
| Produção atual | 67.426 | ~45 s | ~8 s |
| Expansão ×3 | 200.000 | ~130 s | ~20 s |
| Expansão ×10 | 670.000 | ~430 s | ~60 s |

> Estimativas baseadas em benchmark de 4,31 s para 170 testes (talhões menores).

---

## 4. Otimizações Já Aplicadas

| Otimização | Impacto | Onde |
|---|---|---|
| `df.to_dict('records')` em vez de `iterrows()` | ~10× mais rápido na leitura | `transformer.py` |
| `ThreadPoolExecutor` com `as_completed` | Paralelismo por talhão | `transformer.py` |
| `round(valor, 2)` apenas no resultado final | Elimina arredondamentos intermediários | `_base.py resultado()` |
| Parquet em vez de CSV para Silver | Leitura ~5× mais rápida | `loader.py` |

---

## 5. Próximos Passos de Escala

### 5.1 ProcessPoolExecutor (CPU-bound real)

Para volumes acima de 500 mil talhões, o GIL do Python limita o ganho das threads. Trocar por `ProcessPoolExecutor` elimina o GIL:

```python
from concurrent.futures import ProcessPoolExecutor

# Requer que _processar_talhao e REGRAS sejam picklables
with ProcessPoolExecutor(max_workers=n_workers) as executor:
    ...
```

**Pré-requisito:** importar REGRAS dentro do worker (não no nível de módulo) para evitar problemas de serialização no Windows.

### 5.2 Dask para volumes de Big Data

Para inventários com milhões de talhões (cenário de expansão Atvos para outras culturas), Dask permite processar DataFrames maiores que a RAM:

```python
import dask.dataframe as dd

ddf = dd.from_pandas(df_silver, npartitions=16)
resultado = ddf.map_partitions(lambda part: _aplicar_lote(part, hoje)).compute()
```

### 5.3 Cache de resultados inalterados

A maioria dos talhões não muda entre execuções diárias. Um cache por `(CHAVESIG, data_geracao)` evita reprocessar talhões sem alteração no Silver:

```python
def _hash_talhao(row: dict) -> str:
    campos_relevantes = ("TCH_PROD", "NO_CORTE", "CATEGORIA", "AREA_HA")
    return hashlib.md5(str({k: row.get(k) for k in campos_relevantes}).encode()).hexdigest()
```

### 5.4 Execução incremental por unidade

Dividir o Silver por `UNID_IND` e processar apenas a unidade que teve atualização de dados:

```bash
python src/pipeline_gold.py --unidade UMV   # processa apenas UMV
```

---

## 6. Monitoramento de Performance

O `reporter.py` já exibe o resumo pós-execução. Para rastrear tempo por etapa, instrumentar com `time.perf_counter()`:

```python
t0 = time.perf_counter()
df_gold = aplicar_regras(df_silver, hoje)
log("PERF", "transformer", f"{time.perf_counter() - t0:.2f}s para {len(df_silver)} talhões")
```

---

## 7. Resumo da Decisão de Arquitetura

```
Volume atual (67k talhões)  →  ThreadPoolExecutor  ✅ implementado
Volume ×10 (670k talhões)   →  ProcessPoolExecutor  (próximo sprint)
Volume Big Data (milhões)   →  Dask / Spark         (roadmap)
```

A separação entre `loader`, `transformer`, `saver` e `reporter` garante que cada etapa pode ser substituída ou escalonada de forma independente sem alterar as demais.
