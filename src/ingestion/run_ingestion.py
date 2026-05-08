import sys, os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.ingestion.load_files import load_csv, load_excel

RAW_PATH = "data/raw"
dataframes = {}

for arquivo in os.listdir(RAW_PATH):
    caminho = os.path.join(RAW_PATH, arquivo)
    nome = os.path.splitext(arquivo)[0]  # nome sem extensão

    if arquivo.endswith(".xlsx") or arquivo.endswith(".xls"):
        dataframes[nome] = load_excel(caminho)
    elif arquivo.endswith(".csv"):
        dataframes[nome] = load_csv(caminho)

print(f"\n✅ {len(dataframes)} arquivo(s) carregado(s): {list(dataframes.keys())}")