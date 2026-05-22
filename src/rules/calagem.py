"""
Módulo de regras agronômicas: Calagem
======================================
Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022), p. 6 e 10.

Regra central:
  Aplicar calcário para elevar a saturação por bases (V%) a 60%.
  Fórmula: NC (t/ha) = (V_alvo - V_atual) × CTC / 100
  Se Mg < 5 mmolc dm-³: usar calcário dolomítico, mínimo 1 t/ha.

  - Cana Planta: aplicação incorporada, 150 dias antes do plantio
    (3/4 antes do arado + 1/4 antes da grade niveladora)
  - Demais categorias: aplicação superficial, dose reduzida a 50%
    (sem incorporação: menor eficiência)

Parâmetros pendentes de validação pelo PO ATVOS:
  - V_ALVO = 60% (padrão do setor; ATVOS pode adotar valor diferente)
"""

from __future__ import annotations

# ── Constantes ──────────────────────────────────────────────────────────────
V_ALVO = 60.0           # % saturação por bases alvo  [AGUARDA VALIDACAO PO]
MG_MINIMO = 5.0         # mmolc dm-³ — limiar para obrigatoriedade do dolomítico
DOSE_MINIMA_DOLOMIT = 1.0  # t/ha — mínimo quando Mg abaixo do limiar
FATOR_SUPERFICIAL = 0.5    # eficiência relativa sem incorporação (cana soca)
ANTECEDENCIA_PLANTA = 150  # dias antes do plantio (cana planta)
ANTECEDENCIA_SOCA = 60    # dias antes da operação (cana soca)

CATEGORIAS_CANA_PLANTA = {"Cana Planta"}
CATEGORIAS_INAPTAS = {"Em Reforma", "Pousio", "A Definir", "Passagem", "Formação"}


def calcular_calagem(row: dict) -> dict:
    """
    Calcula a necessidade de calagem para um talhão.

    Parâmetros
    ----------
    row : dict
        Linha do DataFrame enriquecido (Silver + Solo). Campos utilizados:
        - V1     : float — saturação por bases 0-25 cm (%)
        - CTC1   : float — capacidade de troca catiônica 0-25 cm (mmolc dm-³)
        - mg1    : float — magnésio trocável 0-25 cm (mmolc dm-³)
        - CATEGORIA : str — tipo de ciclo da cana

    Retorno
    -------
    dict com chaves:
        processo, orientacao, valor_calculado, unidade_medida,
        regra_acionada, flag_aguardando_validacao_po
    """
    base = {"processo": "calagem"}

    categoria = str(row.get("CATEGORIA", "")).strip()

    # Talhões em situação não elegível
    if categoria in CATEGORIAS_INAPTAS:
        return {**base,
                "orientacao": f"Talhão com categoria '{categoria}': calagem não aplicável.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "calagem_nao_aplicavel",
                "flag_aguardando_validacao_po": False}

    # Validação de dados obrigatórios
    v1 = row.get("V1")
    ctc1 = row.get("CTC1")
    mg1 = row.get("mg1")

    if any(v is None or (isinstance(v, float) and v != v) for v in [v1, ctc1, mg1]):
        return {**base,
                "orientacao": "SEM_DADO: análise de solo ausente (V1, CTC1 ou mg1 nulos).",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_ausente_analise_solo",
                "flag_aguardando_validacao_po": False}

    if v1 <= 0 or ctc1 <= 0:
        return {**base,
                "orientacao": "SEM_DADO: valores de V% ou CTC suspeitos (≤ 0).",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_suspeito_v_ctc",
                "flag_aguardando_validacao_po": False}

    # Calcular necessidade de calagem (NC)
    nc = (V_ALVO - float(v1)) * float(ctc1) / 100.0

    if nc <= 0:
        return {**base,
                "orientacao": (f"Solo com V%={v1:.1f}% já acima do alvo ({V_ALVO}%). "
                               "Calagem não necessária."),
                "valor_calculado": 0.0,
                "unidade_medida": "t/ha",
                "regra_acionada": "v_percent_adequado",
                "flag_aguardando_validacao_po": True}   # V_ALVO aguarda validação

    # Tipo de calcário
    if float(mg1) < MG_MINIMO:
        tipo_calcario = "dolomítico"
        nc = max(nc, DOSE_MINIMA_DOLOMIT)
    else:
        tipo_calcario = "calcítico ou dolomítico"

    # Modo de aplicação por categoria
    if categoria in CATEGORIAS_CANA_PLANTA:
        tipo_aplicacao = "incorporada"
        parcelamento = "3/4 antes do arado + 1/4 antes da grade niveladora"
        antecedencia = ANTECEDENCIA_PLANTA
        regra = "calagem_incorporada"
    else:
        tipo_aplicacao = "superficial"
        nc = nc * FATOR_SUPERFICIAL
        parcelamento = "dose única em superfície"
        antecedencia = ANTECEDENCIA_SOCA
        regra = "calagem_superficial"

    orientacao = (
        f"Aplicar {nc:.2f} t/ha de calcário {tipo_calcario} ({tipo_aplicacao}). "
        f"{parcelamento}. "
        f"Realizar {antecedencia} dias antes do plantio/operação. "
        f"[V% atual={v1:.1f}%, alvo={V_ALVO}%, CTC={ctc1:.0f} mmolc dm-³]"
    )

    return {**base,
            "orientacao": orientacao,
            "valor_calculado": round(nc, 2),
            "unidade_medida": "t/ha",
            "regra_acionada": regra,
            "flag_aguardando_validacao_po": True}   # V_ALVO aguarda validação PO
