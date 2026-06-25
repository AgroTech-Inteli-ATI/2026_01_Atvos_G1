"""
src/pipeline_gold.py
Orquestrador da pipeline Silver → Gold.

Uso:
    python src/pipeline_gold.py              # processa e salva
    python src/pipeline_gold.py --dry-run    # processa sem salvar

A lógica de cada etapa vive em src/pipeline/:
  loader.py      — leitura do Silver
  transformer.py — transformação com ThreadPoolExecutor (paralelismo por talhão)
  saver.py       — persistência em Parquet + CSV
  reporter.py    — relatório de validação no console
"""

import sys
from datetime import date

from pipeline.loader      import carregar_silver
from pipeline.transformer import aplicar_regras, preparar_talhao, COLUNAS_GOLD
from pipeline.saver       import salvar_gold
from pipeline.reporter    import relatorio_gold
from pipeline.utils       import log

# Re-exporta os nomes que os testes importam diretamente de pipeline_gold
# (compatibilidade retroativa — não alterar)
_preparar_talhao = preparar_talhao
_aplicar_regras  = aplicar_regras


def executar_pipeline(dry_run: bool = False) -> "pd.DataFrame":
    """
    Executa o pipeline completo Silver → Gold.

    Etapas:
      1. Carregar Silver (loader)
      2. Aplicar regras em paralelo (transformer)
      3. Imprimir relatório (reporter)
      4. Salvar Gold em Parquet + CSV (saver) — pulado em dry_run

    Parameters
    ----------
    dry_run : bool
        Se True, exibe o relatório mas não persiste os arquivos.

    Returns
    -------
    DataFrame Gold com as orientações geradas.
    """
    hoje = date.today()
    log("START", "pipeline_gold", f"data_geracao={hoje} | dry_run={dry_run}")

    df_silver = carregar_silver()

    from rules import REGRAS
    log("RULES", f"{len(REGRAS)} processos", str(list(REGRAS.keys())))

    df_gold = aplicar_regras(df_silver, hoje)
    relatorio_gold(df_gold)

    if not dry_run:
        caminhos = salvar_gold(df_gold, hoje)
        log("DONE", "Gold salvo", str(caminhos))
    else:
        log("DRY-RUN", "arquivos NÃO salvos")

    return df_gold


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    executar_pipeline(dry_run=dry)
