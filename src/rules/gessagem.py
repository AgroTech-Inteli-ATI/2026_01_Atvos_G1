"""
src/rules/gessagem.py
Regra de gessagem (aplicação de gesso agrícola) para cana-de-açúcar.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PSEUDOCÓDIGO (validar com PO Atvos antes de alterar limiares)

  ENTRADAS NECESSÁRIAS:
    saturacao_al : Saturação por Al³⁺ (%) — análise de solo, não na Silver ainda
    ctc          : CTC a pH 7 (mmol_c/dm³) — análise de solo, não na Silver ainda
    desc_ambiente: textura do solo (disponível na Silver como DESC_AMBIENTE)
    categoria    : CATEGORIA Silver

  SE desc_ambiente é nulo E saturacao_al é nulo → SEM_DADO

  CRITÉRIO PRINCIPAL (saturação por Al — quando disponível):
    SE saturacao_al > 20% E textura != "arenoso":
      dose = _calcular_dose_gesso(ctc, textura)
      → "Gessagem recomendada: X t/ha ..."
    SE saturacao_al <= 20%:
      → "Gessagem não indicada (Al³⁺ dentro do limite)"

  CRITÉRIO ALTERNATIVO (apenas textura — quando análise química indisponível):
    SE textura == "muito_argiloso":
      → "Avaliar gessagem: solo muito argiloso, solicitar análise de Al³⁺"
    SE textura == "argiloso":
      → "Avaliar gessagem: solo argiloso, solicitar análise de Al³⁺"
    SE textura == "arenoso":
      → "Gessagem raramente indicada em solos arenosos (baixa CTC)"
    SE textura == "medio":
      → "Avaliar gessagem conforme resultado de Al³⁺"

DOSE DE GESSO (Embrapa — confirmar com PO Atvos):
  Solo arenoso       : 0.5 × CTC / 10  (t/ha)
  Solo médio         : 1.0 × CTC / 10
  Solo argiloso      : 1.5 × CTC / 10
  Solo muito argiloso: 2.0 × CTC / 10
  Limite máximo      : 4.0 t/ha
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ._base import (
    sem_dado, nao_se_aplica, resultado,
    numerico, texto, classificar_textura,
)

# ── PARÂMETROS ────────────────────────────────────────────────────────────────

SAT_AL_CRITICA  = 20.0   # % de saturação por Al³⁺ que dispara gessagem
DOSE_MAX_T_HA   = 4.0    # limite de segurança por aplicação (t/ha)

# Multiplicador de dose por classe de textura (fator × CTC / 10)
_FATOR_TEXTURA = {
    "arenoso":       0.5,
    "medio":         1.0,
    "argiloso":      1.5,
    "muito_argiloso": 2.0,
}


# ── CÁLCULO DE DOSE ───────────────────────────────────────────────────────────

def _calcular_dose_gesso(ctc: float, textura: str) -> float:
    """
    Dose de gesso em t/ha baseada em CTC e textura do solo (Embrapa).

    Parameters
    ----------
    ctc     : CTC a pH 7 em mmol_c/dm³
    textura : "arenoso" | "medio" | "argiloso" | "muito_argiloso"
    """
    fator = _FATOR_TEXTURA.get(textura, 1.0)
    dose = fator * ctc / 10
    return min(dose, DOSE_MAX_T_HA)


# ── REGRA PRINCIPAL ───────────────────────────────────────────────────────────

def calcular_necessidade_gessagem(talhao: dict) -> dict:
    """
    Avalia a necessidade de gessagem para um talhão de cana-de-açúcar.

    Usa saturação por Al³⁺ quando disponível; quando ausente, orienta com base
    na textura do solo (DESC_AMBIENTE da Silver) e solicita análise química.

    Parameters
    ----------
    talhao : dict
        Campos de análise de solo (não disponíveis na Silver ainda):
          saturacao_al (float) saturação por Al³⁺, %, ex: 25.0
          ctc          (float) CTC a pH 7, mmol_c/dm³, ex: 70.0
        Campo disponível na Silver:
          desc_ambiente (str) textura do solo, ex: "Argiloso"

    Returns
    -------
    dict com orientacao, valor_calculado (t/ha ou None), regra_acionada

    Examples
    --------
    >>> calcular_necessidade_gessagem({
    ...     'saturacao_al': 28.0, 'ctc': 70.0,
    ...     'desc_ambiente': 'Argiloso'
    ... })
    {'orientacao': 'Gessagem recomendada: aplicar 1.0 t/ha (Al³⁺ 28.0% > 20%, solo argiloso)',
     'valor_calculado': 1.0,
     'regra_acionada': 'al_alto_gessagem_indicada'}

    >>> calcular_necessidade_gessagem({'desc_ambiente': 'Argiloso'})
    {'orientacao': 'Avaliar gessagem: solo argiloso — solicitar análise de Al³⁺',
     'valor_calculado': None,
     'regra_acionada': 'textura_argiloso_sem_analise_al'}
    """
    sat_al  = talhao.get("saturacao_al")
    ctc     = talhao.get("ctc")
    desc_amb = talhao.get("desc_ambiente")

    textura = classificar_textura(desc_amb)

    # ── caminho com análise química completa ──────────────────────────────────
    if numerico(sat_al):
        sat_al = float(sat_al)

        if sat_al > SAT_AL_CRITICA:
            if not numerico(ctc):
                # Sabe que precisa gessagem, mas não consegue calcular dose
                return resultado(
                    f"Gessagem indicada (Al³⁺ {sat_al:.1f}% > {SAT_AL_CRITICA}%) "
                    f"— CTC ausente, dose a calcular",
                    None,
                    "al_alto_ctc_ausente",
                )
            dose = _calcular_dose_gesso(float(ctc), textura or "medio")
            txt = textura.replace("_", " ") if textura else "textura indefinida"
            return resultado(
                f"Gessagem recomendada: aplicar {dose:.1f} t/ha "
                f"(Al³⁺ {sat_al:.1f}% > {SAT_AL_CRITICA}%, solo {txt})",
                dose,
                "al_alto_gessagem_indicada",
            )

        return resultado(
            f"Gessagem não indicada (Al³⁺ {sat_al:.1f}% ≤ {SAT_AL_CRITICA}%)",
            0.0,
            "al_dentro_limite",
        )

    # ── caminho apenas com textura (sem análise química) ─────────────────────
    if textura is None:
        return sem_dado("saturacao_al_e_desc_ambiente")

    _mensagens = {
        "arenoso":       "Gessagem raramente indicada em solos arenosos (baixa CTC) — confirmar com análise",
        "medio":         "Avaliar gessagem: solo de textura média — solicitar análise de Al³⁺",
        "argiloso":      "Avaliar gessagem: solo argiloso — solicitar análise de Al³⁺",
        "muito_argiloso": "Avaliar gessagem: solo muito argiloso — solicitar análise de Al³⁺ (alta prioridade)",
    }
    return resultado(
        _mensagens[textura],
        None,
        f"textura_{textura}_sem_analise_al",
    )


if __name__ == "__main__":
    casos = [
        {"saturacao_al": 28.0, "ctc": 70.0, "desc_ambiente": "Argiloso"},
        {"saturacao_al": 12.0, "ctc": 70.0, "desc_ambiente": "Argiloso"},
        {"desc_ambiente": "Muito Argiloso"},
        {"desc_ambiente": "Arenoso"},
        {},
    ]
    for c in casos:
        r = calcular_necessidade_gessagem(c)
        print(f"{r['regra_acionada']:<45} | {r['orientacao']}")
