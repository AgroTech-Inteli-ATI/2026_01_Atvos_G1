"""
Módulo de regras agronômicas: Janela de Plantio
=================================================
Fonte: Manual Prático Para o Manejo da Cana-de-Açúcar (Agroadvance, 2022), p. 8 e 15.

Regra central:
  Dado o sistema de plantio (cana de ano, ano e meio, inverno, soca),
  calcula a janela de colheita esperada e verifica se ela cai dentro do
  período ideal (maio–novembro, Centro-Sul).

  Data de referência por tipo de talhão:
  - Cana Planta e outros plantios: DATA_PLANTIO
  - Cana Soca: ULT_CORTE (DATA_PLANTIO é o plantio original, que pode ter
    vários anos; o ciclo atual começa a partir do último corte)

  Ciclos por sistema (manual, p. 15):
  - Cana de Ano e Meio: 14–22 meses
  - Cana de Ano:        12 meses
  - Cana Soca:          12 meses
  - Cana de Inverno:    12–16 meses

  Verificação da janela: checa se QUALQUER mês do intervalo [min, max]
  coincide com mai–nov. Para sistemas de ciclo fixo (soca, ano) min == max
  e a lógica é equivalente ao mês único. Para ciclos variáveis (ano e meio,
  inverno), evita falsos negativos quando parte da janela está dentro do ideal.

  Janela ideal de colheita Centro-Sul: maio–novembro
  Início do preparo de solo: 150 dias antes do plantio

  Mudas necessárias: 10–15 t/ha (12 gemas/m em condições normais;
  15–18 gemas/m em períodos de estiagem)

Parâmetros pendentes de validação pelo PO ATVOS:
  - Matriz de Aptidão por mês (mencionada no TAP — mais granular que esta regra)
  - ATVOS opera exclusivamente no Centro-Sul? Confirmar janela mai–nov.
  - Quantidade de mudas por ambiente de produção específico da ATVOS
"""

from __future__ import annotations
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta  # type: ignore

# ── Constantes ──────────────────────────────────────────────────────────────
MES_COLHEITA_MIN = 5    # maio   [AGUARDA VALIDACAO PO — Matriz de Aptidão]
MES_COLHEITA_MAX = 11   # novembro
ANTECEDENCIA_PREPARO_DIAS = 150

# Ciclos por sistema (meses mínimo e máximo)
CICLOS = {
    "ano_e_meio":  (14, 22),
    "inverno":     (12, 16),
    "ano":         (12, 12),
    "soca":        (12, 12),
}

CATEGORIAS_INAPTAS = {"Em Reforma", "Pousio", "A Definir", "Passagem"}


def _identificar_sistema(estagio: str, categoria: str) -> str:
    """Identifica o sistema de plantio com base no ESTAGIO e CATEGORIA."""
    s = str(estagio).lower()
    if "ano e meio" in s or "18m" in s or "15m" in s:
        return "ano_e_meio"
    elif "inverno" in s:
        return "inverno"
    elif "ano" in s and "meio" not in s:
        return "ano"
    elif "12m" in s or "formação 12" in s:
        return "ano"
    else:
        return "soca"   # cortes numerados e demais → soca (12 meses)


def calcular_janela_plantio(row: dict) -> dict:
    """
    Avalia a janela de plantio e colheita estimada para um talhão.

    Parâmetros
    ----------
    row : dict
        Linha do DataFrame enriquecido (Silver + Solo). Campos utilizados:
        - DATA_PLANTIO : datetime — data de plantio
        - ESTAGIO      : str      — estágio de desenvolvimento
        - CATEGORIA    : str      — tipo de ciclo da cana
        - AREA_HA      : float    — área do talhão (ha)

    Retorno
    -------
    dict com chaves:
        processo, orientacao, valor_calculado, unidade_medida,
        regra_acionada, flag_aguardando_validacao_po,
        data_colheita_min, data_colheita_max, data_preparo_solo

    Exemplo
    -------
    >>> from datetime import datetime
    >>> calcular_janela_plantio({
    ...     "DATA_PLANTIO": datetime(2024, 10, 1),
    ...     "ESTAGIO": "Cana de Ano e Meio",
    ...     "CATEGORIA": "Cana Planta",
    ...     "AREA_HA": 50.0
    ... })
    # Retorna janela de colheita dez/2025–ago/2026, alerta fora de mai-nov
    """
    base = {"processo": "janela_plantio"}

    categoria = str(row.get("CATEGORIA", "")).strip()

    if categoria in CATEGORIAS_INAPTAS:
        return {**base,
                "orientacao": f"Talhão com categoria '{categoria}': janela de plantio não aplicável.",
                "valor_calculado": None,
                "unidade_medida": None,
                "regra_acionada": "janela_nao_aplicavel",
                "flag_aguardando_validacao_po": False,
                "data_colheita_min": None,
                "data_colheita_max": None,
                "data_preparo_solo": None}

    estagio = str(row.get("ESTAGIO", "")).strip()
    sistema = _identificar_sistema(estagio, categoria)
    ciclo_min, ciclo_max = CICLOS[sistema]

    # Escolher data de referência correta
    # - Soca: ULT_CORTE (o ciclo atual começa no último corte, não no plantio original)
    # - Demais: DATA_PLANTIO
    if sistema == "soca":
        data_ref_raw = row.get("ULT_CORTE")
        campo_ref = "ULT_CORTE"
    else:
        data_ref_raw = row.get("DATA_PLANTIO")
        campo_ref = "DATA_PLANTIO"

    # Fallback: se o campo preferido estiver ausente, tenta o outro
    if data_ref_raw is None or (isinstance(data_ref_raw, float) and data_ref_raw != data_ref_raw):
        alt_raw = row.get("DATA_PLANTIO") if sistema == "soca" else row.get("ULT_CORTE")
        if alt_raw is not None and not (isinstance(alt_raw, float) and alt_raw != alt_raw):
            data_ref_raw = alt_raw
            campo_ref = "DATA_PLANTIO (fallback — ULT_CORTE ausente)" if sistema == "soca" else "ULT_CORTE (fallback)"
        else:
            return {**base,
                    "orientacao": f"SEM_DADO: {campo_ref} ausente e sem fallback disponível.",
                    "valor_calculado": None,
                    "unidade_medida": None,
                    "regra_acionada": "dado_ausente_data_referencia",
                    "flag_aguardando_validacao_po": False,
                    "data_colheita_min": None,
                    "data_colheita_max": None,
                    "data_preparo_solo": None}

    # Converter para date
    data_ref = data_ref_raw
    if hasattr(data_ref, "date"):
        data_ref = data_ref.date()
    elif isinstance(data_ref, str):
        try:
            data_ref = date.fromisoformat(str(data_ref)[:10])
        except ValueError:
            return {**base,
                    "orientacao": f"SEM_DADO: {campo_ref} com formato inválido.",
                    "valor_calculado": None,
                    "unidade_medida": None,
                    "regra_acionada": "dado_invalido_data_referencia",
                    "flag_aguardando_validacao_po": False,
                    "data_colheita_min": None,
                    "data_colheita_max": None,
                    "data_preparo_solo": None}

    # Calcular janela de colheita
    data_colheita_min = data_ref + relativedelta(months=ciclo_min)
    data_colheita_max = data_ref + relativedelta(months=ciclo_max)
    data_preparo = data_ref - timedelta(days=ANTECEDENCIA_PREPARO_DIAS)

    # Verificar se ALGUM mês da janela [min, max] cai no período ideal mai-nov.
    # Para ciclos fixos (soca, ano) min == max e isso equivale a checar um único mês.
    # Para ciclos variáveis (ano e meio: 14-22m, inverno: 12-16m) evita falsos
    # negativos quando parte da janela está dentro do período ideal.
    meses_janela: set[int] = set()
    d = data_colheita_min
    while d <= data_colheita_max:
        meses_janela.add(d.month)
        d += relativedelta(months=1)
    janela_ok = bool(meses_janela & set(range(MES_COLHEITA_MIN, MES_COLHEITA_MAX + 1)))

    if janela_ok:
        alerta = "Colheita estimada dentro da janela ideal (mai–nov). ✓"
        regra = "janela_dentro_do_ideal"
    else:
        alerta = (
            f"ATENÇÃO: colheita estimada fora da janela ideal (mai–nov). "
            f"Mês esperado: {data_colheita_min.strftime('%b/%Y')}. "
            f"Risco de brotações comprometidas pelo inverno."
        )
        regra = "janela_fora_do_ideal"

    # Mudas recomendadas
    area_ha = row.get("AREA_HA")
    if area_ha and float(area_ha) > 0:
        mudas_min = float(area_ha) * 10
        mudas_max = float(area_ha) * 15
        mudas_txt = f"Mudas necessárias: {mudas_min:.0f}–{mudas_max:.0f} t (10–15 t/ha × {area_ha:.1f} ha)."
    else:
        mudas_txt = "Mudas necessárias: 10–15 t/ha."

    orientacao = (
        f"Sistema: {sistema.replace('_', ' ')}. "
        f"Ref.: {campo_ref} ({data_ref.strftime('%d/%m/%Y')}). "
        f"Janela de colheita estimada: "
        f"{data_colheita_min.strftime('%b/%Y')}–{data_colheita_max.strftime('%b/%Y')} "
        f"({ciclo_min}–{ciclo_max} meses). "
        f"{alerta} "
        f"Início do preparo de solo: {data_preparo.strftime('%d/%m/%Y')} "
        f"({ANTECEDENCIA_PREPARO_DIAS} dias antes). "
        f"{mudas_txt}"
    )

    return {**base,
            "orientacao": orientacao,
            "valor_calculado": ciclo_min,
            "unidade_medida": "meses_ciclo",
            "regra_acionada": regra,
            "flag_aguardando_validacao_po": True,   # Matriz de Aptidão aguarda PO
            "data_colheita_min": data_colheita_min.isoformat(),
            "data_colheita_max": data_colheita_max.isoformat(),
            "data_preparo_solo": data_preparo.isoformat()}
