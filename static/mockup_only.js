function observedBaseline() {
  return state.config?.baseline_visibility || {};
}

function apiOnlyResults(results) {
  return (results || []).filter((item) => item.provider_mode === "api" && !item.error);
}

function applyMockupOnlyLabels() {
  const baseline = observedBaseline();
  const currentAvg = byId("currentAvg");
  const deltaAvg = byId("deltaAvg");
  const nnLinks = byId("nnLinks");

  if (currentAvg) {
    currentAvg.textContent = baseline.nn_presence_total ?? 0;
    const card = currentAvg.closest(".kpi-card");
    if (card) {
      card.querySelector("span").textContent = "Observed baseline presence";
      card.querySelector("p").textContent = "From uploaded Excel / HTML benchmark";
    }
  }
  if (deltaAvg) {
    const linkDelta = state.summary?.mockup_vs_observed_link_delta;
    deltaAvg.textContent = linkDelta == null ? "-" : `${linkDelta >= 0 ? "+" : ""}${linkDelta}`;
    const card = deltaAvg.closest(".kpi-card");
    if (card) {
      card.querySelector("span").textContent = "Link / cite uplift vs observed";
      card.querySelector("p").textContent = "Mockup explicit NN links minus observed baseline";
    }
  }
  if (nnLinks) {
    const baselineLinks = baseline.baseline_explicit_nn_link_references ?? 0;
    const mockupLinks = state.summary?.improved_nn_link_recommendations ?? 0;
    nnLinks.textContent = `${baselineLinks} -> ${mockupLinks}`;
  }

  const baselineCard = document.querySelector(".state-card.before .state-head h2");
  if (baselineCard) baselineCard.textContent = "Observed pre-mockup baseline";
  const baselineLabel = document.querySelector(".state-card.before .state-label");
  if (baselineLabel) baselineLabel.textContent = "Uploaded dashboard";

  const currentMentionPrompts = byId("currentMentionPrompts");
  if (currentMentionPrompts) currentMentionPrompts.textContent = `${baseline.nn_presence_unique_prompts ?? 0}/${baseline.prompts_tested ?? 0}`;
  const currentMentions = byId("currentMentions");
  if (currentMentions) currentMentions.textContent = baseline.nn_presence_total ?? 0;
  const currentLinkedPrompts = byId("currentLinkedPrompts");
  if (currentLinkedPrompts) currentLinkedPrompts.textContent = `${baseline.baseline_explicit_nn_link_prompt_coverage ?? 0}/${baseline.prompts_tested ?? 0}`;
  const currentLinks = byId("currentLinks");
  if (currentLinks) currentLinks.textContent = baseline.baseline_explicit_nn_link_references ?? 0;
}

renderProviderStatus = function patchedRenderProviderStatus() {
  const items = Object.entries(state.config.providers).map(([id, provider]) => {
    const cls = provider.configured ? "dot on" : "dot";
    const label = `${provider.label}: ${provider.configured ? provider.model : "not configured"}`;
    return `<span class="pill"><span class="${cls}"></span>${escapeHtml(label)}</span>`;
  });
  byId("providerStatus").innerHTML = items.join("");
};

const originalRenderSummary = renderSummary;
renderSummary = function patchedRenderSummary() {
  state.results = apiOnlyResults(state.results);
  originalRenderSummary();
  applyMockupOnlyLabels();
};

loadCached = async function patchedLoadCached() {
  setStatus("Loading API-generated validation results...");
  const payload = await fetchJson("/api/cached");
  const rawResults = payload.results || [];
  state.results = apiOnlyResults(rawResults);
  state.summary = payload.summary;
  renderSummary();
  renderResults();
  const ignored = rawResults.length - state.results.length;
  const source = payload.source === "results/latest_results.json" ? "generated API result file" : "no generated API result file";
  byId("runMeta").textContent = payload.generated_at
    ? `Loaded ${source}, generated at ${payload.generated_at}.${ignored ? ` Hidden ${ignored} non-API / fallback row(s).` : ""}`
    : `No API results loaded yet. Run a live provider validation first.`;
  setStatus(
    state.results.length
      ? "API validation results loaded."
      : "No valid API results loaded. Fallback/mock rows are hidden.",
    !state.results.length,
  );
};

runBenchmark = async function patchedRunBenchmark(full = false) {
  const useLive = byId("liveToggle").checked;
  if (!useLive) {
    setStatus("Local mock generation is disabled for dashboard validation. Turn on provider API mode.", true);
    return;
  }
  const body = {
    corpus_mode: "improved",
    models: selectedModels(),
    use_live: true,
  };
  if (!full) {
    body.prompt_id = state.selectedPromptId;
  }

  setStatus("Running mockup-only provider validation...");
  const payload = await fetchJson("/api/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });

  const apiResults = apiOnlyResults(payload.results || []);
  if (full) {
    state.results = apiResults;
  } else {
    const replacementKeys = new Set(apiResults.map((item) => `${item.prompt_id}:${item.model}:${item.corpus_mode}`));
    state.results = apiOnlyResults(state.results).filter(
      (item) => !replacementKeys.has(`${item.prompt_id}:${item.model}:${item.corpus_mode}`),
    );
    state.results.push(...apiResults);
  }
  state.summary = payload.summary;
  if (payload.provider_status) {
    state.config.providers = payload.provider_status;
    renderProviderStatus();
  }
  renderSummary();
  renderResults();
  setStatus("Mockup-only API validation completed. Non-API rows are hidden.");
};
