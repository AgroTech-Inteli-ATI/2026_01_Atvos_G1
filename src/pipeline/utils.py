"""Utilitário de log compartilhado pelo pacote pipeline."""
from datetime import datetime


def log(status: str, fonte: str, detalhe: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{status}] {fonte}" + (f" — {detalhe}" if detalhe else ""))
