"""tests/test_insumos.py — Testes unitários do módulo insumos.py"""

import pytest
from rules.insumos import (
    calcular_dose_fosfatagem,
    calcular_dose_dessecacao,
    _DOSE_MAX_P_KG_HA,
    _INSUMO_FONE,
    _INSUMO_DESSEC,
)
from helpers import assert_resultado_valido, assert_sem_dado, assert_nao_se_aplica


# ── HELPERS ───────────────────────────────────────────────────────────────────

def assert_resultado_insumo(r: dict) -> None:
    """Verifica contrato estendido com campos de insumo."""
    assert_resultado_valido(r)
    assert "insumo" in r,     "Falta chave 'insumo'"
    assert "dose_kg_ha" in r, "Falta chave 'dose_kg_ha'"


# ══════════════════════════════════════════════════════════════════════════════
# calcular_dose_fosfatagem
# ══════════════════════════════════════════════════════════════════════════════

class TestDoseFosfatagem:

    # ── SEM_DADO ──────────────────────────────────────────────────────────────

    def test_tchan_nulo_retorna_sem_dado(self, talhao_dado_ausente):
        r = calcular_dose_fosfatagem(talhao_dado_ausente)
        assert r["orientacao"] == "SEM_DADO"
        assert r["insumo"] is None
        assert r["dose_kg_ha"] is None

    def test_tchan_texto_retorna_sem_dado(self, talhao_tipo_errado):
        r = calcular_dose_fosfatagem(talhao_tipo_errado)
        assert r["orientacao"] == "SEM_DADO"

    def test_tchan_nan_retorna_sem_dado(self, talhao_nan):
        r = calcular_dose_fosfatagem(talhao_nan)
        assert r["orientacao"] == "SEM_DADO"

    # ── DOSE VARIA COM TCH ────────────────────────────────────────────────────

    def test_dose_cresce_com_tch(self):
        base = {"desc_ambiente": "Argiloso"}
        r60 = calcular_dose_fosfatagem({**base, "tchan_estimado": 60.0})
        r80 = calcular_dose_fosfatagem({**base, "tchan_estimado": 80.0})
        assert r80["dose_kg_ha"] > r60["dose_kg_ha"], \
            "Dose deve ser proporcional à produtividade estimada"

    # ── DOSE VARIA COM TEXTURA ────────────────────────────────────────────────

    def test_argiloso_dose_maior_que_arenoso(self):
        base = {"tchan_estimado": 75.0}
        r_are = calcular_dose_fosfatagem({**base, "desc_ambiente": "Arenoso"})
        r_arg = calcular_dose_fosfatagem({**base, "desc_ambiente": "Argiloso"})
        assert r_arg["dose_kg_ha"] > r_are["dose_kg_ha"], \
            "Solo argiloso fixa mais P, exige dose maior"

    # ── DESCONTOS ORGÂNICOS ───────────────────────────────────────────────────

    def test_torta_reduz_dose(self):
        base = {"tchan_estimado": 70.0}
        r_sem = calcular_dose_fosfatagem({**base, "torta": "N", "vinhaca": "N"})
        r_com = calcular_dose_fosfatagem({**base, "torta": "S", "vinhaca": "N"})
        assert r_com["dose_kg_ha"] < r_sem["dose_kg_ha"]

    def test_vinhaca_reduz_dose(self):
        base = {"tchan_estimado": 70.0}
        r_sem = calcular_dose_fosfatagem({**base, "vinhaca": "N"})
        r_com = calcular_dose_fosfatagem({**base, "vinhaca": "S"})
        assert r_com["dose_kg_ha"] < r_sem["dose_kg_ha"]

    def test_torta_e_vinhaca_reduzem_mais_que_so_torta(self):
        base = {"tchan_estimado": 70.0}
        r_torta  = calcular_dose_fosfatagem({**base, "torta": "S", "vinhaca": "N"})
        r_ambos  = calcular_dose_fosfatagem({**base, "torta": "S", "vinhaca": "S"})
        assert r_ambos["dose_kg_ha"] < r_torta["dose_kg_ha"]

    # ── P DO SOLO REDUZ DOSE ──────────────────────────────────────────────────

    def test_p_alto_reduz_dose_em_relacao_a_p_muito_baixo(self):
        base = {"tchan_estimado": 70.0}
        r_pb = calcular_dose_fosfatagem({**base, "p_disponivel": 5.0})   # muito baixo
        r_pa = calcular_dose_fosfatagem({**base, "p_disponivel": 35.0})  # alto
        assert r_pa["dose_kg_ha"] < r_pb["dose_kg_ha"]

    # ── DOSE MÁXIMA ───────────────────────────────────────────────────────────

    def test_dose_limitada_ao_maximo(self):
        r = calcular_dose_fosfatagem({
            "tchan_estimado": 171.0, "desc_ambiente": "Muito Argiloso"
        })
        assert r["dose_kg_ha"] <= _DOSE_MAX_P_KG_HA

    # ── CAMPOS DE INSUMO ─────────────────────────────────────────────────────

    def test_insumo_preenchido(self, talhao_solo_acido):
        r = calcular_dose_fosfatagem(talhao_solo_acido)
        assert_resultado_insumo(r)
        assert r["insumo"] == _INSUMO_FONE
        assert r["dose_kg_ha"] == r["valor_calculado"]

    # ── CONTRATO ─────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("talhao_fixture", [
        "talhao_solo_acido", "talhao_dado_ausente",
        "talhao_tipo_errado", "talhao_nan",
    ])
    def test_nunca_levanta_excecao(self, talhao_fixture, request):
        talhao = request.getfixturevalue(talhao_fixture)
        r = calcular_dose_fosfatagem(talhao)
        assert_resultado_insumo(r)


# ══════════════════════════════════════════════════════════════════════════════
# calcular_dose_dessecacao
# ══════════════════════════════════════════════════════════════════════════════

class TestDoseDessecacao:

    # ── NAO_SE_APLICA ─────────────────────────────────────────────────────────

    def test_formacao_nao_se_aplica(self, talhao_formacao):
        r = calcular_dose_dessecacao(talhao_formacao)
        assert r["orientacao"] == "NAO_SE_APLICA"
        assert r["insumo"] is None

    def test_muda_nao_se_aplica(self):
        r = calcular_dose_dessecacao({"no_corte": 1, "categoria": "Muda"})
        assert r["orientacao"] == "NAO_SE_APLICA"

    def test_pousio_nao_se_aplica(self):
        r = calcular_dose_dessecacao({"no_corte": 3, "categoria": "Pousio"})
        assert r["orientacao"] == "NAO_SE_APLICA"

    # ── SEM_DADO ──────────────────────────────────────────────────────────────

    def test_no_corte_nulo_retorna_sem_dado(self):
        r = calcular_dose_dessecacao({"no_corte": None, "categoria": "Cana Soca"})
        assert_sem_dado(r, "no_corte")

    def test_no_corte_texto_retorna_sem_dado(self, talhao_tipo_errado):
        r = calcular_dose_dessecacao(talhao_tipo_errado)
        assert_sem_dado(r, "no_corte")

    # ── DOSE VARIA COM IDADE DO CANAVIAL ──────────────────────────────────────

    def test_dose_cresce_com_numero_de_corte(self):
        base = {"categoria": "Cana Soca", "reforma": "N"}
        r1 = calcular_dose_dessecacao({**base, "no_corte": 1})
        r4 = calcular_dose_dessecacao({**base, "no_corte": 4})
        r6 = calcular_dose_dessecacao({**base, "no_corte": 6})
        assert r1["valor_calculado"] < r4["valor_calculado"] < r6["valor_calculado"]

    # ── INFESTAÇÃO AJUSTA DOSE ────────────────────────────────────────────────

    def test_infestacao_alta_aumenta_dose(self):
        base = {"no_corte": 4, "categoria": "Cana Soca"}
        r_med = calcular_dose_dessecacao({**base, "infestacao": "media"})
        r_alt = calcular_dose_dessecacao({**base, "infestacao": "alta"})
        assert r_alt["valor_calculado"] > r_med["valor_calculado"]

    def test_infestacao_baixa_reduz_dose(self):
        base = {"no_corte": 4, "categoria": "Cana Soca"}
        r_med = calcular_dose_dessecacao({**base, "infestacao": "media"})
        r_bai = calcular_dose_dessecacao({**base, "infestacao": "baixa"})
        assert r_bai["valor_calculado"] < r_med["valor_calculado"]

    def test_infestacao_invalida_usa_proxy_corte(self):
        r = calcular_dose_dessecacao({
            "no_corte": 4, "categoria": "Cana Soca",
            "infestacao": "desconhecida"
        })
        assert_resultado_insumo(r)
        assert "proxy_corte" in r["regra_acionada"]

    # ── CAMPOS DE INSUMO ─────────────────────────────────────────────────────

    def test_dose_kg_ha_maior_que_litros(self, talhao_cana_soca_velha):
        r = calcular_dose_dessecacao(talhao_cana_soca_velha)
        assert_resultado_insumo(r)
        assert r["insumo"] == _INSUMO_DESSEC
        # kg/ha (produto comercial) > L/ha porque densidade > 1
        assert r["dose_kg_ha"] > r["valor_calculado"]

    def test_insumo_none_em_nao_se_aplica(self, talhao_formacao):
        r = calcular_dose_dessecacao(talhao_formacao)
        assert r["insumo"] is None
        assert r["dose_kg_ha"] is None

    # ── PRÉ-REFORMA ──────────────────────────────────────────────────────────

    def test_reforma_programada_inclui_pre_reforma(self):
        r = calcular_dose_dessecacao({
            "no_corte": 6, "categoria": "Cana Soca", "reforma": "S"
        })
        assert "pré-reforma" in r["orientacao"]

    # ── CONTRATO ─────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("talhao_fixture", [
        "talhao_cana_soca_velha", "talhao_formacao",
        "talhao_dado_ausente", "talhao_tipo_errado", "talhao_nan",
    ])
    def test_nunca_levanta_excecao(self, talhao_fixture, request):
        talhao = request.getfixturevalue(talhao_fixture)
        r = calcular_dose_dessecacao(talhao)
        assert_resultado_insumo(r)
