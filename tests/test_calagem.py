"""tests/test_calagem.py — Testes unitários do módulo calagem.py"""

import pytest
from rules.calagem import calcular_necessidade_calagem, _calcular_dose, PH_ADEQUADO, PH_CRITICO, DOSE_MAX_T_HA
from helpers import assert_resultado_valido, assert_sem_dado, assert_dado_suspeito


# ── SEM_DADO — entradas inválidas ─────────────────────────────────────────────

def test_ph_nulo_retorna_sem_dado(talhao_dado_ausente):
    r = calcular_necessidade_calagem(talhao_dado_ausente)
    assert_sem_dado(r, "ph_solo")


def test_ph_texto_retorna_sem_dado(talhao_tipo_errado):
    r = calcular_necessidade_calagem(talhao_tipo_errado)
    assert_sem_dado(r, "ph_solo")


def test_ph_nan_retorna_sem_dado(talhao_nan):
    r = calcular_necessidade_calagem(talhao_nan)
    assert_sem_dado(r, "ph_solo")


def test_ctc_nulo_retorna_sem_dado():
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": None, "v_atual": 35.0})
    assert_sem_dado(r, "ctc")


def test_v_atual_nulo_retorna_sem_dado():
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": 80.0, "v_atual": None})
    assert_sem_dado(r, "v_atual")


# ── pH ADEQUADO ───────────────────────────────────────────────────────────────

def test_ph_adequado_sem_calagem(talhao_solo_neutro):
    r = calcular_necessidade_calagem(talhao_solo_neutro)
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "ph_adequado"
    assert r["valor_calculado"] == 0.0


def test_ph_exato_no_limite_adequado():
    r = calcular_necessidade_calagem({"ph_solo": PH_ADEQUADO, "ctc": 70.0, "v_atual": 65.0})
    assert r["regra_acionada"] == "ph_adequado"


# ── pH LEVEMENTE ÁCIDO ────────────────────────────────────────────────────────

def test_ph_levemente_acido_dose_preventiva():
    r = calcular_necessidade_calagem({
        "ph_solo": 5.7, "ctc": 80.0, "v_atual": 40.0, "v_alvo": 60.0
    })
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "ph_levemente_acido"
    assert r["valor_calculado"] > 0
    # Dose preventiva = metade da dose plena
    dose_plena = _calcular_dose(80.0, 40.0, 60.0)
    assert abs(r["valor_calculado"] - dose_plena * 0.5) < 0.01


# ── pH BAIXO — CANA-PLANTA ────────────────────────────────────────────────────

def test_ph_baixo_cana_planta_dose_plena(talhao_solo_acido):
    r = calcular_necessidade_calagem(talhao_solo_acido)
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "ph_baixo_cana_planta"
    assert r["valor_calculado"] > 0


def test_ph_baixo_cana_planta_maior_que_cana_soca():
    base = {"ph_solo": 4.8, "ctc": 80.0, "v_atual": 35.0, "v_alvo": 60.0}
    r_planta = calcular_necessidade_calagem({**base, "categoria": "Formação"})
    r_soca   = calcular_necessidade_calagem({**base, "categoria": "Cana Soca"})
    assert r_planta["valor_calculado"] > r_soca["valor_calculado"]


# ── pH BAIXO — CANA-SOCA ─────────────────────────────────────────────────────

def test_ph_baixo_cana_soca_dose_reduzida(talhao_cana_soca_velha):
    r = calcular_necessidade_calagem(talhao_cana_soca_velha)
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "ph_baixo_cana_soca"
    # Dose cana-soca = metade da dose plena
    dose_plena = _calcular_dose(
        talhao_cana_soca_velha["ctc"],
        talhao_cana_soca_velha["v_atual"],
        talhao_cana_soca_velha["v_alvo"],
    )
    assert abs(r["valor_calculado"] - dose_plena * 0.5) < 0.01


# ── DOSE MÁXIMA ───────────────────────────────────────────────────────────────

def test_dose_nao_excede_maximo():
    r = calcular_necessidade_calagem({
        "ph_solo": 3.0, "ctc": 200.0, "v_atual": 5.0, "v_alvo": 80.0,
        "categoria": "Formação",
    })
    assert r["valor_calculado"] <= DOSE_MAX_T_HA


# ── CICLO INDEFINIDO ─────────────────────────────────────────────────────────

def test_ph_baixo_ciclo_indefinido():
    r = calcular_necessidade_calagem({
        "ph_solo": 4.5, "ctc": 80.0, "v_atual": 30.0, "v_alvo": 60.0,
        "categoria": None,
    })
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "ph_baixo_ciclo_indefinido"
    assert r["valor_calculado"] > 0


# ── OUTLIERS ─────────────────────────────────────────────────────────────────

def test_ph_negativo_e_outlier():
    r = calcular_necessidade_calagem({"ph_solo": -1.0, "ctc": 80.0, "v_atual": 35.0})
    assert_dado_suspeito(r, "ph_solo")


def test_ph_acima_de_14_e_outlier():
    r = calcular_necessidade_calagem({"ph_solo": 14.1, "ctc": 80.0, "v_atual": 35.0})
    assert_dado_suspeito(r, "ph_solo")


def test_ph_exatamente_zero_tratado_pelas_regras():
    """pH=0 é o limite inferior físico — as regras recomendam calagem urgente (não é outlier)."""
    r = calcular_necessidade_calagem({"ph_solo": 0.0, "ctc": 80.0, "v_atual": 35.0})
    assert_resultado_valido(r)
    assert r["orientacao"] != "DADO_SUSPEITO"
    assert r["valor_calculado"] > 0


def test_ph_exatamente_14_nao_e_outlier():
    """pH=14 é o limite máximo físico — válido (borda não deve ser outlier)."""
    r = calcular_necessidade_calagem({"ph_solo": 14.0, "ctc": 80.0, "v_atual": 35.0})
    assert r["orientacao"] != "DADO_SUSPEITO"


def test_ctc_negativa_e_outlier():
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": -10.0, "v_atual": 35.0})
    assert_dado_suspeito(r, "ctc")


def test_v_atual_negativa_e_outlier():
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": 80.0, "v_atual": -5.0})
    assert_dado_suspeito(r, "v_atual")


def test_v_atual_acima_de_100_e_outlier():
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": 80.0, "v_atual": 101.0})
    assert_dado_suspeito(r, "v_atual")


def test_v_atual_exatamente_100_nao_e_outlier():
    """V=100% é saturação total — matematicamente válido."""
    r = calcular_necessidade_calagem({"ph_solo": 4.8, "ctc": 80.0, "v_atual": 100.0})
    assert r["orientacao"] != "DADO_SUSPEITO"


@pytest.mark.parametrize("ph_outlier", [-0.001, 14.001, -100, 999])
def test_ph_fora_do_intervalo_fisico(ph_outlier):
    r = calcular_necessidade_calagem({"ph_solo": ph_outlier, "ctc": 80.0, "v_atual": 35.0})
    assert_dado_suspeito(r, "ph_solo")


# ── CONTRATO DE INTERFACE ─────────────────────────────────────────────────────

@pytest.mark.parametrize("talhao_fixture", [
    "talhao_solo_acido",
    "talhao_solo_neutro",
    "talhao_cana_soca_velha",
    "talhao_dado_ausente",
    "talhao_tipo_errado",
    "talhao_nan",
])
def test_nunca_levanta_excecao(talhao_fixture, request):
    talhao = request.getfixturevalue(talhao_fixture)
    r = calcular_necessidade_calagem(talhao)
    assert_resultado_valido(r)
