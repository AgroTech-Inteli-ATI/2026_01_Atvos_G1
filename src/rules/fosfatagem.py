"""
src/rules/fosfatagem.py
Regra de fosfatagem (adubação fosfatada corretiva) para cana-de-açúcar.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PSEUDOCÓDIGO (validar com PO Atvos antes de alterar limiares)

  ENTRADAS NECESSÁRIAS (análise de solo — ainda não na Silver):
    p_disponivel : P disponível pelo método Mehlich-1 (mg/dm³)
    categoria    : CATEGORIA Silver — define se aplica somente em cana-planta
    area_prod    : Área do talhão (ha) — usada para calcular quantidade total

  SE p_disponivel é nulo → SEM_DADO

  TABELA DE INTERPRETAÇÃO (Embrapa / IAC — confirmar valores com PO):
    p_disponivel <  8 mg/dm³ → "Muito Baixo"  → dose_alta  = 120 kg P₂O₅/ha
    p_disponivel <  15       → "Baixo"        → dose_media =  80 kg P₂O₅/ha
    p_disponivel <  30       → "Médio"        → dose_baixa =  40 kg P₂O₅/ha
    p_disponivel >= 30       → "Alto"         → sem_necessidade = 0

  RESTRIÇÃO DE CICLO:
    Fosfatagem corretiva aplica-se preferencialmente em cana-planta.
    Em cana-soca: dose reduzida a 50% ou manutenção apenas.
    (confirmar com PO Atvos se há exceções)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ._base import sem_dado, resultado, numerico, texto, ciclo_do_talhao

# ── PARÂMETROS (Embrapa/IAC — confirmar com PO Atvos) ────────────────────────

# Limiares de P disponível Mehlich-1 em mg/dm³
P_MUITO_BAIXO = 8.0
P_BAIXO       = 15.0
P_MEDIO       = 30.0

# Doses base de P₂O₅ em kg/ha (cana-planta)
DOSE_MUITO_BAIXO_KG = 120.0
DOSE_BAIXO_KG       = 80.0
DOSE_MEDIO_KG       = 40.0

# Fator de redução para cana-soca (adubação de manutenção)
FATOR_CANA_SOCA = 0.5


# ── INTERPRETAÇÃO ─────────────────────────────────────────────────────────────

def _interpretar_p(p: float) -> tuple:
    """
    Retorna (classe, dose_base_kg_ha) conforme teor de P disponível.

    Returns
    -------
    Tuple (str, float): classe textual e dose base em kg P₂O₅/ha
    """
    if p < P_MUITO_BAIXO:
        return "muito_baixo", DOSE_MUITO_BAIXO_KG
    if p < P_BAIXO:
        return "baixo", DOSE_BAIXO_KG
    if p < P_MEDIO:
        return "medio", DOSE_MEDIO_KG
    return "alto", 0.0


# ── REGRA PRINCIPAL ───────────────────────────────────────────────────────────

def calcular_necessidade_fosfatagem(talhao: dict) -> dict:
    """
    Avalia a necessidade de adubação fosfatada corretiva para um talhão.

    Parameters
    ----------
    talhao : dict
        Campos de análise de solo (não disponíveis na Silver ainda):
          p_disponivel (float) P Mehlich-1, mg/dm³, ex: 10.5
        Campos disponíveis na Silver:
          categoria  (str)   "Formação" | "Cana Soca" | etc.
          area_prod  (float) área de produção, ha

    Returns
    -------
    dict com:
      orientacao       : recomendação textual com dose em kg/ha
      valor_calculado  : dose de P₂O₅ em kg/ha
      regra_acionada   : código da condição disparada

    Examples
    --------
    >>> calcular_necessidade_fosfatagem({
    ...     'p_disponivel': 6.0, 'categoria': 'Formação', 'area_prod': 50.0
    ... })
    {'orientacao': 'Fosfatagem corretiva (P muito baixo): 120 kg P₂O₅/ha ...',
     'valor_calculado': 120.0,
     'regra_acionada': 'p_muito_baixo_cana_planta'}
    """
    p_disp = talhao.get("p_disponivel")
    cat    = talhao.get("categoria")

    if not numerico(p_disp):
        return sem_dado("p_disponivel")

    p     = float(p_disp)
    ciclo = ciclo_do_talhao(cat)  # "cana_planta" | "cana_soca" | None

    classe, dose_base = _interpretar_p(p)

    if dose_base == 0.0:
        return resultado(
            f"Fosfatagem não necessária (P {p:.1f} mg/dm³ — nível alto)",
            0.0,
            f"p_{classe}_sem_necessidade",
        )

    if ciclo == "cana_soca":
        dose = round(dose_base * FATOR_CANA_SOCA, 1)
        return resultado(
            f"Fosfatagem de manutenção (cana-soca): {dose:.0f} kg P₂O₅/ha "
            f"(P {p:.1f} mg/dm³ — nível {classe.replace('_', ' ')})",
            dose,
            f"p_{classe}_cana_soca",
        )

    if ciclo == "cana_planta":
        return resultado(
            f"Fosfatagem corretiva (cana-planta): {dose_base:.0f} kg P₂O₅/ha "
            f"(P {p:.1f} mg/dm³ — nível {classe.replace('_', ' ')})",
            dose_base,
            f"p_{classe}_cana_planta",
        )

    # Ciclo indefinido — ainda recomenda com ressalva
    return resultado(
        f"Fosfatagem indicada: {dose_base:.0f} kg P₂O₅/ha "
        f"(P {p:.1f} mg/dm³ — nível {classe.replace('_', ' ')}) — confirmar ciclo",
        dose_base,
        f"p_{classe}_ciclo_indefinido",
    )


if __name__ == "__main__":
    casos = [
        {"p_disponivel": 6.0,  "categoria": "Formação",  "area_prod": 50.0},
        {"p_disponivel": 12.0, "categoria": "Cana Soca", "area_prod": 30.0},
        {"p_disponivel": 20.0, "categoria": "Formação",  "area_prod": 25.0},
        {"p_disponivel": 35.0, "categoria": "Cana Soca", "area_prod": 40.0},
        {"p_disponivel": None, "categoria": "Formação",  "area_prod": 20.0},
    ]
    for c in casos:
        r = calcular_necessidade_fosfatagem(c)
        print(f"P={c.get('p_disponivel'):<6} | {r['regra_acionada']:<35} | {r['orientacao']}")
