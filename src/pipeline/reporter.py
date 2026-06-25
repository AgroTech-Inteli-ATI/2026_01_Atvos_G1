"""
src/pipeline/reporter.py
Responsabilidade única: exibir relatório de validação do DataFrame Gold no console.
"""
import pandas as pd


def relatorio_gold(df: pd.DataFrame) -> None:
    """Imprime resumo do output Gold para validação rápida após o pipeline."""
    print(f"\n{'='*65}")
    print("RELATÓRIO — CAMADA GOLD")
    print(f"{'='*65}")
    print(f"  Total de registros  : {len(df)}")
    print(f"  Talhões únicos      : {df['id_talhao'].nunique()}")
    print(f"  Unidades            : {sorted(df['unidade'].dropna().unique())}")

    print(f"\n  Por processo:")
    for proc in sorted(df["processo"].unique()):
        sub = df[df["processo"] == proc]
        sem_dado   = sub["regra_acionada"].str.startswith("dado_ausente").sum()
        suspeito   = sub["regra_acionada"].str.startswith("outlier_").sum()
        tem_insumo = sub["insumo"].notna().sum()
        extras = []
        if tem_insumo > 0:
            extras.append(f"com_insumo: {tem_insumo}")
        if suspeito > 0:
            extras.append(f"outliers: {suspeito}")
        extra_str = " | " + " | ".join(extras) if extras else ""
        print(f"    {proc:<22} {len(sub):>7} registros | SEM_DADO: {sem_dado}{extra_str}")

    print(f"\n  Regras mais acionadas (top 10):")
    top = df["regra_acionada"].value_counts().head(10)
    for regra, n in top.items():
        print(f"    {regra:<45} {n:>6}")

    area_total = df.drop_duplicates("id_talhao")["area_ha"].dropna().sum()
    print(f"\n  Área total coberta   : {area_total:,.1f} ha")
    print()
