"""
Pipeline Gold — Motor de Orientações Agronômicas
=================================================
Sprint 2 | AgroTech Inteli + ATVOS

Executa 4 passos em sequência:

  Passo 1 — Unificar Silver
    Concatena os 4 parquets do inventário Silver.
    Saída: data/processed/inventario_silver_unificado.parquet

  Passo 2 — Aplicar tabela de correção de talhões
    Remapeia CHAVEs reformadas para os identificadores atuais.
    Saída: data/processed/inventario_silver_corrigido.parquet

  Passo 3 — Join com análise de solo
    Left join via CHAVE == FST.
    Saída: data/processed/inventario_silver_enriquecido.parquet

  Passo 4 — Aplicar regras e gerar Gold (formato wide)
    Uma linha por talhão, colunas por processo.
    Por padrão processa uma amostra representativa (N_POR_UNIDADE por unidade industrial).
    Saída: data/gold/amostra_gold_YYYY-MM-DD.parquet/.csv

Uso:
    python src/pipeline_gold.py              # amostra (padrão)
    python src/pipeline_gold.py --todos      # todos os talhões com solo
"""

import sys
import argparse
from pathlib import Path
from datetime import date

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.rules.calagem        import calcular_calagem
from src.rules.gessagem       import calcular_gessagem
from src.rules.fosfatagem     import calcular_fosfatagem
from src.rules.erradicacao    import calcular_erradicacao
from src.rules.janela_plantio import calcular_janela_plantio

DATA_PROCESSED = ROOT / "data" / "processed"
DATA_GOLD      = ROOT / "data" / "gold"
DATA_GOLD.mkdir(parents=True, exist_ok=True)

N_POR_UNIDADE = 30   # talhões por unidade industrial na amostra

REGRAS = [
    ("calagem",        calcular_calagem,
     ["orientacao", "valor_calculado", "regra_acionada", "flag_aguardando_validacao_po"]),
    ("gessagem",       calcular_gessagem,
     ["orientacao", "valor_calculado", "regra_acionada", "flag_aguardando_validacao_po"]),
    ("fosfatagem",     calcular_fosfatagem,
     ["orientacao", "valor_calculado", "regra_acionada", "flag_aguardando_validacao_po"]),
    ("erradicacao",    calcular_erradicacao,
     ["orientacao", "valor_calculado", "regra_acionada", "flag_aguardando_validacao_po",
      "prioridade_reforma"]),
    ("janela_plantio", calcular_janela_plantio,
     ["orientacao", "valor_calculado", "regra_acionada", "flag_aguardando_validacao_po"]),
]

COLUNAS_CONTEXTO = [
    "id_talhao", "SAFRA", "unidade", "CATEGORIA",
    "NO_CORTE", "TCH_PROD", "AREA_HA", "DE_TP_SOLO", "data_geracao",
]


def log(msg: str) -> None:
    print(f"[pipeline_gold] {msg}", flush=True)


# ── Passo 1 ─────────────────────────────────────────────────────────────────
def passo1_unificar_silver() -> pd.DataFrame:
    log("PASSO 1 — Unificando Silver...")
    arquivos = sorted(DATA_PROCESSED.glob("Inventario_atvos_*_silver.parquet"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo Silver em {DATA_PROCESSED}")
    df = pd.concat([pd.read_parquet(a) for a in arquivos], ignore_index=True)
    log(f"  {len(df):,} linhas × {df.shape[1]} colunas")
    df.to_parquet(DATA_PROCESSED / "inventario_silver_unificado.parquet", index=False)
    return df


# ── Passo 2 ─────────────────────────────────────────────────────────────────
def passo2_aplicar_correcao(df: pd.DataFrame) -> pd.DataFrame:
    log("PASSO 2 — Aplicando correção de talhões...")
    arq = DATA_PROCESSED / "Correcao_talhoes_para_unificacao_silver.parquet"
    if not arq.exists():
        log("  AVISO: arquivo de correção não encontrado. Pulando.")
        df.to_parquet(DATA_PROCESSED / "inventario_silver_corrigido.parquet", index=False)
        return df
    cor = pd.read_parquet(arq)
    cor["chave_origem"]  = cor["Faz_Origem"].astype(str)  + "-" + cor["Setor_Origem"].astype(str)  + "-" + cor["Talhao_Origem"].astype(str)
    cor["chave_destino"] = cor["Faz_Destino"].astype(str) + "-" + cor["Setor_Destino"].astype(str) + "-" + cor["Talhao_Destino"].astype(str)
    mapa = dict(zip(cor["chave_origem"], cor["chave_destino"]))
    antes = df["CHAVE"].nunique()
    df["CHAVE"] = df["CHAVE"].map(lambda c: mapa.get(str(c), str(c)))
    log(f"  CHAVEs únicas: {antes:,} → {df['CHAVE'].nunique():,} | mapeamentos: {len(mapa):,}")
    df.to_parquet(DATA_PROCESSED / "inventario_silver_corrigido.parquet", index=False)
    return df


# ── Passo 3 ─────────────────────────────────────────────────────────────────
def passo3_join_solo(df: pd.DataFrame) -> pd.DataFrame:
    log("PASSO 3 — Join com análise de solo...")
    solo = pd.read_csv(ROOT / "data" / "Dados_analise_solo.csv", sep=";")
    solo["FST"] = solo["FST"].astype(str).str.strip()
    df["CHAVE"]  = df["CHAVE"].astype(str).str.strip()
    enriquecido = df.merge(solo, left_on="CHAVE", right_on="FST", how="left")
    com  = enriquecido["FST"].notna().sum()
    sem  = enriquecido["FST"].isna().sum()
    log(f"  Com solo: {com:,} ({com/len(enriquecido)*100:.1f}%) | Sem solo: {sem:,} ({sem/len(enriquecido)*100:.1f}%)")
    enriquecido.to_parquet(DATA_PROCESSED / "inventario_silver_enriquecido.parquet", index=False)
    return enriquecido


# ── Passo 4 ─────────────────────────────────────────────────────────────────
def _aplicar_regras_linha(row: dict) -> dict:
    """Chama os 5 módulos de regra para uma linha e retorna colunas wide."""
    resultado = {
        "id_talhao":    row.get("CHAVE"),
        "SAFRA":        row.get("SAFRA"),
        "unidade":      row.get("UNID_IND"),
        "CATEGORIA":    row.get("CATEGORIA"),
        "NO_CORTE":     row.get("NO_CORTE"),
        "TCH_PROD":     row.get("TCH_PROD"),
        "AREA_HA":      row.get("AREA_HA"),
        "DE_TP_SOLO":   row.get("DE_TP_SOLO"),
        "data_geracao": date.today().isoformat(),
    }
    for nome, fn, campos in REGRAS:
        try:
            res = fn(row)
        except Exception as exc:
            res = {c: f"ERRO: {exc}" if c == "orientacao" else None for c in campos}
        for campo in campos:
            resultado[f"{nome}_{campo}"] = res.get(campo)
    return resultado


def passo4_gerar_gold(df: pd.DataFrame, amostra: bool = True) -> pd.DataFrame:
    log("PASSO 4 — Aplicando regras (formato wide)...")

    base = df[df["FST"].notna()].copy()   # apenas talhões com análise de solo

    if amostra:
        subset = (base.groupby("UNID_IND", group_keys=False)
                      .apply(lambda x: x.sample(min(N_POR_UNIDADE, len(x)), random_state=42),
                             include_groups=False))
        log(f"  Amostra: {len(subset):,} talhões ({subset['UNID_IND'].nunique()} unidades)")
        prefixo = "amostra_gold"
    else:
        subset = base
        log(f"  Processando todos: {len(subset):,} talhões com solo")
        prefixo = "gold"

    gold = pd.DataFrame(subset.apply(lambda r: _aplicar_regras_linha(r.to_dict()), axis=1).tolist())

    # Relatório rápido no terminal
    for nome, _, _ in REGRAS:
        col = f"{nome}_regra_acionada"
        if col in gold.columns:
            log(f"  {nome}: {gold[col].value_counts().to_dict()}")

    hoje = date.today().isoformat()
    gold.to_parquet(DATA_GOLD / f"{prefixo}_{hoje}.parquet", index=False)
    gold.to_csv(DATA_GOLD / f"{prefixo}_{hoje}.csv", index=False, encoding="utf-8-sig")
    log(f"  Salvo: {prefixo}_{hoje}.parquet e .csv ({len(gold):,} talhões × {gold.shape[1]} colunas)")
    return gold


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--todos", action="store_true", help="Processar todos os talhões com solo")
    args = parser.parse_args()

    log("=" * 55)
    log("Pipeline Gold — AgroTech ATVOS | Sprint 2")
    log("=" * 55)

    df1 = passo1_unificar_silver()
    df2 = passo2_aplicar_correcao(df1)
    df3 = passo3_join_solo(df2)
    df4 = passo4_gerar_gold(df3, amostra=not args.todos)

    log("=" * 55)
    log(f"Concluído. Gold: {len(df4):,} talhões × {df4.shape[1]} colunas.")
    log("=" * 55)
