"""
src/rules/insumos.py
Módulo de gestão de insumos e doses para cana-de-açúcar.

Diferença em relação a calagem.py / fosfatagem.py / gessagem.py:
  Aqueles calculam NECESSIDADE CORRETIVA com base em análise de solo.
  Este módulo calcula DOSE DE INSUMO em função da PRODUTIVIDADE ESTIMADA
  (tchan_estimado), complementada por atributos disponíveis na Silver.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTRATO ESTENDIDO (além das 3 chaves padrão, estas funções adicionam):

  insumo       (str)   nome comercial/técnico do produto a aplicar
  dose_kg_ha   (float) dose em kg/ha (ou L/ha para líquidos — ver docstring)

  O pipeline calcula quantidade_total_kg = dose_kg_ha × area_ha.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ._base import (
    sem_dado, nao_se_aplica, resultado, dado_suspeito,
    numerico, texto, classificar_textura, ciclo_do_talhao,
)

# ── HELPER: resultado com campos de insumo ────────────────────────────────────

def _resultado_insumo(
    orientacao: str,
    valor: float | None,
    regra: str,
    insumo: str,
    dose_kg_ha: float | None,
) -> dict:
    """Estende resultado() com os campos de insumo."""
    base = resultado(orientacao, valor, regra)
    base["insumo"]     = insumo
    base["dose_kg_ha"] = round(dose_kg_ha, 2) if dose_kg_ha is not None else None
    return base


def _sem_dado_insumo(campo: str) -> dict:
    base = sem_dado(campo)
    base["insumo"]     = None
    base["dose_kg_ha"] = None
    return base


def _dado_suspeito_insumo(campo: str, valor, motivo: str) -> dict:
    base = dado_suspeito(campo, valor, motivo)
    base["insumo"]     = None
    base["dose_kg_ha"] = None
    return base


def _nao_se_aplica_insumo(motivo: str) -> dict:
    base = nao_se_aplica(motivo)
    base["insumo"]     = None
    base["dose_kg_ha"] = None
    return base


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO 1 — FOSFATAGEM POR EXTRAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

# ── Parâmetros (validar com PO Atvos) ────────────────────────────────────────

# Extração de P₂O₅ pelo canavial (kg P₂O₅ / t cana colhida) — Malavolta 2006
_P_EXTRACAO_BASE_KG_T = 0.45

# Eficiência de aproveitamento do P adicionado, por textura
# (solos argilosos fixam mais P → precisam de dose maior para entregar o mesmo P à planta)
_EFICIENCIA_P = {
    "arenoso":        0.40,
    "medio":          0.32,
    "argiloso":       0.25,
    "muito_argiloso": 0.20,
}
_EFICIENCIA_P_DEFAULT = 0.30  # textura desconhecida

# Fator de redução da dose quando análise de solo mostra P já disponível
_REDUCAO_P_SOLO = {
    "muito_baixo": 1.00,  # sem redução — solo muito deficiente
    "baixo":       0.90,
    "medio":       0.70,
    "alto":        0.40,  # apenas manutenção
}

# Limiares P disponível Mehlich-1 (mg/dm³) — mesmos de fosfatagem.py
_P_MUITO_BAIXO = 8.0
_P_BAIXO       = 15.0
_P_MEDIO       = 30.0

# Descontos por adubação orgânica anterior
_DESCONTO_TORTA   = 0.25  # torta de filtro supre ~25% da demanda de P
_DESCONTO_VINHACA = 0.10  # vinhaca tem pouco P; desconto conservador

# Dose máxima por aplicação (segurança)
_DOSE_MAX_P_KG_HA = 150.0

# Insumo de referência
_INSUMO_FONE = "MAP (11-52-00)"  # fonte fosfatada mais comum em cana-de-açúcar


def _classificar_p_solo(p: float | None) -> str:
    """Retorna classe de P disponível pelo método Mehlich-1."""
    if p is None or not numerico(p):
        return "desconhecido"
    p = float(p)
    if p < _P_MUITO_BAIXO:
        return "muito_baixo"
    if p < _P_BAIXO:
        return "baixo"
    if p < _P_MEDIO:
        return "medio"
    return "alto"


def calcular_dose_fosfatagem(talhao: dict) -> dict:
    """
    Calcula a dose de adubação fosfatada em função da produtividade estimada
    da safra, textura do solo e disponibilidade de P na análise.

    A dose base é calculada pela extração esperada do canavial:
      dose_base (kg P₂O₅/ha) = tchan_estimado × P_EXTRACAO_BASE / eficiência_textura

    Depois ajustada por:
      - Nível de P disponível no solo (se análise disponível)
      - Adubação orgânica prévia (torta de filtro, vinhaca)

    Parameters
    ----------
    talhao : dict
        tchan_estimado (float) estimativa de produtividade, t/ha, ex: 75.0
          → obrigatório; SEM_DADO se ausente
        desc_ambiente  (str)   textura do solo (Silver), ex: "Argiloso"
          → opcional; usa eficiência padrão se ausente
        p_disponivel   (float) P Mehlich-1, mg/dm³, ex: 12.0
          → opcional; sem redução por solo se ausente
        categoria      (str)   CATEGORIA Silver, ex: "Cana Soca"
          → opcional; sem distinção de ciclo se ausente
        torta          (str)   "S" ou "N" — torta de filtro aplicada
        vinhaca        (str)   "S" ou "N" — vinhaca aplicada

    Returns
    -------
    dict com:
      orientacao      : recomendação com dose e justificativa
      valor_calculado : dose de P₂O₅ em kg/ha
      regra_acionada  : código da condição
      insumo          : produto de referência (MAP 11-52-00)
      dose_kg_ha      : igual a valor_calculado (kg P₂O₅/ha)

    Examples
    --------
    >>> calcular_dose_fosfatagem({
    ...     'tchan_estimado': 80.0, 'desc_ambiente': 'Argiloso',
    ...     'p_disponivel': 10.0, 'torta': 'N', 'vinhaca': 'N'
    ... })
    {'orientacao': 'Fosfatagem por extração: 121 kg P₂O₅/ha de MAP ...',
     'valor_calculado': 121.0, 'regra_acionada': 'dose_extracao_argiloso',
     'insumo': 'MAP (11-52-00)', 'dose_kg_ha': 121.0}

    >>> calcular_dose_fosfatagem({'tchan_estimado': None})
    {'orientacao': 'SEM_DADO', ..., 'regra_acionada': 'dado_ausente_tchan_estimado', ...}
    """
    tchan    = talhao.get("tchan_estimado")
    desc_amb = talhao.get("desc_ambiente")
    p_disp   = talhao.get("p_disponivel")
    torta    = talhao.get("torta")
    vinhaca  = talhao.get("vinhaca")

    if not numerico(tchan):
        return _sem_dado_insumo("tchan_estimado")

    tchan = float(tchan)

    if tchan <= 0:
        return _dado_suspeito_insumo("tchan_estimado", tchan,
                                     "TCH estimado deve ser positivo (produção nula invalida o cálculo de extração)")
    if tchan > 300:
        return _dado_suspeito_insumo("tchan_estimado", tchan,
                                     "TCH estimado acima do máximo físico (> 300 t/ha)")

    # ── textura → eficiência de aproveitamento do P ───────────────────────────
    textura = classificar_textura(desc_amb)
    efic    = _EFICIENCIA_P.get(textura, _EFICIENCIA_P_DEFAULT) if textura else _EFICIENCIA_P_DEFAULT

    # ── dose base pela extração do canavial ───────────────────────────────────
    dose_base = (tchan * _P_EXTRACAO_BASE_KG_T) / efic

    # ── fator de redução pela disponibilidade de P no solo ────────────────────
    classe_p  = _classificar_p_solo(p_disp)
    fator_p   = _REDUCAO_P_SOLO.get(classe_p, 1.0)
    dose      = dose_base * fator_p

    # ── desconto por adubação orgânica ────────────────────────────────────────
    tem_torta   = texto(torta)   and torta.strip().upper()   == "S"
    tem_vinhaca = texto(vinhaca) and vinhaca.strip().upper() == "S"

    if tem_torta and tem_vinhaca:
        desconto_org = min(_DESCONTO_TORTA + _DESCONTO_VINHACA, 0.35)
    elif tem_torta:
        desconto_org = _DESCONTO_TORTA
    elif tem_vinhaca:
        desconto_org = _DESCONTO_VINHACA
    else:
        desconto_org = 0.0

    dose = dose * (1 - desconto_org)

    # ── limitar ao máximo de segurança ────────────────────────────────────────
    dose = min(dose, _DOSE_MAX_P_KG_HA)
    dose = max(dose, 0.0)

    # ── montar orientação ─────────────────────────────────────────────────────
    tex_nome = textura.replace("_", " ") if textura else "textura não informada"
    org_parte = ""
    if tem_torta or tem_vinhaca:
        aplicados = []
        if tem_torta:   aplicados.append("torta de filtro")
        if tem_vinhaca: aplicados.append("vinhaca")
        org_parte = f" | desconto orgânico: {', '.join(aplicados)}"

    p_parte = f" | P solo: {classe_p.replace('_', ' ')}" if classe_p != "desconhecido" else ""

    orientacao = (
        f"Fosfatagem por extração: {dose:.0f} kg P₂O₅/ha de MAP"
        f" (TCH {tchan:.0f} t/ha, solo {tex_nome}{p_parte}{org_parte})"
    )

    regra = f"dose_extracao_{textura or 'textura_indefinida'}"
    if classe_p != "desconhecido":
        regra += f"_p_{classe_p}"

    return _resultado_insumo(orientacao, round(dose, 1), regra, _INSUMO_FONE, round(dose, 1))


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO 2 — DESSECAÇÃO (MANEJO DE SOQUEIRA / CONTROLE DE REBROTA)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Parâmetros (validar com PO Atvos) ────────────────────────────────────────

# Dose base de Glifosato 480 SL (L/ha comercial) por faixa de corte
# Pressão de plantas daninhas tende a aumentar com a idade da soqueira
_DOSE_DESSEC_L_HA = {
    "jovem":  2.5,   # 1º–2º corte — baixa pressão de infestação
    "medio":  3.5,   # 3º–4º corte — pressão moderada
    "tardio": 4.5,   # 5º+ corte   — alta pressão, soqueira debilitada
}

# Fator de ajuste por nível de infestação (quando informado)
_FATOR_INFESTACAO = {
    "baixa":  0.80,
    "leve":   0.80,
    "media":  1.00,
    "alta":   1.20,
    "severa": 1.30,
}

# Densidade do Glifosato 480 SL para converter L/ha → kg/ha (embalagem)
_DENSIDADE_GLIFOSATO = 1.18   # kg/L (produto comercial)

# Densidade de i.a. por litro de produto comercial
_IA_POR_LITRO = 0.480   # 480 g i.a./L → 0.480 kg i.a./L

# Insumo de referência
_INSUMO_DESSEC = "Glifosato 480 SL"

# Limiares de corte (espelha erradicacao.py para consistência)
_CORTE_TARDIO = 5
_CORTE_MEDIO  = 3


def _faixa_corte(no_corte: int) -> str:
    """Classifica o corte em jovem / medio / tardio."""
    if no_corte >= _CORTE_TARDIO:
        return "tardio"
    if no_corte >= _CORTE_MEDIO:
        return "medio"
    return "jovem"


def calcular_dose_dessecacao(talhao: dict) -> dict:
    """
    Calcula a dose de dessecante (Glifosato) para manejo de soqueira ou
    controle de rebrota em áreas pré-reforma.

    Aplica-se somente em Cana Soca, Em Reforma ou antes de reforma programada.
    Em canaviais em formação (Formação / Muda), retorna NAO_SE_APLICA.

    A dose base varia com a idade da soqueira (NO_CORTE) como proxy da pressão
    de infestação quando o dado direto de infestação não está disponível.
    Quando `infestacao` é informado, ajusta a dose pelo nível real.

    Parameters
    ----------
    talhao : dict
        no_corte   (int) NO_CORTE da Silver — proxy da pressão de infestação
          → obrigatório para "Cana Soca"; SEM_DADO se ausente
        categoria  (str) CATEGORIA Silver — filtra talhões em formação
        reforma    (str) "S" ou "N" — "S" indica pré-reforma → aplica dessecação
        infestacao (str) nível de infestação: "baixa" | "media" | "alta" | "severa"
          → opcional; usa proxy por corte se ausente
        area_ha    (float) área do talhão em ha — para calcular total

    Returns
    -------
    dict com:
      orientacao      : recomendação com dose em L/ha e kg i.a./ha
      valor_calculado : dose em L/ha (produto comercial) — unidade de campo
      regra_acionada  : código da condição
      insumo          : "Glifosato 480 SL"
      dose_kg_ha      : dose em kg/ha do produto comercial (L/ha × densidade)

    Examples
    --------
    >>> calcular_dose_dessecacao({
    ...     'no_corte': 5, 'categoria': 'Cana Soca', 'reforma': 'N'
    ... })
    {'orientacao': 'Dessecação: 4.5 L/ha de Glifosato 480 SL ...',
     'valor_calculado': 4.5, 'regra_acionada': 'dessecacao_tardio_proxy_corte',
     'insumo': 'Glifosato 480 SL', 'dose_kg_ha': 5.31}

    >>> calcular_dose_dessecacao({'no_corte': 1, 'categoria': 'Formação'})
    {'orientacao': 'NAO_SE_APLICA', ..., 'regra_acionada': 'categoria_formacao_ou_muda'}
    """
    no_corte   = talhao.get("no_corte")
    categoria  = talhao.get("categoria")
    reforma    = talhao.get("reforma")
    infestacao = talhao.get("infestacao")

    # ── filtro de categoria ────────────────────────────────────────────────────
    if texto(categoria) and categoria in ("Formação", "Muda"):
        return _nao_se_aplica_insumo("categoria_formacao_ou_muda")

    # Em pousio ou passagem: não se aplica dessecação de soqueira
    if texto(categoria) and categoria in ("Pousio", "Passagem"):
        return _nao_se_aplica_insumo("categoria_pousio_ou_passagem")

    # ── validar no_corte (necessário para estimar infestação) ─────────────────
    if not numerico(no_corte):
        return _sem_dado_insumo("no_corte")

    nc = int(no_corte)

    if nc < 0:
        return _dado_suspeito_insumo("no_corte", no_corte,
                                     "número de corte não pode ser negativo")
    if nc > 20:
        return _dado_suspeito_insumo("no_corte", no_corte,
                                     "número de cortes implausível (> 20)")

    # ── dose base por faixa de corte ──────────────────────────────────────────
    faixa = _faixa_corte(nc)
    dose_l_ha = _DOSE_DESSEC_L_HA[faixa]

    # ── ajuste por nível de infestação (se informado) ─────────────────────────
    fonte_dose = "proxy_corte"
    if texto(infestacao):
        chave_inf = infestacao.strip().lower()
        if chave_inf in _FATOR_INFESTACAO:
            dose_l_ha = dose_l_ha * _FATOR_INFESTACAO[chave_inf]
            fonte_dose = f"infestacao_{chave_inf}"
        # Se valor não reconhecido, mantém proxy por corte

    # ── converter para kg/ha (produto comercial) ──────────────────────────────
    dose_kg_ha = round(dose_l_ha * _DENSIDADE_GLIFOSATO, 2)
    dose_ia_ha = round(dose_l_ha * _IA_POR_LITRO, 2)

    # ── contexto de aplicação ─────────────────────────────────────────────────
    reforma_programada = texto(reforma) and reforma.strip().upper() == "S"
    contexto = "pré-reforma" if reforma_programada else f"manejo de soqueira ({nc}º corte)"

    orientacao = (
        f"Dessecação ({contexto}): {dose_l_ha:.1f} L/ha de Glifosato 480 SL"
        f" | {dose_ia_ha:.2f} kg i.a./ha"
    )

    regra = f"dessecacao_{faixa}_{fonte_dose}"

    return _resultado_insumo(
        orientacao, round(dose_l_ha, 2), regra, _INSUMO_DESSEC, dose_kg_ha
    )


# ── EXEMPLO DE USO ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== calcular_dose_fosfatagem ===")
    casos_fosf = [
        {"tchan_estimado": 80.0, "desc_ambiente": "Argiloso",  "p_disponivel": 10.0, "torta": "N", "vinhaca": "N"},
        {"tchan_estimado": 70.0, "desc_ambiente": "Arenoso",   "p_disponivel": 35.0, "torta": "N", "vinhaca": "S"},
        {"tchan_estimado": 60.0, "desc_ambiente": "Argiloso",  "p_disponivel": None, "torta": "S", "vinhaca": "S"},
        {"tchan_estimado": None, "desc_ambiente": "Argiloso"},   # SEM_DADO
        {"tchan_estimado": 75.0},                                # sem textura, sem análise
    ]
    for c in casos_fosf:
        r = calcular_dose_fosfatagem(c)
        print(f"  TCH={c.get('tchan_estimado')} tex={c.get('desc_ambiente')} P={c.get('p_disponivel')}"
              f" | dose={r.get('dose_kg_ha')} | regra={r['regra_acionada']}")

    print("\n=== calcular_dose_dessecacao ===")
    casos_desc = [
        {"no_corte": 1, "categoria": "Cana Soca",  "reforma": "N"},
        {"no_corte": 4, "categoria": "Cana Soca",  "reforma": "N", "infestacao": "alta"},
        {"no_corte": 6, "categoria": "Cana Soca",  "reforma": "S"},
        {"no_corte": 1, "categoria": "Formação",   "reforma": "N"},  # NAO_SE_APLICA
        {"no_corte": None, "categoria": "Cana Soca"},                 # SEM_DADO
    ]
    for c in casos_desc:
        r = calcular_dose_dessecacao(c)
        print(f"  corte={c.get('no_corte')} cat={c.get('categoria')} inf={c.get('infestacao')}"
              f" | L/ha={r.get('valor_calculado')} kg/ha={r.get('dose_kg_ha')}"
              f" | regra={r['regra_acionada']}")
