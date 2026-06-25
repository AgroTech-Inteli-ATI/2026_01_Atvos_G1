"""
src/pipeline/loader.py
Responsabilidade única: localizar e carregar os arquivos Silver em um DataFrame.
"""
import os
import glob
import pandas as pd
from pipeline.utils import log

SILVER_PATH      = "data/processed"
SILVER_COM_SAFRA = os.path.join(SILVER_PATH, "silver_com_safra.parquet")


def carregar_silver() -> pd.DataFrame:
    """
    Carrega os dados Silver. Prioriza silver_com_safra.parquet (com tchan_estimado)
    se disponível; caso contrário concatena os arquivos Inventario_*_silver.parquet
    e avisa que os módulos de insumo retornarão SEM_DADO.

    Returns
    -------
    DataFrame Silver pronto para a etapa de transformação.
    """
    if os.path.exists(SILVER_COM_SAFRA):
        log("LOAD", SILVER_COM_SAFRA, "silver_com_safra — tchan_estimado disponível")
        df = pd.read_parquet(SILVER_COM_SAFRA)
        log("CONCAT", "silver_com_safra", f"{len(df)} linhas, {len(df.columns)} colunas")
        return df

    log(
        "AVISO", SILVER_COM_SAFRA,
        "não encontrado — execute extract_safra.py para habilitar módulos de insumo",
    )

    padrao = os.path.join(SILVER_PATH, "Inventario_*_silver.parquet")
    arquivos = sorted(glob.glob(padrao))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo Silver encontrado em '{SILVER_PATH}'. "
            "Execute src/processing/run_processing.py primeiro."
        )

    partes = []
    for arq in arquivos:
        log("LOAD", arq)
        partes.append(pd.read_parquet(arq))

    df_total = pd.concat(partes, ignore_index=True)
    log("CONCAT", f"{len(arquivos)} arquivos", f"{len(df_total)} linhas, {len(df_total.columns)} colunas")
    return df_total
