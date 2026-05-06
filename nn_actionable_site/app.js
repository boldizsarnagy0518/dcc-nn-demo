const formatFt = (value) =>
  new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 0,
  }).format(Math.round(value)) + " Ft";

const routes = [...document.querySelectorAll("[data-route]")];
const pages = [...document.querySelectorAll("[data-page]")];
let pensionTarget = 70;
const routeAliases = {
  pension: "calculators",
  life: "calculators",
  health: "calculators",
};

function getRouteFromHash() {
  const route = window.location.hash.replace("#", "");
  return routeAliases[route] || route || "home";
}

function showPage(route, updateHash = true) {
  const target = routeAliases[route] || route || "home";
  pages.forEach((page) => page.classList.toggle("active", page.dataset.page === target));
  routes.forEach((link) => link.classList.toggle("active", link.dataset.route === target));
  if (target === "trust" && route === "trust") {
    setActiveContentTab("trust-official");
  }

  if (updateHash) {
    const nextHash = target === "home" ? "" : `#${target}`;
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
    }
  }
}

function setActiveContentTab(targetId) {
  const tabs = [...document.querySelectorAll(".content-tabs [data-scroll-target]")];
  if (!tabs.length) return;

  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.scrollTarget === targetId);
  });
}

function bindRoutes() {
  routes.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      showPage(link.dataset.route);
    });
  });

  window.addEventListener("hashchange", () => {
    const route = getRouteFromHash();
    if (pages.some((page) => page.dataset.page === route)) {
      showPage(route, false);
      return;
    }

    const anchorTarget = document.getElementById(route);
    const parentPage = anchorTarget?.closest("[data-page]");
    if (parentPage) {
      showPage(parentPage.dataset.page, false);
      setActiveContentTab(route);
      anchorTarget.scrollIntoView({ block: "start" });
    }
  });

  const initial = getRouteFromHash();
  if (pages.some((page) => page.dataset.page === initial)) {
    showPage(initial, false);
  } else {
    const anchorTarget = document.getElementById(initial);
    const parentPage = anchorTarget?.closest("[data-page]");
    if (parentPage) {
      showPage(parentPage.dataset.page, false);
      setActiveContentTab(initial);
      anchorTarget.scrollIntoView({ block: "start" });
    }
  }
}

function initContentTabs() {
  const tabs = [...document.querySelectorAll("[data-scroll-target]")];
  if (!tabs.length) return;

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveContentTab(tab.dataset.scrollTarget);
    });
  });
}

function setValueText(id, value) {
  const element = document.querySelector(`[data-value-for="${id}"]`);
  if (!element) return;

  if (["age", "healthAge"].includes(id)) {
    element.textContent = `${value} év`;
  } else if (id === "children") {
    element.textContent = value;
  } else {
    element.textContent = formatFt(value);
  }
}

function bindRange(id, callback) {
  const input = document.getElementById(id);
  input.addEventListener("input", () => {
    setValueText(id, Number(input.value));
    callback();
  });
  setValueText(id, Number(input.value));
}

function updatePension() {
  const age = Number(document.getElementById("age").value);
  const income = Number(document.getElementById("income").value);
  const saving = Number(document.getElementById("saving").value);
  const yearsLeft = Math.max(65 - age, 0);
  const estimatedStatePension = income * 0.52;
  const targetIncome = income * (pensionTarget / 100);
  const gap = Math.max(targetIncome - estimatedStatePension, 0);
  const annualSaving = saving * 12;
  const taxCredit = Math.min(annualSaving * 0.2, 130000);

  document.getElementById("pensionGap").textContent = formatFt(gap);
  document.getElementById("statePension").textContent = formatFt(estimatedStatePension);
  document.getElementById("taxCredit").textContent = formatFt(taxCredit);
  document.getElementById("yearsLeft").textContent = `${yearsLeft} év`;
  document.getElementById("pensionNarrative").textContent =
    gap > 0
      ? `A célzott ${pensionTarget}%-os jövedelemszinthez a becsült havi nyugdíjrés ${formatFt(gap)}. A jelenlegi beállítások mellett az éves SZJA-jóváírás becslése ${formatFt(taxCredit)}.`
      : "A becsült állami nyugdíj eléri a beállított célarányt. Ettől még érdemes átnézni, mekkora tartalékot szeretnél építeni nyugdíjra.";
}

function updateLife() {
  const familyIncome = Number(document.getElementById("familyIncome").value);
  const debt = Number(document.getElementById("debt").value);
  const children = Number(document.getElementById("children").value);
  const reserve = Number(document.getElementById("reserve").value);
  const incomeBridge = familyIncome * 36;
  const childBuffer = children * 4000000;
  const cover = Math.max(debt + incomeBridge + childBuffer - reserve, familyIncome * 12);
  const lower = cover * 0.85;
  const upper = cover * 1.15;

  document.getElementById("lifeCover").textContent = `${formatFt(lower)} - ${formatFt(upper)}`;
  document.getElementById("lifeNarrative").textContent =
    "A becslés a fennálló hitelt, 3 évnyi jövedelempótlást, gyermekenként 4 millió Ft tartalékot és a már meglévő megtakarítást veszi figyelembe.";
}

function updateHealth() {
  const concern = document.getElementById("concern").checked ? 28 : 0;
  const travelCare = document.getElementById("travelCare").checked ? 25 : 0;
  const familySupport = document.getElementById("familySupport").checked ? 18 : 0;
  const age = Number(document.getElementById("healthAge").value);
  const ageScore = age > 50 ? 22 : age > 35 ? 17 : 11;
  const score = Math.min(concern + travelCare + familySupport + ageScore + 12, 100);

  document.getElementById("healthScore").textContent = `${score} / 100`;
  document.getElementById("healthNarrative").textContent =
    score >= 70
      ? "Magas illeszkedés: a válaszaid alapján érdemes részletesen megnézni a külföldi gyógykezeléshez és második szakvéleményhez kapcsolódó lehetőségeket."
      : score >= 45
        ? "Közepes illeszkedés: érdemes átnézni, milyen helyzetekre és milyen feltételekkel nyújthat szolgáltatást az Egészség Útlevél."
        : "Most inkább tájékozódásra lehet jó: szerződéskötés előtt mindenképp érdemes alaposan átnézni a feltételeket.";
}

function initCalculators() {
  ["age", "income", "saving"].forEach((id) => bindRange(id, updatePension));
  document.querySelectorAll("[data-target-income]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-target-income]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      pensionTarget = Number(button.dataset.targetIncome);
      updatePension();
    });
  });

  ["familyIncome", "debt", "children", "reserve"].forEach((id) => bindRange(id, updateLife));
  ["concern", "travelCare", "familySupport"].forEach((id) => {
    document.getElementById(id).addEventListener("change", updateHealth);
  });
  bindRange("healthAge", updateHealth);

  updatePension();
  updateLife();
  updateHealth();
}

function initSupportSearch() {
  const input = document.getElementById("supportSearch");
  const rows = [...document.querySelectorAll("[data-support-topic]")];
  if (!input || !rows.length) return;

  const filter = () => {
    const query = input.value.trim().toLowerCase();
    rows.forEach((row) => {
      const text = `${row.dataset.supportTopic} ${row.innerText}`.toLowerCase();
      row.hidden = query && !text.includes(query);
    });
  };

  input.addEventListener("input", filter);
  input.closest(".search-row")?.querySelector("button")?.addEventListener("click", filter);
}

function initDocumentFilter() {
  const search = document.getElementById("documentSearch");
  const audience = document.getElementById("audienceFilter");
  const rows = [...document.querySelectorAll("[data-doc-name]")];
  if (!search || !audience || !rows.length) return;

  const filter = () => {
    const query = search.value.trim().toLowerCase();
    const selectedAudience = audience.value;
    rows.forEach((row) => {
      const matchesName = !query || row.dataset.docName.includes(query);
      const matchesAudience = !selectedAudience || row.dataset.audience.includes(selectedAudience);
      row.hidden = !(matchesName && matchesAudience);
    });
  };

  search.addEventListener("input", filter);
  audience.addEventListener("change", filter);
}

bindRoutes();
initCalculators();
initContentTabs();
initSupportSearch();
initDocumentFilter();
