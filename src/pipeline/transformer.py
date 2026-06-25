"""
src/pipeline/transformer.py
Responsabilidade única: transformar o DataFrame Silver em registros Gold.

Fluxo por talhão:
  1. preparar_talhao(row)         — Silver dict → input das regras
  2. _processar_talhao(row, hoje) — aplica REGRAS e monta os registros
  3. aplicar_regras(df, hoje)     — paraleliza sobre todos os talhões

Paralelismo:
  Cada talhão é processado de forma independente (sem estado compartilhado),
  o que torna a etapa de transformação naturalmente paralelizável.
  ThreadPoolExecutor distribui os talhões entre os workers sem risco de
  condições de corrida, pois as funções de regra são puras.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Optional

import pandas as pd

from rules import REGRAS

# Número de threads: limitado a 8 para não sobrecarregar máquinas com poucos núcleos
N_WORKERS: int = min(os.cpu_count() or 4, 8)

COLUNAS_GOLD = [
    "id_talhao",
    "chave",
    "unidade",
    "safra",
    "processo",
    "orientacao",
    "valor_calculado",
    "regra_acionada",
    "insumo",
    "dose_kg_ha",
    "quantidade_total_kg",
    "area_ha",
    "data_geracao",
]


# ── MAPEAMENTO SILVER → INPUT DAS REGRAS ─────────────────────────────────────

def preparar_talhao(row: Any) -> dict:
    """
    Converte uma linha do DataFrame Silver (dict ou pd.Series) no dicionário
    de entrada das regras agronômicas.

    Campos de análise de solo (ph_solo, ctc, etc.) ainda não existem na Silver —
    ficam como None e dispararão SEM_DADO nas regras que os exigem.
    Quando esses dados chegarem, adicionar o mapeamento aqui.

    Parameters
    ----------
    row : dict | pd.Series
        Uma linha do DataFrame Silver.

    Returns
    -------
    dict com todos os campos esperados pelas funções de regra.
    """
    def safe(col):
        val = row.get(col) if hasattr(row, "get") else row.get(col, None)
        if val is None:
            return None
        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass
        return val

    return {
        # ── identificação ──────────────────────────────────────────────────────
        "id_talhao":    safe("CHAVESIG"),
        "chave":        safe("CHAVE"),
        "unidade":      safe("DESC_EMPRESA"),
        "unid_ind":     safe("UNID_IND"),
        "safra":        safe("SAFRA"),

        # ── cultura e manejo ───────────────────────────────────────────────────
        "no_corte":     safe("NO_CORTE"),
        "categoria":    safe("CATEGORIA"),
        "estagio":      safe("ESTAGIO"),
        "man_hipot":    safe("MAN_HIPOT"),
        "data_plantio": safe("DATA_PLANTIO"),
        "tp_reforma":   safe("TP_REFORMA"),
        "reforma":      safe("Reforma"),
        "vinhaca":      safe("Vinhaca_E"),
        "torta":        safe("TORTA"),

        # ── produção ───────────────────────────────────────────────────────────
        "tch_prod":     safe("TCH_PROD"),
        "area_prod":    safe("AREA_PROD"),
        "ton_estim":    safe("TON_ESTIM"),
        "area_ha":      safe("AREA_HA"),

        # ── solo — disponível na Silver ────────────────────────────────────────
        "desc_ambiente": safe("DESC_AMBIENTE"),
        "de_tp_solo":    safe("DE_TP_SOLO"),
        "ambiente":      safe("AMBIENTE"),

        # ── solo — análise química (NÃO disponível na Silver ainda) ───────────
        "ph_solo":       safe("ph_solo"),
        "ctc":           safe("ctc"),
        "v_atual":       safe("v_atual"),
        "v_alvo":        safe("v_alvo"),
        "p_disponivel":  safe("p_disponivel"),
        "saturacao_al":  safe("saturacao_al"),
        "ca_cmolc":      safe("ca_cmolc"),
        "mg_cmolc":      safe("mg_cmolc"),

        # ── safra — integrado por extract_safra.py ────────────────────────────
        "tchan_estimado": safe("tchan_estimado"),
        "safra_estimada": safe("safra_estimada"),

        # ── campo interno para cálculo de quantidade_total_kg ─────────────────
        "_area_ha":        safe("AREA_HA"),
    }


# ── PROCESSAMENTO DE UM ÚNICO TALHÃO ─────────────────────────────────────────

def _processar_talhao(row: Any, hoje: date) -> list:
    """
    Aplica todos os módulos de regra a um único talhão.

    Retorna uma lista de registros (um por processo), prontos para compor
    o DataFrame Gold. Nunca lança exceção: erros internos de regra são
    capturados e registrados como ERRO_INTERNO.

    Esta função é a unidade de trabalho dos workers do ThreadPoolExecutor.
    É pura quanto ao estado: lê apenas `REGRAS` (dict imutável após import)
    e o `row` passado por parâmetro, sem escrita em estruturas compartilhadas.
    """
    talhao = preparar_talhao(row)
    registros = []

    for processo, func_regra in REGRAS.items():
        try:
            resultado = func_regra(talhao)
        except Exception as e:
            resultado = {
                "orientacao":      f"ERRO_INTERNO: {type(e).__name__}",
                "valor_calculado": None,
                "regra_acionada":  "erro_execucao",
            }

        dose_kg_ha = resultado.get("dose_kg_ha")
        area_ha    = talhao.get("_area_ha")
        qtd_total  = (
            round(dose_kg_ha * float(area_ha), 2)
            if dose_kg_ha is not None and area_ha is not None
            else None
        )

        registros.append({
            "id_talhao":           talhao["id_talhao"],
            "chave":               talhao["chave"],
            "unidade":             talhao["unidade"],
            "safra":               talhao["safra"],
            "processo":            processo,
            "orientacao":          resultado["orientacao"],
            "valor_calculado":     resultado["valor_calculado"],
            "regra_acionada":      resultado["regra_acionada"],
            "insumo":              resultado.get("insumo"),
            "dose_kg_ha":          dose_kg_ha,
            "quantidade_total_kg": qtd_total,
            "area_ha":             area_ha,
            "data_geracao":        hoje,
        })

    return registros


# ── APLICAÇÃO PARALELA DAS REGRAS ─────────────────────────────────────────────

def aplicar_regras(
    df: pd.DataFrame,
    hoje: date,
    n_workers: int = N_WORKERS,
) -> pd.DataFrame:
    """
    Aplica o motor de regras a cada talhão do DataFrame Silver usando
    múltiplas threads.

    Cada talhão (linha do Silver) é processado de forma independente, o
    que permite paralelismo seguro sem locks nem filas compartilhadas.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame Silver já carregado.
    hoje : date
        Data de geração a ser gravada no campo data_geracao.
    n_workers : int
        Número de threads paralelas (padrão: min(cpu_count, 8)).

    Returns
    -------
    DataFrame Gold no formato long — uma linha por (talhão × processo).
    """
    # to_dict('records') é ~10× mais rápido que iterrows() em DataFrames grandes
    rows = df.to_dict("records")

    todos_registros: list = []

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_processar_talhao, row, hoje) for row in rows]
        for future in as_completed(futures):
            todos_registros.extend(future.result())

    return pd.DataFrame(todos_registros, columns=COLUNAS_GOLD)
