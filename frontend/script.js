const orientations = [
  {
    id: "410149",
    unit: "UMV",
    process: "erradicacao",
    orientation: "MONITORAR: canavial tardio...",
    input: "-",
    dose: "-",
    rule: "tardio_tch_adequado",
    date: "08/06/2026",
    status: "normal",
  },
  {
    id: "410150",
    unit: "UMV",
    process: "calagem",
    orientation: "SEM_DADO: pH_solo ausente",
    input: "-",
    dose: "-",
    rule: "dado_ausente_ph_solo",
    date: "08/06/2026",
    status: "normal",
  },
  {
    id: "410152",
    unit: "URC",
    process: "janela_plantio",
    orientation: "Plantio DENTRO DA JANELA: I",
    input: "-",
    dose: "-",
    rule: "plantio_dentro_janela",
    date: "08/06/2026",
    status: "normal",
  },
  {
    id: "410155",
    unit: "URC",
    process: "insumos",
    orientation: "Fosfatagem corretiva: 120 kg/ha P₂O₅",
    input: "P₂O₅",
    dose: "120",
    rule: "p_muito_baixo_cana",
    date: "08/06/2026",
    status: "normal",
  },
  {
    id: "410158",
    unit: "UEL",
    process: "insumos",
    orientation: "Dessecação: 2,5 L/ha glifosato",
    input: "Glifosato",
    dose: "2,5 L",
    rule: "dessecacao_alta",
    date: "08/06/2026",
    status: "normal",
  },
  {
    id: "410163",
    unit: "UEL",
    process: "erradicacao",
    orientation: "ERRADICAÇÃO RECOMENDADA",
    input: "-",
    dose: "-",
    rule: "tardio_tch_critico",
    date: "08/06/2026",
    status: "urgente",
  },
];

const elements = {
  rows: document.querySelector("#orientationRows"),
  unit: document.querySelector("#unitFilter"),
  process: document.querySelector("#processFilter"),
  input: document.querySelector("#inputFilter"),
  status: document.querySelector("#statusFilter"),
  search: document.querySelector("#searchInput"),
  clear: document.querySelector("#clearFilters"),
  export: document.querySelector("#exportButton"),
  count: document.querySelector("#resultCount"),
  description: document.querySelector("#tableDescription"),
  empty: document.querySelector("#emptyState"),
  table: document.querySelector(".table-wrapper"),
  toast: document.querySelector("#toast"),
};

const totalTalhoes = 67426;
let visibleRows = [...orientations];
let toastTimer;

function addOptions(select, values) {
  values
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b, "pt-BR"))
    .forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
}

function initializeFilters() {
  addOptions(elements.unit, [...new Set(orientations.map((item) => item.unit))]);
  addOptions(
    elements.process,
    [...new Set(orientations.map((item) => item.process))],
  );
  addOptions(
    elements.input,
    [...new Set(orientations.map((item) => item.input))].filter(
      (value) => value !== "-",
    ),
  );
}

function normalize(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function matchesSearch(item, query) {
  if (!query) return true;
  return Object.values(item).some((value) => normalize(value).includes(query));
}

function applyFilters() {
  const query = normalize(elements.search.value.trim());

  visibleRows = orientations.filter(
    (item) =>
      (!elements.unit.value || item.unit === elements.unit.value) &&
      (!elements.process.value || item.process === elements.process.value) &&
      (!elements.input.value || item.input === elements.input.value) &&
      (!elements.status.value || item.status === elements.status.value) &&
      matchesSearch(item, query),
  );

  renderRows();
}

function renderRows() {
  elements.rows.replaceChildren(
    ...visibleRows.map((item) => {
      const row = document.createElement("tr");
      if (item.status === "urgente") row.classList.add("is-urgent");

      row.innerHTML = `
        <td>${item.id}</td>
        <td>${item.unit}</td>
        <td class="process-tag">${item.process}</td>
        <td class="${item.status === "urgente" ? "orientation-urgent" : ""}" title="${item.orientation}">
          ${item.orientation}
        </td>
        <td>${item.input}</td>
        <td>${item.dose}</td>
        <td title="${item.rule}">${item.rule}</td>
        <td>${item.date}</td>
        <td>${item.status === "urgente" ? '<span class="alert-pill">Urgente</span>' : "-"}</td>
      `;

      return row;
    }),
  );

  const isFiltered =
    elements.unit.value ||
    elements.process.value ||
    elements.input.value ||
    elements.status.value ||
    elements.search.value.trim();

  const proportionalTotal = isFiltered
    ? Math.round(totalTalhoes * (visibleRows.length / orientations.length))
    : totalTalhoes;

  elements.count.textContent = proportionalTotal.toLocaleString("pt-BR");
  elements.description.textContent = `Exibindo ${visibleRows.length} de ${proportionalTotal.toLocaleString("pt-BR")} registros`;
  elements.empty.hidden = visibleRows.length > 0;
  elements.table.hidden = visibleRows.length === 0;
}

function clearFilters() {
  elements.unit.value = "";
  elements.process.value = "";
  elements.input.value = "";
  elements.status.value = "";
  elements.search.value = "";
  applyFilters();
  showToast("Filtros removidos.");
}

function escapeCsv(value) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

function exportCsv() {
  if (!visibleRows.length) {
    showToast("Não há registros para exportar.");
    return;
  }

  const headers = [
    "id_talhao",
    "unidade",
    "processo",
    "orientacao",
    "insumo",
    "dose_kg_ha",
    "regra_acionada",
    "data_geracao",
    "status",
  ];

  const rows = visibleRows.map((item) =>
    [
      item.id,
      item.unit,
      item.process,
      item.orientation,
      item.input,
      item.dose,
      item.rule,
      item.date,
      item.status,
    ]
      .map(escapeCsv)
      .join(";"),
  );

  const csv = `\uFEFF${[headers.join(";"), ...rows].join("\n")}`;
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "orientacoes-talhao.csv";
  link.click();
  URL.revokeObjectURL(url);
  showToast(`${visibleRows.length} registros exportados.`);
}

function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  toastTimer = setTimeout(() => {
    elements.toast.classList.remove("is-visible");
  }, 2400);
}

[elements.unit, elements.process, elements.input, elements.status].forEach(
  (filter) => filter.addEventListener("change", applyFilters),
);
elements.search.addEventListener("input", applyFilters);
elements.clear.addEventListener("click", clearFilters);
elements.export.addEventListener("click", exportCsv);

initializeFilters();
renderRows();
