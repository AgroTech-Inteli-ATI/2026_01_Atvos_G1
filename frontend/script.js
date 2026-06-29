/**
 * Monitor Agronomico Atvos — SPA
 * Três views: Dashboard, Talhões, Relatórios.
 * Consome http://localhost:8000/api  (src/api/server.py).
 * Fallback para dados de demonstração quando a API está offline.
 */

const API = "http://localhost:8000/api";
const PER = 20;

// ── Labels ─────────────────────────────────────────────────────────────────
const PROC = {
  calagem:           "Calagem",
  gessagem:          "Gessagem",
  fosfatagem:        "Fosfatagem",
  fosfatagem_insumo: "Fosfatagem Insumo",
  erradicacao:       "Erradicação",
  janela_plantio:    "Janela de Plantio",
  dessecacao:        "Dessecação",
};

const STATUS = { urgent: "Urgente", attention: "Atenção", monitor: "Monitorar", ok: "OK" };

// ── Demo data ───────────────────────────────────────────────────────────────
const DEMO_RECS = [
  { id_talhao:"41014900010008", chave:"410149-1-8", unidade:"UMV", safra:"22122",
    processo:"erradicacao", orientacao:"MONITORAR: desempenho abaixo do esperado (3º corte, TCH 49.0 t/ha)",
    regra_acionada:"medio_tch_monitorar", insumo:"", dose_kg_ha:"", quantidade_total_kg:"",
    data_geracao:"2026-06-11", status:"monitor" },
  { id_talhao:"41014900020001", chave:"410149-2-1", unidade:"UMV", safra:"22122",
    processo:"calagem", orientacao:"SEM_DADO: pH do solo ausente.",
    regra_acionada:"dado_ausente_ph_solo", insumo:"calcario_dolomitico",
    dose_kg_ha:"", quantidade_total_kg:"", data_geracao:"2026-06-11", status:"attention" },
  { id_talhao:"41015200030002", chave:"410152-3-2", unidade:"URC", safra:"22122",
    processo:"janela_plantio", orientacao:"Plantio DENTRO DA JANELA ideal.",
    regra_acionada:"janela_dentro_do_ideal", insumo:"mudas",
    dose_kg_ha:"14500", quantidade_total_kg:"72500", data_geracao:"2026-06-11", status:"ok" },
  { id_talhao:"41015500040001", chave:"410155-4-1", unidade:"URC", safra:"22122",
    processo:"fosfatagem", orientacao:"Fosfatagem corretiva recomendada: 120 kg/ha.",
    regra_acionada:"fosfatagem_manutencao_cana_planta", insumo:"p2o5",
    dose_kg_ha:"120", quantidade_total_kg:"600", data_geracao:"2026-06-11", status:"attention" },
  { id_talhao:"41015800050003", chave:"410158-5-3", unidade:"UEL", safra:"22122",
    processo:"gessagem", orientacao:"Aplicar gesso agrícola conforme análise de subsolo.",
    regra_acionada:"gessagem_necessaria", insumo:"gesso_agricola",
    dose_kg_ha:"2500", quantidade_total_kg:"12500", data_geracao:"2026-06-11", status:"attention" },
  { id_talhao:"41016300060001", chave:"410163-6-1", unidade:"UEL", safra:"22122",
    processo:"erradicacao", orientacao:"ERRADICACAO RECOMENDADA: TCH baixo e corte alto.",
    regra_acionada:"erradicacao_tch_baixo_e_corte_alto", insumo:"",
    dose_kg_ha:"", quantidade_total_kg:"", data_geracao:"2026-06-11", status:"urgent" },
  { id_talhao:"41017200070002", chave:"410172-7-2", unidade:"UCP", safra:"22122",
    processo:"calagem", orientacao:"Calagem superficial recomendada.",
    regra_acionada:"calagem_superficial", insumo:"calcario_calcitico",
    dose_kg_ha:"3200", quantidade_total_kg:"16000", data_geracao:"2026-06-11", status:"attention" },
  { id_talhao:"41018100080001", chave:"410181-8-1", unidade:"UCP", safra:"22122",
    processo:"fosfatagem", orientacao:"Dose de manutenção calculada para cana soca.",
    regra_acionada:"fosfatagem_manutencao_soca", insumo:"p2o5",
    dose_kg_ha:"31.7", quantidade_total_kg:"158.5", data_geracao:"2026-06-11", status:"ok" },
  { id_talhao:"41019400090004", chave:"410194-9-4", unidade:"URC", safra:"22122",
    processo:"janela_plantio", orientacao:"ATENCAO: colheita estimada fora da janela ideal.",
    regra_acionada:"janela_fora_do_ideal", insumo:"mudas",
    dose_kg_ha:"12800", quantidade_total_kg:"64000", data_geracao:"2026-06-11", status:"attention" },
  { id_talhao:"41020500100001", chave:"410205-10-1", unidade:"UMV", safra:"22122",
    processo:"gessagem", orientacao:"Gessagem não necessária para o talhão.",
    regra_acionada:"gessagem_nao_necessaria", insumo:"gesso_agricola",
    dose_kg_ha:"0", quantidade_total_kg:"0", data_geracao:"2026-06-11", status:"ok" },
];

const DEMO_META = {
  total_registros: 471982, total_talhoes: 67426,
  urgent: 0, attention: 159181, monitor: 11179, ok: 301622,
  unidades:  ["UAE","UAT","UCP","UCR","UEL","UMV","URC","USL"],
  processos: ["calagem","dessecacao","erradicacao","fosfatagem","fosfatagem_insumo","gessagem","janela_plantio"],
};

function buildDemoTalhoes(recs) {
  const g = {};
  const pri = { urgent: 3, attention: 2, monitor: 1, ok: 0 };
  for (const r of recs) {
    if (!g[r.id_talhao]) g[r.id_talhao] = {
      id_talhao: r.id_talhao, chave: r.chave, unidade: r.unidade,
      safra: r.safra, status_geral: "ok", _p: 0, alertas: [], total_alertas: 0,
    };
    const t = g[r.id_talhao];
    if ((pri[r.status] ?? 0) > t._p) { t._p = pri[r.status]; t.status_geral = r.status; }
    if (r.status !== "ok") { t.alertas.push(r.processo); t.total_alertas++; }
  }
  return Object.values(g).map(t => { const { _p, ...rest } = t; return rest; });
}

function buildDemoRelatorio(recs) {
  const proc = {}, unit = {};
  const _pct = (a, t) => t > 0 ? Math.round(a / t * 100) : 0;
  for (const r of recs) {
    if (!proc[r.processo]) proc[r.processo] = {
      total:0, urgent:0, attention:0, monitor:0, ok:0, sem_dado:0,
      area_urgent_ha:0, area_attention_ha:0, area_monitor_ha:0, area_ok_ha:0, area_total_ha:0,
    };
    proc[r.processo].total++;
    proc[r.processo][r.status]++;
    if (r.regra_acionada.includes("dado_ausente")) proc[r.processo].sem_dado++;
    proc[r.processo][`area_${r.status}_ha`] += 5;
    proc[r.processo].area_total_ha += 5;

    if (!unit[r.unidade]) unit[r.unidade] = {
      talhoes: new Set(), urgent:0, attention:0, monitor:0, ok:0,
      area_urgent_ha:0, area_attention_ha:0, area_monitor_ha:0, area_ok_ha:0, area_total_ha:0,
    };
    unit[r.unidade].talhoes.add(r.id_talhao);
    unit[r.unidade][r.status]++;
    unit[r.unidade][`area_${r.status}_ha`] += 5;
    unit[r.unidade].area_total_ha += 5;
  }
  return {
    por_processo: Object.entries(proc).map(([p,d]) => ({
      processo:p, label: PROC[p]||p, ...d,
      pct_area_urgent:    _pct(d.area_urgent_ha,    d.area_total_ha),
      pct_area_attention: _pct(d.area_attention_ha, d.area_total_ha),
      pct_area_monitor:   _pct(d.area_monitor_ha,   d.area_total_ha),
      pct_area_ok:        _pct(d.area_ok_ha,        d.area_total_ha),
    })),
    por_unidade: Object.entries(unit).map(([u,d]) => ({
      unidade:u, total_talhoes: d.talhoes.size,
      urgent:d.urgent, attention:d.attention, monitor:d.monitor, ok:d.ok,
      area_total_ha:      d.area_total_ha,
      pct_area_urgent:    _pct(d.area_urgent_ha,    d.area_total_ha),
      pct_area_attention: _pct(d.area_attention_ha, d.area_total_ha),
      pct_area_monitor:   _pct(d.area_monitor_ha,   d.area_total_ha),
      pct_area_ok:        _pct(d.area_ok_ha,        d.area_total_ha),
    })),
    top_regras: [
      { regra:"dado_ausente_ph_solo",          total:67426, pct:14.3 },
      { regra:"dado_ausente_p_disponivel",     total:67426, pct:14.3 },
      { regra:"categoria_nao_plantio",         total:58608, pct:12.4 },
      { regra:"textura_arenoso_sem_analise_al",total:30107, pct:6.4  },
    ],
  };
}

const DEMO_TALHOES   = buildDemoTalhoes(DEMO_RECS);
const DEMO_RELATORIO = buildDemoRelatorio(DEMO_RECS);

let _relatorioTotalAll = 471982;  // atualizado por renderRelatorio()

// ── Estado global ───────────────────────────────────────────────────────────
let isDemo = false;

const dashState = {
  page: 1, total: 0, total_pages: 1,
  filters: { unit:"all", processo:"all", status:"all", search:"" },
};
const talhoesState = {
  page: 1, total: 0, total_pages: 1,
  filters: { unit:"all", status:"all", search:"" },
  loaded: false,
};
let relatorioLoaded = false;

// ── Helpers DOM ─────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const e = (id) => document.getElementById(id);

function esc(s) {
  return String(s ?? "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Toast ───────────────────────────────────────────────────────────────────
let _tt;
function toast(msg) {
  clearTimeout(_tt);
  const el = e("toast");
  el.textContent = msg;
  el.classList.add("show");
  _tt = setTimeout(() => el.classList.remove("show"), 2500);
}

// ── Modal ───────────────────────────────────────────────────────────────────
function openModal(title, bodyHtml) {
  e("modal-title").textContent = title;
  e("modal-body").innerHTML = bodyHtml;
  e("modal").hidden = false;
  e("modal-close").focus();
}
function closeModal() { e("modal").hidden = true; }

// ── Pagination ──────────────────────────────────────────────────────────────
function buildRange(cur, max) {
  if (max <= 7) return Array.from({ length: max }, (_, i) => i + 1);
  if (cur <= 4) return [1, 2, 3, 4, 5, "…", max];
  if (cur >= max - 3) return [1, "…", max-4, max-3, max-2, max-1, max];
  return [1, "…", cur-1, cur, cur+1, "…", max];
}

function renderPagination(containerId, cur, total_pages, onPageClick) {
  const container = e(containerId);
  if (total_pages <= 1) { container.innerHTML = ""; return; }
  const range = buildRange(cur, total_pages);
  container.innerHTML = [
    `<button class="page-btn" data-p="${cur-1}" ${cur===1?"disabled":""}>‹</button>`,
    ...range.map(p => p === "…"
      ? `<span class="page-ellipsis">…</span>`
      : `<button class="page-btn ${p===cur?"active":""}" data-p="${p}">${p}</button>`
    ),
    `<button class="page-btn" data-p="${cur+1}" ${cur===total_pages?"disabled":""}>›</button>`,
  ].join("");
  container.querySelectorAll("[data-p]").forEach(btn =>
    btn.addEventListener("click", () => onPageClick(Number(btn.dataset.p)))
  );
}

// ── Router ──────────────────────────────────────────────────────────────────
const VIEWS_WITH_SIDEBAR = ["dashboard", "talhoes"];
let currentView = "";

function navigate(view) {
  if (!["dashboard","talhoes","relatorios"].includes(view)) view = "dashboard";
  console.log("[Navigate]", view, "| prev:", currentView, "| relatorioLoaded:", relatorioLoaded, "| isDemo:", isDemo);
  if (view === currentView) { console.log("[Navigate] já nessa view, ignorando"); return; }
  currentView = view;

  // Nav links
  document.querySelectorAll(".nav-link").forEach(a =>
    a.classList.toggle("active", a.dataset.view === view)
  );

  // Views
  document.querySelectorAll(".view").forEach(v => v.hidden = true);
  e(`view-${view}`).hidden = false;

  // Sidebar panels
  document.querySelectorAll(".sidebar-panel").forEach(p => p.hidden = true);
  const panel = e(`sidebar-${view}`);
  const hasSidebar = VIEWS_WITH_SIDEBAR.includes(view);
  e("layout").classList.toggle("no-sidebar", !hasSidebar);
  if (hasSidebar && panel) panel.hidden = false;

  // Load data
  if (view === "talhoes" && !talhoesState.loaded) refreshTalhoes();
  if (view === "relatorios" && !relatorioLoaded)  loadRelatorio();
}

// ── API fetch helpers ────────────────────────────────────────────────────────
async function apiFetch(path) {
  const url = `${API}${path}`;
  console.log("[API] GET", url);
  const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
  console.log("[API]", res.status, url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function filterStr(f, extra = {}) {
  return new URLSearchParams({ ...f, ...extra }).toString();
}

function demoFilter(recs, f) {
  const s = (f.search || "").toLowerCase();
  return recs.filter(r => {
    if (f.unit     && f.unit     !== "all" && r.unidade     !== f.unit)      return false;
    if (f.processo && f.processo !== "all" && r.processo    !== f.processo)  return false;
    if (f.status   && f.status   !== "all" && r.status      !== f.status)    return false;
    if (f.status_geral && f.status_geral !== "all" && r.status_geral !== f.status_geral) return false;
    if (s) {
      const hay = [r.id_talhao,r.chave,r.unidade,r.processo,
                   r.orientacao,r.regra_acionada,r.insumo||""].join(" ").toLowerCase();
      if (!hay.includes(s)) return false;
    }
    return true;
  });
}

function demoPage(arr, page) {
  const total = arr.length;
  const pages = Math.max(1, Math.ceil(total / PER));
  const p     = Math.min(page, pages);
  return { records: arr.slice((p-1)*PER, p*PER), total, page: p, total_pages: pages };
}

// ── DASHBOARD ────────────────────────────────────────────────────────────────

async function refreshDash() {
  const f   = dashState.filters;
  const qs  = filterStr({ page: dashState.page, per_page: PER, ...f });
  let result;

  if (isDemo) {
    result = demoPage(demoFilter(DEMO_RECS, f), dashState.page);
  } else {
    try {
      result = await apiFetch(`/data?${qs}`);
    } catch {
      isDemo = true; toast("API offline — modo demonstração");
      result = demoPage(demoFilter(DEMO_RECS, f), dashState.page);
    }
  }

  dashState.total       = result.total;
  dashState.total_pages = result.total_pages;
  dashState.page        = result.page;

  renderDashTable(result.records);
  renderPagination("d-pagination", dashState.page, dashState.total_pages, p => {
    dashState.page = p; refreshDash();
  });
  renderDashChips();
  e("d-showing").textContent = result.records.length.toLocaleString("pt-BR");
  e("d-total").textContent   = result.total.toLocaleString("pt-BR");
}

function renderDashTable(rows) {
  e("d-empty").hidden = rows.length > 0;
  if (!rows.length) { e("d-tbody").innerHTML = ""; return; }
  e("d-tbody").innerHTML = rows.map((r, i) => {
    const dose = r.dose_kg_ha
      ? Number(r.dose_kg_ha).toLocaleString("pt-BR", { maximumFractionDigits: 1 })
      : "—";
    return `<tr${r.status==="urgent"?' class="row-urgent"':""}>
      <td title="${esc(r.chave)}">${esc(r.id_talhao)}</td>
      <td>${esc(r.unidade)}</td>
      <td><span class="process-tag">${esc(PROC[r.processo]||r.processo)}</span></td>
      <td title="${esc(r.orientacao)}">${esc(r.orientacao)}</td>
      <td title="${esc(r.insumo)}">${esc(r.insumo||"—")}</td>
      <td>${esc(dose)}</td>
      <td title="${esc(r.regra_acionada)}" style="max-width:150px">${esc(r.regra_acionada)}</td>
      <td>${esc(r.data_geracao)}</td>
      <td><span class="badge badge-${r.status}">${esc(STATUS[r.status]||r.status)}</span></td>
      <td><button class="btn-ver" data-idx="${i}">Ver</button></td>
    </tr>`;
  }).join("");
  e("d-tbody")._rows = rows;
  e("d-tbody").querySelectorAll(".btn-ver").forEach(btn =>
    btn.addEventListener("click", () => openDashModal(e("d-tbody")._rows[+btn.dataset.idx]))
  );
}

function openDashModal(r) {
  const fields = [
    ["ID Talhão",      r.id_talhao],
    ["Chave",          r.chave],
    ["Unidade",        r.unidade],
    ["Safra",          r.safra],
    ["Processo",       PROC[r.processo]||r.processo],
    ["Orientação",     r.orientacao],
    ["Regra Acionada", r.regra_acionada],
    ["Insumo",         r.insumo||"—"],
    ["Dose kg/ha",     r.dose_kg_ha||"—"],
    ["Qtd Total kg",   r.quantidade_total_kg||"—"],
    ["Data Geração",   r.data_geracao],
    ["Status",         STATUS[r.status]||r.status],
  ];
  openModal(`Talhão ${r.id_talhao}`,
    `<dl class="modal-dl">${fields.map(([k,v])=>
      `<div class="modal-row"><dt>${esc(k)}</dt><dd>${esc(String(v))}</dd></div>`
    ).join("")}</dl>`
  );
}

function renderDashChips() {
  const f = dashState.filters;
  const items = [];
  if (f.unit     !== "all") items.push(`Unidade: ${f.unit}`);
  if (f.processo !== "all") items.push(`Processo: ${PROC[f.processo]||f.processo}`);
  if (f.status   !== "all") items.push(`Status: ${STATUS[f.status]}`);
  if (f.search)             items.push(`Busca: "${f.search}"`);
  e("d-chips").innerHTML = items.map(t => `<span class="chip">${esc(t)}</span>`).join("");
}

function applyDash() {
  dashState.filters = {
    unit:     e("d-unit").value,
    processo: e("d-processo").value,
    status:   e("d-status").value,
    search:   e("d-search").value.trim(),
  };
  dashState.page = 1;
  refreshDash();
}

function clearDash() {
  e("d-unit").value = e("d-processo").value = e("d-status").value = "all";
  e("d-search").value = "";
  dashState.filters = { unit:"all", processo:"all", status:"all", search:"" };
  dashState.page = 1;
  refreshDash();
  toast("Filtros removidos");
}

function exportDash() {
  if (isDemo) { toast("Exportação disponível apenas com a API ativa"); return; }
  const f = dashState.filters;
  window.location.href = `${API}/export?${filterStr(f)}`;
  toast("Exportação iniciada");
}

// ── TALHÕES ──────────────────────────────────────────────────────────────────

async function refreshTalhoes() {
  talhoesState.loaded = true;
  const f  = talhoesState.filters;
  const qs = filterStr({ page: talhoesState.page, per_page: PER, ...f });
  let result;

  if (isDemo) {
    const filtered = demoFilter(DEMO_TALHOES, { unit: f.unit, status_geral: f.status, search: f.search });
    result = demoPage(filtered, talhoesState.page);
  } else {
    try {
      result = await apiFetch(`/talhoes?${qs}`);
    } catch {
      isDemo = true; toast("API offline — modo demonstração");
      const filtered = demoFilter(DEMO_TALHOES, { unit: f.unit, status_geral: f.status, search: f.search });
      result = demoPage(filtered, talhoesState.page);
    }
  }

  talhoesState.total       = result.total;
  talhoesState.total_pages = result.total_pages;
  talhoesState.page        = result.page;

  renderTalhoesTable(result.records);
  renderPagination("t-pagination", talhoesState.page, talhoesState.total_pages, p => {
    talhoesState.page = p; refreshTalhoes();
  });
  renderTalhoesChips();
  e("t-showing").textContent = result.records.length.toLocaleString("pt-BR");
  e("t-total").textContent   = result.total.toLocaleString("pt-BR");
}

function renderTalhoesTable(rows) {
  e("t-empty").hidden = rows.length > 0;
  if (!rows.length) { e("t-tbody").innerHTML = ""; return; }

  e("t-tbody").innerHTML = rows.map((t, i) => {
    const pills = (t.alertas||[]).map(p => {
      const procRecords = isDemo ? DEMO_RECS.filter(r => r.id_talhao===t.id_talhao&&r.processo===p) : [];
      const s = procRecords[0]?.status || "attention";
      return `<span class="alert-pill pill-${s}">${esc(PROC[p]||p)}</span>`;
    }).join("") || `<span style="color:var(--text-300);font-size:11px">Nenhum</span>`;

    return `<tr${t.status_geral==="urgent"?' class="row-urgent"':""}>
      <td>${esc(t.id_talhao)}</td>
      <td>${esc(t.chave)}</td>
      <td>${esc(t.unidade)}</td>
      <td>${esc(t.safra)}</td>
      <td><span class="badge badge-${t.status_geral}">${esc(STATUS[t.status_geral]||t.status_geral)}</span></td>
      <td style="max-width:300px;white-space:normal"><div class="alert-pills">${pills}</div></td>
      <td><button class="btn-ver" data-idx="${i}">Ver processos</button></td>
    </tr>`;
  }).join("");

  e("t-tbody")._rows = rows;
  e("t-tbody").querySelectorAll(".btn-ver").forEach(btn =>
    btn.addEventListener("click", () => openTalhaoModal(e("t-tbody")._rows[+btn.dataset.idx]))
  );
}

async function openTalhaoModal(t) {
  let procs;
  if (isDemo) {
    procs = DEMO_RECS.filter(r => r.id_talhao === t.id_talhao);
  } else {
    try {
      const data = await apiFetch(`/talhao?id=${encodeURIComponent(t.id_talhao)}`);
      procs = data.records;
    } catch {
      procs = [];
      toast("Erro ao carregar processos");
    }
  }

  const meta = `
    <dl class="modal-talhao-meta">
      <div class="meta-item"><dt>ID Talhão</dt><dd>${esc(t.id_talhao)}</dd></div>
      <div class="meta-item"><dt>Unidade</dt><dd>${esc(t.unidade)}</dd></div>
      <div class="meta-item"><dt>Safra</dt><dd>${esc(t.safra)}</dd></div>
    </dl>`;

  const list = procs.length
    ? `<div class="proc-list">${procs.map(r => `
        <div class="proc-item">
          <div>
            <div class="proc-item-name">${esc(PROC[r.processo]||r.processo)}</div>
            <div class="proc-item-ori">${esc(r.orientacao)}</div>
            <div class="proc-item-regra">${esc(r.regra_acionada)}${r.dose_kg_ha ? ` · ${esc(r.dose_kg_ha)} kg/ha` : ""}</div>
          </div>
          <span class="badge badge-${r.status}">${esc(STATUS[r.status]||r.status)}</span>
        </div>`).join("")}</div>`
    : `<p style="color:var(--text-500);font-size:13px">Nenhum processo encontrado.</p>`;

  openModal(`Talhão ${t.id_talhao}`, meta + list);
}

function renderTalhoesChips() {
  const f = talhoesState.filters;
  const items = [];
  if (f.unit   !== "all") items.push(`Unidade: ${f.unit}`);
  if (f.status !== "all") items.push(`Status: ${STATUS[f.status]}`);
  if (f.search)           items.push(`Busca: "${f.search}"`);
  e("t-chips").innerHTML = items.map(t => `<span class="chip">${esc(t)}</span>`).join("");
}

function applyTalhoes() {
  talhoesState.filters = {
    unit:   e("t-unit").value,
    status: e("t-status").value,
    search: e("t-search").value.trim(),
  };
  talhoesState.page = 1;
  refreshTalhoes();
}

function clearTalhoes() {
  e("t-unit").value = e("t-status").value = "all";
  e("t-search").value = "";
  talhoesState.filters = { unit:"all", status:"all", search:"" };
  talhoesState.page = 1;
  refreshTalhoes();
  toast("Filtros removidos");
}

// ── RELATÓRIOS ───────────────────────────────────────────────────────────────

async function loadRelatorio() {
  console.log("[Relatorio] iniciando | isDemo:", isDemo);
  relatorioLoaded = true;
  e("relatorio-loading").hidden = false;
  e("relatorio-content").hidden = true;
  e("relatorio-loading").innerHTML =
    `<div class="spinner" aria-label="Carregando..."></div><p>Carregando relatório...</p>`;

  let data;
  try {
    if (isDemo) {
      console.log("[Relatorio] modo demo");
      data = DEMO_RELATORIO;
    } else {
      console.log("[Relatorio] buscando /api/relatorio …");
      data = await apiFetch("/relatorio");
      console.log("[Relatorio] recebido | processos:", data?.por_processo?.length,
                  "unidades:", data?.por_unidade?.length,
                  "regras:", data?.top_regras?.length);
    }
  } catch (err) {
    console.error("[Relatorio] erro na API:", err);
    isDemo = true;
    toast("API offline — modo demonstração");
    data = DEMO_RELATORIO;
  }

  try {
    renderRelatorio(data);
    console.log("[Relatorio] renderizado com sucesso");
    e("relatorio-loading").hidden = true;
    e("relatorio-content").hidden = false;
  } catch (err) {
    console.error("[Relatorio] erro ao renderizar:", err);
    e("relatorio-loading").innerHTML =
      `<p style="color:var(--red);margin:0 0 12px">Erro: ${err.message}</p>
       <button class="btn-primary" onclick="relatorioLoaded=false;loadRelatorio()">Tentar novamente</button>`;
  }
}

function exportRelatorio() {
  const date = new Date().toLocaleDateString("pt-BR", { day:"2-digit", month:"long", year:"numeric" });
  const meta = `Gerado em ${date} · ${_relatorioTotalAll.toLocaleString("pt-BR")} orientações · Safra 2026/27`;
  const pm = e("r-print-meta");
  if (pm) pm.textContent = meta;
  window.print();
}

function renderRelatorio(data) {
  const totalAll = data.por_processo.reduce((s, p) => s + p.total, 0) || 1;
  _relatorioTotalAll = totalAll;
  const nProc    = data.por_processo.length;
  const avaliacoes = Math.round(totalAll / nProc);   // linhas Silver = talhão × safra
  const talhoesUnicos = data.por_unidade.reduce((s, u) => s + u.total_talhoes, 0);
  const now = new Date().toLocaleDateString("pt-BR", { day:"2-digit", month:"long", year:"numeric" });
  const dg = e("r-data-geracao"); if (dg) dg.textContent = now;
  const pm = e("r-print-meta");   if (pm) pm.textContent = `Gerado em ${now} · ${totalAll.toLocaleString("pt-BR")} orientações`;

  // Fórmula explicativa dos números
  const fEl = e("r-formula");
  if (fEl) fEl.innerHTML = `
    <div class="rf-item rf-talhoes">
      <span class="rf-num">${talhoesUnicos.toLocaleString("pt-BR")}</span>
      <span class="rf-label">talhões únicos</span>
      <span class="rf-hint">IDs distintos no inventário</span>
    </div>
    <div class="rf-op">×</div>
    <div class="rf-item rf-safras">
      <span class="rf-num">~${(avaliacoes / talhoesUnicos).toFixed(1).replace(".",",")}</span>
      <span class="rf-label">safras por talhão</span>
      <span class="rf-hint">média — safras 21/22 e 22/23</span>
    </div>
    <div class="rf-op">=</div>
    <div class="rf-item rf-avaliacoes">
      <span class="rf-num">${avaliacoes.toLocaleString("pt-BR")}</span>
      <span class="rf-label">avaliações</span>
      <span class="rf-hint">linhas no relatório por processo</span>
    </div>
    <div class="rf-op">×</div>
    <div class="rf-item rf-processos">
      <span class="rf-num">${nProc}</span>
      <span class="rf-label">processos</span>
      <span class="rf-hint">calagem, gessagem, fosfatagem…</span>
    </div>
    <div class="rf-op">=</div>
    <div class="rf-item rf-total">
      <span class="rf-num">${totalAll.toLocaleString("pt-BR")}</span>
      <span class="rf-label">orientações Gold</span>
      <span class="rf-hint">total na camada Gold</span>
    </div>
  `;

  // Por processo
  e("r-proc-tbody").innerHTML = data.por_processo.map(p => `
    <tr>
      <td><strong>${esc(p.label||p.processo)}</strong></td>
      <td class="num-col">${p.total.toLocaleString("pt-BR")}</td>
      <td class="num-col ${p.urgent    ? "num-urgent"    : ""}">${(p.urgent||0).toLocaleString("pt-BR")}</td>
      <td class="num-col ${p.pct_area_urgent  ? "num-urgent"    : ""}">${p.pct_area_urgent  != null ? p.pct_area_urgent  + "%" : "—"}</td>
      <td class="num-col ${p.attention ? "num-attention" : ""}">${(p.attention||0).toLocaleString("pt-BR")}</td>
      <td class="num-col ${p.pct_area_attention ? "num-attention" : ""}">${p.pct_area_attention != null ? p.pct_area_attention + "%" : "—"}</td>
      <td class="num-col ${p.monitor   ? "num-monitor"   : ""}">${(p.monitor||0).toLocaleString("pt-BR")}</td>
      <td class="num-col ${p.ok        ? "num-ok"        : ""}">${(p.ok||0).toLocaleString("pt-BR")}</td>
      <td class="num-col">${(p.sem_dado||0).toLocaleString("pt-BR")}</td>
    </tr>`).join("");

  // Por unidade
  e("r-unit-tbody").innerHTML = data.por_unidade.map(u => `
    <tr>
      <td><strong>${esc(u.unidade)}</strong></td>
      <td class="num-col">${(u.total_talhoes||0).toLocaleString("pt-BR")}</td>
      <td class="num-col">${u.area_total_ha != null ? (u.area_total_ha||0).toLocaleString("pt-BR",{maximumFractionDigits:0}) : "—"}</td>
      <td class="num-col ${u.pct_area_urgent    ? "num-urgent"    : ""}">${u.pct_area_urgent    != null ? u.pct_area_urgent    + "%" : (u.urgent||0)}</td>
      <td class="num-col ${u.pct_area_attention ? "num-attention" : ""}">${u.pct_area_attention != null ? u.pct_area_attention + "%" : (u.attention||0)}</td>
      <td class="num-col ${u.pct_area_monitor   ? "num-monitor"   : ""}">${u.pct_area_monitor   != null ? u.pct_area_monitor   + "%" : (u.monitor||0)}</td>
      <td class="num-col ${u.pct_area_ok        ? "num-ok"        : ""}">${u.pct_area_ok        != null ? u.pct_area_ok        + "%" : (u.ok||0)}</td>
    </tr>`).join("");

  // Top regras
  const maxReg = data.top_regras[0]?.total || 1;
  e("r-regras-tbody").innerHTML = data.top_regras.map((r, i) => `
    <tr>
      <td class="num-col">${i + 1}</td>
      <td title="${esc(r.regra)}" style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(r.regra)}</td>
      <td class="num-col">${r.total.toLocaleString("pt-BR")}</td>
      <td class="num-col">${r.pct}%</td>
      <td class="bar-cell">
        <div class="mini-bar-wrap">
          <div class="mini-bar" style="width:${Math.round(r.total/maxReg*100)}%"></div>
        </div>
      </td>
    </tr>`).join("");
}

// ── Inicialização ────────────────────────────────────────────────────────────
async function init() {
  let meta = DEMO_META;
  try {
    meta = await apiFetch("/stats");
  } catch {
    isDemo = true;
    toast("API offline — exibindo dados de demonstração");
  }

  e("kpi-talhoes").textContent  = meta.total_talhoes.toLocaleString("pt-BR");
  e("kpi-urgent").textContent   = meta.urgent.toLocaleString("pt-BR");
  e("kpi-attention").textContent = meta.attention.toLocaleString("pt-BR");
  e("kpi-processos").textContent = meta.processos.length;

  // Nota: avaliações = registros Gold / processos = combinações talhão × safra
  const totalAvaliacoes = Math.round(meta.total_registros / meta.processos.length);
  const noteEl = e("kpi-note-avaliacoes");
  if (noteEl) noteEl.textContent = totalAvaliacoes.toLocaleString("pt-BR") + " combinações talhão × safra";

  // Rodapé da tela de Talhões
  const tf = e("t-footer-meta");
  if (tf) tf.textContent =
    `Silver · ${meta.total_talhoes.toLocaleString("pt-BR")} talhões únicos (IDs distintos) em ${totalAvaliacoes.toLocaleString("pt-BR")} combinações talhão × safra`;

  const safra = "2026/27";
  e("navbar-safra").textContent = `Safra ${safra}`;
  e("d-footer").textContent     = `Camada Gold · Safra ${safra}`;

  // Popula selects do Dashboard
  meta.unidades.forEach(u => {
    e("d-unit").add(new Option(u, u));
    e("t-unit").add(new Option(u, u));
  });
  meta.processos.forEach(p => e("d-processo").add(new Option(PROC[p]||p, p)));

  // Navegação hash — só aplica se o usuário ainda não navegou manualmente
  if (!currentView) {
    const hash = location.hash.replace("#","") || "dashboard";
    navigate(hash);
  }
  await refreshDash();
}

// ── Eventos globais ──────────────────────────────────────────────────────────

// Nav links
document.querySelectorAll(".nav-link").forEach(a =>
  a.addEventListener("click", e => { e.preventDefault(); navigate(a.dataset.view); })
);

// Dashboard
e("d-apply").addEventListener("click",  applyDash);
e("d-clear-top").addEventListener("click", clearDash);
e("d-clear").addEventListener("click",  clearDash);
e("d-export").addEventListener("click", exportDash);
e("d-search").addEventListener("keydown", ev => { if (ev.key === "Enter") applyDash(); });

// Talhões
e("t-apply").addEventListener("click",     applyTalhoes);
e("t-clear-top").addEventListener("click", clearTalhoes);
e("t-clear").addEventListener("click",     clearTalhoes);
e("t-search").addEventListener("keydown",  ev => { if (ev.key === "Enter") applyTalhoes(); });

// Modal
e("modal-close").addEventListener("click", closeModal);
e("modal").addEventListener("click", ev => { if (ev.target === e("modal")) closeModal(); });
document.addEventListener("keydown", ev => { if (ev.key === "Escape") closeModal(); });

// Hash routing (botão back/forward do browser)
window.addEventListener("hashchange", () =>
  navigate(location.hash.replace("#","") || "dashboard")
);

init();
