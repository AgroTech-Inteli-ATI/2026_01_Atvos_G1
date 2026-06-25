"""
tests/conftest.py — Fixtures reutilizáveis para todos os módulos de teste.

Cada fixture representa um perfil agrícola típico que cobre
um caminho diferente na árvore de decisão das regras.
"""

import datetime
import pytest


# ── FIXTURES DE TALHÃO ────────────────────────────────────────────────────────

@pytest.fixture
def talhao_solo_acido():
    """Solo ácido com análise completa — cana-planta. Dispara calagem incorporada."""
    return {
        "id_talhao": "T001",
        "ph_solo":   4.8,
        "ctc":       80.0,
        "v_atual":   35.0,
        "v_alvo":    60.0,
        "categoria": "Formação",
        "desc_ambiente": "Argiloso",
        "saturacao_al":  25.0,
        "p_disponivel":  6.0,
        "tchan_estimado": 75.0,
        "no_corte":  1,
        "tch_prod":  75.0,
        "reforma":   "N",
        "area_ha":   50.0,
        "torta":     "N",
        "vinhaca":   "N",
        "_area_ha":  50.0,
    }


@pytest.fixture
def talhao_solo_neutro():
    """Solo com pH adequado — nenhuma calagem necessária."""
    return {
        "id_talhao": "T002",
        "ph_solo":   6.5,
        "ctc":       70.0,
        "v_atual":   65.0,
        "v_alvo":    60.0,
        "categoria": "Cana Soca",
        "desc_ambiente": "Médio",
        "saturacao_al":  10.0,
        "p_disponivel":  35.0,
        "tchan_estimado": 80.0,
        "no_corte":  3,
        "tch_prod":  80.0,
        "reforma":   "N",
        "area_ha":   30.0,
        "torta":     "N",
        "vinhaca":   "S",
        "_area_ha":  30.0,
    }


@pytest.fixture
def talhao_cana_soca_velha():
    """Cana-soca tardio (6º corte) com baixa produtividade. Erradicação recomendada."""
    return {
        "id_talhao": "T003",
        "ph_solo":   5.1,
        "ctc":       60.0,
        "v_atual":   40.0,
        "v_alvo":    60.0,
        "categoria": "Cana Soca",
        "desc_ambiente": "Argiloso",
        "saturacao_al":  30.0,
        "p_disponivel":  5.0,
        "tchan_estimado": 45.0,
        "no_corte":  6,
        "tch_prod":  45.0,
        "reforma":   "N",
        "area_ha":   40.0,
        "torta":     "N",
        "vinhaca":   "N",
        "_area_ha":  40.0,
    }


@pytest.fixture
def talhao_dado_ausente():
    """Talhão com todos os campos opcionais ausentes (None). Simula Silver incompleta."""
    return {
        "id_talhao":     "T004",
        "ph_solo":       None,
        "ctc":           None,
        "v_atual":       None,
        "v_alvo":        None,
        "categoria":     None,
        "desc_ambiente": None,
        "saturacao_al":  None,
        "p_disponivel":  None,
        "tchan_estimado": None,
        "no_corte":      None,
        "tch_prod":      None,
        "reforma":       None,
        "area_ha":       None,
        "torta":         None,
        "vinhaca":       None,
        "_area_ha":      None,
    }


@pytest.fixture
def talhao_tipo_errado():
    """Campos numéricos preenchidos com strings — simula dado corrompido."""
    return {
        "id_talhao":     "T005",
        "ph_solo":       "alto",
        "ctc":           "desconhecido",
        "v_atual":       "?",
        "v_alvo":        "60%",
        "categoria":     "Cana Soca",
        "desc_ambiente": "Argiloso",
        "saturacao_al":  "alto",
        "p_disponivel":  "baixo",
        "tchan_estimado": "bom",
        "no_corte":      "terceiro",
        "tch_prod":      "ok",
        "reforma":       "N",
        "area_ha":       None,
        "torta":         "N",
        "vinhaca":       "N",
        "_area_ha":      None,
    }


@pytest.fixture
def talhao_sem_id():
    """Talhão sem id — simula linha corrompida no Silver."""
    return {
        "id_talhao":     None,
        "ph_solo":       4.5,
        "ctc":           75.0,
        "v_atual":       38.0,
        "categoria":     "Cana Soca",
        "desc_ambiente": "Argiloso",
        "tchan_estimado": 65.0,
        "no_corte":      4,
        "tch_prod":      65.0,
        "reforma":       "N",
        "_area_ha":      25.0,
    }


@pytest.fixture
def talhao_formacao():
    """Talhão em formação (cana-planta) dentro da janela de plantio."""
    return {
        "id_talhao":     "T006",
        "ph_solo":       5.0,
        "ctc":           85.0,
        "v_atual":       30.0,
        "v_alvo":        60.0,
        "categoria":     "Formação",
        "desc_ambiente": "Arenoso",
        "saturacao_al":  None,
        "p_disponivel":  7.0,
        "tchan_estimado": 90.0,
        "no_corte":      0,
        "tch_prod":      90.0,
        "reforma":       "N",
        "man_hipot":     "Precoce",
        "tp_reforma":    "Convencional",
        "data_plantio":  datetime.date(2025, 5, 10),
        "area_ha":       20.0,
        "torta":         "S",
        "vinhaca":       "N",
        "_area_ha":      20.0,
    }


@pytest.fixture
def talhao_nan():
    """Talhão com valores NaN explícitos (comportamento pandas para campos vazios)."""
    return {
        "id_talhao":     "T007",
        "ph_solo":       float("nan"),
        "ctc":           float("nan"),
        "v_atual":       float("nan"),
        "categoria":     "Cana Soca",
        "desc_ambiente": float("nan"),
        "tchan_estimado": float("nan"),
        "no_corte":      float("nan"),
        "tch_prod":      float("nan"),
        "reforma":       "N",
        "_area_ha":      float("nan"),
    }
