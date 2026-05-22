"""
Módulo de regras agronômicas: Gessagem
========================================
Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022), p. 6.

Regra central (ambos os critérios devem ser verdadeiros):
  1. Ca no subsolo (25-50 cm) < 4 mmolc dm-³
  2. Saturação por Al (m%) no subsolo > 40%
     Fórmula: m% = Al / (SB + Al) × 100
     Fonte da fórmula: padrão da química do solo brasileira
     (Embrapa / IAC — não consta explicitamente no manual Agroadvance)

  Dose: argila (g/kg) × 5 = kg/ha de gesso agrícola
  Timing: 60-90 dias antes do plantio, na passagem da grade niveladora.

Parâmetros pendentes de validação pelo PO ATVOS:
  - Dicionário de conversão DE_TP_SOLO → argila (g/kg)
  - Critérios de disparo (Ca < 4 e m% > 40) estão no manual Agroadvance
"""

from __future__ import annotations

# ── Constantes ──────────────────────────────────────────────────────────────
CA_CRITICO_SUBSOLO = 4.0    # mmolc dm-³  (manual Agroadvance, p.6)
M_PERCENT_CRITICO = 40.0    # % saturação por Al  (manual Agroadvance, p.6)
FATOR_DOSE = 5.0            # kg gesso / (g argila / kg solo)


def _argila_por_textura(de_tp_solo: str) -> tuple[float, bool]:
    """
    Converte a descrição textual do solo (DE_TP_SOLO) em teor estimado de argila (g/kg).

    Lógica: matching por palavras-chave em ordem de especificidade.
    Flag de incerteza = True quando a descrição não se encaixa em nenhum padrão.

    AGUARDA VALIDACAO PO: valores de argila por classe textural.

    Retorno
    -------
    (argila_g_kg: float, flag_incerteza: bool)
    """
    s = str(de_tp_solo).lower()

    if "muito argilosa" in s:
        return 500.0, False
    elif "media argilosa" in s or "média argilosa" in s or "media-argilosa" in s:
        return 250.0, False
    elif "argilosa" in s:
        return 350.0, False
    elif "media arenosa" in s or "média arenosa" in s or "media-arenosa" in s:
        return 150.0, False
    elif "muito arenosa" in s:
        return 80.0, False
    elif "arenosa" in s:
        return 100.0, False
    else:
        return 200.0, True   # fallback com flag de incerteza


def _calcular_m_percent(al2: float, sb2: float) -> float | None:
    """
    Calcula a saturação por alumínio (m%) no subsolo.

    Fórmula: m% = Al / (SB + Al) × 100
    Fonte: padrão da química do solo brasileira (Embrapa/IAC).

    Retorna None se denominador for zero.
    """
    denominador = float(sb2) + float(al2)
    if denominador == 0:
        return None
    return (float(al2) / denominador) * 100.0


def calcular_gessagem(row: dict) -> dict:
    """
    Calcula a necessidade de gessagem para um talhão.

    Parâmetros
    ----------
    row : dict
        Linha do DataFrame enriquecido (Silver + Solo). Campos utilizados:
        - ca2        : float — cálcio no subsolo 25-50 cm (mmolc dm-³)
        - al2        : float — alumínio trocável no subsolo 25-50 cm (mmolc dm-³)
        - sb2        : float — soma de bases no subsolo 25-50 cm (mmolc dm-³)
        - DE_TP_SOLO : str   — descrição textual do tipo de solo

    Retorno
    -------
    dict com chaves:
        processo, orientacao, valor_calculado, unidade_medida,
        regra_acionada, flag_aguardando_validacao_po
    """
    base = {"processo": "gessagem"}

    # Validação de dados obrigatórios
    ca2 = row.get("ca2")
    al2 = row.get("al2")
    sb2 = row.get("sb2")

    if any(v is None or (isinstance(v, float) and v != v) for v in [ca2, al2, sb2]):
        return {**base,
                "orientacao": "SEM_DADO: análise de subsolo ausente (ca2, al2 ou sb2 nulos).",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_ausente_analise_subsolo",
                "flag_aguardando_validacao_po": False}

    # Calcular m%
    m_percent = _calcular_m_percent(al2, sb2)
    if m_percent is None:
        return {**base,
                "orientacao": "SEM_DADO: SB + Al = 0 no subsolo (dado suspeito).",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "dado_suspeito_sb_al_zero",
                "flag_aguardando_validacao_po": False}

    # Verificar critérios de disparo (ambos devem ser verdadeiros)
    criterio_ca = float(ca2) < CA_CRITICO_SUBSOLO
    criterio_al = m_percent > M_PERCENT_CRITICO

    if not (criterio_ca and criterio_al):
        motivo = []
        if not criterio_ca:
            motivo.append(f"Ca subsolo={ca2:.1f} ≥ {CA_CRITICO_SUBSOLO} mmolc dm-³")
        if not criterio_al:
            motivo.append(f"m%={m_percent:.1f}% ≤ {M_PERCENT_CRITICO}%")

        return {**base,
                "orientacao": (f"Gessagem não indicada. {'; '.join(motivo)}. "
                               f"Ambos os critérios (Ca < {CA_CRITICO_SUBSOLO} E m% > {M_PERCENT_CRITICO}%) "
                               "são necessários."),
                "valor_calculado": 0.0,
                "unidade_medida": "kg/ha",
                "regra_acionada": "gessagem_nao_necessaria",
                "flag_aguardando_validacao_po": False}

    # Calcular dose com base na textura
    de_tp_solo = row.get("DE_TP_SOLO", "")
    argila_g_kg, flag_incerteza = _argila_por_textura(de_tp_solo)
    dose_gesso = argila_g_kg * FATOR_DOSE  # kg/ha

    aviso_incerteza = (
        " [ATENÇÃO: textura não identificada — argila estimada como 200 g/kg (mediana). "
        "Aguarda validação PO.]" if flag_incerteza else ""
    )

    orientacao = (
        f"Aplicar {dose_gesso:.0f} kg/ha de gesso agrícola na grade niveladora "
        f"(60-90 dias antes do plantio). "
        f"Ca subsolo={ca2:.1f} mmolc dm-³, m%={m_percent:.1f}%, "
        f"argila estimada={argila_g_kg:.0f} g/kg.{aviso_incerteza}"
    )

    return {**base,
            "orientacao": orientacao,
            "valor_calculado": round(dose_gesso, 0),
            "unidade_medida": "kg/ha",
            "regra_acionada": "gessagem_necessaria",
            "flag_aguardando_validacao_po": True}   # dicionário argila aguarda PO
