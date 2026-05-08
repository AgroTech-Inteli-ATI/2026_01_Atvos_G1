"""
src/ingestion/extract_local.py
Alternativa local ao extract_bigquery.py e extract_gcs.py.
Lê arquivos do sistema de arquivos local com logging estruturado.

Alternativas GCP:
  - BigQuery   → DuckDB (pip install duckdb) — SQL in-process sobre DataFrames/Parquet
  - GCS buckets → data/raw/ local (esta função)
"""

import pandas as pd
import os
from datetime import datetime

RAW_PATH = "data/raw"


def _log(status: str, fonte: str, detalhe: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{status}] {fonte} — {detalhe}")


def extract_csv(caminho: str, separador: str = ",", encoding: str = "utf-8") -> pd.DataFrame | None:
    """Lê um CSV local. Equivalente ao extract_gcs para CSVs."""
    try:
        try:
            df = pd.read_csv(caminho, sep=separador, encoding=encoding)
        except UnicodeDecodeError:
            df = pd.read_csv(caminho, sep=separador, encoding="latin1")
        _log("OK", caminho, f"{len(df)} linhas")
        return df
    except Exception as e:
        _log("ERRO", caminho, str(e))
        return None


def extract_excel(caminho: str, aba: int | str = 0) -> pd.DataFrame | None:
    """Lê um Excel local. Equivalente ao extract_gcs para XLS/XLSX."""
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
        _log("OK", caminho, f"{len(df)} linhas")
        return df
    except Exception as e:
        _log("ERRO", caminho, str(e))
        return None


def extract_parquet(caminho: str) -> pd.DataFrame | None:
    """Lê um Parquet local. Equivalente ao extract_gcs para Parquet."""
    try:
        df = pd.read_parquet(caminho)
        _log("OK", caminho, f"{len(df)} linhas")
        return df
    except Exception as e:
        _log("ERRO", caminho, str(e))
        return None


def extract_all_raw(pasta: str = RAW_PATH) -> dict[str, pd.DataFrame]:
    """
    Carrega todos os arquivos suportados de uma pasta local.
    Retorna dict {nome_sem_extensao: DataFrame}.
    """
    LEITORES = {
        ".xlsx": extract_excel,
        ".xls": extract_excel,
        ".csv": extract_csv,
        ".parquet": extract_parquet,
    }
    dataframes = {}
    for arquivo in sorted(os.listdir(pasta)):
        ext = os.path.splitext(arquivo)[1].lower()
        if ext not in LEITORES:
            continue
        caminho = os.path.join(pasta, arquivo)
        nome = os.path.splitext(arquivo)[0]
        df = LEITORES[ext](caminho)
        if df is not None:
            dataframes[nome] = df

    print(f"\n[INGESTÃO] {len(dataframes)} arquivo(s): {list(dataframes.keys())}")
    return dataframes


if __name__ == "__main__":
    extract_all_raw()
