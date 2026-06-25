---
title: "Análise de Custo"
sidebar_position: 4
---

# Análise de Custo — Solução vs. Alternativas

**Sprint:** 4  
**Última atualização:** 2026-06-25  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Custo da Solução Atual (Local / On-Premise)

A solução foi desenvolvida para rodar inteiramente no ambiente local da Atvos, sem dependência de serviços cloud pagos.

### Custo de infraestrutura: R$ 0/mês

| Componente | Tecnologia adotada | Alternativa cloud | Custo cloud estimado |
|---|---|---|---|
| Armazenamento de dados | Sistema de arquivos local (`data/`) | AWS S3 / GCS | R$ 50–200/mês |
| Processamento da pipeline | Python local (`src/pipeline/`) | AWS Lambda / Cloud Run | R$ 100–500/mês |
| Banco de dados | Parquet + DuckDB | BigQuery / Redshift | R$ 200–800/mês |
| Servidor da API | `http.server` embutido do Python | Cloud Run / App Engine | R$ 150–600/mês |
| Frontend | HTML/CSS/JS estático | Vercel / Netlify | R$ 0–100/mês |
| **Total mensal** | **R$ 0** | | **R$ 500–2.200/mês** |

### Custo de desenvolvimento

| Item | Horas estimadas | Observação |
|---|---|---|
| Ingestão e limpeza (Sprint 1) | ~40h | Pipeline Raw → Silver |
| Motor de regras (Sprint 2) | ~60h | 7 módulos + 170 testes |
| API REST (Sprint 3) | ~30h | Servidor HTTP puro Python |
| Frontend (Sprint 4) | ~40h | SPA 3 telas sem framework |
| **Total** | **~170h** | |

---

## 2. Custo da Arquitetura Alternativa (GCP / AWS)

Estimativa para o mesmo volume de dados (471 mil registros Gold, 67 mil talhões):

### Google Cloud Platform

| Serviço | Uso estimado | Custo mensal (USD) |
|---|---|---|
| Cloud Storage | 10 GB (Parquet + Excel) | $0,23 |
| Cloud Run | 1 instância 1vCPU/2GB, 730h | $21,60 |
| BigQuery | 10 GB armazenados + 100 GB queries/mês | $7,00 |
| Cloud Scheduler | 30 execuções/mês (pipeline diário) | $0,10 |
| **Total** | | **~$29/mês (~R$ 165/mês)** |

### Amazon Web Services

| Serviço | Uso estimado | Custo mensal (USD) |
|---|---|---|
| S3 | 10 GB | $0,23 |
| Lambda | 30 execuções × 5 min × 1 GB | $0,50 |
| RDS PostgreSQL | db.t3.micro | $15,00 |
| EC2 t3.small (API) | On-demand 730h | $16,80 |
| **Total** | | **~$33/mês (~R$ 190/mês)** |

---

## 3. Comparação Direta

| Dimensão | Solução Atual | GCP | AWS |
|---|---|---|---|
| Custo mensal | **R$ 0** | R$ 165 | R$ 190 |
| Custo anual | **R$ 0** | R$ 1.980 | R$ 2.280 |
| Dependência externa | Nenhuma | Alta | Alta |
| Portabilidade | Total | Média | Média |
| SLA de disponibilidade | Depende do hardware local | 99,9%+ | 99,9%+ |
| Escalabilidade automática | Manual (adicionar workers) | Automática | Automática |
| Setup inicial | Baixo | Médio | Alto |
| Segurança dos dados | Controle total (on-premise) | Compartilhada | Compartilhada |

---

## 4. Valor Gerado vs. Custo

### Impacto financeiro potencial

O motor de regras identifica talhões com necessidade de erradicação (custo de ~R$ 800–1.500/ha) e prioriza por urgência. Para a Atvos com ~200.000 ha cultivados:

| Cenário | Impacto estimado |
|---|---|
| Reduzir 1% de erradicações tardias (200 ha) | Economia de R$ 160–300 mil/safra |
| Otimizar dose de calcário em 5% dos talhões | Economia de R$ 50–100 mil/safra |
| Antecipar 2% de dessecações (400 ha) | Ganho de qualidade estimado R$ 200 mil/safra |

### ROI estimado

```
Custo total de desenvolvimento (170h × R$ 80/h):   R$ 13.600
Custo operacional anual:                            R$      0
Economia estimada conservadora (1ª safra):          R$ 200.000+

ROI no 1º ano: (200.000 - 13.600) / 13.600 = 1.370%
```

---

## 5. Decisão de Arquitetura e Justificativa

A solução local foi escolhida pelos seguintes critérios:

1. **Confidencialidade dos dados** — Dados de produção da Atvos (volumes, talhões, produtividade) não saem do ambiente da empresa
2. **Zero custo recorrente** — Viável para projeto-piloto sem aprovação de budget cloud
3. **Independência de conectividade** — Opera mesmo sem internet (campo agrícola)
4. **Velocidade de iteração** — Deploy é apenas copiar arquivos; sem CI/CD cloud necessário

### Quando migrar para cloud?

A migração para cloud passa a ser justificada quando:
- Mais de 3 usuários simultâneos precisam da API em tempo real
- O volume de dados cresce acima de 50 GB (Parquet fica lento)
- A Atvos deseja integrar com ERPs ou sistemas externos via API pública
- SLA de 99,9%+ é exigido para o sistema

---

## 6. Custo de Manutenção e Evolução

| Tarefa | Frequência | Esforço |
|---|---|---|
| Atualizar dados Excel raw | Mensal | 5 min (rodar pipeline) |
| Ajustar limiares agronômicos | A pedido do PO | 1–2h por módulo |
| Adicionar novo módulo de regra | Por demanda | 4–8h (incluindo testes) |
| Atualizar frontend | Por demanda | 2–4h |
| Backup dos dados Gold | Automático via OS | R$ 0 (disco local) |
