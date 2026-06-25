"""
src/api/server.py
Backend HTTP para o Monitor Agronomico Atvos.
Le a camada Gold (Parquet preferencial, CSV como fallback) e expoe
endpoints JSON para o frontend.

Uso (da raiz do projeto):
    python src/api/server.py          # http://localhost:8000
    python src/api/server.py 5000     # porta alternativa
"""
import collections, csv, glob, io, json, mimetypes, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from datetime import datetime

GOLD_PATH    = "data/gold"
FRONTEND_DIR = "frontend"
PER_PAGE_MAX = 500

STATUS_PRIORITY = {"urgent": 3, "attention": 2, "monitor": 1, "ok": 0}

LABEL_PROCESSO = {
    "calagem":           "Calagem",
    "gessagem":          "Gessagem",
    "fosfatagem":        "Fosfatagem",
    "fosfatagem_insumo": "Fosfatagem Insumo",
    "erradicacao":       "Erradicação",
    "janela_plantio":    "Janela de Plantio",
    "dessecacao":        "Dessecação",
}

# ── Dados (carregados uma vez na inicialização) ────────────────────────────────

_RECORDS:   list | None = None
_META:      dict | None = None
_TALHOES:   list | None = None
_RELATORIO: dict | None = None
_INDEX:     dict | None = None   # id_talhao → [records]


_STR_COLS = [
    "id_talhao", "chave", "unidade", "safra", "processo", "orientacao",
    "regra_acionada", "insumo", "dose_kg_ha", "quantidade_total_kg", "data_geracao",
]


def _latest_gold() -> str:
    """Prefere Parquet (rapido, 4 MB) em vez de CSV (lento, 67 MB)."""
    for pat in ("orientacoes_*.parquet", "orientacoes_*.csv"):
        files = sorted(glob.glob(os.path.join(GOLD_PATH, pat)))
        if files:
            return files[-1]
    raise FileNotFoundError(
        f"Nenhum orientacoes_*.parquet ou .csv em '{GOLD_PATH}'.\n"
        "Execute src/pipeline_gold.py primeiro."
    )


def _classify(row: dict) -> str:
    regra = row.get("regra_acionada", "")
    ori   = row.get("orientacao", "").upper()
    if "dado_ausente" in regra or "SEM_DADO" in ori:
        return "attention"
    if "ERRADICACAO" in ori and "RECOMENDADA" in ori:
        return "urgent"
    if "MONITORAR" in ori or "monitorar" in regra:
        return "monitor"
    return "ok"


def _load() -> list:
    path = _latest_gold()
    t0   = datetime.now()

    if path.endswith(".parquet"):
        import pandas as pd
        import numpy as np

        df = pd.read_parquet(path)
        for col in _STR_COLS:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
            else:
                df[col] = ""

        regra     = df["regra_acionada"]
        ori_upper = df["orientacao"].str.upper()
        df["status"] = np.select(
            [
                regra.str.contains("dado_ausente", regex=False)
                    | ori_upper.str.contains("SEM_DADO", regex=False),
                ori_upper.str.contains("ERRADICACAO", regex=False)
                    & ori_upper.str.contains("RECOMENDADA", regex=False),
                ori_upper.str.contains("MONITORAR", regex=False)
                    | regra.str.contains("monitorar", regex=False),
            ],
            ["attention", "urgent", "monitor"],
            default="ok",
        )
        rows = df[_STR_COLS + ["status"]].to_dict("records")

    else:
        rows = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rows.append({
                    "id_talhao":           row.get("id_talhao", ""),
                    "chave":               row.get("chave", ""),
                    "unidade":             row.get("unidade", ""),
                    "safra":               row.get("safra", ""),
                    "processo":            row.get("processo", ""),
                    "orientacao":          row.get("orientacao", ""),
                    "regra_acionada":      row.get("regra_acionada", ""),
                    "insumo":              row.get("insumo") or "",
                    "dose_kg_ha":          row.get("dose_kg_ha") or "",
                    "quantidade_total_kg": row.get("quantidade_total_kg") or "",
                    "data_geracao":        row.get("data_geracao", ""),
                    "status":              _classify(row),
                })

    _log(f"{len(rows):,} registros carregados em {(datetime.now()-t0).total_seconds():.1f}s  <<  {path}")
    return rows


def _compute_meta(records: list) -> dict:
    counts    = {"urgent": 0, "attention": 0, "monitor": 0, "ok": 0}
    unidades  = set()
    processos = set()
    for r in records:
        counts[r["status"]] += 1
        if r["unidade"]:  unidades.add(r["unidade"])
        if r["processo"]: processos.add(r["processo"])
    return {
        "total_registros": len(records),
        "total_talhoes":   len({r["id_talhao"] for r in records}),
        **counts,
        "unidades":     sorted(unidades),
        "processos":    sorted(processos),
        "carregado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def _compute_talhoes(records: list) -> list:
    groups: dict = {}
    for r in records:
        tid = r["id_talhao"]
        if tid not in groups:
            groups[tid] = {
                "id_talhao":     tid,
                "chave":         r["chave"],
                "unidade":       r["unidade"],
                "safra":         r["safra"],
                "status_geral":  "ok",
                "_pri":          0,
                "alertas":       [],
                "total_alertas": 0,
            }
        g   = groups[tid]
        pri = STATUS_PRIORITY.get(r["status"], 0)
        if pri > g["_pri"]:
            g["_pri"]         = pri
            g["status_geral"] = r["status"]
        if r["status"] != "ok":
            g["alertas"].append(r["processo"])
            g["total_alertas"] += 1

    result = []
    for t in groups.values():
        del t["_pri"]
        t["alertas"] = list(dict.fromkeys(t["alertas"]))   # dedupe, preserva ordem
        result.append(t)
    return result


def _compute_relatorio(records: list) -> dict:
    por_proc  = collections.defaultdict(
        lambda: {"total": 0, "urgent": 0, "attention": 0, "monitor": 0, "ok": 0, "sem_dado": 0}
    )
    por_unit  = collections.defaultdict(
        lambda: {"_set": set(), "urgent": 0, "attention": 0, "monitor": 0, "ok": 0}
    )
    regras_ct = collections.Counter()
    total     = len(records)

    for r in records:
        por_proc[r["processo"]]["total"] += 1
        por_proc[r["processo"]][r["status"]] += 1
        if "dado_ausente" in r["regra_acionada"]:
            por_proc[r["processo"]]["sem_dado"] += 1

        por_unit[r["unidade"]]["_set"].add(r["id_talhao"])
        por_unit[r["unidade"]][r["status"]] += 1

        regras_ct[r["regra_acionada"]] += 1

    return {
        "por_processo": sorted(
            [{"processo": p, "label": LABEL_PROCESSO.get(p, p), **d}
             for p, d in por_proc.items()],
            key=lambda x: x["processo"],
        ),
        "por_unidade": sorted(
            [{"unidade": u,
              "total_talhoes": len(d["_set"]),
              "urgent":    d["urgent"],
              "attention": d["attention"],
              "monitor":   d["monitor"],
              "ok":        d["ok"]}
             for u, d in por_unit.items()],
            key=lambda x: x["unidade"],
        ),
        "top_regras": [
            {"regra": r, "total": ct, "pct": round(ct / total * 100, 1) if total else 0}
            for r, ct in regras_ct.most_common(15)
        ],
    }


def _compute_index(records: list) -> dict:
    idx: dict = collections.defaultdict(list)
    for r in records:
        idx[r["id_talhao"]].append(r)
    return dict(idx)


def get_data():
    global _RECORDS, _META, _TALHOES, _RELATORIO, _INDEX
    if _RECORDS is None:
        _RECORDS   = _load()
        _META      = _compute_meta(_RECORDS)
        _TALHOES   = _compute_talhoes(_RECORDS)
        _RELATORIO = _compute_relatorio(_RECORDS)
        _INDEX     = _compute_index(_RECORDS)
        _log(f"Pronto: {len(_TALHOES):,} talhoes indexados")
    return _RECORDS, _META, _TALHOES, _RELATORIO, _INDEX


# ── Filtros ────────────────────────────────────────────────────────────────────

def _filter_records(records: list, q) -> list:
    unit     = q("unit",     "all")
    processo = q("processo", "all")
    status   = q("status",   "all")
    search   = q("search",   "").lower().strip()
    out = []
    for r in records:
        if unit     != "all" and r["unidade"]  != unit:     continue
        if processo != "all" and r["processo"] != processo: continue
        if status   != "all" and r["status"]   != status:   continue
        if search:
            hay = (f"{r['id_talhao']} {r['chave']} {r['unidade']} "
                   f"{r['processo']} {r['orientacao']} {r['regra_acionada']} {r['insumo']}").lower()
            if search not in hay:
                continue
        out.append(r)
    return out


def _filter_talhoes(talhoes: list, q) -> list:
    unit   = q("unit",   "all")
    status = q("status", "all")
    search = q("search", "").lower().strip()
    out = []
    for t in talhoes:
        if unit   != "all" and t["unidade"]      != unit:   continue
        if status != "all" and t["status_geral"] != status: continue
        if search:
            hay = f"{t['id_talhao']} {t['chave']} {t['unidade']}".lower()
            if search not in hay:
                continue
        out.append(t)
    return out


def _paginate(lst: list, q):
    page     = max(1, int(q("page",     "1")))
    per_page = min(PER_PAGE_MAX, max(1, int(q("per_page", "20"))))
    total    = len(lst)
    pages    = max(1, (total + per_page - 1) // per_page)
    page     = min(page, pages)
    i0, i1  = (page - 1) * per_page, page * per_page
    return lst[i0:i1], total, page, per_page, pages


# ── Handler HTTP ───────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *a):
        _log(f"{self.command} {self.path}  >>  {fmt % a}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, obj, status: int = 200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _file(self, rel: str):
        if not os.path.isfile(rel):
            return self._json({"error": "not found"}, 404)
        ct, _ = mimetypes.guess_type(rel)
        with open(rel, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type",    ct or "application/octet-stream")
        self.send_header("Content-Length",  str(len(body)))
        self.send_header("Cache-Control",   "no-cache, no-store, must-revalidate")
        self.send_header("Pragma",          "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _csv_dl(self, records: list):
        fields = ["id_talhao","chave","unidade","safra","processo","orientacao",
                  "regra_acionada","insumo","dose_kg_ha","quantidade_total_kg",
                  "data_geracao","status"]
        buf = io.StringIO()
        w   = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore",
                             lineterminator="\r\n")
        w.writeheader(); w.writerows(records)
        body  = ("﻿" + buf.getvalue()).encode("utf-8-sig")
        fname = f"orientacoes_atvos_{datetime.now():%Y-%m-%d}.csv"
        self.send_response(200)
        self.send_header("Content-Type",        "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.send_header("Content-Length",      str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)
        q      = lambda k, d="": qs.get(k, [d])[0]

        try:
            records, meta, talhoes, relatorio, index = get_data()

            if path == "/api/stats":
                self._json(meta); return

            if path == "/api/data":
                f = _filter_records(records, q)
                rows, total, page, pp, pages = _paginate(f, q)
                self._json({"records": rows, "total": total,
                            "page": page, "per_page": pp, "total_pages": pages})
                return

            if path == "/api/export":
                self._csv_dl(_filter_records(records, q)); return

            if path == "/api/talhoes":
                f = _filter_talhoes(talhoes, q)
                rows, total, page, pp, pages = _paginate(f, q)
                self._json({"records": rows, "total": total,
                            "page": page, "per_page": pp, "total_pages": pages})
                return

            if path == "/api/talhao":
                self._json({"records": index.get(q("id", ""), [])}); return

            if path == "/api/relatorio":
                self._json(relatorio); return

            if path in ("/", ""):
                self._file(os.path.join(FRONTEND_DIR, "index.html")); return
            if path in ("/styles.css", "/script.js"):
                self._file(os.path.join(FRONTEND_DIR, path.lstrip("/"))); return
            rel = path.lstrip("/")
            if rel.startswith(FRONTEND_DIR + "/"):
                self._file(rel); return

            self._json({"error": "not found"}, 404)

        except Exception as exc:
            import traceback; traceback.print_exc()
            self._json({"error": str(exc)}, 500)


# ── Main ───────────────────────────────────────────────────────────────────────

def _log(msg: str):
    print(f"[{datetime.now():%H:%M:%S}]  {msg}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(root)
    _log(f"Raiz: {root}")
    get_data()   # carrega todos os dados antes de aceitar conexões
    _log(f"Monitor Agronomico API  >>  http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
