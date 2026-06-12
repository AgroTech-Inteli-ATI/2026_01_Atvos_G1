"""
src/rules/__init__.py
Motor de Regras Agronômicas — Camada Gold (Sprint 2)

Exporta todas as funções de regra para uso no pipeline_gold.py.
Cada função segue o contrato definido em _base.py:
  Entrada: dict com dados de um talhão (gerado por pipeline_gold._preparar_talhao)
  Saída  : dict {orientacao, valor_calculado, regra_acionada}
"""

from .calagem        import calcular_necessidade_calagem
from .gessagem       import calcular_necessidade_gessagem
from .fosfatagem     import calcular_necessidade_fosfatagem
from .erradicacao    import calcular_necessidade_erradicacao
from .janela_plantio import calcular_janela_plantio
from .insumos        import calcular_dose_fosfatagem, calcular_dose_dessecacao

# Mapeamento processo → função — usado pelo pipeline para iterar sobre todos
REGRAS = {
    "calagem":           calcular_necessidade_calagem,
    "gessagem":          calcular_necessidade_gessagem,
    "fosfatagem":        calcular_necessidade_fosfatagem,
    "erradicacao":       calcular_necessidade_erradicacao,
    "janela_plantio":    calcular_janela_plantio,
    "fosfatagem_insumo": calcular_dose_fosfatagem,
    "dessecacao":        calcular_dose_dessecacao,
}

__all__ = [
    "calcular_necessidade_calagem",
    "calcular_necessidade_gessagem",
    "calcular_necessidade_fosfatagem",
    "calcular_necessidade_erradicacao",
    "calcular_janela_plantio",
    "calcular_dose_fosfatagem",
    "calcular_dose_dessecacao",
    "REGRAS",
]
