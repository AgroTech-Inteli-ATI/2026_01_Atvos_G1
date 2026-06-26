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

# As três colunas de produção têm relação física: TON_ESTIM = AREA_PROD × TCH_PROD
# Imputer em dois passos: derivação matemática → mediana estratificada
COLUNAS_PRODUCAO = ["AREA_PROD", "TCH_PROD", "TON_ESTIM"]

# Mínimo de amostras não-nulas em um grupo para aceitar sua mediana.
# Grupos menores sobem ao nível seguinte da hierarquia.
MIN_AMOSTRAS_GRUPO = 5

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


# ── IMPUTAÇÃO DE PRODUÇÃO ─────────────────────────────────────────────────────

def _faixa_corte(no_corte) -> str:
    """
    Agrupa NO_CORTE em faixas com perfil de TCH similar.

    Referência: curva de senescência de cana-de-açúcar (Embrapa Agroenergia).
    TCH médio de cana-planta é ~25% superior ao de soca tardia (7+ corte).
    Usar mediana sem estratificação mistura esses perfis e introduz viés sistemático.
    """
    try:
        n = int(no_corte)
    except (TypeError, ValueError):
        return "desconhecido"
    if n <= 1:
        return "plantio"      # cana-planta: maior TCH médio
    if n <= 3:
        return "soca_nova"    # 2º–3º corte: curva descendente inicial
    if n <= 6:
        return "soca_media"   # 4º–6º corte: produtividade intermediária
    return "soca_tardia"      # 7º+ corte: candidatos a erradicação


def imputar_producao(df: pd.DataFrame):
    """
    Imputa AREA_PROD, TCH_PROD e TON_ESTIM em dois passos sequenciais.

    Passo 1 — Derivação matemática (sem estimativa estatística):
        Quando dois dos três campos estão presentes, o terceiro é calculado
        pela relação física TON_ESTIM = AREA_PROD × TCH_PROD.
        Isso mantém consistência interna sem introduzir viés.

    Passo 2 — Mediana estratificada em hierarquia de 4 níveis:
        Nível 1: UNID_IND + CATEGORIA + faixa_corte  (mais específico)
        Nível 2: UNID_IND + CATEGORIA
        Nível 3: UNID_IND
        Nível 4: mediana global                       (garantia de completude)

        Grupos com menos de MIN_AMOSTRAS_GRUPO amostras válidas sobem ao nível
        seguinte sem imputar — evita mediana instável de grupos pequenos.
    """
    relatorio = {"derivados": 0, "por_coluna": {}}
    cols_presentes = [c for c in COLUNAS_PRODUCAO if c in df.columns]
    if not cols_presentes:
        return df, relatorio

    # ── Passo 1: derivação matemática ─────────────────────────────────────────
    if set(COLUNAS_PRODUCAO).issubset(df.columns):
        # AREA_PROD = TON_ESTIM / TCH_PROD
        mask = (
            df["AREA_PROD"].isna()
            & df["TON_ESTIM"].notna()
            & df["TCH_PROD"].notna()
            & (df["TCH_PROD"] > 0)
        )
        if mask.any():
            df.loc[mask, "AREA_PROD"] = (
                df.loc[mask, "TON_ESTIM"] / df.loc[mask, "TCH_PROD"]
            ).round(4)
            relatorio["derivados"] += int(mask.sum())

        # TCH_PROD = TON_ESTIM / AREA_PROD
        mask = (
            df["TCH_PROD"].isna()
            & df["TON_ESTIM"].notna()
            & df["AREA_PROD"].notna()
            & (df["AREA_PROD"] > 0)
        )
        if mask.any():
            df.loc[mask, "TCH_PROD"] = (
                df.loc[mask, "TON_ESTIM"] / df.loc[mask, "AREA_PROD"]
            ).round(2)
            relatorio["derivados"] += int(mask.sum())

        # TON_ESTIM = AREA_PROD × TCH_PROD
        mask = (
            df["TON_ESTIM"].isna()
            & df["AREA_PROD"].notna()
            & df["TCH_PROD"].notna()
        )
        if mask.any():
            df.loc[mask, "TON_ESTIM"] = (
                df.loc[mask, "AREA_PROD"] * df.loc[mask, "TCH_PROD"]
            ).round(2)
            relatorio["derivados"] += int(mask.sum())

    # ── Passo 2: mediana estratificada ────────────────────────────────────────
    if "UNID_IND" not in df.columns:
        return df, relatorio

    # Coluna temporária de faixa de corte
    col_faixa = "_faixa_corte"
    df[col_faixa] = (
        df["NO_CORTE"].apply(_faixa_corte)
        if "NO_CORTE" in df.columns
        else "desconhecido"
    )

    # Hierarquia de estratificação: mais específico → menos específico
    col_cat = "CATEGORIA" if "CATEGORIA" in df.columns else None
    if col_cat:
        niveis = [
            ["UNID_IND", col_cat, col_faixa],
            ["UNID_IND", col_cat],
            ["UNID_IND"],
        ]
    else:
        niveis = [
            ["UNID_IND", col_faixa],
            ["UNID_IND"],
        ]

    for col in cols_presentes:
        antes = int(df[col].isna().sum())
        if antes == 0:
            relatorio["por_coluna"][col] = {
                "nulos_antes": 0, "nulos_depois": 0, "imputados": 0,
            }
            continue

        for nivel in niveis:
            nivel_ok = [c for c in nivel if c in df.columns]
            if not nivel_ok:
                continue
            # Preenchimento só onde o grupo tem amostras suficientes
            df[col] = df.groupby(nivel_ok)[col].transform(
                lambda x: x.fillna(x.median())
                if x.notna().sum() >= MIN_AMOSTRAS_GRUPO
                else x
            )

        # Nível 4: mediana global — garante que nenhum nulo persista por falta de grupo
        mask_restante = df[col].isna()
        if mask_restante.any():
            global_median = df[col].median()
            if pd.notna(global_median):
                df.loc[mask_restante, col] = global_median

        depois = int(df[col].isna().sum())
        relatorio["por_coluna"][col] = {
            "nulos_antes":  antes,
            "nulos_depois": depois,
            "imputados":    antes - depois,
        }

    df = df.drop(columns=[col_faixa])
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

    imp = meta.get("imputacoes", {})
    if imp.get("derivados", 0) or imp.get("por_coluna"):
        print(f"\n  [IMPUTAÇÃO DE PRODUÇÃO]:")
        print(f"    Derivados matematicamente (TON=AREA×TCH): {imp.get('derivados', 0)}")
        for col, info in imp.get("por_coluna", {}).items():
            if info["imputados"] > 0:
                print(
                    f"    {col}: {info['imputados']} imputados por mediana estratificada "
                    f"({info['nulos_antes']} → {info['nulos_depois']} nulos)"
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
    df, meta["colunas_index"]    = dropar_colunas_index(df)
    df, meta["colunas_100_nulos"] = dropar_colunas_100_nulos(df)
    df, meta["flags"]            = criar_flags_negocio(df)
    df, meta["imputacoes"]       = imputar_producao(df)
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
