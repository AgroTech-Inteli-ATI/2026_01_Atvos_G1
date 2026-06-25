"""
src/pipeline/
Pacote de pipeline Silver → Gold dividido por responsabilidade:

  loader.py      — leitura dos arquivos Silver
  transformer.py — transformação: Silver row → regras → registros Gold
  saver.py       — persistência do DataFrame Gold
  reporter.py    — relatório de validação em console
"""
