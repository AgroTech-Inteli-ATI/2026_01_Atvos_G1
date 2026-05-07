import pandas as pd
from datetime import datetime

def load_csv(caminho, separador=",", encoding="utf-8"):
    try:
        df = pd.read_csv(caminho, sep=separador, encoding=encoding)
        print(f"[{datetime.now()}] [OK] {caminho} — {len(df)} linhas carregadas")
        return df
    except Exception as e:
        print(f"[{datetime.now()}] [ERRO] {caminho} — {e}")
        return None

def load_excel(caminho, aba=0):
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
        print(f"[{datetime.now()}] [OK] {caminho} — {len(df)} linhas carregadas")
        return df
    except Exception as e:
        print(f"[{datetime.now()}] [ERRO] {caminho} — {e}")
        return None