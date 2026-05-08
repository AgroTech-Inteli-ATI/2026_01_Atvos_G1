"""
src/processing/clean_data.py
Pipeline Raw → Silver com as regras definidas em docs/regras_limpeza.md
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

RAW_PATH = "data/raw"
PROCESSED_PATH = "data/processed"

# ── CLASSIFICAÇÃO DE NULOS ────────────────────────────────────────────────────

COLUNAS_INDEX = ["Unnamed: 0"]

# Nulo = negócio: (colunas_do_grupo, nome_da_flag)
# Flag = True quando TODAS as colunas do grupo são nulas simultaneamente
FLAG_NEGOCIO = [
    (["BLOCO"],                                "flag_bloco_ausente"),
    (["DT_CARACT", "CARACT"],                 "flag_caract_ausente"),
    (["CANA_ENT"],                             "flag_cana_ent_ausente"),
    (["TP_REFORMA"],                           "flag_tp_reforma_ausente"),
    (["AREA_REEST", "TCH_REEST", "TON_REEST"], "flag_reestimativa_ausente"),
    (["AREA_MUDA", "TCH_MUDA", "TON_MUDA"],   "flag_muda_ausente"),
    (["AREA_COLHIDA"],                         "flag_colheita_ausente"),
    (["DATA_FECHA"],                           "flag_talhao_aberto"),
]

# Nulo = faltante: imputar mediana por UNID_IND
COLUNAS_MEDIANA = ["AREA_PROD", "TCH_PROD", "TON_ESTIM"]

# Nulo = geo: manter, cruzar com outro dataset depois
COLUNAS_GEO = {
    "LATITUDE", "LONGITUDE",
    "ZONA_AGRO_ECOLOGICA", "DESC_ZONA",
    "DESC_AMBIENTE",
}

# ── CARREGAMENTO ──────────────────────────────────────────────────────────────

def carregar_arquivo(caminho: str) -> pd.DataFrame:
    ext = os.path.splitext(caminho)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(caminho)
    elif ext == ".csv":
        try:
            df = pd.read_csv(caminho, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(caminho, encoding="latin1")
    else:
        raise ValueError(f"Formato não suportado: {ext}")
    _log("LOAD", caminho, f"{len(df)} linhas, {len(df.columns)} colunas")
    return df

# ── REGRAS DE NULOS ───────────────────────────────────────────────────────────

def dropar_colunas_index(df: pd.DataFrame):
    cols = [c for c in COLUNAS_INDEX if c in df.columns]
    return df.drop(columns=cols), cols


def dropar_colunas_100_nulos(df: pd.DataFrame):
    # Detecta dinamicamente — não depende de lista estática
    cols = [c for c in df.columns if df[c].isnull().all()]
    return df.drop(columns=cols), cols


def criar_flags_negocio(df: pd.DataFrame):
    flags_criadas = {}
    for colunas, nome_flag in FLAG_NEGOCIO:
        presentes = [c for c in colunas if c in df.columns]
        if not presentes:
            continue
        mask = df[presentes].isnull().all(axis=1)
        df[nome_flag] = mask
        flags_criadas[nome_flag] = {"colunas": presentes, "n_true": int(mask.sum())}
    return df, flags_criadas


def imputar_mediana_por_unidade(df: pd.DataFrame):
    relatorio = {}
    if "UNID_IND" not in df.columns:
        return df, relatorio
    for col in COLUNAS_MEDIANA:
        if col not in df.columns:
            continue
        antes = int(df[col].isnull().sum())
        if antes == 0:
            continue
        df[col] = df.groupby("UNID_IND")[col].transform(
            lambda x: x.fillna(x.median())
        )
        depois = int(df[col].isnull().sum())
        relatorio[col] = {
            "nulos_antes": antes,
            "nulos_depois": depois,
            "imputados": antes - depois,
        }
    return df, relatorio

# ── PADRONIZAÇÃO ──────────────────────────────────────────────────────────────

def corrigir_encoding(df: pd.DataFrame) -> pd.DataFrame:
    def fix(s):
        if not isinstance(s, str):
            return s
        try:
            return s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(fix)
    return df


def padronizar_texto(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def padronizar_datas(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        if any(kw in col.lower() for kw in ("data", "date", "dt_")):
            try:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            except Exception:
                pass
    return df

# ── RELATÓRIO ─────────────────────────────────────────────────────────────────

def relatorio_qualidade(df: pd.DataFrame, nome: str, meta: dict) -> None:
    print(f"\n{'='*60}")
    print(f"RELATÓRIO DE QUALIDADE — {nome}")
    print(f"{'='*60}")
    print(f"  Linhas : {len(df)}")
    print(f"  Colunas: {len(df.columns)}")

    if meta.get("colunas_index"):
        print(f"\n  [INDEX DROPADAS]   : {meta['colunas_index']}")
    if meta.get("colunas_100_nulos"):
        print(f"  [100% NULO DROP]   : {meta['colunas_100_nulos']}")

    if meta.get("flags"):
        print(f"\n  [FLAGS DE NEGÓCIO criadas]:")
        for flag, info in meta["flags"].items():
            pct = info["n_true"] / len(df) * 100
            print(f"    {flag}: {info['n_true']} True ({pct:.1f}%) | colunas: {info['colunas']}")

    if meta.get("imputacoes"):
        print(f"\n  [IMPUTAÇÃO MEDIANA por UNID_IND]:")
        for col, info in meta["imputacoes"].items():
            print(
                f"    {col}: {info['imputados']} imputados "
                f"({info['nulos_antes']} -> {info['nulos_depois']} nulos)"
            )

    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if len(nulos):
        print(f"\n  [NULOS RESTANTES]:")
        for col, n in nulos.items():
            pct = n / len(df) * 100
            cat = "geo" if col in COLUNAS_GEO else "poucos/negócio"
            print(f"    {col}: {n} ({pct:.1f}%) [{cat}]")
    else:
        print(f"\n  Nenhum nulo restante.")
    print()

# ── SALVAR ────────────────────────────────────────────────────────────────────

def salvar_silver(df: pd.DataFrame, nome: str) -> str:
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    saida = os.path.join(PROCESSED_PATH, f"{nome}_silver.parquet")
    df.to_parquet(saida, index=False)
    _log("SAVE", saida, f"{len(df)} linhas, {len(df.columns)} colunas")
    return saida

# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def limpar(caminho: str) -> pd.DataFrame:
    nome = os.path.splitext(os.path.basename(caminho))[0]
    meta = {}

    df = carregar_arquivo(caminho)
    df, meta["colunas_index"] = dropar_colunas_index(df)
    df, meta["colunas_100_nulos"] = dropar_colunas_100_nulos(df)
    df, meta["flags"] = criar_flags_negocio(df)
    df, meta["imputacoes"] = imputar_mediana_por_unidade(df)
    df = corrigir_encoding(df)
    df = padronizar_texto(df)
    df = padronizar_datas(df)

    relatorio_qualidade(df, nome, meta)
    salvar_silver(df, nome)
    return df

# ── UTILITÁRIO ────────────────────────────────────────────────────────────────

def _log(status: str, fonte: str, detalhe: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{status}] {fonte} — {detalhe}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/processing/clean_data.py NOME_DO_ARQUIVO.xlsx")
        sys.exit(1)
    arquivo = sys.argv[1]
    caminho = os.path.join(RAW_PATH, arquivo) if not os.path.isabs(arquivo) else arquivo
    limpar(caminho)
