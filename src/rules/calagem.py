"""
src/rules/calagem.py
Regra de calagem (correção de pH) para cana-de-açúcar.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PSEUDOCÓDIGO (validar com PO Atvos antes de alterar limiares)

  ENTRADAS NECESSÁRIAS (análise de solo — ainda não na Silver):
    ph_solo   : pH em água
    ctc       : Capacidade de Troca Catiônica (mmol_c/dm³)
    v_atual   : Saturação de bases atual (%)
    v_alvo    : Saturação de bases alvo (%)  ← definido pelo agrônomo Atvos
    categoria : CATEGORIA da Silver ("Formação", "Cana Soca", ...)

  SE qualquer entrada for nula → SEM_DADO

  SE ph_solo >= 6.0:
    → sem necessidade de calagem
    → dose = 0, regra = "ph_adequado"

  SE ph_solo >= 5.5 E ph_solo < 6.0:
    → dose baixa, preventiva
    → dose = _calcular_dose(ctc, v_atual, v_alvo) * 0.5
    → tipo = "superficial"
    → regra = "ph_levemente_acido"

  SE ph_solo < 5.5 E ciclo == "cana_planta":
    → dose plena, incorporada (solo mobilizado no plantio)
    → dose = _calcular_dose(ctc, v_atual, v_alvo)
    → tipo = "incorporada"
    → regra = "ph_baixo_cana_planta"

  SE ph_solo < 5.5 E ciclo == "cana_soca":
    → dose reduzida, superficial (solo não mobilizado)
    → dose = _calcular_dose(ctc, v_atual, v_alvo) * 0.5
    → tipo = "superficial"
    → regra = "ph_baixo_cana_soca"

FÓRMULA DE DOSE (método da saturação de bases — Embrapa/IAC):
  NC (t/ha) = [(V_alvo - V_atual) × CTC] / (PRNT × 10)
  CTC em mmolc/dm³ (ex: 80). Se a fonte usar cmolc/dm³, divisor muda para PRNT.
  PRNT = 80 (calcário dolomítico padrão Atvos — confirmar com PO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ._base import sem_dado, nao_se_aplica, resultado, dado_suspeito, numerico, texto, ciclo_do_talhao

# ── PARÂMETROS (ajustar após validação com PO Atvos) ─────────────────────────

PH_ADEQUADO    = 6.0    # pH acima deste valor: sem necessidade de calagem
PH_CRITICO     = 5.5    # pH abaixo deste valor: calagem necessária
PRNT_PADRAO    = 80.0   # PRNT do calcário padrão Atvos (%)
V_ALVO_PADRAO  = 60.0   # Saturação de bases alvo (%) — confirmar com PO
DOSE_MAX_T_HA  = 6.0    # Limite máximo por aplicação (t/ha) — segurança


# ── CÁLCULO DE DOSE ───────────────────────────────────────────────────────────

def _calcular_dose(ctc: float, v_atual: float, v_alvo: float) -> float:
    """
    Necessidade de calagem pelo método da saturação de bases (Embrapa).

    NC (t/ha) = [(V_alvo - V_atual) × CTC] / (PRNT × 10)

    Parameters
    ----------
    ctc    : CTC a pH 7 em mmolc/dm³ (ex: 80.0)
    v_atual: saturação de bases atual em % (ex: 35.0)
    v_alvo : saturação de bases alvo em % (ex: 60.0)

    Returns
    -------
    Dose em t/ha, limitada a DOSE_MAX_T_HA e nunca negativa.
    """
    delta_v = max(v_alvo - v_atual, 0)
    dose = (delta_v * ctc) / (PRNT_PADRAO * 10)
    return min(dose, DOSE_MAX_T_HA)


# ── REGRA PRINCIPAL ───────────────────────────────────────────────────────────

def calcular_necessidade_calagem(talhao: dict) -> dict:
    """
    Avalia a necessidade de calagem para um talhão de cana-de-açúcar.

    Parameters
    ----------
    talhao : dict
        Campos obrigatórios (análise de solo — ainda não disponíveis na Silver):
          ph_solo  (float) pH em água, ex: 5.2
          ctc      (float) CTC a pH 7, mmol_c/dm³, ex: 80.0
          v_atual  (float) saturação de bases atual, %, ex: 35.0
          v_alvo   (float) saturação de bases alvo, %, ex: 60.0
        Campo da Silver:
          categoria (str) "Formação" | "Cana Soca" | etc.

    Returns
    -------
    dict com:
      orientacao       : texto descritivo da recomendação
      valor_calculado  : dose de calcário em t/ha (ou None)
      regra_acionada   : código da condição disparada

    Examples
    --------
    >>> calcular_necessidade_calagem({
    ...     'ph_solo': 4.8, 'ctc': 80.0,
    ...     'v_atual': 35.0, 'v_alvo': 60.0,
    ...     'categoria': 'Formação'
    ... })
    {'orientacao': 'Calagem incorporada: aplicar 2.0 t/ha de calcário (pH 4.8, cana-planta)',
     'valor_calculado': 2.0,
     'regra_acionada': 'ph_baixo_cana_planta'}
    """
    ph     = talhao.get("ph_solo")
    ctc    = talhao.get("ctc")
    v_at   = talhao.get("v_atual")
    v_alvo = talhao.get("v_alvo") or V_ALVO_PADRAO
    cat    = talhao.get("categoria")

    # ── validação de entradas ──────────────────────────────────────────────────
    if not numerico(ph):
        return sem_dado("ph_solo")
    if not numerico(ctc):
        return sem_dado("ctc")
    if not numerico(v_at):
        return sem_dado("v_atual")

    ph   = float(ph)
    ctc  = float(ctc)
    v_at = float(v_at)

    # ── detecção de outliers ───────────────────────────────────────────────────
    if ph < 0 or ph > 14:
        return dado_suspeito("ph_solo", ph, "pH deve estar entre 0 e 14")
    if ctc < 0:
        return dado_suspeito("ctc", ctc, "CTC não pode ser negativa")
    if v_at < 0 or v_at > 100:
        return dado_suspeito("v_atual", v_at, "saturação de bases deve estar entre 0% e 100%")

    ciclo = ciclo_do_talhao(cat)  # "cana_planta" | "cana_soca" | None

    # ── árvore de decisão ─────────────────────────────────────────────────────
    if ph >= PH_ADEQUADO:
        return resultado(
            f"Sem necessidade de calagem (pH {ph:.1f} ≥ {PH_ADEQUADO})",
            0.0,
            "ph_adequado",
        )

    dose = _calcular_dose(ctc, v_at, float(v_alvo))

    if ph >= PH_CRITICO:
        dose_prev = round(dose * 0.5, 2)
        return resultado(
            f"Calagem preventiva superficial: aplicar {dose_prev:.1f} t/ha "
            f"(pH {ph:.1f}, levemente ácido — dose reduzida, preventiva)",
            dose_prev,
            "ph_levemente_acido",
        )

    # pH < 5.5 — calagem necessária, modo varia com o ciclo
    if ciclo == "cana_planta":
        return resultado(
            f"Calagem incorporada: aplicar {dose:.1f} t/ha de calcário "
            f"(pH {ph:.1f}, cana-planta)",
            dose,
            "ph_baixo_cana_planta",
        )

    if ciclo == "cana_soca":
        dose_soca = round(dose * 0.5, 2)
        return resultado(
            f"Calagem superficial: aplicar {dose_soca:.1f} t/ha de calcário "
            f"(pH {ph:.1f}, cana-soca — dose reduzida)",
            dose_soca,
            "ph_baixo_cana_soca",
        )

    # Ciclo desconhecido mas pH crítico — ainda recomenda, ciclo indefinido
    return resultado(
        f"Calagem necessária: {dose:.1f} t/ha (pH {ph:.1f}) — confirmar ciclo para definir modo",
        dose,
        "ph_baixo_ciclo_indefinido",
    )


# ── EXEMPLO DE USO (rodar: python -m src.rules.calagem) ──────────────────────

if __name__ == "__main__":
    casos = [
        {"ph_solo": 4.8, "ctc": 80.0, "v_atual": 35.0, "v_alvo": 60.0, "categoria": "Formação"},
        {"ph_solo": 5.3, "ctc": 60.0, "v_atual": 42.0, "v_alvo": 60.0, "categoria": "Cana Soca"},
        {"ph_solo": 6.2, "ctc": 70.0, "v_atual": 65.0, "v_alvo": 60.0, "categoria": "Cana Soca"},
        {"ph_solo": None, "ctc": 80.0, "v_atual": 35.0, "v_alvo": 60.0, "categoria": "Formação"},
    ]
    for c in casos:
        r = calcular_necessidade_calagem(c)
        print(f"pH={c.get('ph_solo')} | {r['regra_acionada']} | {r['orientacao']}")
