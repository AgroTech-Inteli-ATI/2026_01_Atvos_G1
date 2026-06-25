"""
src/rules/_base.py
Tipos, constantes e utilitários compartilhados por todos os módulos de regras.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTRATO DE INTERFACE — lei para todo módulo em src/rules/

  Cada módulo expõe UMA função principal com a assinatura:

      def calcular_<processo>(talhao: dict) -> dict

  Entrada : dict gerado por pipeline_gold._preparar_talhao() a partir de
            uma linha do DataFrame Silver.

  Saída   : dict com exatamente estas três chaves:

      orientacao       (str)          descrição da ação recomendada
      valor_calculado  (float | None) dose ou índice calculado, quando aplicável
      regra_acionada   (str)          código que identifica qual condição disparou

  Campos ausentes / nulos → chamar sem_dado(campo), nunca levantar exceção.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import math
from typing import Any, Optional


# ── CONSTRUTORES DE RESULTADO ─────────────────────────────────────────────────

def sem_dado(campo: str) -> dict:
    """Campo obrigatório ausente ou nulo — retorna SEM_DADO padronizado."""
    return {
        "orientacao": "SEM_DADO",
        "valor_calculado": None,
        "regra_acionada": f"dado_ausente_{campo}",
    }


def nao_se_aplica(motivo: str) -> dict:
    """Regra não aplicável ao perfil deste talhão."""
    return {
        "orientacao": "NAO_SE_APLICA",
        "valor_calculado": None,
        "regra_acionada": motivo,
    }


def dado_suspeito(campo: str, valor, motivo: str) -> dict:
    """Valor presente mas fisicamente impossível ou fora do intervalo esperado."""
    return {
        "orientacao": f"DADO_SUSPEITO: {motivo}",
        "valor_calculado": None,
        "regra_acionada": f"outlier_{campo}",
    }


def resultado(orientacao: str, valor: Optional[float], regra: str) -> dict:
    """Constrói resultado válido; arredonda valor_calculado a 2 casas."""
    return {
        "orientacao": orientacao,
        "valor_calculado": round(valor, 2) if valor is not None else None,
        "regra_acionada": regra,
    }


# ── VALIDADORES ───────────────────────────────────────────────────────────────

def numerico(valor: Any) -> bool:
    """True quando valor é float/int finito (não None, não NaN, não inf)."""
    if valor is None:
        return False
    try:
        return math.isfinite(float(valor))
    except (TypeError, ValueError):
        return False


def texto(valor: Any) -> bool:
    """True quando valor é string não vazia."""
    return isinstance(valor, str) and bool(valor.strip())


# ── CONSTANTES AGRONÔMICAS ────────────────────────────────────────────────────
# Manter aqui para evitar repetição entre módulos e facilitar ajuste futuro.

# Valores de CATEGORIA na camada Silver
CATEGORIAS_CANA_PLANTA = {"Formação", "Cana Planta", "Muda"}
CATEGORIAS_CANA_SOCA   = {"Cana Soca"}


def classificar_textura(desc_ambiente: Any) -> Optional[str]:
    """
    Converte DESC_AMBIENTE (texto livre) em classe de textura padronizada.

    Returns
    -------
    "arenoso" | "medio" | "argiloso" | "muito_argiloso" | None
    """
    if not texto(desc_ambiente):
        return None
    desc = desc_ambiente.lower()
    if "muito argiloso" in desc:
        return "muito_argiloso"
    if "argiloso" in desc:
        return "argiloso"
    if "arenos" in desc:
        return "arenoso"
    if "médio" in desc or "medio" in desc or "franco" in desc:
        return "medio"
    return None


def ciclo_do_talhao(categoria: Any) -> Optional[str]:
    """
    Converte CATEGORIA Silver em 'cana_planta' ou 'cana_soca'.

    Returns
    -------
    "cana_planta" | "cana_soca" | None
    """
    if not texto(categoria):
        return None
    if categoria in CATEGORIAS_CANA_PLANTA:
        return "cana_planta"
    if categoria in CATEGORIAS_CANA_SOCA:
        return "cana_soca"
    return None
