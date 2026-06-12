"""
src/ingestion/extract_safra.py
Integração dos modelos de estimativa de safra da ATVOS ao Silver.

Fluxo:
    1. Procura arquivo de estimativa em data/raw/ (Excel, CSV ou Parquet)
       com nome que contenha "safra" ou "estimativa".
    2. Se encontrado: faz merge com Silver por CHAVESIG → safra_estimada=True.
    3. Se não encontrado: usa TCH_PROD do próprio Silver como proxy
       → safra_estimada=False, tchan_estimado = TCH_PROD.
    4. Talhões sem estimativa (após merge) mantidos no DataFrame com flag False.
    5. Salva resultado em data/processed/silver_com_safra.parquet.

Quando o arquivo ATVOS chegar, basta colocá-lo em data/raw/ com "safra" ou
"estimativa" no nome. O script detecta automaticamente e usa o dado real.
A coluna de referência do arquivo externo é configurável em COLUNA_CHAVESIG_SAFRA
e COLUNA_TCH_SAFRA abaixo.
"""

import glob
import os
from datetime import datetime

import pandas as pd

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

RAW_PATH       = "data/raw"
PROCESSED_PATH = "data/processed"
SAIDA_PARQUET  = os.path.join(PROCESSED_PATH, "silver_com_safra.parquet")

# Padrão de busca do arquivo de safra em data/raw/
PADROES_SAFRA  = ["*safra*", "*estimativa*", "*modelo*safra*"]

# Nomes esperados das colunas no arquivo externo (ajustar quando arquivo chegar)
COLUNA_CHAVESIG_SAFRA = "CHAVESIG"   # chave de join com Silver
COLUNA_TCH_SAFRA      = "tchan_estimado"   # estimativa de produtividade (t/ha)

# Nome da coluna resultado no Silver unificado
COL_TCHAN   = "tchan_estimado"
COL_FLAG    = "safra_estimada"


# ── LOGGING ───────────────────────────────────────────────────────────────────

def _log(status: str, fonte: str, detalhe: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{status}] {fonte}" + (f" — {detalhe}" if detalhe else ""))


# ── CARREGAMENTO DO ARQUIVO DE SAFRA ─────────────────────────────────────────

def _buscar_arquivo_safra() -> str | None:
    """Procura arquivo de estimativa de safra em data/raw/. Retorna o caminho ou None."""
    for padrao in PADROES_SAFRA:
        encontrados = sorted(glob.glob(os.path.join(RAW_PATH, padrao), recursive=False))
        if encontrados:
            return encontrados[-1]  # usa o mais recente se houver mais de um
    return None


def _carregar_safra(caminho: str) -> pd.DataFrame | None:
    """Lê o arquivo de estimativa de safra e retorna DataFrame com CHAVESIG e tchan_estimado."""
    ext = os.path.splitext(caminho)[1].lower()
    try:
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(caminho)
        elif ext == ".csv":
            try:
                df = pd.read_csv(caminho)
            except UnicodeDecodeError:
                df = pd.read_csv(caminho, encoding="latin1")
        elif ext == ".parquet":
            df = pd.read_parquet(caminho)
        else:
            _log("AVISO", caminho, f"Extensão '{ext}' não suportada — ignorando")
            return None
    except Exception as e:
        _log("ERRO", caminho, str(e))
        return None

    if COLUNA_CHAVESIG_SAFRA not in df.columns:
        _log("ERRO", caminho,
             f"Coluna '{COLUNA_CHAVESIG_SAFRA}' não encontrada. "
             f"Colunas disponíveis: {list(df.columns)}")
        return None

    if COLUNA_TCH_SAFRA not in df.columns:
        _log("ERRO", caminho,
             f"Coluna '{COLUNA_TCH_SAFRA}' não encontrada. "
             f"Colunas disponíveis: {list(df.columns)}")
        return None

    df_safra = df[[COLUNA_CHAVESIG_SAFRA, COLUNA_TCH_SAFRA]].rename(
        columns={COLUNA_CHAVESIG_SAFRA: "CHAVESIG", COLUNA_TCH_SAFRA: COL_TCHAN}
    )
    _log("LOAD", caminho, f"{len(df_safra)} linhas | colunas: {list(df_safra.columns)}")
    return df_safra


# ── INTEGRAÇÃO ────────────────────────────────────────────────────────────────

def _carregar_silver() -> pd.DataFrame:
    """Lê e concatena todos os arquivos Inventario_*_silver.parquet."""
    padrao = os.path.join(PROCESSED_PATH, "Inventario_*_silver.parquet")
    arquivos = sorted(glob.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo Silver encontrado em '{PROCESSED_PATH}'. "
            "Execute src/processing/run_processing.py primeiro."
        )
    partes = [pd.read_parquet(a) for a in arquivos]
    df = pd.concat(partes, ignore_index=True)
    _log("LOAD", "Silver", f"{len(df)} linhas de {len(arquivos)} arquivo(s)")
    return df


def integrar_safra(forcar_proxy: bool = False) -> pd.DataFrame:
    """
    Integra os modelos de estimativa de safra ao Silver.

    Parameters
    ----------
    forcar_proxy : bool
        Se True, ignora arquivo externo e sempre usa TCH_PROD como proxy.
        Útil para testes.

    Returns
    -------
    DataFrame Silver estendido com as colunas:
      tchan_estimado  (float) — estimativa de produtividade (t/ha)
      safra_estimada  (bool)  — True se veio do modelo ATVOS, False se proxy
    """
    df_silver = _carregar_silver()

    # ── tentar usar modelo de safra externo ──────────────────────────────────
    arquivo_safra = None if forcar_proxy else _buscar_arquivo_safra()

    if arquivo_safra:
        _log("FOUND", arquivo_safra, "usando modelo de safra ATVOS")
        df_safra = _carregar_safra(arquivo_safra)
    else:
        df_safra = None
        _log("INFO", "Arquivo de safra não encontrado",
             "usando TCH_PROD como proxy (safra_estimada=False)")

    if df_safra is not None:
        # Merge left: mantém todos os talhões Silver
        antes = len(df_silver)
        df_merged = df_silver.merge(
            df_safra[["CHAVESIG", COL_TCHAN]],
            on="CHAVESIG",
            how="left",
        )
        sem_match = df_merged[COL_TCHAN].isna().sum()
        _log("MERGE", "Silver + Safra",
             f"{antes} talhões | sem match: {sem_match} → proxy TCH_PROD nesses casos")

        # Talhões sem estimativa no modelo → preenche com TCH_PROD como proxy
        df_merged[COL_TCHAN] = df_merged[COL_TCHAN].fillna(df_merged["TCH_PROD"])
        # Flag: True onde o modelo forneceu dado, False onde usou proxy
        df_merged[COL_FLAG] = df_merged[COL_TCHAN].notna() & (sem_match == 0)

        # Recalcular corretamente o flag por linha
        # (True = veio do modelo externo, ou seja, linha teve match)
        modelo_cols = df_safra.set_index("CHAVESIG")[COL_TCHAN]
        df_merged[COL_FLAG] = df_merged["CHAVESIG"].map(modelo_cols).notna()

        df_out = df_merged

    else:
        # Sem arquivo externo: usa TCH_PROD como proxy para todos
        df_silver[COL_TCHAN] = df_silver["TCH_PROD"]
        df_silver[COL_FLAG]  = False
        df_out = df_silver

    _log("RESULT",
         "silver_com_safra",
         f"{len(df_out)} linhas | "
         f"com_modelo={df_out[COL_FLAG].sum()} | "
         f"proxy={( ~df_out[COL_FLAG]).sum()}")

    return df_out


# ── EXECUÇÃO E SAVE ───────────────────────────────────────────────────────────

def executar(forcar_proxy: bool = False) -> str:
    """
    Executa a integração e salva o resultado.

    Returns
    -------
    Caminho do arquivo Parquet gerado.
    """
    _log("START", "extract_safra")
    df = integrar_safra(forcar_proxy=forcar_proxy)

    os.makedirs(PROCESSED_PATH, exist_ok=True)
    df.to_parquet(SAIDA_PARQUET, index=False)
    _log("SAVE", SAIDA_PARQUET, f"{len(df)} linhas | {len(df.columns)} colunas")
    _log("DONE", "extract_safra")
    return SAIDA_PARQUET


if __name__ == "__main__":
    import sys
    proxy = "--proxy" in sys.argv
    executar(forcar_proxy=proxy)
