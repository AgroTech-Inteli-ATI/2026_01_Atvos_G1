"""tests/helpers.py — Funções de asserção reutilizáveis (não fixtures)."""
import math


def assert_resultado_valido(r: dict) -> None:
    """Verifica que um resultado respeita o contrato de interface dos módulos."""
    assert isinstance(r, dict), f"Resultado deve ser dict, got {type(r)}"
    assert "orientacao" in r,      "Falta chave 'orientacao'"
    assert "valor_calculado" in r, "Falta chave 'valor_calculado'"
    assert "regra_acionada" in r,  "Falta chave 'regra_acionada'"
    assert isinstance(r["orientacao"], str),     "orientacao deve ser str"
    assert isinstance(r["regra_acionada"], str), "regra_acionada deve ser str"
    if r["valor_calculado"] is not None:
        assert isinstance(r["valor_calculado"], (int, float)), \
            "valor_calculado deve ser numérico ou None"
        assert not math.isnan(r["valor_calculado"]), "valor_calculado não pode ser NaN"


def assert_sem_dado(r: dict, campo: str) -> None:
    """Verifica resposta SEM_DADO para campo obrigatório ausente."""
    assert_resultado_valido(r)
    assert r["orientacao"] == "SEM_DADO", \
        f"Esperado SEM_DADO, got '{r['orientacao']}'"
    assert r["valor_calculado"] is None, \
        "valor_calculado deve ser None em SEM_DADO"
    assert f"dado_ausente_{campo}" in r["regra_acionada"], \
        f"regra_acionada '{r['regra_acionada']}' não indica campo '{campo}'"


def assert_nao_se_aplica(r: dict) -> None:
    """Verifica resposta NAO_SE_APLICA."""
    assert_resultado_valido(r)
    assert r["orientacao"] == "NAO_SE_APLICA", \
        f"Esperado NAO_SE_APLICA, got '{r['orientacao']}'"


def assert_dado_suspeito(r: dict, campo: str) -> None:
    """Verifica resposta DADO_SUSPEITO para valor fora do intervalo físico."""
    assert_resultado_valido(r)
    assert r["orientacao"].startswith("DADO_SUSPEITO"), \
        f"Esperado DADO_SUSPEITO, got '{r['orientacao']}'"
    assert r["valor_calculado"] is None, \
        "valor_calculado deve ser None em DADO_SUSPEITO"
    assert f"outlier_{campo}" in r["regra_acionada"], \
        f"regra_acionada '{r['regra_acionada']}' não indica outlier de '{campo}'"
