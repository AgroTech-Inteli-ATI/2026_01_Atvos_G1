"""
src/processing/run_processing.py
Executa a limpeza Raw → Silver em todos os arquivos de data/raw/.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.processing.clean_data import limpar

RAW_PATH = "data/raw"
EXTENSOES_SUPORTADAS = {".xlsx", ".xls", ".csv"}

if __name__ == "__main__":
    arquivos = sorted(
        f for f in os.listdir(RAW_PATH)
        if os.path.splitext(f)[1].lower() in EXTENSOES_SUPORTADAS
    )
    print(f"Arquivos encontrados em '{RAW_PATH}': {arquivos}\n")

    processados, erros = 0, 0
    for arquivo in arquivos:
        caminho = os.path.join(RAW_PATH, arquivo)
        try:
            limpar(caminho)
            processados += 1
        except Exception as e:
            print(f"[ERRO] {arquivo}: {e}")
            erros += 1

    print(f"\n{'='*60}")
    print(f"Concluído: {processados} processados, {erros} erro(s).")
