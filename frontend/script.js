const records = [
  {
    id: "410149",
    unit: "UMV",
    process: "erradicacao",
    orientation: "MONITORAR: canavial tardio com sexto corte.",
    input: "none",
    inputLabel: "-",
    dose: "-",
    rule: "erradicacao_corte_alto_tch_ok",
    date: "08/06/2026",
    status: "monitor",
  },
  {
    id: "410150",
    unit: "UMV",
    process: "calagem",
    orientation: "SEM_DADO: pH do solo ausente.",
    input: "calcario",
    inputLabel: "Calcario dolomitico",
    dose: "-",
    rule: "dado_ausente_analise_solo",
    date: "08/06/2026",
    status: "attention",
  },
  {
    id: "410152",
    unit: "URC",
    process: "janela_plantio",
    orientation: "Plantio DENTRO DA JANELA ideal.",
    input: "mudas",
    inputLabel: "Mudas",
    dose: "14.500",
    rule: "janela_dentro_do_ideal",
    date: "08/06/2026",
    status: "ok",
  },
  {
    id: "410155",
    unit: "URC",
    process: "fosfatagem",
    orientation: "Fosfatagem corretiva recomendada: 120 kg/ha.",
    input: "fosforo",
    inputLabel: "P2O5",
    dose: "120",
    rule: "fosfatagem_manutencao_cana_planta",
    date: "08/06/2026",
    status: "attention",
  },
  {
    id: "410158",
    unit: "UEL",
    process: "gessagem",
    orientation: "Aplicar gesso agricola conforme analise de subsolo.",
    input: "gesso",
    inputLabel: "Gesso agricola",
    dose: "2.500",
    rule: "gessagem_necessaria",
    date: "08/06/2026",
    status: "attention",
  },
  {
    id: "410163",
    unit: "UEL",
    process: "erradicacao",
    orientation: "ERRADICACAO RECOMENDADA: TCH baixo e corte alto.",
    input: "none",
    inputLabel: "-",
    dose: "-",
    rule: "erradicacao_tch_baixo_e_corte_alto",
    date: "08/06/2026",
    status: "urgent",
  },
  {
    id: "410172",
    unit: "UCP",
    process: "calagem",
    orientation: "Calagem superficial recomendada.",
    input: "calcario",
    inputLabel: "Calcario calcitico",
    dose: "3.200",
    rule: "calagem_superficial",
    date: "08/06/2026",
    status: "attention",
  },
  {
    id: "410181",
    unit: "UCP",
    process: "fosfatagem",
    orientation: "Dose de manutencao calculada para cana soca.",
    input: "fosforo",
    inputLabel: "P2O5",
    dose: "31,7",
    rule: "fosfatagem_manutencao_soca",
    date: "08/06/2026",
    status: "ok",
  },
  {
    id: "410194",
    unit: "URC",
    process: "janela_plantio",
    orientation: "ATENCAO: colheita estimada fora da janela ideal.",
    input: "mudas",
    inputLabel: "Mudas",
    dose: "12.800",
    rule: "janela_fora_do_ideal",
    date: "08/06/2026",
    status: "attention",
  },
  {
    id: "410205",
    unit: "UMV",
    process: "gessagem",
    orientation: "Gessagem nao necessaria para o talhao.",
    input: "gesso",
    inputLabel: "Gesso agricola",
    dose: "0",
    rule: "gessagem_nao_necessaria",
    date: "08/06/2026",
    status: "ok",
  },
];

const elements = {
  body: document.querySelector("#records-body"),
  emptyState: document.querySelector("#empty-state"),
  visibleRecords: document.querySelector("#visible-records"),
  filteredCount: document.querySelector("#filtered-count"),
  progress: document.querySelector("#summary-progress"),
  activeFilters: document.querySelector("#active-filters"),
  search: document.querySelector("#search-input"),
  unit: document.querySelector("#unit-filter"),
  process: document.querySelector("#process-filter"),
  input: document.querySelector("#input-filter"),
  status: document.querySelector("#status-filter"),
  reset: document.querySelector("#reset-filters"),
  export: document.querySelector("#export-button"),
  toast: document.querySelector("#toast"),
  mobileFilter: document.querySelector("#mobile-filter-button"),
  filtersPanel: document.querySelector("#filters-panel"),
};

const labels = {
  process: {
    calagem: "Calagem",
    gessagem: "Gessagem",
    fosfatagem: "Fosfatagem",
    erradicacao: "Erradicacao",
    janela_plantio: "Janela de plantio",
  },
  status: {
    urgent: "Urgente",
    attention: "Atencao",
    monitor: "Monitorar",
    ok: "Sem alerta",
  },
};

let filteredRecords = [...records];
let toastTimer;

function normalizeText(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function getFilters() {
  return {
    search: normalizeText(elements.search.value.trim()),
    unit: elements.unit.value,
    process: elements.process.value,
    input: elements.input.value,
    status: elements.status.value,
  };
}

function matchesSearch(record, search) {
  if (!search) return true;

  return [
    record.id,
    record.unit,
    record.process,
    record.orientation,
    record.inputLabel,
    record.rule,
  ].some((value) => normalizeText(value).includes(search));
}

function renderRecords() {
  const filters = getFilters();

  filteredRecords = records.filter((record) => {
    return (
      matchesSearch(record, filters.search) &&
      (filters.unit === "all" || record.unit === filters.unit) &&
      (filters.process === "all" || record.process === filters.process) &&
      (filters.input === "all" || record.input === filters.input) &&
      (filters.status === "all" || record.status === filters.status)
    );
  });

  elements.body.innerHTML = filteredRecords
    .map(
      (record) => `
        <tr class="${record.status === "urgent" ? "row-urgent" : ""}">
          <td>${record.id}</td>
          <td>${record.unit}</td>
          <td><span class="process-label">${labels.process[record.process]}</span></td>
          <td title="${record.orientation}">${record.orientation}</td>
          <td>${record.inputLabel}</td>
          <td>${record.dose}</td>
          <td title="${record.rule}">${record.rule}</td>
          <td>${record.date}</td>
          <td>
            <span class="status-badge status-${record.status}">
              ${labels.status[record.status]}
            </span>
          </td>
        </tr>
      `,
    )
    .join("");

  elements.visibleRecords.textContent = filteredRecords.length;
  elements.emptyState.hidden = filteredRecords.length > 0;
  elements.body.closest(".table-wrapper").hidden = filteredRecords.length === 0;

  const estimatedTotal = Math.round(
    67426 * (filteredRecords.length / records.length),
  );
  elements.filteredCount.textContent = estimatedTotal.toLocaleString("pt-BR");
  elements.progress.style.width = `${Math.max(
    4,
    (filteredRecords.length / records.length) * 100,
  )}%`;

  renderActiveFilters(filters);
}

function renderActiveFilters(filters) {
  const chips = [];

  if (filters.unit !== "all") chips.push(`Unidade: ${filters.unit}`);
  if (filters.process !== "all") {
    chips.push(`Processo: ${labels.process[filters.process]}`);
  }
  if (filters.input !== "all") {
    chips.push(
      `Insumo: ${elements.input.options[elements.input.selectedIndex].text}`,
    );
  }
  if (filters.status !== "all") {
    chips.push(`Status: ${labels.status[filters.status]}`);
  }
  if (filters.search) chips.push(`Busca: "${elements.search.value.trim()}"`);

  elements.activeFilters.innerHTML = chips
    .map((chip) => `<span class="filter-chip">${chip}</span>`)
    .join("");
}

function resetFilters() {
  elements.search.value = "";
  elements.unit.value = "all";
  elements.process.value = "all";
  elements.input.value = "all";
  elements.status.value = "all";
  renderRecords();
  showToast("Filtros removidos");
}

function escapeCsvValue(value) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

function exportCsv() {
  if (!filteredRecords.length) {
    showToast("Nao ha registros para exportar");
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

  const rows = filteredRecords.map((record) => [
    record.id,
    record.unit,
    record.process,
    record.orientation,
    record.inputLabel,
    record.dose,
    record.rule,
    record.date,
    labels.status[record.status],
  ]);

  const csv = [headers, ...rows]
    .map((row) => row.map(escapeCsvValue).join(";"))
    .join("\n");
  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `orientacoes_atvos_${new Date()
    .toISOString()
    .slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  showToast(`${filteredRecords.length} registros exportados`);
}

function showToast(message) {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => {
    elements.toast.classList.remove("is-visible");
  }, 2400);
}

function toggleMobileFilters() {
  const isOpen = elements.filtersPanel.classList.toggle("is-open");
  elements.mobileFilter.setAttribute("aria-expanded", String(isOpen));
}

[
  elements.unit,
  elements.process,
  elements.input,
  elements.status,
].forEach((select) => select.addEventListener("change", renderRecords));

elements.search.addEventListener("input", renderRecords);
elements.reset.addEventListener("click", resetFilters);
elements.export.addEventListener("click", exportCsv);
elements.mobileFilter.addEventListener("click", toggleMobileFilters);

renderRecords();
