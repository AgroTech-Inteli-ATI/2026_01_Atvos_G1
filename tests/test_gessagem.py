"""tests/test_gessagem.py — Testes unitários do módulo gessagem.py"""

import pytest
from rules.gessagem import calcular_necessidade_gessagem, SAT_AL_CRITICA, DOSE_MAX_T_HA
from helpers import assert_resultado_valido, assert_sem_dado, assert_nao_se_aplica


# ── SEM_DADO — sem dado algum ─────────────────────────────────────────────────

def test_sem_qualquer_dado_retorna_sem_dado(talhao_dado_ausente):
    r = calcular_necessidade_gessagem(talhao_dado_ausente)
    assert_sem_dado(r, "saturacao_al_e_desc_ambiente")


def test_dict_vazio_retorna_sem_dado():
    r = calcular_necessidade_gessagem({})
    assert r["orientacao"] == "SEM_DADO"


# ── CAMINHO COM ANÁLISE DE AL³⁺ ───────────────────────────────────────────────

def test_al_alto_com_ctc_retorna_dose(talhao_solo_acido):
    r = calcular_necessidade_gessagem(talhao_solo_acido)
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "al_alto_gessagem_indicada"
    assert r["valor_calculado"] > 0


def test_al_alto_sem_ctc_indica_sem_dose():
    r = calcular_necessidade_gessagem({
        "saturacao_al": 30.0, "ctc": None, "desc_ambiente": "Argiloso"
    })
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "al_alto_ctc_ausente"
    assert r["valor_calculado"] is None


def test_al_dentro_limite_sem_necessidade(talhao_solo_neutro):
    r = calcular_necessidade_gessagem(talhao_solo_neutro)
    assert_resultado_valido(r)
    assert r["regra_acionada"] == "al_dentro_limite"
    assert r["valor_calculado"] == 0.0


def test_al_exato_no_limite():
    r = calcular_necessidade_gessagem({"saturacao_al": SAT_AL_CRITICA, "ctc": 60.0})
    assert r["regra_acionada"] == "al_dentro_limite"


def test_dose_aumenta_com_textura_mais_argilosa():
    # CTC=15 mantém todas as doses abaixo do DOSE_MAX (4 t/ha) para comparação válida
    base = {"saturacao_al": 30.0, "ctc": 15.0}
    r_are = calcular_necessidade_gessagem({**base, "desc_ambiente": "Arenoso"})
    r_arg = calcular_necessidade_gessagem({**base, "desc_ambiente": "Argiloso"})
    r_mar = calcular_necessidade_gessagem({**base, "desc_ambiente": "Muito Argiloso"})
    assert r_are["valor_calculado"] < r_arg["valor_calculado"]
    assert r_arg["valor_calculado"] < r_mar["valor_calculado"]


def test_dose_nao_excede_maximo():
    r = calcular_necessidade_gessagem({
        "saturacao_al": 80.0, "ctc": 500.0, "desc_ambiente": "Muito Argiloso"
    })
    assert r["valor_calculado"] <= DOSE_MAX_T_HA


# ── CAMINHO APENAS COM TEXTURA (sem análise de Al³⁺) ─────────────────────────

@pytest.mark.parametrize("textura,regra_esperada", [
    ("Arenoso",        "textura_arenoso_sem_analise_al"),
    ("Argiloso",       "textura_argiloso_sem_analise_al"),
    ("Muito Argiloso", "textura_muito_argiloso_sem_analise_al"),
])
def test_apenas_textura_orienta_sem_dose(textura, regra_esperada):
    r = calcular_necessidade_gessagem({"desc_ambiente": textura})
    assert_resultado_valido(r)
    assert r["regra_acionada"] == regra_esperada
    assert r["valor_calculado"] is None


# ── TIPOS INVÁLIDOS ───────────────────────────────────────────────────────────

def test_al_texto_invalido_cai_para_textura():
    r = calcular_necessidade_gessagem({"saturacao_al": "alto", "desc_ambiente": "Argiloso"})
    assert_resultado_valido(r)
    # saturacao_al inválido → ignora → usa textura
    assert "textura_argiloso" in r["regra_acionada"]


def test_al_nan_cai_para_textura(talhao_nan):
    r = calcular_necessidade_gessagem({**talhao_nan, "desc_ambiente": "Argiloso"})
    assert_resultado_valido(r)
    assert "textura_argiloso" in r["regra_acionada"]


# ── CONTRATO DE INTERFACE ─────────────────────────────────────────────────────

@pytest.mark.parametrize("talhao_fixture", [
    "talhao_solo_acido",
    "talhao_solo_neutro",
    "talhao_dado_ausente",
    "talhao_tipo_errado",
    "talhao_nan",
])
def test_nunca_levanta_excecao(talhao_fixture, request):
    talhao = request.getfixturevalue(talhao_fixture)
    r = calcular_necessidade_gessagem(talhao)
    assert_resultado_valido(r)
