"""
src/rules/erradicacao.py
Regra de erradicação (decisão de reforma/substituição do canavial).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PSEUDOCÓDIGO (validar com PO Atvos antes de alterar limiares)

  ENTRADAS DISPONÍVEIS NA SILVER:
    no_corte  : NO_CORTE — número do corte (0 = formação, 1 = 1º socamento, ...)
    tch_prod  : TCH_PROD — produtividade estimada (t cana/ha)
    categoria : CATEGORIA — "Formação", "Cana Soca", "Muda"
    reforma   : Reforma   — "S" se o talhão já está programado para reforma

  SE tch_prod é nulo → SEM_DADO
  SE no_corte é nulo → SEM_DADO
  SE categoria == "Formação" → NAO_SE_APLICA (canavial ainda em formação)
  SE reforma == "S" → NAO_SE_APLICA (reforma já programada pela usina)

  MATRIZ DE DECISÃO:
    ┌────────────────┬─────────────────┬──────────────────────────────────────┐
    │ NO_CORTE       │ TCH_PROD (t/ha) │ Recomendação                         │
    ├────────────────┼─────────────────┼──────────────────────────────────────┤
    │ >= 5 (tardio)  │ < 50            │ RECOMENDADA — alta prioridade        │
    │ >= 5 (tardio)  │ 50 – 70         │ AVALIAR — custo-benefício crítico    │
    │ >= 5 (tardio)  │ > 70            │ MONITORAR — ainda produtivo          │
    │ 3 – 4 (médio)  │ < 40            │ INVESTIGAR — baixa produtividade cedo│
    │ 3 – 4 (médio)  │ 40 – 60         │ MONITORAR — acompanhar próxima safra │
    │ 3 – 4 (médio)  │ > 60            │ NAO_RECOMENDADA — bom desempenho     │
    │ 1 – 2 (jovem)  │ < 40            │ INVESTIGAR — falha grave de campo    │
    │ 1 – 2 (jovem)  │ >= 40           │ NAO_RECOMENDADA — canavial jovem     │
    └────────────────┴─────────────────┴──────────────────────────────────────┘

  Limiares (t/ha) — confirmar com PO Atvos:
    TCH crítico (erradicação quase certa)   : 50 t/ha
    TCH de alerta (avaliar)                 : 70 t/ha
    TCH de investigação (canavial jovem)    : 40 t/ha
    Corte tardio (alta chance de declínio)  : NO_CORTE >= 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from ._base import sem_dado, nao_se_aplica, resultado, dado_suspeito, numerico, texto

# ── PARÂMETROS (confirmar com PO Atvos) ──────────────────────────────────────

CORTE_TARDIO         = 5     # NO_CORTE >= este valor é considerado canavial tardio
TCH_CRITICO          = 50.0  # t/ha — abaixo disso em canavial tardio → erradicação
TCH_ALERTA           = 70.0  # t/ha — zona de avaliação para canavial tardio
TCH_INVESTIGACAO     = 40.0  # t/ha — abaixo disso em canavial jovem → investigar

# Limites físicos de sanidade de dados
TCH_MAX_VALIDO       = 300.0  # t/ha — acima disso é fisicamente impossível para cana
NO_CORTE_MAX_VALIDO  = 20     # número de cortes implausível acima disso (~20 anos)


# ── REGRA PRINCIPAL ───────────────────────────────────────────────────────────

def calcular_necessidade_erradicacao(talhao: dict) -> dict:
    """
    Avalia a necessidade de erradicação/reforma do canavial.

    Esta é a única regra 100% implementável com os dados Silver atuais.

    Parameters
    ----------
    talhao : dict
        Todos os campos abaixo vêm diretamente da Silver:
          no_corte  (int)   NO_CORTE, número do corte atual, ex: 4
          tch_prod  (float) TCH_PROD, t/ha estimadas, ex: 45.0
          categoria (str)   CATEGORIA, ex: "Cana Soca"
          reforma   (str)   Reforma, "S" ou "N"

    Returns
    -------
    dict com:
      orientacao       : recomendação qualitativa com justificativa
      valor_calculado  : TCH_PROD usado como referência (facilita ranking)
      regra_acionada   : código da linha da matriz de decisão

    Examples
    --------
    >>> calcular_necessidade_erradicacao({
    ...     'no_corte': 6, 'tch_prod': 45.0,
    ...     'categoria': 'Cana Soca', 'reforma': 'N'
    ... })
    {'orientacao': 'ERRADICAÇÃO RECOMENDADA: canavial tardio (6º corte) com TCH 45.0 t/ha — prioridade alta',
     'valor_calculado': 45.0,
     'regra_acionada': 'tardio_tch_critico'}

    >>> calcular_necessidade_erradicacao({'no_corte': 1, 'tch_prod': 85.0,
    ...                                   'categoria': 'Cana Soca', 'reforma': 'N'})
    {'orientacao': 'Erradicação não recomendada: canavial jovem (1º corte), bom desempenho',
     'valor_calculado': 85.0,
     'regra_acionada': 'jovem_tch_adequado'}
    """
    no_corte  = talhao.get("no_corte")
    tch_prod  = talhao.get("tch_prod")
    categoria = talhao.get("categoria")
    reforma   = talhao.get("reforma")

    # ── validação de entradas ──────────────────────────────────────────────────
    if not numerico(tch_prod):
        return sem_dado("tch_prod")
    if not numerico(no_corte):
        return sem_dado("no_corte")

    # ── detecção de outliers ───────────────────────────────────────────────────
    _tch = float(tch_prod)
    _nc  = int(no_corte)
    if _tch < 0:
        return dado_suspeito("tch_prod", tch_prod, "TCH não pode ser negativo")
    if _tch > TCH_MAX_VALIDO:
        return dado_suspeito("tch_prod", tch_prod,
                             f"TCH acima do máximo físico ({TCH_MAX_VALIDO} t/ha)")
    if _nc < 0:
        return dado_suspeito("no_corte", no_corte, "número de corte não pode ser negativo")
    if _nc > NO_CORTE_MAX_VALIDO:
        return dado_suspeito("no_corte", no_corte,
                             f"número de cortes implausível (> {NO_CORTE_MAX_VALIDO})")

    # ── casos que não se aplicam ───────────────────────────────────────────────
    if texto(categoria) and categoria in ("Formação", "Muda"):
        return nao_se_aplica("categoria_formacao_ou_muda")

    if texto(reforma) and reforma.strip().upper() == "S":
        return nao_se_aplica("reforma_ja_programada")

    tch  = float(tch_prod)
    nc   = int(no_corte)
    nc_s = f"{nc}º corte"

    # ── canavial tardio (NO_CORTE >= CORTE_TARDIO) ────────────────────────────
    if nc >= CORTE_TARDIO:
        if tch < TCH_CRITICO:
            return resultado(
                f"ERRADICAÇÃO RECOMENDADA: canavial tardio ({nc_s}) com "
                f"TCH {tch:.1f} t/ha — prioridade alta",
                tch, "tardio_tch_critico",
            )
        if tch <= TCH_ALERTA:
            return resultado(
                f"AVALIAR ERRADICAÇÃO: canavial tardio ({nc_s}), TCH {tch:.1f} t/ha — "
                f"custo-benefício crítico, analisar antes da próxima safra",
                tch, "tardio_tch_alerta",
            )
        return resultado(
            f"MONITORAR: canavial tardio ({nc_s}) ainda produtivo — "
            f"TCH {tch:.1f} t/ha, acompanhar próxima safra",
            tch, "tardio_tch_adequado",
        )

    # ── canavial de ciclo médio (3º ou 4º corte) ──────────────────────────────
    if nc in (3, 4):
        if tch < TCH_INVESTIGACAO:
            return resultado(
                f"INVESTIGAR: baixa produtividade precoce ({nc_s}, TCH {tch:.1f} t/ha) — "
                f"verificar pragas, doenças ou falhas de implantação",
                tch, "medio_tch_investigar",
            )
        if tch <= TCH_ALERTA:
            return resultado(
                f"MONITORAR: desempenho abaixo do esperado ({nc_s}, TCH {tch:.1f} t/ha) — "
                f"reavaliar na próxima safra",
                tch, "medio_tch_monitorar",
            )
        return resultado(
            f"Erradicação não recomendada: bom desempenho ({nc_s}, TCH {tch:.1f} t/ha)",
            tch, "medio_tch_adequado",
        )

    # ── canavial jovem (1º ou 2º corte) ──────────────────────────────────────
    if tch < TCH_INVESTIGACAO:
        return resultado(
            f"INVESTIGAR: produtividade muito baixa em canavial jovem ({nc_s}, "
            f"TCH {tch:.1f} t/ha) — falha grave, avaliar replantio",
            tch, "jovem_tch_investigar",
        )
    return resultado(
        f"Erradicação não recomendada: canavial jovem ({nc_s}), bom desempenho "
        f"(TCH {tch:.1f} t/ha)",
        tch, "jovem_tch_adequado",
    )


if __name__ == "__main__":
    casos = [
        {"no_corte": 6, "tch_prod": 45.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 5, "tch_prod": 62.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 5, "tch_prod": 78.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 4, "tch_prod": 35.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 4, "tch_prod": 55.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 1, "tch_prod": 85.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 1, "tch_prod": 30.0, "categoria": "Cana Soca", "reforma": "N"},
        {"no_corte": 0, "tch_prod": 90.0, "categoria": "Formação",  "reforma": "N"},
        {"no_corte": 6, "tch_prod": 40.0, "categoria": "Cana Soca", "reforma": "S"},
        {"no_corte": None, "tch_prod": 50.0, "categoria": "Cana Soca", "reforma": "N"},
    ]
    for c in casos:
        r = calcular_necessidade_erradicacao(c)
        print(f"corte={c.get('no_corte')} tch={c.get('tch_prod')} | {r['regra_acionada']:<30} | {r['orientacao']}")
