"""
src/pipeline_gold.py
Pipeline Silver → Gold: aplica o motor de regras e gera orientações por talhão.

Uso:
    python src/pipeline_gold.py              # processa todos os arquivos Silver
    python src/pipeline_gold.py --dry-run    # mostra o que processaria, sem salvar
"""

import os
import sys
import glob
import pandas as pd
from datetime import datetime, date

from rules import REGRAS

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

SILVER_PATH      = "data/processed"
GOLD_PATH        = "data/gold"
SILVER_COM_SAFRA = os.path.join(SILVER_PATH, "silver_com_safra.parquet")

# Colunas obrigatórias no output Gold
COLUNAS_GOLD = [
    "id_talhao",
    "chave",
    "unidade",
    "safra",
    "processo",
    "orientacao",
    "valor_calculado",
    "regra_acionada",
    "insumo",
    "dose_kg_ha",
    "quantidade_total_kg",
    "data_geracao",
]


# ── MAPEAMENTO SILVER → INPUT DAS REGRAS ──────────────────────────────────────

def _preparar_talhao(row: pd.Series) -> dict:
    """
    Converte uma linha do DataFrame Silver no dicionário de entrada das regras.

    Campos de análise de solo (ph_solo, ctc, etc.) ainda não existem na Silver —
    ficam como None e dispararão SEM_DADO nas regras que os exigem.
    Quando esses dados chegarem, adicionar o mapeamento aqui.

    Parameters
    ----------
    row : pd.Series
        Uma linha do DataFrame Silver (Inventario_atvos).

    Returns
    -------
    dict com todos os campos esperados pelas funções de regra.
    """
    def safe(col):
        val = row.get(col)
        if val is None:
            return None
        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass
        return val

    return {
        # ── identificação (da Silver) ──────────────────────────────────────────
        "id_talhao":    safe("CHAVESIG"),
        "chave":        safe("CHAVE"),
        "unidade":      safe("DESC_EMPRESA"),
        "unid_ind":     safe("UNID_IND"),
        "safra":        safe("SAFRA"),

        # ── cultura e manejo (da Silver) ───────────────────────────────────────
        "no_corte":     safe("NO_CORTE"),
        "categoria":    safe("CATEGORIA"),      # "Formação", "Cana Soca", "Muda"
        "estagio":      safe("ESTAGIO"),
        "man_hipot":    safe("MAN_HIPOT"),      # "Precoce", "Média", "Tardia"
        "data_plantio": safe("DATA_PLANTIO"),
        "tp_reforma":   safe("TP_REFORMA"),
        "reforma":      safe("Reforma"),        # "S" ou "N"
        "vinhaca":      safe("Vinhaca_E"),
        "torta":        safe("TORTA"),

        # ── produção (da Silver) ───────────────────────────────────────────────
        "tch_prod":     safe("TCH_PROD"),
        "area_prod":    safe("AREA_PROD"),
        "ton_estim":    safe("TON_ESTIM"),
        "area_ha":      safe("AREA_HA"),

        # ── solo — disponível na Silver ────────────────────────────────────────
        "desc_ambiente": safe("DESC_AMBIENTE"),  # textura: "Argiloso", "Arenoso"...
        "de_tp_solo":    safe("DE_TP_SOLO"),
        "ambiente":      safe("AMBIENTE"),        # código A–G

        # ── solo — análise química (NÃO disponível na Silver ainda) ───────────
        # Adicionar mapeamento quando a fonte de análise de solo for integrada.
        "ph_solo":       safe("ph_solo"),         # pH em água
        "ctc":           safe("ctc"),             # CTC mmol_c/dm³
        "v_atual":       safe("v_atual"),         # saturação de bases atual (%)
        "v_alvo":        safe("v_alvo"),          # saturação de bases alvo (%)
        "p_disponivel":  safe("p_disponivel"),    # P Mehlich-1 mg/dm³
        "saturacao_al":  safe("saturacao_al"),    # saturação por Al³⁺ (%)
        "ca_cmolc":      safe("ca_cmolc"),        # Ca cmolc/dm³
        "mg_cmolc":      safe("mg_cmolc"),        # Mg cmolc/dm³

        # ── safra — integrado por extract_safra.py ────────────────────────────
        "tchan_estimado":  safe("tchan_estimado"),   # estimativa de prod. (t/ha)
        "safra_estimada":  safe("safra_estimada"),   # True=modelo ATVOS / False=proxy

        # ── campo para cálculo de quantidade total ────────────────────────────
        # (usado pelo pipeline para calcular quantidade_total_kg = dose × área)
        "_area_ha":        safe("AREA_HA"),
    }


# ── APLICAÇÃO DAS REGRAS ──────────────────────────────────────────────────────

def _aplicar_regras(df: pd.DataFrame, hoje: date) -> pd.DataFrame:
    """
    Itera sobre cada talhão e aplica todos os módulos de regra.

    Retorna um DataFrame no formato long com uma linha por (talhão × processo).
    """
    registros = []

    for _, row in df.iterrows():
        talhao = _preparar_talhao(row)

        for processo, func_regra in REGRAS.items():
            try:
                resultado = func_regra(talhao)
            except Exception as e:
                # Nunca deixar uma exceção em uma regra travar o pipeline inteiro
                resultado = {
                    "orientacao":      f"ERRO_INTERNO: {type(e).__name__}",
                    "valor_calculado": None,
                    "regra_acionada":  "erro_execucao",
                }

            dose_kg_ha  = resultado.get("dose_kg_ha")
            area_ha     = talhao.get("_area_ha")
            qtd_total   = (
                round(dose_kg_ha * float(area_ha), 2)
                if dose_kg_ha is not None and area_ha is not None
                else None
            )

            registros.append({
                "id_talhao":          talhao["id_talhao"],
                "chave":              talhao["chave"],
                "unidade":            talhao["unidade"],
                "safra":              talhao["safra"],
                "processo":           processo,
                "orientacao":         resultado["orientacao"],
                "valor_calculado":    resultado["valor_calculado"],
                "regra_acionada":     resultado["regra_acionada"],
                "insumo":             resultado.get("insumo"),
                "dose_kg_ha":         dose_kg_ha,
                "quantidade_total_kg": qtd_total,
                "data_geracao":       hoje,
            })

    return pd.DataFrame(registros, columns=COLUNAS_GOLD)


# ── LEITURA DO SILVER ─────────────────────────────────────────────────────────

def _carregar_silver() -> pd.DataFrame:
    """
    Carrega os dados Silver. Prioriza silver_com_safra.parquet (com tchan_estimado)
    se disponível; caso contrário concatena os arquivos Inventario_*_silver.parquet
    e avisa que os módulos de insumo retornarão SEM_DADO.
    """
    if os.path.exists(SILVER_COM_SAFRA):
        _log("LOAD", SILVER_COM_SAFRA, "silver_com_safra — tchan_estimado disponível")
        df = pd.read_parquet(SILVER_COM_SAFRA)
        _log("CONCAT", "silver_com_safra", f"{len(df)} linhas, {len(df.columns)} colunas")
        return df

    _log("AVISO", SILVER_COM_SAFRA,
         "não encontrado — execute extract_safra.py para habilitar módulos de insumo")

    padrao = os.path.join(SILVER_PATH, "Inventario_*_silver.parquet")
    arquivos = sorted(glob.glob(padrao))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo Silver encontrado em '{SILVER_PATH}'. "
            "Execute src/processing/run_processing.py primeiro."
        )

    partes = []
    for arq in arquivos:
        _log("LOAD", arq)
        df = pd.read_parquet(arq)
        partes.append(df)

    df_total = pd.concat(partes, ignore_index=True)
    _log("CONCAT", f"{len(arquivos)} arquivos", f"{len(df_total)} linhas, {len(df_total.columns)} colunas")
    return df_total


# ── SALVAMENTO DO GOLD ────────────────────────────────────────────────────────

def _salvar_gold(df: pd.DataFrame, hoje: date) -> dict:
    """Salva o DataFrame Gold em Parquet e CSV. Retorna os caminhos."""
    os.makedirs(GOLD_PATH, exist_ok=True)
    sufixo = hoje.strftime("%Y-%m-%d")

    caminho_parquet = os.path.join(GOLD_PATH, f"orientacoes_{sufixo}.parquet")
    caminho_csv     = os.path.join(GOLD_PATH, f"orientacoes_{sufixo}.csv")

    df.to_parquet(caminho_parquet, index=False)
    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")

    _log("SAVE", caminho_parquet, f"{len(df)} registros")
    _log("SAVE", caminho_csv, "para inspeção manual")

    return {"parquet": caminho_parquet, "csv": caminho_csv}


# ── RELATÓRIO GOLD ────────────────────────────────────────────────────────────

def _relatorio_gold(df: pd.DataFrame) -> None:
    """Imprime resumo do output Gold para validação rápida."""
    print(f"\n{'='*65}")
    print("RELATÓRIO — CAMADA GOLD")
    print(f"{'='*65}")
    print(f"  Total de registros  : {len(df)}")
    print(f"  Talhões únicos      : {df['id_talhao'].nunique()}")
    print(f"  Unidades            : {sorted(df['unidade'].dropna().unique())}")

    print(f"\n  Por processo:")
    for proc in sorted(df["processo"].unique()):
        sub = df[df["processo"] == proc]
        sem_dado = (sub["regra_acionada"].str.startswith("dado_ausente")).sum()
        tem_insumo = sub["insumo"].notna().sum()
        insumo_str = f" | com_insumo: {tem_insumo}" if tem_insumo > 0 else ""
        print(f"    {proc:<22} {len(sub):>7} registros | SEM_DADO: {sem_dado}{insumo_str}")

    print(f"\n  Regras mais acionadas (top 10):")
    top = df["regra_acionada"].value_counts().head(10)
    for regra, n in top.items():
        print(f"    {regra:<45} {n:>6}")
    print()


# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def executar_pipeline(dry_run: bool = False) -> pd.DataFrame:
    """
    Executa o pipeline completo Silver → Gold.

    Parameters
    ----------
    dry_run : bool
        Se True, processa e exibe o relatório mas não salva os arquivos.

    Returns
    -------
    DataFrame Gold com as orientações geradas.
    """
    hoje = date.today()
    _log("START", "pipeline_gold", f"data_geracao={hoje} | dry_run={dry_run}")

    df_silver = _carregar_silver()
    _log("RULES", f"{len(REGRAS)} processos", str(list(REGRAS.keys())))

    df_gold = _aplicar_regras(df_silver, hoje)
    _relatorio_gold(df_gold)

    if not dry_run:
        caminhos = _salvar_gold(df_gold, hoje)
        _log("DONE", "Gold salvo", str(caminhos))
    else:
        _log("DRY-RUN", "arquivos NÃO salvos")

    return df_gold


# ── UTILITÁRIO ────────────────────────────────────────────────────────────────

def _log(status: str, fonte: str, detalhe: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{status}] {fonte}" + (f" — {detalhe}" if detalhe else ""))


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    executar_pipeline(dry_run=dry)
