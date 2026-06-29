---
title: "Análise de Custo"
sidebar_position: 4
---

# Análise de Custo — Solução vs. Alternativas

**Sprint:** 4  
**Última atualização:** 2026-06-25  
**Responsável:** Módulo 10 — Atvos G1

---

## 1. Custo de Desenvolvimento

A solução foi entregue como **projeto acadêmico pelo Inteli** — o custo de desenvolvimento para a Atvos foi **R$ 0**. Não houve contratação de equipe externa nem horas faturadas ao parceiro.

---

## 2. Custo de Manutenção — Desenvolvedor de Mercado

Após a entrega, a manutenção e evolução do sistema requer um perfil de **desenvolvedor pleno** com conhecimento em Python, engenharia de dados e domínio agronômico básico.

### Encargos reais de um dev pleno CLT no Brasil (2025)

| Item | Cálculo |
|---|---|
| Salário bruto mensal | R$ 8.000 |
| INSS patronal (20%) | R$ 1.600 |
| FGTS (8%) | R$ 640 |
| 13º salário (8,33%/mês) | R$ 666 |
| Férias + 1/3 (11,1%/mês) | R$ 888 |
| RAT + Sistema S (~5,8%) | R$ 464 |
| VR/VA + Plano de saúde | R$ 1.200 |
| **Custo real/mês para a empresa** | **R$ 13.458** |
| **Custo/hora (168h úteis/mês)** | **~R$ 80/h** |

### Horas de manutenção estimadas por ano

| Tarefa | Frequência | Horas/ano |
|---|---|---|
| Executar pipeline e validar Gold | Mensal (30 min) | 6h |
| Atualizar dados Excel raw | Mensal (1h) | 12h |
| Ajustar limiares agronômicos (a pedido do PO) | Trimestral (3h) | 12h |
| Adicionar novo módulo de regra (com testes) | Semestral (8h) | 16h |
| Atualizar frontend e API | Trimestral (4h) | 16h |
| Monitoramento e correção de bugs | Contínuo | 20h |
| **Total estimado** | | **~82h/ano** |

**Custo de manutenção anual:** 82h × R$ 80/h = **~R$ 6.560/ano**

> Comparação: contratação de consultoria PJ (R$ 120–180/h) → R$ 9.840–14.760/ano

---

## 3. Custo de Infraestrutura no GCP

A Atvos já utiliza Google Cloud Platform. Os serviços incrementais para hospedar esta solução são:

### Serviços GCP necessários (preços GCP Calculator, jun/2025, câmbio R$ 5,70)

| Serviço | Configuração | Custo/mês (USD) | Custo/mês (BRL) |
|---|---|---|---|
| Cloud Storage | 15 GB Standard (Parquet + Excel + Gold) | $0,30 | R$ 1,71 |
| Cloud Run — API | 1 vCPU / 512 MB, 730h contínuas | $14,40 | R$ 82,08 |
| Cloud Run — Pipeline | 2 vCPU / 2 GB, 30 execuções × 2 min | $0,18 | R$ 1,03 |
| Cloud Scheduler | 2 jobs (pipeline diário + limpeza) | $0,00 | R$ 0,00 (free tier) |
| BigQuery | 10 GB armazenados + 50 GB queries | $0,45 | R$ 2,57 |
| Artifact Registry | Imagem Docker (~500 MB) | $0,05 | R$ 0,29 |
| **Total mensal** | | **~$15,38** | **~R$ 87,70** |
| **Total anual** | | **~$184,56** | **~R$ 1.052** |

> Se a Atvos já tem **Committed Use Discount (CUD)** de 1 ou 3 anos no GCP, o custo de Cloud Run cai 37–55%, reduzindo o total para R$ 55–70/mês.

### Por que usar o GCP da Atvos e não on-premise

| Critério | On-premise | GCP Atvos |
|---|---|---|
| Custo incremental | R$ 0 (já tem servidor) | ~R$ 88/mês |
| Disponibilidade para múltiplos usuários | Depende da rede interna | 99,95% SLA |
| Backup automático | Manual | Automático (versioning GCS) |
| Integração com outros sistemas Atvos | Mais complexa | Nativa (IAM, VPC) |
| Deploy de atualização | Copiar arquivos manualmente | `gcloud run deploy` |

---

## 4. Custo Total da Solução em Produção (Cenário GCP)

| Componente | Custo anual |
|---|---|
| Desenvolvimento inicial (Inteli) | **R$ 0** |
| Infraestrutura GCP | **~R$ 1.052** |
| Manutenção (dev pleno, 82h/ano) | **~R$ 6.560** |
| **Total ano 1** | **~R$ 7.612** |
| **Total ano 2 em diante** | **~R$ 7.612/ano** |

---

## 5. ROI — Comparação com Alternativas Reais

### Alternativa A: Análise manual por agrônomo

Um agrônomo sênior dedicado a analisar 67.426 talhões manualmente por safra:

| Item | Estimativa |
|---|---|
| Horas para analisar 67k talhões manualmente | 400–800h/safra |
| Custo do agrônomo sênior (R$ 100–150/h consultor) | R$ 40.000–120.000/safra |
| Frequência da análise completa | 1–2× por safra |
| **Custo anual da alternativa manual** | **R$ 40.000–120.000** |

**Economia anual vs. análise manual:** R$ 32.400–112.400  
**ROI:** (economia − custo solução) / custo solução = **325% a 1.377%**

### Alternativa B: Contratação de empresa de dados para construir solução equivalente

| Item | Estimativa de mercado |
|---|---|
| Desenvolvimento de pipeline + API + frontend equivalente | R$ 120.000–250.000 |
| Manutenção anual contratada | R$ 24.000–60.000/ano |
| Custo total 3 anos | R$ 192.000–430.000 |
| **Custo da nossa solução em 3 anos** | **~R$ 22.836** |
| **Economia em 3 anos** | **R$ 169.000–407.000** |

### Alternativa C: Ferramenta SaaS de analytics agronômico

Plataformas como Trimble Ag, John Deere Operations Center ou AgWorld:

| Item | Estimativa |
|---|---|
| Licença por usuário/mês | R$ 150–500/usuário |
| Para 10 usuários (agrônomos + gestores) | R$ 1.500–5.000/mês |
| Custo anual | R$ 18.000–60.000 |
| Customização para regras Atvos | Não disponível (regras genéricas) |

> SaaS genérico não implementa as regras específicas da Atvos (PRNT=80, limiares por faixa de corte, textura do Cerrado). A solução entregue é customizada para o portfólio de talhões e dados do parceiro.

---

## 6. Resumo do ROI

| Comparação | Custo anual da alternativa | Custo anual da solução | Economia/ano | ROI |
|---|---|---|---|---|
| vs. agrônomo consultor (conservador) | R$ 40.000 | R$ 7.612 | R$ 32.388 | **325%** |
| vs. agrônomo consultor (completo) | R$ 120.000 | R$ 7.612 | R$ 112.388 | **1.377%** |
| vs. empresa de dados (3 anos) | R$ 64.000/ano | R$ 7.612/ano | R$ 56.388/ano | **641%** |
| vs. SaaS genérico | R$ 36.000/ano | R$ 7.612/ano | R$ 28.388/ano | **273%** |

**Pior cenário defensável: ROI de 273% ao ano** (vs. SaaS genérico mais barato do mercado, sem customização)

---

## 7. Quando Migrar para Cloud / Escalar

| Gatilho | Ação recomendada | Custo adicional estimado |
|---|---|---|
| > 5 usuários simultâneos na API | Cloud Run com autoscaling | +R$ 50/mês |
| Volume > 500k talhões | ProcessPoolExecutor ou Dask | Apenas dev (sem infra extra) |
| Integração com ERP Atvos | Cloud Pub/Sub + Dataflow | +R$ 200–500/mês |
| SLA 99,9%+ exigido | Cloud Run multi-region | +R$ 150/mês |
| Dados de solo disponíveis | Adicionar mapeamento em `_preparar_talhao()` | ~8h dev (R$ 640) |
