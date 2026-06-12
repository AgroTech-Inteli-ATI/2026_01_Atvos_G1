"""
src/rules/janela_plantio.py
Regra de janela de plantio para reforma e expansão de canavial.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PSEUDOCÓDIGO (validar com PO Atvos antes de alterar meses)

  ENTRADAS DISPONÍVEIS NA SILVER:
    data_plantio : DATA_PLANTIO — data real ou prevista de plantio
    man_hipot    : MAN_HIPOT    — maturação hipotética ("Precoce","Média","Tardia","A Definir")
    tp_reforma   : TP_REFORMA   — tipo de reforma ("Convencional","Inverno","18 Meses")
    categoria    : CATEGORIA    — filtro: aplicar apenas em "Formação" ou "Muda"

  SE categoria NOT IN {"Formação", "Muda"} → NAO_SE_APLICA (já estabelecido)
  SE data_plantio é nulo E man_hipot é nulo → SEM_DADO

  JANELAS POR MATURAÇÃO (meses ideais — região Centro-Oeste/SP — confirmar):
    "Precoce" → plantio: abril – junho    (colheita: jun–set ano seguinte)
    "Média"   → plantio: junho – agosto   (colheita: ago–nov ano seguinte)
    "Tardia"  → plantio: agosto – outubro (colheita: out–jan ano seguinte)
    "A Definir" → orientar a definir com agrônomo antes do plantio

  JANELAS POR TIPO DE REFORMA:
    "Convencional" → mesmas janelas por maturação acima
    "Inverno"      → plantio: abril – julho (aproveitamento de chuva invernal)
    "18 Meses"     → plantio: março – maio  (ciclo mais longo, antecipa)

  AVALIAÇÃO DO PLANTIO REALIZADO:
    SE data_plantio informada:
      → verificar se o mês de plantio está dentro da janela esperada
      → retornar "DENTRO_DA_JANELA" | "FORA_DA_JANELA" | "LIMITE_DA_JANELA"
    SE data_plantio nula:
      → retornar orientação sobre a janela recomendada sem avaliar real vs. esperado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
from ._base import sem_dado, nao_se_aplica, resultado, texto

# ── JANELAS DE PLANTIO (meses do ano, 1=jan ... 12=dez) ──────────────────────
# Confirmar com PO Atvos — variam por unidade industrial e microrregião

_JANELAS_MATURACAO = {
    "Precoce":    (4, 6),    # abril – junho
    "Média":      (6, 8),    # junho – agosto
    "Tardia":     (8, 10),   # agosto – outubro
    "A Definir":  None,      # sem janela definida
}

_JANELAS_REFORMA = {
    "Convencional": None,          # usa janela por maturação
    "Inverno":      (4, 7),        # abril – julho
    "18 Meses":     (3, 5),        # março – maio
}

_NOME_MES = {
    1: "janeiro", 2: "fevereiro", 3: "março",    4: "abril",
    5: "maio",    6: "junho",     7: "julho",     8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _janela_para_texto(inicio: int, fim: int) -> str:
    return f"{_NOME_MES[inicio]} a {_NOME_MES[fim]}"


def _avaliar_mes(mes: int, inicio: int, fim: int) -> str:
    """Verifica se um mês está dentro da janela [inicio, fim]."""
    # Janela pode cruzar virada de ano (ex: nov–jan)
    if inicio <= fim:
        dentro = inicio <= mes <= fim
    else:
        dentro = mes >= inicio or mes <= fim

    if dentro:
        return "dentro"
    # Um mês de distância → limite
    if mes == inicio - 1 or mes == fim + 1:
        return "limite"
    return "fora"


# ── REGRA PRINCIPAL ───────────────────────────────────────────────────────────

def calcular_janela_plantio(talhao: dict) -> dict:
    """
    Avalia a adequação da janela de plantio para um talhão em formação.

    Compara DATA_PLANTIO real (se disponível) com a janela ideal definida
    por MAN_HIPOT e TP_REFORMA. Se sem data real, retorna orientação preventiva.

    Parameters
    ----------
    talhao : dict
        Campos disponíveis na Silver:
          data_plantio (datetime | str | None) DATA_PLANTIO
          man_hipot    (str)  MAN_HIPOT: "Precoce" | "Média" | "Tardia" | "A Definir"
          tp_reforma   (str)  TP_REFORMA: "Convencional" | "Inverno" | "18 Meses"
          categoria    (str)  CATEGORIA: deve ser "Formação" ou "Muda"

    Returns
    -------
    dict com:
      orientacao       : avaliação da janela (DENTRO / FORA / orientação)
      valor_calculado  : mês do plantio como float (ex: 4.0 = abril), ou None
      regra_acionada   : código da condição

    Examples
    --------
    >>> from datetime import date
    >>> calcular_janela_plantio({
    ...     'data_plantio': date(2025, 5, 15),
    ...     'man_hipot': 'Precoce', 'tp_reforma': 'Convencional',
    ...     'categoria': 'Formação'
    ... })
    {'orientacao': 'Plantio DENTRO DA JANELA: maio (janela Precoce: abril a junho)',
     'valor_calculado': 5.0,
     'regra_acionada': 'plantio_dentro_janela_maturacao'}
    """
    data_plantio = talhao.get("data_plantio")
    man_hipot    = talhao.get("man_hipot")
    tp_reforma   = talhao.get("tp_reforma")
    categoria    = talhao.get("categoria")

    # ── filtro de categoria ────────────────────────────────────────────────────
    if texto(categoria) and categoria not in ("Formação", "Muda"):
        return nao_se_aplica("categoria_nao_plantio")

    # ── determinar janela vigente ──────────────────────────────────────────────
    # Prioridade: TP_REFORMA específico > MAN_HIPOT
    janela = None
    fonte_janela = ""

    if texto(tp_reforma) and tp_reforma in _JANELAS_REFORMA:
        janela_reforma = _JANELAS_REFORMA[tp_reforma]
        if janela_reforma is not None:
            janela = janela_reforma
            fonte_janela = f"reforma '{tp_reforma}'"

    if janela is None and texto(man_hipot) and man_hipot in _JANELAS_MATURACAO:
        janela_mat = _JANELAS_MATURACAO[man_hipot]
        if janela_mat is not None:
            janela = janela_mat
            fonte_janela = f"maturação '{man_hipot}'"

    if janela is None and man_hipot == "A Definir":
        return resultado(
            "Janela indefinida: MAN_HIPOT = 'A Definir' — definir variedade/maturação "
            "com o agrônomo antes do plantio",
            None,
            "man_hipot_a_definir",
        )

    if janela is None:
        return sem_dado("man_hipot_ou_tp_reforma")

    inicio, fim = janela
    janela_txt = _janela_para_texto(inicio, fim)

    # ── sem data de plantio → orientação preventiva ───────────────────────────
    if data_plantio is None:
        return resultado(
            f"Janela de plantio recomendada ({fonte_janela}): {janela_txt}",
            None,
            "janela_sem_data_plantio",
        )

    # ── com data de plantio → avaliar ─────────────────────────────────────────
    try:
        dt = pd.Timestamp(data_plantio)
        mes = dt.month
    except Exception:
        return sem_dado("data_plantio_formato_invalido")

    situacao = _avaliar_mes(mes, inicio, fim)
    mes_txt = _NOME_MES.get(mes, str(mes))

    if situacao == "dentro":
        return resultado(
            f"Plantio DENTRO DA JANELA: {mes_txt} "
            f"(janela {fonte_janela}: {janela_txt})",
            float(mes),
            f"plantio_dentro_janela_{fonte_janela.split()[0].lower()}",
        )

    if situacao == "limite":
        return resultado(
            f"Plantio no LIMITE DA JANELA: {mes_txt} — "
            f"janela ideal ({fonte_janela}): {janela_txt}",
            float(mes),
            f"plantio_limite_janela",
        )

    return resultado(
        f"Plantio FORA DA JANELA: {mes_txt} — "
        f"janela ideal ({fonte_janela}): {janela_txt} — "
        f"avaliar impacto na maturação",
        float(mes),
        f"plantio_fora_janela",
    )


if __name__ == "__main__":
    import datetime
    casos = [
        {"data_plantio": datetime.date(2025, 5, 15), "man_hipot": "Precoce",  "tp_reforma": "Convencional", "categoria": "Formação"},
        {"data_plantio": datetime.date(2025, 9, 10), "man_hipot": "Precoce",  "tp_reforma": "Convencional", "categoria": "Formação"},
        {"data_plantio": datetime.date(2025, 4, 20), "man_hipot": "Média",    "tp_reforma": "Inverno",      "categoria": "Formação"},
        {"data_plantio": None,                       "man_hipot": "Tardia",   "tp_reforma": "Convencional", "categoria": "Formação"},
        {"data_plantio": None,                       "man_hipot": "A Definir","tp_reforma": None,           "categoria": "Formação"},
        {"data_plantio": datetime.date(2025, 7, 1),  "man_hipot": "Média",    "tp_reforma": None,           "categoria": "Cana Soca"},
    ]
    for c in casos:
        r = calcular_janela_plantio(c)
        print(f"{r['regra_acionada']:<45} | {r['orientacao']}")
