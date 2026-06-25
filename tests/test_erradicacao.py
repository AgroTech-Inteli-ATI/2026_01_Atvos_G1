"""tests/test_erradicacao.py — Testes unitários do módulo erradicacao.py"""

import pytest
from rules.erradicacao import (
    calcular_necessidade_erradicacao,
    CORTE_TARDIO, TCH_CRITICO, TCH_ALERTA, TCH_INVESTIGACAO,
    TCH_MAX_VALIDO, NO_CORTE_MAX_VALIDO,
)
from helpers import assert_resultado_valido, assert_sem_dado, assert_dado_suspeito


# ── SEM_DADO — entradas inválidas ─────────────────────────────────────────────

def test_tch_nulo_retorna_sem_dado(talhao_dado_ausente):
    r = calcular_necessidade_erradicacao(talhao_dado_ausente)
    assert_sem_dado(r, "tch_prod")


def test_tch_texto_retorna_sem_dado(talhao_tipo_errado):
    r = calcular_necessidade_erradicacao(talhao_tipo_errado)
    assert_sem_dado(r, "tch_prod")


def test_tch_nan_retorna_sem_dado(talhao_nan):
    r = calcular_necessidade_erradicacao(talhao_nan)
    assert_sem_dado(r, "tch_prod")


def test_no_corte_nulo_retorna_sem_dado():
    r = calcular_necessidade_erradicacao({"tch_prod": 60.0, "no_corte": None})
    assert_sem_dado(r, "no_corte")


# ── NAO_SE_APLICA ─────────────────────────────────────────────────────────────

def test_formacao_nao_se_aplica(talhao_formacao):
    r = calcular_necessidade_erradicacao(talhao_formacao)
    assert r["orientacao"] == "NAO_SE_APLICA"
    assert r["regra_acionada"] == "categoria_formacao_ou_muda"


def test_reforma_programada_nao_se_aplica(talhao_cana_soca_velha):
    t = {**talhao_cana_soca_velha, "reforma": "S"}
    r = calcular_necessidade_erradicacao(t)
    assert r["orientacao"] == "NAO_SE_APLICA"
    assert r["regra_acionada"] == "reforma_ja_programada"


# ── CANAVIAL TARDIO (NO_CORTE >= 5) ──────────────────────────────────────────

def test_tardio_tch_critico_recomendado():
    r = calcular_necessidade_erradicacao({
        "no_corte": 6, "tch_prod": 45.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "tardio_tch_critico"
    assert "RECOMENDADA" in r["orientacao"].upper()


def test_tardio_tch_alerta_avaliar():
    r = calcular_necessidade_erradicacao({
        "no_corte": 5, "tch_prod": 62.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "tardio_tch_alerta"


def test_tardio_tch_adequado_monitorar():
    r = calcular_necessidade_erradicacao({
        "no_corte": 7, "tch_prod": 80.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "tardio_tch_adequado"


def test_limite_exato_corte_tardio():
    """NO_CORTE exatamente igual a CORTE_TARDIO deve entrar na faixa tardio."""
    r = calcular_necessidade_erradicacao({
        "no_corte": CORTE_TARDIO, "tch_prod": 40.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert "tardio" in r["regra_acionada"]


def test_tch_exatamente_no_limite_critico():
    """TCH == TCH_CRITICO está na zona de alerta, não crítica."""
    r = calcular_necessidade_erradicacao({
        "no_corte": 6, "tch_prod": TCH_CRITICO, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "tardio_tch_alerta"


# ── CANAVIAL MÉDIO (3º ou 4º corte) ──────────────────────────────────────────

def test_medio_tch_investigar():
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": 35.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "medio_tch_investigar"


def test_medio_tch_monitorar():
    r = calcular_necessidade_erradicacao({
        "no_corte": 4, "tch_prod": 55.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "medio_tch_monitorar"


def test_medio_tch_adequado():
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": 75.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "medio_tch_adequado"


# ── CANAVIAL JOVEM (1º ou 2º corte) ──────────────────────────────────────────

def test_jovem_tch_investigar():
    r = calcular_necessidade_erradicacao({
        "no_corte": 1, "tch_prod": 30.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "jovem_tch_investigar"


def test_jovem_tch_adequado():
    r = calcular_necessidade_erradicacao({
        "no_corte": 2, "tch_prod": 80.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["regra_acionada"] == "jovem_tch_adequado"


# ── VALOR CALCULADO ───────────────────────────────────────────────────────────

def test_valor_calculado_e_tch_prod():
    """valor_calculado deve refletir o TCH_PROD para facilitar ranking."""
    tch = 47.3
    r = calcular_necessidade_erradicacao({
        "no_corte": 6, "tch_prod": tch, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["valor_calculado"] == tch


# ── OUTLIERS ─────────────────────────────────────────────────────────────────

def test_tch_negativo_e_outlier():
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": -1.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "tch_prod")


def test_tch_zero_tratado_como_falha_de_campo():
    """TCH=0 é uma falha real de campo — as regras o tratam normalmente (não é outlier)."""
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": 0.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_resultado_valido(r)
    assert r["orientacao"] != "DADO_SUSPEITO"
    # TCH=0 < TCH_INVESTIGACAO=40 → investigar
    assert r["regra_acionada"] == "medio_tch_investigar"


def test_tch_acima_do_maximo_fisico_e_outlier():
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": TCH_MAX_VALIDO + 1, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "tch_prod")


def test_no_corte_negativo_e_outlier():
    r = calcular_necessidade_erradicacao({
        "no_corte": -1, "tch_prod": 70.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "no_corte")


def test_no_corte_acima_do_maximo_e_outlier():
    r = calcular_necessidade_erradicacao({
        "no_corte": NO_CORTE_MAX_VALIDO + 1, "tch_prod": 60.0,
        "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "no_corte")


@pytest.mark.parametrize("tch_outlier", [-0.001, -100.0, TCH_MAX_VALIDO + 0.001, 9999.0])
def test_tch_fora_do_intervalo_fisico(tch_outlier):
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": tch_outlier, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "tch_prod")


@pytest.mark.parametrize("nc_outlier", [-1, -10, NO_CORTE_MAX_VALIDO + 1, 99])
def test_no_corte_fora_do_intervalo(nc_outlier):
    r = calcular_necessidade_erradicacao({
        "no_corte": nc_outlier, "tch_prod": 60.0, "categoria": "Cana Soca", "reforma": "N"
    })
    assert_dado_suspeito(r, "no_corte")


def test_tch_max_valido_exato_nao_e_outlier():
    """TCH exatamente no limite máximo não deve ser outlier."""
    r = calcular_necessidade_erradicacao({
        "no_corte": 3, "tch_prod": TCH_MAX_VALIDO, "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["orientacao"] != "DADO_SUSPEITO"


def test_no_corte_max_valido_exato_nao_e_outlier():
    """NO_CORTE=20 é o limite máximo — não deve ser outlier."""
    r = calcular_necessidade_erradicacao({
        "no_corte": NO_CORTE_MAX_VALIDO, "tch_prod": 55.0,
        "categoria": "Cana Soca", "reforma": "N"
    })
    assert r["orientacao"] != "DADO_SUSPEITO"


# ── CONTRATO DE INTERFACE ─────────────────────────────────────────────────────

@pytest.mark.parametrize("talhao_fixture", [
    "talhao_solo_acido",
    "talhao_solo_neutro",
    "talhao_cana_soca_velha",
    "talhao_dado_ausente",
    "talhao_tipo_errado",
    "talhao_nan",
    "talhao_formacao",
])
def test_nunca_levanta_excecao(talhao_fixture, request):
    talhao = request.getfixturevalue(talhao_fixture)
    r = calcular_necessidade_erradicacao(talhao)
    assert_resultado_valido(r)
