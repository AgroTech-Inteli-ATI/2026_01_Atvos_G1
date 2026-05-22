"""
Módulo de regras agronômicas: Fosfatagem
==========================================
Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022), p. 10.

Regra central (dose de manutenção):
  Repor a exportação de fósforo pela colheita estimada.
  Exportação: 19 kg P / 100 t de colmo colhido (Orlando F., 1983 apud Agroadvance).

  - Cana Planta: 100% no sulco de plantio
  - Demais: cobertura 30-60 dias após a colheita

  OBS: Esta implementação cobre apenas a dose de MANUTENÇÃO.
  A dose de CORREÇÃO (quando P no solo está abaixo do limiar crítico)
  depende de validação do PO ATVOS para definição dos limiares por textura
  e será implementada após aprovação.

Parâmetros pendentes de validação pelo PO ATVOS:
  - Limiares críticos de P no solo por textura (Boletim 100/IAC ou protocolo ATVOS)
  - Fator de conversão P → P₂O₅ (padrão: × 2.29) confirmado?
"""

from __future__ import annotations

# ── Constantes ──────────────────────────────────────────────────────────────
EXPORTACAO_P_POR_100T = 19.0    # kg P / 100 t colhida  (Orlando F., 1983)
FATOR_P_PARA_P2O5 = 2.29        # conversão P elementar → P₂O₅
CATEGORIAS_CANA_PLANTA = {"Cana Planta"}
CATEGORIAS_INAPTAS = {"Em Reforma", "Pousio", "A Definir", "Passagem", "Formação"}


def calcular_fosfatagem(row: dict) -> dict:
    """
    Calcula a dose de fósforo para um talhão (dose de manutenção).

    Parâmetros
    ----------
    row : dict
        Linha do DataFrame enriquecido (Silver + Solo). Campos utilizados:
        - TCH_PROD   : float — produtividade estimada (t/ha)
        - CATEGORIA  : str   — tipo de ciclo da cana
        - p1         : float — fósforo disponível 0-25 cm (mg/dm³) [referência futura]

    Retorno
    -------
    dict com chaves:
        processo, orientacao, valor_calculado, unidade_medida,
        regra_acionada, flag_aguardando_validacao_po

    Exemplo
    -------
    >>> calcular_fosfatagem({"TCH_PROD": 80.0, "CATEGORIA": "Cana Planta", "p1": 12.0})
    {
        "processo": "fosfatagem",
        "orientacao": "Aplicar 34.76 kg P₂O₅/ha no sulco de plantio...",
        "valor_calculado": 34.76,
        "unidade_medida": "kg P₂O₅/ha",
        "regra_acionada": "fosfatagem_manutencao_cana_planta",
        "flag_aguardando_validacao_po": True
    }
    """
    base = {"processo": "fosfatagem"}

    categoria = str(row.get("CATEGORIA", "")).strip()

    if categoria in CATEGORIAS_INAPTAS:
        return {**base,
                "orientacao": f"Talhão com categoria '{categoria}': fosfatagem não aplicável.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "fosfatagem_nao_aplicavel",
                "flag_aguardando_validacao_po": False}

    # Validação de TCH
    tch = row.get("TCH_PROD")
    if tch is None or (isinstance(tch, float) and tch != tch) or float(tch) <= 0:
        return {**base,
                "orientacao": "SEM_DADO: TCH_PROD ausente ou inválido.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_ausente_tch_prod",
                "flag_aguardando_validacao_po": False}

    # Calcular dose de manutenção
    dose_p = EXPORTACAO_P_POR_100T * (float(tch) / 100.0)       # kg P/ha
    dose_p2o5 = dose_p * FATOR_P_PARA_P2O5                       # kg P₂O₅/ha

    # Momento de aplicação
    if categoria in CATEGORIAS_CANA_PLANTA:
        momento = "100% no sulco de plantio"
        regra = "fosfatagem_manutencao_cana_planta"
    else:
        momento = "cobertura 30-60 dias após a colheita"
        regra = "fosfatagem_manutencao_soca"

    orientacao = (
        f"Aplicar {dose_p2o5:.2f} kg P₂O₅/ha ({momento}). "
        f"Base: exportação de {EXPORTACAO_P_POR_100T} kg P / 100 t × TCH={tch:.0f} t/ha. "
        f"[NOTA: dose de manutenção apenas. "
        f"Dose de correção por deficiência de P no solo aguarda validação PO.]"
    )

    return {**base,
            "orientacao": orientacao,
            "valor_calculado": round(dose_p2o5, 2),
            "unidade_medida": "kg P₂O₅/ha",
            "regra_acionada": regra,
            "flag_aguardando_validacao_po": True}
