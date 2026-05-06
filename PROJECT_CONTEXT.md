# Project Context — NN GEO Recommendation Impact Simulator

## 1. One-sentence summary

This repository contains a controlled A/B evidence pipeline and clickable NN mockup site for the NN Hungary GenAI visibility / GEO case. It uses the original 48-prompt benchmark as diagnosis, then tests whether NN's actionable GEO recommendations improve AI-style answer quality, citations and next-step actionability under controlled conditions.

---

## 2. Case and business context

This project was built for a Deloitte Consulting Course case about **NN Hungary** and its visibility in the emerging GenAI search environment.

The strategic problem is that consumer search behaviour is shifting from traditional keyword-based search toward conversational AI-driven search. Users increasingly ask ChatGPT, Gemini, Claude, Perplexity, AI Overviews or similar tools questions such as:

- "What life insurance should I choose in Hungary?"
- "Which insurer is reliable?"
- "How much life insurance coverage does my family need?"
- "Which pension insurance offers tax benefits?"
- "Which insurer should I compare before making a decision?"

In this environment, ranking on a traditional Google search result page is no longer enough. NN needs to be present inside AI-generated answers, ideally as a trusted, cited and actionable next step.

The strategic shift is:

```text
From SEO: ranking in search results
To GEO: being retrieved, understood, cited and recommended by generative AI systems
```

Core strategic objective:

> Make NN easier for AI systems to find, understand, trust, cite and recommend as the next step.

---

## 3. Expected communication style

When supporting the project, use a senior strategy-consulting style:

- clear and structured;
- executive-friendly;
- business-focused;
- suitable for a client presentation to NN;
- focused on overview-level recommendations, not overly detailed implementation specs;
- aligned with a 0-3 year recommendation roadmap;
- not overclaiming beyond what the POC proves.

Use English for slide titles, slide text, dashboards, README text and recommendation labels unless the user asks otherwise. Use Hungarian when preparing speaking notes or explaining to the team.

Avoid an obviously AI-generated tone. Prefer natural, presentation-ready language.

---

## 4. Current project positioning

The project should be positioned as:

```text
NN GEO Recommendation Impact Simulator
```

Best one-sentence description:

> This POC validates whether NN's actionable GEO recommendations can improve GenAI-style answer quality by making answers more specific, credible, citable and actionable.

Important: this is **not** a real-time public web visibility tracker.

The dashboard does not claim to measure live public ChatGPT, Gemini or Claude rankings. It validates recommendation impact under controlled conditions.

The safest wording is:

> The POC demonstrates under controlled conditions that the recommended NN assets can improve AI-style answer quality, citations and actionability.

Avoid claiming:

```text
This proves NN will rank higher in public ChatGPT/Gemini/Claude.
```

---

## 5. Current methodology

The project now uses a two-part methodology.

### 1. Original live-web benchmark as diagnosis

The original baseline is not regenerated as the main proof. It comes from the manually collected benchmark and uploaded analysis.

Source files / data:

```text
n8n_DCC.xlsx
NN_Analysis.html
data/baseline_visibility.json
data/original_analysis_summary.json
```

Benchmark setup:

- 48 Hungarian life-insurance-related prompts;
- 3 model families;
- 144 total model-prompt outputs;
- agents had internet access in the original n8n run.

Main baseline metrics:

| Metric | Observed baseline |
|---|---:|
| Prompts tested | 48 |
| AI models | 3 |
| Model outputs | 144 |
| Total NN mentions | 223 |
| NN prompt-level presence | 64 / 144 |
| NN unique prompt coverage | 32 / 48 |
| NN vs competitor average | 2.0x |
| Explicit NN cite/link references | 5 / 144 |
| Positive / negative keyword context | 210 / 6 |
| Approx. share of voice | ~13% |

Strategic interpretation:

> NN is already visible in GenAI answers, but the next opportunity is to make this visibility more product-specific, more credible, more citable and more actionable.

### 2. Controlled A/B validation as intervention proof

The current evidence run is a controlled A/B test. It does not browse the public web. It isolates the effect of the recommended NN assets by changing only the controlled source environment.

Current default evidence workflow:

```text
A = current NN/current-like corpus
B = current corpus + actionable recommendation/mockup corpus + parsed mockup HTML signals
```

Full evidence run:

```text
48 prompts x 2 corpus modes x 3 OpenRouter model-family routes = 288 provider calls
```

The primary runner is:

```powershell
python run_controlled_ab.py path\to\n8n_DCC.xlsx
```

The runner writes:

```text
results/controlled_ab_<timestamp>/
  checkpoint.jsonl
  all_results.json
  all_results.csv
  A_current_outputs.xlsx
  B_improved_outputs.xlsx
  AB_summary.xlsx
```

Evidence-mode requirements:

- provider_mode must equal api;
- no mock fallback rows are accepted;
- checkpointing allows a failed run to resume;
- Excel outputs are the primary client-facing evidence artifact.

## 6. Why websearch is intentionally not required

The core POC intentionally does not use paid websearch APIs.

Reason:

> The purpose is to isolate the impact of NN's proposed recommendation assets, not to introduce live-web ranking noise.

If live websearch were added too early, the test would depend on:

- changing search results;
- search index freshness;
- crawler behaviour;
- competitor page updates;
- provider-specific grounding behaviour;
- inconsistent citations;
- API cost and rate limits.

For the current POC, the stronger logic is:

```text
Real observed baseline
→ recommended mockup assets
→ controlled LLM answer generation
→ measurable uplift in mentions, links and actionability
```

Future versions can add search-grounded APIs and live monitoring, but those are extensions, not core requirements.

---

## 7. What the evidence outputs should show

The primary output is now Excel evidence, not a dashboard-first workflow. The optional dashboard can still be used for exploration, but the final proof should rely on the controlled A/B workbook outputs.

### A_current_outputs.xlsx

Should contain every current-corpus model answer with:

- prompt id, category and prompt text;
- provider and exact model id;
- retrieved current source IDs and URLs;
- NN mentions, explicit NN links and competitor mentions;
- score breakdown: mention quality, product specificity, credibility and actionability.

### B_improved_outputs.xlsx

Should contain every improved-corpus model answer with the same columns, plus recommendation IDs represented in retrieved evidence. B uses current content plus all actionable recommendation assets and parsed mockup HTML signals.

### AB_summary.xlsx

Should show:

- overall current vs improved score delta;
- model-level current vs improved scores;
- prompt-level uplift;
- explicit NN link uplift;
- recommendation-level coverage for R1-R10;
- run metadata and methodology wording.

Main evidence message:

> The controlled A/B validation isolates whether the recommended NN assets can make AI-style answers more specific, credible, citable and actionable.
## 8. Important implementation decision: no live API fallback

Live API mode should not silently fallback to mock answers.

Current intended behaviour:

```text
Live API success → provider_mode = api
Live API error → error is raised
```

Do not mix real API answers with fallback mock answers in an evidence run.

A local mock mode can still exist for UI testing, but it is not validation evidence.

Good evidence run:

```text
48 results
48 provider_mode = api
0 fallback rows
```

Bad evidence run:

```text
Some api rows + some mock_fallback rows
```

If a run contains fallback rows, it should be treated as partial / invalid for final validation.

---

## 9. Strategic framework

Use this four-part GEO logic:

1. **Discoverability** — NN must be easy to find.
2. **Clarity** — NN must be easy to understand.
3. **Credibility** — NN must be easy to cite.
4. **Actionability** — NN must give users a clear next step.

The key strategic upgrade is **Actionability**.

Explanation:

> Visibility only creates business value if users know what to do next. It is not enough for AI to mention NN in a list. The stronger outcome is when AI can guide users toward an NN calculator, guide, quote request, product page or advisor handoff.

---

## 10. Current actionable recommendations

The recommendation roadmap contains ten actions.

### R1 — Rebuild key product pages around conversational search

**Horizon:** 0-3 months  
**Pillar:** Clarity  
**Priority:** High

NN should redesign priority product pages around natural-language questions users would ask AI systems.

Examples:

- "Mi az életbiztosítás és mire nyújt védelmet?"
- "Mennyi életbiztosítást érdemes kötni?"
- "Milyen adókedvezmény jár nyugdíjbiztosítás után?"
- "Miben különbözik a kockázati és a megtakarításos életbiztosítás?"

Mockup signal:

- product Q&A pages;
- extractable answer blocks;
- stronger product specificity;
- more direct NN product links.

### R2 — Strengthen NN's machine-readable identity

**Horizon:** 0-3 months  
**Pillar:** Discoverability + Credibility  
**Priority:** High

Build a clearer entity chain:

```text
nn.hu → sameAs links → Wikidata → third-party proof
```

Mockup signal:

- entity/schema mock;
- sameAs / Wikidata-style identity evidence;
- stronger credibility score.

### R3 — Fix technical discoverability hygiene

**Horizon:** 0-6 months  
**Pillar:** Discoverability  
**Priority:** Medium-high

Actions:

- sitemap freshness audit;
- IndexNow implementation;
- crawler access policy review;
- structured-data validation;
- meta description cleanup;
- optional llms.txt pilot.

Caveat:

> llms.txt should be treated as a low-priority pilot, not a core dependency.

### R4 — Build an AI visibility dashboard

**Horizon:** 0-3 months  
**Pillar:** Measurement / governance  
**Priority:** Medium

The current repository itself acts as the POC for this recommendation.

Track:

- prompt coverage;
- model differences;
- product-specific mentions;
- citation/link references;
- competitor visibility;
- recommendation impact over time.

### R5 — Build a third-party credibility ecosystem

**Horizon:** 3-12 months  
**Pillar:** Credibility  
**Priority:** High

Priority sources:

- Google Business Profile;
- review platforms;
- Netrisk.hu;
- Biztositas.hu;
- independent financial media;
- industry / MNB references.

Mockup signal:

- external proof assets;
- stronger credibility score;
- stronger comparison-answer support.

### R6 — Publish original Hungarian AI-finance research

**Horizon:** 3-12 months  
**Pillar:** Credibility + Authority  
**Priority:** High

Possible title:

```text
Magyarok és az AI: pénzügyi döntéshozatal a mesterséges intelligencia korában
```

Purpose:

- create a unique, citable Hungarian authority asset;
- position NN as a thought leader in AI + financial decision-making;
- support media and AI citation potential.

### R7 — Build decision-guide pages

**Horizon:** 3-12 months  
**Pillar:** Clarity + Actionability  
**Priority:** Medium

Example pages:

- "Mikor érdemes életbiztosítást kötni?"
- "Nyugdíjbiztosítás vagy önkéntes nyugdíjpénztár?"
- "Mekkora életbiztosítási fedezet kell egy családnak?"
- "Hogyan gondolkodjak biztosításról 30/40/50 évesen?"

Mockup signal:

- clearer decision support;
- guide links;
- stronger actionability.

### R8 — Build toward Wikipedia authority path

**Horizon:** 12-36 months  
**Pillar:** Authority  
**Priority:** Medium

Important caveat:

> Wikipedia should not be framed as a quick marketing action. It requires neutral notability and independent sources.

Goal:

- build independent coverage;
- collect notability evidence;
- later consider a neutral Wikipedia path if conditions are met.

### R9 — Launch public financial calculators

**Horizon:** 12-36 months  
**Pillar:** Actionability  
**Priority:** High

Recommended tools:

- pension gap calculator;
- SZJA tax benefit calculator;
- life insurance need estimator;
- health insurance decision-support calculator.

Expected impact:

- more explicit NN links;
- stronger actionability;
- clearer bridge from AI answers to lead potential.

### R10 — Advanced personalization

**Horizon:** 12-36 months  
**Pillar:** Actionability / conversion  
**Priority:** Lower-medium initially, higher later

Examples:

- personalized guides by age group;
- calculator output with next best action;
- life-stage-based recommendations;
- advisor handoff;
- CRM / lead scoring integration.

---

## 11. Impact × time prioritization

### 0-3 months

High priority:

- conversational product pages + Q&A;
- entity schema + sameAs + Wikidata path;
- AI visibility dashboard.

Support / hygiene:

- robots;
- sitemap;
- IndexNow;
- optional llms.txt.

Objective:

```text
Make NN easier to find, understand and measure.
```

### 3-12 months

High priority:

- third-party credibility ecosystem;
- original Hungarian AI-finance research.

Medium priority:

- decision-guide pages.

Objective:

```text
Build credibility and create citable external proof.
```

### 12-36 months

High priority:

- public calculators.

Medium priority:

- Wikipedia authority path;
- advanced personalization.

Objective:

```text
Turn AI visibility into action, lead generation and long-term authority.
```

---

## 12. Repository structure

Important files and folders:

```text
README.md
PROJECT_CONTEXT.md
FIRST_API_RUN.md
RECOMMENDATION_IMPLEMENTATION_MAP.md
.env.example
run_controlled_ab.py
generate_responses.py
import_prompts_from_excel.py
dashboard.py

geo_demo/
  benchmark.py
  data.py
  env.py
  evidence_export.py
  excel_export.py
  mockup_site.py
  providers.py
  retrieval.py
  scoring.py
  linking.py
  results.py
  server.py

data/
  prompts.json
  original_analysis_summary.json
  baseline_visibility.json
  corpus_current.json
  corpus_improved.json
  recommendations.json

nn_actionable_site/
  index.html
  styles.css
  app.js
  NN-logo.png

results/
  controlled_ab_<timestamp>/
    checkpoint.jsonl
    A_current_outputs.xlsx
    B_improved_outputs.xlsx
    AB_summary.xlsx

tests/
```

Removed / deprecated files:

```text
NN_GenAI_DCC_AI_context.md
PROJECT_FEEDBACK.md
```

---
## 13. Prompt source

The prompt set is stored in:

```text
data/prompts.json
```

It was generated from the uploaded Excel benchmark:

```text
n8n_DCC.xlsx
```

Source:

```text
Sheet: PROMPTS
Prompt column: A
Header row: row 1
Prompt rows: row 2 onward
Category / segment column: B
```

Regenerate prompts locally with:

```powershell
uv run python import_prompts_from_excel.py path\to\n8n_DCC.xlsx --sheet PROMPTS --prompt-col A --category-col B --output data/prompts.json
```

Expected count:

```text
48 prompts
```

---

## 14. Providers and API usage

Supported providers:

```text
openrouter_openai
openrouter_gemini
openrouter_claude
openrouter
openai
gemini
claude
```

Environment variables:

```text
OPENROUTER_API_KEY=
OPENROUTER_OPENAI_MODEL=openai/gpt-5.2
OPENROUTER_GEMINI_MODEL=google/gemini-3-pro-preview
OPENROUTER_CLAUDE_MODEL=anthropic/claude-sonnet-4.6

# Optional direct-provider routes
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.2
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3-pro-preview
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

OpenRouter is useful as a temporary free-model route when Gemini quota is exhausted. It uses an OpenAI-compatible chat completions endpoint.

Recommended OpenRouter smoke test:

```powershell
uv run python generate_responses.py --live --models openrouter --delay-seconds 4
```

Caution:

```text
48 requests is very close to a 50/day free OpenRouter limit.
```

Do a one-prompt UI test before running the full 48-prompt benchmark.

---

## 15. How to run

### Create env file

```powershell
Copy-Item .env.example .env
notepad .env
```

### Controlled A/B evidence run

```powershell
python run_controlled_ab.py path/to/n8n_DCC.xlsx --delay-seconds 2
```

Optional smoke test:

```powershell
python run_controlled_ab.py path/to/n8n_DCC.xlsx --limit-prompts 1
```

The evidence runner writes Excel workbooks and checkpoint files under results/controlled_ab_<timestamp>/. It requires OPENROUTER_API_KEY by default and does not use mock fallback.

### Optional legacy dashboard

```powershell
python dashboard.py --host 127.0.0.1 --port 8765
```

### Tests

```powershell
python -m compileall -q geo_demo tests run_controlled_ab.py
python -m unittest discover -s tests
```

## 16. Dashboard / API endpoints

The dashboard server exposes:

```text
GET  /api/config
GET  /api/cached
GET  /api/sources?mode=improved
GET  /api/sources?mode=current
GET  /api/export.csv
POST /api/run
```

`/api/config` returns:

- prompts;
- recommendations;
- baseline visibility data;
- original analysis summary;
- provider status;
- corpus modes.

`/api/cached` loads:

```text
results/latest_results.json
```

if available.

`/api/run` can run selected prompt/model combinations from the dashboard.

---

## 17. Interpretation rules

### Do not overclaim

Do not claim:

- FAQ schema guarantees AI citation.
- llms.txt is required for AI visibility.
- Wikipedia can be created quickly as a marketing action.
- Robots.txt changes alone will create visibility.
- AI mentions directly equal customer conversion.
- The POC proves live public AI ranking improvement.

Use safer phrases:

- indicates;
- suggests;
- demonstrates under controlled conditions;
- validates the direction of the recommendation;
- supports the business case.

### Distinguish mentions from citations / links

An NN mention is awareness.

An explicit NN link or citation is stronger because it directs the user toward an NN-owned source or action.

Key gap:

```text
NN has strong mention baseline but weak explicit link/citation baseline.
```

### Treat mock results carefully

Local mock results are for UI stability and demo backup.

Live API controlled-source results are stronger evidence because a real model generated the answer.

### Keep the story simple

The final storyline should be:

```text
NN is already visible.
But visibility is not yet actionable enough.
The recommended GEO assets aim to make NN easier to cite, link and choose.
The POC validates this direction under controlled conditions.
```

---

## 18. Recommended presentation narrative

### English version

> NN already appears frequently in GenAI answers. The opportunity is not simply to increase mentions, but to improve the quality of those mentions. The goal is to make NN more product-specific, more credible, more citable and more actionable. This POC uses the original 48-prompt benchmark as the observed baseline, then tests whether recommended mockup assets can improve AI-style answers under controlled conditions.

### Hungarian version

> NN már most is látható a generatív AI válaszokban, tehát nem nulláról kell építkeznie. A probléma inkább az, hogy ez a visibility még nem mindig elég konkrét, nem mindig elég hitelesen alátámasztott, és nem mindig vezet világos következő lépéshez. A POC ezért azt validálja, hogy az ajánlott GEO assetek kontrollált környezetben konkrétabbá, hivatkozhatóbbá és actionable-bbé teszik-e a válaszokat.

Short version:

> We are not trying to recreate the whole public web. We are validating whether the recommended NN assets would make GenAI answers better under controlled conditions.

---

## 19. Final project interpretation

This is a strategic and technical POC that supports the NN GEO roadmap.

Its value is not that it perfectly recreates the entire GenAI ecosystem. Its value is that it connects:

- a real observed baseline;
- a clear strategic gap;
- actionable recommendations;
- mocked future assets;
- controlled answer generation;
- measurable KPIs;
- and a business-facing impact story.

The core message is:

> NN should not only aim to appear in GenAI answers. NN should build the assets that make it easier for AI systems to find, understand, trust, cite, link and recommend NN as the next step.
