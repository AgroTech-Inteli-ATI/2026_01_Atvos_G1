"""
Módulo de regras agronômicas: Erradicação de Soqueira
=======================================================
Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022), p. 15.

Regra central:
  Produtividades inferiores a 55 t/ha no ciclo → reforma do canavial recomendada.
  Referência complementar: reforma típica entre o 5° e 6° corte no setor.

  Prioridade de reforma:
  - ALTA:  TCH < 55 t/ha E NO_CORTE >= 6
  - MÉDIA: TCH < 55 t/ha (independente do corte)
  - BAIXA: TCH adequado mas NO_CORTE >= 6 (monitorar)
  - NENHUMA: TCH adequado e corte dentro do esperado

  Rotação sugerida pós-reforma (manual, p. 15):
  - Soja precoce ou amendoim: outubro–fevereiro
  - Adubos verdes (crotalária-juncea, mucuna-preta, guandu):
    setembro–outubro, incorporar em janeiro–fevereiro

Parâmetros pendentes de validação pelo PO ATVOS:
  - TCH_CRITICO = 55 t/ha (manual Agroadvance genérico;
    ATVOS pode ter limiares por unidade industrial ou variedade)
  - CORTE_LIMITE = 6 (referência do setor; ATVOS pode adotar valor diferente)
"""

from __future__ import annotations

# ── Constantes ──────────────────────────────────────────────────────────────
TCH_CRITICO = 55.0   # t/ha — limiar de reforma  [AGUARDA VALIDACAO PO]
CORTE_LIMITE = 6     # número de cortes — alerta de longevidade  [AGUARDA VALIDACAO PO]

CATEGORIAS_INAPTAS = {
    "Em Reforma", "Pousio", "A Definir", "Passagem",
    "Formação", "Cana Planta"
}


def calcular_erradicacao(row: dict) -> dict:
    """
    Avalia a necessidade de erradicação/reforma de soqueira para um talhão.

    Parâmetros
    ----------
    row : dict
        Linha do DataFrame enriquecido (Silver + Solo). Campos utilizados:
        - TCH_PROD   : float — produtividade estimada (t/ha)
        - NO_CORTE   : int   — número do corte atual
        - CATEGORIA  : str   — tipo de ciclo da cana
        - SIT_TALHAO : str   — situação atual do talhão

    Retorno
    -------
    dict com chaves:
        processo, orientacao, valor_calculado, unidade_medida,
        regra_acionada, flag_aguardando_validacao_po, prioridade_reforma

    Exemplo
    -------
    >>> calcular_erradicacao({"TCH_PROD": 48.0, "NO_CORTE": 7, "CATEGORIA": "Cana Soca", "SIT_TALHAO": "A Colher"})
    {
        "processo": "erradicacao",
        "orientacao": "REFORMA INDICADA COM PRIORIDADE ALTA...",
        "valor_calculado": 48.0,
        "unidade_medida": "t/ha",
        "regra_acionada": "erradicacao_tch_baixo_e_corte_alto",
        "flag_aguardando_validacao_po": True,
        "prioridade_reforma": "ALTA"
    }
    """
    base = {"processo": "erradicacao"}

    categoria = str(row.get("CATEGORIA", "")).strip()
    sit_talhao = str(row.get("SIT_TALHAO", "")).strip()

    # Talhões não elegíveis para avaliação
    if categoria in CATEGORIAS_INAPTAS or sit_talhao == "Fechado":
        return {**base,
                "orientacao": (f"Talhão não elegível para erradicação "
                               f"(categoria='{categoria}', situação='{sit_talhao}')."),
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "erradicacao_nao_aplicavel",
                "flag_aguardando_validacao_po": False,
                "prioridade_reforma": "N/A"}

    # Validação de dados obrigatórios
    tch = row.get("TCH_PROD")
    no_corte = row.get("NO_CORTE")

    if tch is None or (isinstance(tch, float) and tch != tch) or float(tch) <= 0:
        return {**base,
                "orientacao": "SEM_DADO: TCH_PROD ausente ou inválido.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_ausente_tch_prod",
                "flag_aguardando_validacao_po": False,
                "prioridade_reforma": "N/A"}

    if no_corte is None or (isinstance(no_corte, float) and no_corte != no_corte):
        return {**base,
                "orientacao": "SEM_DADO: NO_CORTE ausente.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_ausente_no_corte",
                "flag_aguardando_validacao_po": False,
                "prioridade_reforma": "N/A"}

    tch = float(tch)
    no_corte = int(no_corte)
    tch_baixo = tch < TCH_CRITICO
    corte_alto = no_corte >= CORTE_LIMITE

    rotacao = (
        "Rotação sugerida: soja/amendoim (out-fev) ou "
        "adubos verdes crotalária/mucuna/guandu (set-out, incorporar jan-fev)."
    )

    if tch_baixo and corte_alto:
        prioridade = "ALTA"
        regra = "erradicacao_tch_baixo_e_corte_alto"
        orientacao = (
            f"REFORMA INDICADA — PRIORIDADE ALTA. "
            f"TCH={tch:.1f} t/ha (< {TCH_CRITICO} t/ha) e {no_corte}° corte (≥ {CORTE_LIMITE}). "
            f"{rotacao}"
        )

    elif tch_baixo:
        prioridade = "MÉDIA"
        regra = "erradicacao_tch_baixo"
        orientacao = (
            f"REFORMA SUGERIDA — PRIORIDADE MÉDIA. "
            f"TCH={tch:.1f} t/ha (< {TCH_CRITICO} t/ha), {no_corte}° corte. "
            f"Avaliar custo-benefício reforma vs. manutenção. {rotacao}"
        )

    elif corte_alto:
        prioridade = "BAIXA"
        regra = "erradicacao_corte_alto_tch_ok"
        orientacao = (
            f"MONITORAR — PRIORIDADE BAIXA. "
            f"TCH={tch:.1f} t/ha ainda aceitável, mas {no_corte}° corte (≥ {CORTE_LIMITE}). "
            f"Planejar reforma nos próximos 1-2 ciclos."
        )

    else:
        prioridade = "NENHUMA"
        regra = "erradicacao_nao_necessaria"
        orientacao = (
            f"Sem indicação de reforma. "
            f"TCH={tch:.1f} t/ha (≥ {TCH_CRITICO} t/ha) e {no_corte}° corte (< {CORTE_LIMITE})."
        )

    return {**base,
            "orientacao": orientacao,
            "valor_calculado": tch,
            "unidade_medida": "t/ha",
            "regra_acionada": regra,
            "flag_aguardando_validacao_po": True,   # TCH_CRITICO e CORTE_LIMITE aguardam PO
            "prioridade_reforma": prioridade}
