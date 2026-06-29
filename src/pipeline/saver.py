"""
src/pipeline/saver.py
Responsabilidade única: persistir o DataFrame Gold em disco (Parquet + CSV).
"""
import os
from datetime import date

import pandas as pd

from pipeline.utils import log

GOLD_PATH = "data/gold"


def salvar_gold(df: pd.DataFrame, hoje: date) -> dict:
    """
    Salva o DataFrame Gold em Parquet e CSV.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame Gold gerado pelo transformer.
    hoje : date
        Data usada como sufixo nos nomes dos arquivos.

    Returns
    -------
    dict com as chaves "parquet" e "csv" apontando para os caminhos salvos.
    """
    os.makedirs(GOLD_PATH, exist_ok=True)
    sufixo = hoje.strftime("%Y-%m-%d")

    caminho_parquet = os.path.join(GOLD_PATH, f"orientacoes_{sufixo}.parquet")
    caminho_csv     = os.path.join(GOLD_PATH, f"orientacoes_{sufixo}.csv")

    df.to_parquet(caminho_parquet, index=False)
    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")

    log("SAVE", caminho_parquet, f"{len(df)} registros")
    log("SAVE", caminho_csv, "para inspeção manual")

    return {"parquet": caminho_parquet, "csv": caminho_csv}
