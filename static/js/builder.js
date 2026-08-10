const CATEGORIES = [
  "gpu",
  "cpu",
  "motherboard",
  "cooler",
  "ram",
  "storage",
  "psu",
  "case",
];

const CATEGORY_LABELS = {
  gpu: "GPU",
  cpu: "CPU",
  motherboard: "Motherboard",
  cooler: "CPU Cooler",
  ram: "RAM",
  storage: "Storage",
  psu: "PSU",
  case: "Case",
};

const REASON_CODE_CATEGORIES = {
  SOCKET_MISMATCH: ["cpu", "motherboard"],
  RAM_CPU_DDR_MISMATCH: ["ram", "cpu"],
  RAM_MOBO_DDR_MISMATCH: ["ram", "motherboard"],
  COOLER_TDP_INSUFFICIENT: ["cooler", "cpu"],
  COOLER_SOCKET_MISMATCH: ["cooler", "cpu"],
  GPU_TOO_LONG: ["gpu", "case"],
  MOBO_FORM_FACTOR_MISMATCH: ["motherboard", "case"],
  RADIATOR_TOO_LARGE: ["cooler", "case"],
  PSU_INSUFFICIENT: ["cpu", "gpu", "psu"],
};

const PAGE_SIZE = 10;

function parseEmbedded(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : null;
}

const CATALOGS = {
  gpu: parseEmbedded("gpus-data"),
  cpu: parseEmbedded("cpus-data"),
  motherboard: parseEmbedded("motherboards-data"),
  cooler: parseEmbedded("coolers-data"),
  ram: parseEmbedded("rams-data"),
  storage: parseEmbedded("storages-data"),
  psu: parseEmbedded("psus-data"),
  case: parseEmbedded("cases-data"),
};
const GPU_BENCHMARKS = parseEmbedded("gpu-benchmarks-data") || [];

const root = document.getElementById("builder-root");
const checkUrl = root.dataset.checkUrl;
const isAuthenticated = root.dataset.isAuthenticated === "true";

const selection = {};
const currentPage = {};
let currentStepIndex = 0;
const compatCache = new Map();

function getCsrfToken() {
  const name = "csrftoken";
  for (const part of document.cookie.split(";")) {
    const trimmed = part.trim();
    if (trimmed.startsWith(name + "=")) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }
  return "";
}

function buildPayload(excludeCategory) {
  const payload = {};
  for (const category of CATEGORIES) {
    if (category === excludeCategory) continue;
    if (selection[category] != null) payload[category] = selection[category];
  }
  if (selection.resolution) payload.target_resolution = selection.resolution;
  return payload;
}

function buildPayloadUpTo(categoryIndex) {
  // Only resolution + categories strictly *before* categoryIndex in
  // wizard order -- deliberately ignores any already-made later
  // selection, even if one exists from editing a fully-populated build.
  // Keeps predictive gray-out strictly one-directional.
  const payload = {};
  for (let i = 0; i < categoryIndex; i++) {
    const cat = CATEGORIES[i];
    if (selection[cat] != null) payload[cat] = selection[cat];
  }
  if (selection.resolution) payload.target_resolution = selection.resolution;
  return payload;
}

async function checkCompatibility(hypotheticalSelection) {
  const key = JSON.stringify(
    Object.keys(hypotheticalSelection)
      .sort()
      .map((k) => [k, hypotheticalSelection[k]]),
  );
  if (compatCache.has(key)) {
    return compatCache.get(key);
  }
  const response = await fetch(checkUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(hypotheticalSelection),
  });
  const data = await response.json();
  compatCache.set(key, data);
  return data;
}

async function computeGrayOutForCategory(category) {
  const categoryIndex = CATEGORIES.indexOf(category);
  const catalog = CATALOGS[category];
  const basePayload = buildPayloadUpTo(categoryIndex);

  const results = await Promise.all(
    catalog.map(async (item) => {
      const hypothetical = { ...basePayload, [category]: item.id };
      const result = await checkCompatibility(hypothetical);
      return {
        id: item.id,
        compatible: result.violations.length === 0,
        violations: result.violations,
      };
    }),
  );

  const map = {};
  results.forEach((r) => {
    map[r.id] = r;
  });
  return map;
}

function clearInvalidatedLaterSelections(violations) {
  let cleared = false;
  violations.forEach((violation) => {
    const involved = (
      REASON_CODE_CATEGORIES[violation.reason_code] || []
    ).filter((cat) => selection[cat] != null);
    if (involved.length < 2) return;
    // Only the single latest-in-wizard-order category among the ones
    // involved gets cleared. A 3-category rule like PSU_INSUFFICIENT
    // (cpu + gpu + psu) must not clear cpu just because gpu has the
    // smallest index -- only the actual dependent (psu) is cleared.
    const latest = involved.reduce((a, b) =>
      CATEGORIES.indexOf(a) > CATEGORIES.indexOf(b) ? a : b,
    );
    selection[latest] = null;
    cleared = true;
  });
  return cleared;
}

function furthestReachableIndex() {
  if (!selection.resolution) return 0;
  for (let i = 0; i < CATEGORIES.length; i++) {
    if (selection[CATEGORIES[i]] == null) return i + 1;
  }
  return CATEGORIES.length;
}

let nameManuallyEdited = false;
const nameInput = document.querySelector('#save-form input[name="name"]');
if (nameInput && nameInput.value.trim() !== "") {
  nameManuallyEdited = true;
}
if (nameInput) {
  nameInput.addEventListener("input", () => {
    nameManuallyEdited = true;
  });
}

function shortName(fullName) {
  return fullName
    .replace("NVIDIA GeForce ", "")
    .replace("AMD Radeon ", "")
    .replace("Intel Core ", "")
    .replace("AMD Ryzen ", "Ryzen ");
}

function updateAutoName() {
  if (!nameInput || nameManuallyEdited) return;
  const parts = [];
  if (selection.resolution) parts.push(selection.resolution);
  if (selection.gpu) {
    const gpu = CATALOGS.gpu.find((g) => g.id === selection.gpu);
    if (gpu) parts.push(shortName(gpu.name));
  }
  if (selection.cpu) {
    const cpu = CATALOGS.cpu.find((c) => c.id === selection.cpu);
    if (cpu) parts.push(shortName(cpu.name));
  }
  nameInput.value = parts.join(" · ");
}

function renderFpsPanel() {
  const container = document.getElementById("fps-panel");
  if (!container) return;

  if (!selection.gpu || !selection.resolution) {
    container.innerHTML = "";
    return;
  }
  if (!isAuthenticated) {
    container.innerHTML = `
            <div class="alert alert-secondary d-flex justify-content-between align-items-center flex-wrap gap-2">
                <span>Log in to see per-game FPS for this GPU at your chosen resolution.</span>
                <a href="/accounts/login/" class="btn btn-sm btn-outline-light">Log In</a>
            </div>`;
    return;
  }

  const rows = GPU_BENCHMARKS.filter(
    (b) => b.gpu_id === selection.gpu && b.resolution === selection.resolution,
  ).sort((a, b) => b.fps - a.fps);

  if (!rows.length) {
    container.innerHTML =
      '<p class="text-body-secondary">No benchmark data for this combination.</p>';
    return;
  }

  const rowsHtml = rows
    .map(
      (r) =>
        `<tr><td>${r.game}</td><td class="rc-mono text-end">${r.fps} FPS</td></tr>`,
    )
    .join("");
  container.innerHTML = `
        <h3 class="h6">Estimated Game Performance</h3>
        <table class="table table-sm">
            <tbody>${rowsHtml}</tbody>
        </table>`;
}

async function revalidateAll() {
  let payload = buildPayload();
  let result = await checkCompatibility(payload);

  if (clearInvalidatedLaterSelections(result.violations)) {
    payload = buildPayload();
    result = await checkCompatibility(payload);
  }

  renderViolations(result.violations);
  renderBottleneck(result.bottleneck_status);
  updateSaveFormFields();
  updateAutoName();
  renderFpsPanel();
  return result;
}

function renderViolations(violations) {
  const container = document.getElementById("violation-list");
  if (!violations.length) {
    container.innerHTML =
      '<p class="text-success mb-0">No compatibility issues so far.</p>';
    return;
  }
  container.innerHTML = violations
    .map((v) => `<div class="alert alert-warning py-2 mb-2">${v.message}</div>`)
    .join("");
}

function renderBottleneck(status) {
  document.getElementById("bottleneck-status").textContent = status
    ? `Bottleneck: ${status}`
    : "";
}

function updateSaveFormFields() {
  const resolutionField = document.getElementById("save-resolution");
  if (!resolutionField) return;
  resolutionField.value = selection.resolution || "";
  CATEGORIES.forEach((cat) => {
    document.getElementById(`save-${cat}`).value = selection[cat] || "";
  });
}

function averageFpsForGpu(gpuId, resolution) {
  if (!resolution) return null;
  const rows = GPU_BENCHMARKS.filter(
    (b) => b.gpu_id === gpuId && b.resolution === resolution,
  );
  if (!rows.length) return null;
  return Math.round(rows.reduce((sum, r) => sum + r.fps, 0) / rows.length);
}

function describeItem(category, item) {
  switch (category) {
    case "gpu": {
      const avgFps = averageFpsForGpu(item.id, selection.resolution);
      return `${item.brand} · ${item.vram}GB VRAM · ${item.tdp}W${avgFps ? ` · ~${avgFps} FPS avg` : ""}`;
    }
    case "cpu":
      return `${item.brand} · ${item.socket} · ${item.tdp}W`;
    case "motherboard":
      return `${item.brand} · ${item.socket} · ${item.form_factor} · ${item.ddr_support}`;
    case "cooler":
      return `${item.brand} · ${item.type} · up to ${item.tdp_support}W`;
    case "ram":
      return `${item.brand} · ${item.capacity_gb}GB ${item.ddr_type} · ${item.frequency_mhz}MHz`;
    case "storage":
      return `${item.brand} · ${item.capacity_gb}GB · ${item.interface_generation}`;
    case "psu":
      return `${item.brand} · ${item.wattage}W · ${item.efficiency_rating}`;
    case "case":
      return `${item.brand} · fits up to ${item.max_gpu_length_mm}mm GPU`;
    default:
      return "";
  }
}

function renderStepIndicator() {
  const container = document.getElementById("step-indicator");
  container.innerHTML = "";
  const labels = ["Resolution", ...CATEGORIES.map((c) => CATEGORY_LABELS[c])];
  const maxReachable = furthestReachableIndex();
  labels.forEach((label, index) => {
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className =
      "btn btn-sm " +
      (index === currentStepIndex ? "btn-primary" : "btn-outline-light");
    pill.textContent = `${index + 1}. ${label}`;
    pill.disabled = index > maxReachable;
    pill.addEventListener("click", () => {
      currentStepIndex = index;
      renderStep();
    });
    container.appendChild(pill);
  });
}

function renderPagination(category, totalItems, currentPageNum) {
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const container = document.getElementById("step-pagination");
  container.innerHTML = "";
  for (let p = 1; p <= totalPages; p++) {
    const li = document.createElement("li");
    li.className = "page-item" + (p === currentPageNum ? " active" : "");
    const link = document.createElement("button");
    link.type = "button";
    link.className = "page-link";
    link.textContent = String(p);
    link.addEventListener("click", () => {
      currentPage[category] = p;
      renderStep();
    });
    li.appendChild(link);
    container.appendChild(li);
  }
}

function renderResolutionStep() {
  document.getElementById("step-title").textContent = "Target Resolution";
  const container = document.getElementById("step-options");
  container.innerHTML = "";
  const resolutions = [
    { value: "1080p", label: "1080p (Full HD)" },
    { value: "1440p", label: "1440p (QHD)" },
    { value: "4K", label: "4K (UHD)" },
  ];
  resolutions.forEach((res) => {
    const col = document.createElement("div");
    col.className = "col-md-4";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className =
      "card w-100 rc-option-card" +
      (selection.resolution === res.value ? " rc-option-selected" : "");
    btn.innerHTML = `<div class="card-body fw-semibold">${res.label}</div>`;
    btn.addEventListener("click", async () => {
      selection.resolution = res.value;
      await revalidateAll();
      currentStepIndex = Math.min(currentStepIndex + 1, CATEGORIES.length);
      renderStep();
    });
    col.appendChild(btn);
    container.appendChild(col);
  });
  document.getElementById("step-pagination").innerHTML = "";
}

async function renderCategoryStep(category) {
  document.getElementById("step-title").textContent = CATEGORY_LABELS[category];
  const optionsContainer = document.getElementById("step-options");
  optionsContainer.innerHTML =
    '<p class="text-body-secondary">Checking compatibility…</p>';

  const grayOutMap = await computeGrayOutForCategory(category);

  // Compatible items first, incompatible after -- stable sort keeps each
  // group's original catalog order (e.g. GPUs still ranked by score)
  // intact within itself.
  const sortedCatalog = [...CATALOGS[category]].sort((a, b) => {
    const aCompatible = grayOutMap[a.id].compatible;
    const bCompatible = grayOutMap[b.id].compatible;
    if (aCompatible === bCompatible) return 0;
    return aCompatible ? -1 : 1;
  });

  const page = currentPage[category] || 1;
  const startIndex = (page - 1) * PAGE_SIZE;
  const pageItems = sortedCatalog.slice(startIndex, startIndex + PAGE_SIZE);

  optionsContainer.innerHTML = "";
  pageItems.forEach((item) => {
    const info = grayOutMap[item.id];
    const isSelected = selection[category] === item.id;
    const isDisabled = !info.compatible;

    const col = document.createElement("div");
    col.className = "col-md-6 col-lg-4";

    const card = document.createElement("button");
    card.type = "button";
    card.className =
      "card w-100 h-100 rc-option-card" +
      (isSelected ? " rc-option-selected" : "") +
      (isDisabled ? " rc-option-disabled" : "");
    card.disabled = isDisabled;
    if (isDisabled) {
      card.title = info.violations.map((v) => v.message).join(" | ");
    }
    card.innerHTML = `
            <div class="card-body">
                <div class="fw-semibold">${item.name}</div>
                <div class="text-body-secondary small rc-mono">${describeItem(category, item)}</div>
            </div>`;
    card.addEventListener("click", async () => {
      selection[category] = item.id;
      await revalidateAll();
      currentStepIndex = Math.min(currentStepIndex + 1, CATEGORIES.length);
      renderStep();
    });

    col.appendChild(card);
    optionsContainer.appendChild(col);
  });

  renderPagination(category, sortedCatalog.length, page);
}

function renderStep() {
  currentStepIndex = Math.min(currentStepIndex, furthestReachableIndex());
  renderStepIndicator();
  document.getElementById("prev-step-btn").disabled = currentStepIndex === 0;
  if (currentStepIndex === 0) {
    renderResolutionStep();
  } else {
    renderCategoryStep(CATEGORIES[currentStepIndex - 1]);
  }
}

function loadInitialSelection() {
  const raw = parseEmbedded("initial-selection-data");
  if (!raw) return;
  Object.keys(raw).forEach((key) => {
    if (raw[key] != null) selection[key] = raw[key];
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  loadInitialSelection();
  if (Object.keys(selection).length > 0) {
    await revalidateAll();
  }
  renderStep();

  document.getElementById("prev-step-btn").addEventListener("click", () => {
    if (currentStepIndex > 0) {
      currentStepIndex -= 1;
      renderStep();
    }
  });
});
