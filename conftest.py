"""conftest.py — raiz do projeto. Configura sys.path para pytest."""
import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))

# src/ → importar rules, pipeline_gold, ingestion
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# tests/ → importar helpers (assert_resultado_valido, etc.)
_tests = os.path.join(_root, "tests")
if _tests not in sys.path:
    sys.path.insert(0, _tests)

# cwd = raiz do projeto (pipeline_gold usa caminhos relativos a ela)
os.chdir(_root)
