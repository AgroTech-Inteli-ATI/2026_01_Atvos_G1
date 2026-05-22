"""
Motor de Regras Agronômicas — Sprint 2
=======================================
Exporta todas as funções de regra para facilitar imports no pipeline.

Uso:
    from src.rules import calcular_calagem, calcular_gessagem, \
        calcular_fosfatagem, calcular_erradicacao, calcular_janela_plantio

    resultado = calcular_calagem(row_dict)
"""

from src.rules.calagem import calcular_calagem
from src.rules.gessagem import calcular_gessagem
from src.rules.fosfatagem import calcular_fosfatagem
from src.rules.erradicacao import calcular_erradicacao
from src.rules.janela_plantio import calcular_janela_plantio

__all__ = [
    "calcular_calagem",
    "calcular_gessagem",
    "calcular_fosfatagem",
    "calcular_erradicacao",
    "calcular_janela_plantio",
]
