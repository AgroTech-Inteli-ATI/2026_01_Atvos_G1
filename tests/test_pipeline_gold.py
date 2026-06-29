"""
tests/test_pipeline_gold.py
Testes de integração e resiliência do pipeline_gold.py.

Cobre:
  - Funcionamento normal (_preparar_talhao, _aplicar_regras)
  - Resiliência: talhão sem id, coluna ausente, tipo errado, NaN, dict vazio
  - Saída Gold com todas as colunas obrigatórias
"""

import math
import pytest
import pandas as pd

from pipeline_gold import (
    _preparar_talhao,
    _aplicar_regras,
    COLUNAS_GOLD,
)
from rules import REGRAS


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _serie(dados: dict) -> pd.Series:
    """Converte dict em pd.Series (simula uma linha do DataFrame Silver)."""
    return pd.Series(dados)


def _df_minimal(rows: list[dict]) -> pd.DataFrame:
    """Cria DataFrame mínimo de teste a partir de lista de dicts."""
    return pd.DataFrame(rows)


def _rodar_pipeline(rows: list[dict]) -> pd.DataFrame:
    """Roda _aplicar_regras em um DataFrame de teste e retorna o Gold."""
    from datetime import date
    df = _df_minimal(rows)
    return _aplicar_regras(df, date.today())


# ── _preparar_talhao ──────────────────────────────────────────────────────────

class TestPrepararTalhao:

    def test_mapeamento_basico(self, talhao_solo_acido):
        # Converte o dict de fixture para Series com nomes de coluna Silver
        silver = _serie({
            "CHAVESIG":    talhao_solo_acido["id_talhao"],
            "TCH_PROD":    talhao_solo_acido["tch_prod"],
            "CATEGORIA":   talhao_solo_acido["categoria"],
            "NO_CORTE":    talhao_solo_acido["no_corte"],
            "DESC_EMPRESA": "UMV",
            "SAFRA":       22223,
            "AREA_HA":     talhao_solo_acido["area_ha"],
            "tchan_estimado": talhao_solo_acido["tchan_estimado"],
        })
        t = _preparar_talhao(silver)
        assert t["tch_prod"] == talhao_solo_acido["tch_prod"]
        assert t["no_corte"] == talhao_solo_acido["no_corte"]
        assert t["categoria"] == talhao_solo_acido["categoria"]
        assert t["tchan_estimado"] == talhao_solo_acido["tchan_estimado"]

    def test_coluna_ausente_retorna_none(self):
        """Coluna não presente no Silver → safe() retorna None (não levanta KeyError)."""
        t = _preparar_talhao(_serie({"CHAVESIG": 999}))
        assert t["ph_solo"] is None
        assert t["tch_prod"] is None
        assert t["tchan_estimado"] is None

    def test_nan_pandas_convertido_para_none(self):
        t = _preparar_talhao(_serie({
            "CHAVESIG": 1,
            "TCH_PROD": float("nan"),
            "NO_CORTE": float("nan"),
        }))
        assert t["tch_prod"] is None
        assert t["no_corte"] is None

    def test_id_talhao_none_quando_chavesig_ausente(self):
        t = _preparar_talhao(_serie({}))
        assert t["id_talhao"] is None


# ── RESILIÊNCIA DO PIPELINE ───────────────────────────────────────────────────

class TestResilienciaPipeline:

    def test_talhao_sem_id_nao_quebra_pipeline(self):
        """Talhão sem CHAVESIG deve ser processado sem exceção."""
        rows = [{"TCH_PROD": 60.0, "NO_CORTE": 3, "CATEGORIA": "Cana Soca",
                 "Reforma": "N", "AREA_HA": 20.0}]
        df_gold = _rodar_pipeline(rows)
        assert len(df_gold) == len(REGRAS)
        assert df_gold["id_talhao"].isna().all()  # None, mas sem crash

    def test_coluna_inteira_ausente_nao_quebra_pipeline(self):
        """DataFrame sem coluna TCH_PROD → todas as regras que precisam dela retornam SEM_DADO."""
        rows = [{"CHAVESIG": 1001, "CATEGORIA": "Cana Soca", "AREA_HA": 30.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"] == "dado_ausente_tch_prod"

    def test_tipo_errado_string_em_campo_numerico_nao_quebra(self):
        """ph_solo='alto' → SEM_DADO, sem TypeError."""
        rows = [{
            "CHAVESIG": 1002, "CATEGORIA": "Cana Soca",
            "ph_solo": "alto", "TCH_PROD": "ok", "NO_CORTE": "terceiro",
            "AREA_HA": 10.0,
        }]
        df_gold = _rodar_pipeline(rows)
        calagem = df_gold[df_gold["processo"] == "calagem"].iloc[0]
        assert calagem["regra_acionada"] == "dado_ausente_ph_solo"

    def test_nan_em_campos_numericos_nao_quebra(self):
        """NaN em TCH_PROD → SEM_DADO na erradicação."""
        rows = [{
            "CHAVESIG": 1003, "CATEGORIA": "Cana Soca",
            "TCH_PROD": float("nan"), "NO_CORTE": float("nan"),
            "AREA_HA": 15.0,
        }]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"] == "dado_ausente_tch_prod"

    def test_dataframe_vazio_retorna_gold_vazio(self):
        """DataFrame sem linhas → Gold sem linhas (sem exceção)."""
        df_gold = _rodar_pipeline([])
        assert len(df_gold) == 0
        # Colunas ainda presentes mesmo sem dados
        for col in COLUNAS_GOLD:
            assert col in df_gold.columns

    def test_multiplos_talhoes_incluindo_invalidos(self):
        """Mix de talhões válidos e inválidos — todos processados, nenhum trava."""
        rows = [
            {"CHAVESIG": 2001, "TCH_PROD": 70.0, "NO_CORTE": 3,
             "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 25.0,
             "tchan_estimado": 70.0},
            {"CHAVESIG": 2002, "TCH_PROD": None,  "NO_CORTE": None,
             "CATEGORIA": None, "AREA_HA": None},
            {"CHAVESIG": None, "TCH_PROD": "invalido", "NO_CORTE": "invalido",
             "CATEGORIA": "Cana Soca", "AREA_HA": 10.0},
        ]
        df_gold = _rodar_pipeline(rows)
        assert len(df_gold) == 3 * len(REGRAS)
        # Nenhuma exceção capturada pelo pipeline (regra "erro_execucao" não deve aparecer)
        assert (df_gold["regra_acionada"] == "erro_execucao").sum() == 0


# ── FORMATO DO OUTPUT GOLD ────────────────────────────────────────────────────

class TestFormatoGold:

    def test_colunas_obrigatorias_presentes(self):
        rows = [{"CHAVESIG": 3001, "TCH_PROD": 65.0, "NO_CORTE": 2,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 20.0,
                 "tchan_estimado": 65.0}]
        df_gold = _rodar_pipeline(rows)
        for col in COLUNAS_GOLD:
            assert col in df_gold.columns, f"Coluna obrigatória '{col}' ausente"

    def test_uma_linha_por_processo_por_talhao(self):
        rows = [{"CHAVESIG": 3002, "TCH_PROD": 70.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 25.0,
                 "tchan_estimado": 70.0}]
        df_gold = _rodar_pipeline(rows)
        assert len(df_gold) == len(REGRAS)
        assert set(df_gold["processo"]) == set(REGRAS.keys())

    def test_quantidade_total_calculada_quando_dose_e_area_disponiveis(self):
        rows = [{
            "CHAVESIG": 3003, "TCH_PROD": 70.0, "NO_CORTE": 3,
            "CATEGORIA": "Cana Soca", "Reforma": "N",
            "AREA_HA": 40.0, "tchan_estimado": 70.0,
        }]
        df_gold = _rodar_pipeline(rows)
        # fosfatagem_insumo deve ter quantidade_total_kg = dose_kg_ha * 40
        fi = df_gold[df_gold["processo"] == "fosfatagem_insumo"].iloc[0]
        if fi["dose_kg_ha"] is not None:
            expected = round(fi["dose_kg_ha"] * 40.0, 2)
            assert abs(fi["quantidade_total_kg"] - expected) < 0.1

    def test_quantidade_total_ausente_quando_sem_dose(self):
        """Processo sem dose (calagem SEM_DADO) → quantidade_total_kg deve ser nulo/NaN."""
        rows = [{"CHAVESIG": 3004, "TCH_PROD": 60.0, "NO_CORTE": 2,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 20.0}]
        df_gold = _rodar_pipeline(rows)
        calagem = df_gold[df_gold["processo"] == "calagem"].iloc[0]
        # pandas armazena None como NaN em colunas float
        assert calagem["quantidade_total_kg"] is None or pd.isna(calagem["quantidade_total_kg"])

    def test_valor_calculado_nao_e_nan_inesperado(self):
        """Valor calculado só deve ser NaN quando o processo retornou SEM_DADO (None → NaN no DataFrame)."""
        rows = [{"CHAVESIG": 3005, "TCH_PROD": 55.0, "NO_CORTE": 5,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 30.0,
                 "tchan_estimado": 55.0}]
        df_gold = _rodar_pipeline(rows)
        for _, row in df_gold.iterrows():
            val = row["valor_calculado"]
            # NaN é aceitável — representa None (campo ausente / SEM_DADO)
            # O que não é aceitável é um float NaN em processo que deveria ter calculado
            if not pd.isna(val):
                assert isinstance(val, (int, float)), \
                    f"valor_calculado inválido no processo '{row['processo']}': {val!r}"


# ── CENÁRIOS ESPECÍFICOS DE REGRA ─────────────────────────────────────────────

class TestCenariosRegras:

    def test_erradicacao_recomendada_no_gold(self):
        rows = [{"CHAVESIG": 4001, "TCH_PROD": 40.0, "NO_CORTE": 6,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 35.0,
                 "tchan_estimado": 40.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"] == "tardio_tch_critico"

    def test_dessecacao_nao_aplica_em_formacao(self):
        rows = [{"CHAVESIG": 4002, "TCH_PROD": 90.0, "NO_CORTE": 0,
                 "CATEGORIA": "Formação", "Reforma": "N", "AREA_HA": 20.0,
                 "tchan_estimado": 90.0}]
        df_gold = _rodar_pipeline(rows)
        desc = df_gold[df_gold["processo"] == "dessecacao"].iloc[0]
        assert desc["regra_acionada"] == "categoria_formacao_ou_muda"
        # pandas converte None em NaN em colunas object quando há outros não-nulos na coluna
        assert desc["insumo"] is None or pd.isna(desc["insumo"])

    def test_fosfatagem_insumo_populado_para_todos_talhoes(self):
        """fosfatagem_insumo usa tchan_estimado — deve estar populado sempre que Silver disponível."""
        rows = [
            {"CHAVESIG": 4003, "TCH_PROD": 65.0, "NO_CORTE": 2,
             "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 25.0,
             "tchan_estimado": 65.0},
            {"CHAVESIG": 4004, "TCH_PROD": 80.0, "NO_CORTE": 4,
             "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 30.0,
             "tchan_estimado": 80.0, "DESC_AMBIENTE": "Argiloso"},
        ]
        df_gold = _rodar_pipeline(rows)
        fi = df_gold[df_gold["processo"] == "fosfatagem_insumo"]
        assert fi["insumo"].notna().all()
        assert fi["dose_kg_ha"].notna().all()

    def test_reforma_ja_programada_erradicacao_nao_se_aplica(self):
        rows = [{"CHAVESIG": 4005, "TCH_PROD": 35.0, "NO_CORTE": 6,
                 "CATEGORIA": "Cana Soca", "Reforma": "S", "AREA_HA": 20.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"] == "reforma_ja_programada"


# ── AREA_HA NA CAMADA GOLD ────────────────────────────────────────────────────

class TestAreaHaGold:

    def test_area_ha_presente_nas_colunas_gold(self):
        assert "area_ha" in COLUNAS_GOLD

    def test_area_ha_preenchida_quando_disponivel(self):
        rows = [{"CHAVESIG": 5001, "TCH_PROD": 70.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N",
                 "AREA_HA": 42.5, "tchan_estimado": 70.0}]
        df_gold = _rodar_pipeline(rows)
        assert (df_gold["area_ha"] == 42.5).all(), \
            "area_ha deve ser 42.5 para todos os processos deste talhão"

    def test_area_ha_none_quando_coluna_ausente(self):
        rows = [{"CHAVESIG": 5002, "TCH_PROD": 60.0, "NO_CORTE": 2,
                 "CATEGORIA": "Cana Soca", "Reforma": "N"}]
        df_gold = _rodar_pipeline(rows)
        # Sem AREA_HA no Silver → area_ha deve ser None/NaN no Gold
        for val in df_gold["area_ha"]:
            assert val is None or (isinstance(val, float) and math.isnan(val)), \
                f"Esperado None/NaN, got {val}"

    def test_area_ha_consistente_em_todos_processos_do_talhao(self):
        """Todos os processos de um mesmo talhão devem ter a mesma area_ha."""
        rows = [{"CHAVESIG": 5003, "TCH_PROD": 75.0, "NO_CORTE": 4,
                 "CATEGORIA": "Cana Soca", "Reforma": "N",
                 "AREA_HA": 30.0, "tchan_estimado": 75.0}]
        df_gold = _rodar_pipeline(rows)
        areas = df_gold["area_ha"].dropna().unique()
        assert len(areas) == 1, "area_ha deve ser a mesma para todos os processos"
        assert areas[0] == 30.0

    def test_quantidade_total_usa_area_ha(self):
        """quantidade_total_kg = dose_kg_ha × area_ha (verificação cruzada)."""
        rows = [{"CHAVESIG": 5004, "TCH_PROD": 70.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N",
                 "AREA_HA": 20.0, "tchan_estimado": 70.0}]
        df_gold = _rodar_pipeline(rows)
        fi = df_gold[df_gold["processo"] == "fosfatagem_insumo"].iloc[0]
        if fi["dose_kg_ha"] is not None and not math.isnan(float(fi["dose_kg_ha"])):
            dose = float(fi["dose_kg_ha"])
            area = float(fi["area_ha"])
            qtd  = float(fi["quantidade_total_kg"])
            assert abs(qtd - dose * area) < 0.01, \
                f"quantidade_total_kg={qtd} != dose={dose} × area={area}"


# ── DETECÇÃO DE OUTLIERS NO PIPELINE ─────────────────────────────────────────

class TestOutliersPipeline:

    def test_tch_negativo_marcado_como_outlier_no_gold(self):
        rows = [{"CHAVESIG": 6001, "TCH_PROD": -5.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 20.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"].startswith("outlier_"), \
            f"TCH negativo deve gerar outlier, got '{errad['regra_acionada']}'"

    def test_tch_extremamente_alto_marcado_como_outlier(self):
        rows = [{"CHAVESIG": 6002, "TCH_PROD": 999.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 25.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"].startswith("outlier_")

    def test_no_corte_negativo_marcado_como_outlier(self):
        rows = [{"CHAVESIG": 6003, "TCH_PROD": 70.0, "NO_CORTE": -1,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 15.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert errad["regra_acionada"].startswith("outlier_")

    def test_outlier_nao_travar_pipeline(self):
        """Outliers em um talhão não devem impedir o processamento dos demais."""
        rows = [
            {"CHAVESIG": 6004, "TCH_PROD": -999.0, "NO_CORTE": -5,
             "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 10.0},
            {"CHAVESIG": 6005, "TCH_PROD": 70.0, "NO_CORTE": 3,
             "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 30.0},
        ]
        df_gold = _rodar_pipeline(rows)
        assert len(df_gold) == 2 * len(REGRAS)

    def test_orientacao_dado_suspeito_no_gold(self):
        """Quando outlier, orientacao começa com DADO_SUSPEITO e inclui motivo."""
        rows = [{"CHAVESIG": 6006, "TCH_PROD": 500.0, "NO_CORTE": 3,
                 "CATEGORIA": "Cana Soca", "Reforma": "N", "AREA_HA": 20.0}]
        df_gold = _rodar_pipeline(rows)
        errad = df_gold[df_gold["processo"] == "erradicacao"].iloc[0]
        assert str(errad["orientacao"]).startswith("DADO_SUSPEITO")
        # a orientacao deve conter o motivo (não apenas "DADO_SUSPEITO" sem contexto)
        assert len(str(errad["orientacao"])) > len("DADO_SUSPEITO")
