from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Mapping


MESES_ANO_E_MEIO = {1, 2, 3}
MESES_INVERNO = {4, 5, 6, 7, 8}
MESES_CANA_ANO = {9, 10, 11}
MESES_COLHEITA_RECOMENDADA = {5, 6, 7, 8, 9, 10, 11}


def calcular_janela_plantio(talhao: Mapping[str, Any]) -> dict[str, Any]:
    data_plantio = _parse_date(_first_present(talhao, "DATA_PLANTIO", "data_plantio"))
    if data_plantio is None:
        return _resultado(
            orientacao="SEM_DADO",
            valor_calculado=None,
            regra_acionada="dado_ausente_data_plantio",
            sistema_recomendado=None,
            preparo_solo_inicio=None,
            corretivos_inicio=None,
            corretivos_fim=None,
            observacao="DATA_PLANTIO ausente ou invalida.",
        )

    mes = data_plantio.month
    sistema_informado = _normalizar_texto(
        _first_present(talhao, "TP_REFORMA", "SIST_PLANT", "ESTAGIO", "CATEGORIA")
    )
    sistema_recomendado, regra = _classificar_sistema(mes, sistema_informado)
    preparo_solo_inicio = data_plantio - timedelta(days=150)
    corretivos_inicio = data_plantio - timedelta(days=90)
    corretivos_fim = data_plantio - timedelta(days=60)

    if mes in MESES_ANO_E_MEIO:
        orientacao = "JANELA_APTA"
        observacao = (
            "Manter distribuicao, picacao e cobrimento das mudas no mesmo dia "
            "para favorecer germinacao e uniformidade."
        )
        regra_acionada = regra
    elif mes in MESES_INVERNO:
        orientacao = "JANELA_INVERNO"
        observacao = (
            "Validar disponibilidade de agua e qualidade de muda; em estiagem, "
            "priorizar maior densidade de gemas por metro."
        )
        regra_acionada = regra
    elif mes in MESES_CANA_ANO:
        orientacao = "JANELA_APTA"
        observacao = (
            "Manter distribuicao, picacao e cobrimento das mudas no mesmo dia "
            "para favorecer germinacao e uniformidade."
        )
        regra_acionada = regra
    else:
        orientacao = "ATENCAO"
        observacao = (
            "Plantio em dezembro fica fora das janelas principais usadas nesta "
            "versao; validar com PDA/PO antes de executar."
        )
        regra_acionada = regra

    return _resultado(
        orientacao=orientacao,
        valor_calculado=float(mes),
        regra_acionada=regra_acionada,
        sistema_recomendado=sistema_recomendado,
        preparo_solo_inicio=preparo_solo_inicio.isoformat(),
        corretivos_inicio=corretivos_inicio.isoformat(),
        corretivos_fim=corretivos_fim.isoformat(),
        observacao=observacao,
    )


def avaliar_colheita_pos_plantio(talhao: Mapping[str, Any]) -> dict[str, Any]:
    data_colheita = _parse_date(_first_present(talhao, "DATA_FECHA", "ULT_CORTE"))
    if data_colheita is None:
        return _resultado(
            orientacao="SEM_DADO",
            valor_calculado=None,
            regra_acionada="dado_ausente_data_colheita",
            sistema_recomendado=None,
            preparo_solo_inicio=None,
            corretivos_inicio=None,
            corretivos_fim=None,
            observacao="DATA_FECHA/ULT_CORTE ausente ou invalida.",
        )

    mes = data_colheita.month
    if mes in MESES_COLHEITA_RECOMENDADA:
        orientacao = "COLHEITA_NA_JANELA"
        regra_acionada = "colheita_maio_novembro"
        observacao = "Colheita dentro do periodo recomendado de maio a novembro."
    else:
        orientacao = "ATENCAO"
        regra_acionada = "colheita_fora_maio_novembro"
        observacao = (
            "Colheita fora de maio a novembro pode afetar brotacoes e "
            "desenvolvimento inicial da soqueira."
        )

    return _resultado(
        orientacao=orientacao,
        valor_calculado=float(mes),
        regra_acionada=regra_acionada,
        sistema_recomendado=None,
        preparo_solo_inicio=None,
        corretivos_inicio=None,
        corretivos_fim=None,
        observacao=observacao,
    )


def _classificar_sistema(mes: int, sistema_informado: str) -> tuple[str, str]:
    if "18" in sistema_informado or "ano e meio" in sistema_informado:
        return "cana_ano_e_meio", "sistema_informado_ano_e_meio"
    elif "inverno" in sistema_informado:
        return "plantio_inverno", "sistema_informado_inverno"
    elif "12" in sistema_informado or "ano" in sistema_informado:
        return "cana_de_ano", "sistema_informado_cana_de_ano"
    elif mes in MESES_ANO_E_MEIO:
        return "cana_ano_e_meio", "mes_jan_mar_ano_e_meio"
    elif mes in MESES_INVERNO:
        return "plantio_inverno", "mes_abr_ago_inverno"
    elif mes in MESES_CANA_ANO:
        return "cana_de_ano", "mes_set_nov_cana_de_ano"
    else:
        return "fora_janela_preferencial", "mes_dez_fora_janela_preferencial"


def _resultado(
    *,
    orientacao: str,
    valor_calculado: float | None,
    regra_acionada: str,
    sistema_recomendado: str | None,
    preparo_solo_inicio: str | None,
    corretivos_inicio: str | None,
    corretivos_fim: str | None,
    observacao: str,
) -> dict[str, Any]:
    return {
        "processo": "janela_plantio",
        "orientacao": orientacao,
        "valor_calculado": valor_calculado,
        "regra_acionada": regra_acionada,
        "sistema_recomendado": sistema_recomendado,
        "preparo_solo_inicio": preparo_solo_inicio,
        "corretivos_inicio": corretivos_inicio,
        "corretivos_fim": corretivos_fim,
        "observacao": observacao,
    }


def _first_present(talhao: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = talhao.get(key)
        if value is not None and str(value).strip() not in {"", "NaT", "nan", "None"}:
            return value
    return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    texto = str(value).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date()
        except ValueError:
            pass
    try:
        import pandas as pd

        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def _normalizar_texto(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()
