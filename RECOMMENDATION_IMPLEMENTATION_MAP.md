# Actionable Recommendation Implementation Map

## Purpose of this document

This file explains, in detail, where each actionable GEO recommendation is represented in the current project, which files implement it, which mockup assets support it, and how the dashboard validates it.

The project is no longer designed as a full current-vs-improved API benchmark. The current / pre-mockup state is represented by the observed Excel/HTML benchmark. The API run is now focused on the **mockup / improved corpus only**.

Core logic:

```text
Observed baseline dashboard
→ recommendation mockup assets
→ mockup-only API validation
→ mention + cite/link + actionability uplift
```

---

## 1. Project setup at a glance

### Observed baseline

The pre-mockup state comes from the uploaded manual AI visibility benchmark dashboard:

- `NN_AI_prompt_presence_dashboard_v2.html` uploaded by the user.
- Its key metrics are stored in `data/baseline_visibility.json`.

Baseline numbers used in the project:

| Metric | Value |
|---|---:|
| Prompts tested | 48 |
| Model outputs | 144 |
| NN prompt-level presence | 64 / 144 |
| NN unique prompt coverage | 32 / 48 |
| NN vs competitor average | 2.0× |
| Explicit NN cite/link references | 5 / 144 |

### Mockup validation

The mockup state is represented by:

- `data/corpus_improved.json`
- `data/recommendations.json`
- live/mock LLM responses generated through `generate_responses.py`
- dashboard visualization in `static/index.html`, `static/app.js`, `static/mockup_only.js`

Default run mode:

```powershell
uv run python generate_responses.py --live --models gemini
```

This now runs only:

```text
corpus_mode = improved
```

Therefore the lowest-cost full validation is:

```text
48 prompts × 1 corpus mode × 1 model = 48 requests
```

---

## 2. Key files and what they do

### Baseline / observed pre-mockup state

| File | Role |
|---|---|
| `data/baseline_visibility.json` | Stores the observed benchmark numbers from the uploaded Excel/HTML dashboard. |
| `static/index.html` | Displays the observed baseline block at the top of the dashboard. |
| `static/mockup_only.js` | Ensures the dashboard interprets baseline numbers from `baseline_visibility.json` rather than requiring a second current-corpus API run. |
| `geo_demo/server.py` | Exposes baseline data through `/api/config` and includes it in summary output. |
| `README.md` | Explains that the observed baseline comes from the uploaded manual benchmark. |
| `PROJECT_CONTEXT.md` | Gives the full strategic and technical context. |

### Recommendation mockup assets

| File | Role |
|---|---|
| `data/recommendations.json` | The ten actionable recommendations, with horizon, pillar, priority, validation hypothesis, expected signal and asset type mapping. |
| `data/corpus_improved.json` | The actual mocked future GEO assets used as controlled source material for the LLM. |
| `geo_demo/retrieval.py` | Retrieves relevant mockup assets for each prompt. |
| `geo_demo/providers.py` | Builds the grounded prompt from selected mockup assets and calls providers. |
| `geo_demo/scoring.py` | Scores generated answers for mention quality, product specificity, credibility and actionability. |
| `geo_demo/linking.py` | Counts NN mentions and extracts explicit `nn.hu` link recommendations. |
| `static/app.js` | Renders prompt-level results, answer boxes, next-step mix and recommendation coverage. |
| `static/mockup_only.js` | Forces UI-triggered runs to use the mockup / improved corpus only. |

### API / run logic

| File | Role |
|---|---|
| `generate_responses.py` | CLI script for generating benchmark outputs. Defaults to `--corpus-mode improved`. |
| `geo_demo/server.py` | Dashboard API server. Defaults `/api/run` to `corpus_mode=improved`. |
| `.env.example` | Template for API keys. Gemini is the recommended low-cost first run. |
| `.gitignore` | Ensures `.env` and generated result files are not committed. |

---

## 3. Recommendation-by-recommendation implementation

## R1 — Rebuild key product pages around conversational search

### Business goal

Make NN product pages easier for AI systems to extract, summarize and cite. Instead of generic product descriptions, the content should directly answer real user questions in conversational form.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R1",
  "title": "Rebuild key product pages around conversational search",
  "pillar": "Clarity",
  "asset_types": ["product_qa"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-life-qa`
  - Type: `product_qa`
  - Mock URL: `https://www.nn.hu/mock/eletbiztositas-qa`
  - Purpose: answers what life insurance is and when it is relevant.

- `improved-pension-tax-qa`
  - Type: `product_qa`
  - Mock URL: `https://www.nn.hu/mock/nyugdijbiztositas-adokedvezmeny`
  - Purpose: explains pension insurance tax benefit in a direct Q&A format.

- `improved-health-qa`
  - Type: `product_qa`
  - Mock URL: `https://www.nn.hu/mock/egeszseg-utlevel-qa`
  - Purpose: explains when health insurance for foreign treatment is useful.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially:
  - product specificity
  - mention quality
  - clarity-related improvement

### Expected validation signal

- Higher product specificity score.
- More concrete NN product mentions.
- More direct product-page or Q&A-page links.
- Stronger answers for life, pension and health insurance prompts.

---

## R2 — Strengthen NN's machine-readable identity

### Business goal

Make NN easier for AI systems to understand as a distinct Hungarian insurer and connect to parent-company/entity proof.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R2",
  "title": "Strengthen NN's machine-readable identity",
  "pillar": "Discoverability + Credibility",
  "asset_types": ["entity"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-entity-schema`
  - Type: `entity`
  - Mock URL: `https://www.nn.hu/mock/entity-schema`
  - Includes Organization JSON-LD style information, sameAs links, parent organization and entity relationship logic.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially credibility
- `Source Domain Mix` as part of mockup source evidence

### Expected validation signal

- Higher credibility score.
- Better entity-level justification in generated answers.
- Stronger ability to say why NN is a relevant and verifiable insurer.

---

## R3 — Fix technical discoverability hygiene

### Business goal

Improve technical readiness so AI crawlers and search systems can discover NN pages more reliably.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R3",
  "title": "Fix technical discoverability hygiene",
  "pillar": "Discoverability",
  "asset_types": ["technical_hygiene"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-technical-hygiene`
  - Type: `technical_hygiene`
  - Mock URL: `https://www.nn.hu/mock/geo-hygiene`
  - Covers sitemap audit, IndexNow, crawler access, structured-data validation, meta description cleanup and llms.txt pilot.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Retrieved Mockup Source Evidence`
- `Source Domain Mix`

### Expected validation signal

This recommendation is mostly a readiness / discoverability support signal. It should not be interpreted as a guarantee of AI citation.

Expected dashboard effect:

- better explanation of why NN assets are machine-readable and source-ready;
- stronger discoverability rationale;
- not necessarily direct link uplift by itself.

---

## R4 — Build an AI visibility dashboard

### Business goal

Make AI visibility measurable and repeatable instead of anecdotal.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R4",
  "title": "Build an AI visibility dashboard",
  "pillar": "Measurement",
  "asset_types": ["dashboard"]
}
```

### Project implementation

This repository itself is the POC implementation of R4.

Key files:

- `dashboard.py`
- `geo_demo/server.py`
- `static/index.html`
- `static/app.js`
- `static/mockup_only.js`
- `static/styles.css`
- `static/baseline.css`
- `generate_responses.py`
- `results/latest_results.json` generated locally, ignored by git
- `results/latest_results.csv` generated locally, ignored by git

### Where it appears in the dashboard

The whole dashboard validates R4.

Specific visible parts:

- observed baseline block;
- mockup answer quality score;
- link/cite uplift vs observed baseline;
- prompt-level mockup coverage;
- model summary;
- CSV export;
- recommendation coverage;
- source evidence.

### Expected validation signal

- Measurable prompt-level visibility.
- Repeatable runs.
- Exportable results.
- Clear separation between observed baseline and mockup validation.

---

## R5 — Build a third-party credibility ecosystem

### Business goal

AI systems should not rely only on NN-owned marketing pages. They should find or be able to use external validation signals.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R5",
  "title": "Build a third-party credibility ecosystem",
  "pillar": "Credibility",
  "asset_types": ["third_party", "benchmark"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-third-party-proof`
  - Type: `third_party`
  - Mock URL: `https://www.nn.hu/mock/third-party-proof`
  - Includes Google Business Profile, review platforms, Netrisk, Biztositas.hu, MNB/industry references and financial media signals.

- `improved-calculator-benchmark`
  - Type: `benchmark`
  - Source URL: external Progressive calculator example
  - Shows international benchmark logic for calculator-led next steps.

- `improved-hungarian-competitor-benchmark`
  - Type: `benchmark`
  - Source URL: external Hungarian competitor benchmark example
  - Shows how competitors use calculators, online flows and callback CTAs.

### Where it appears in the dashboard

- `GEO Pillar Breakdown`, especially credibility
- `Source Domain Mix`
- `Competitor Mention Check`
- `Retrieved Mockup Source Evidence`
- `Actionable Recommendation Coverage`

### Expected validation signal

- Higher credibility score.
- More external-source/domain evidence.
- Better ability to support comparison prompts.
- More credible answers in competitor-related prompts.

---

## R6 — Publish original Hungarian AI-finance research

### Business goal

Create a unique citable authority asset that positions NN as a source in the Hungarian AI + financial decision-making conversation.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R6",
  "title": "Publish original Hungarian AI-finance research",
  "pillar": "Credibility + Authority",
  "asset_types": ["research"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-ai-finance-study`
  - Type: `research`
  - Mock URL: `https://www.nn.hu/mock/ai-penzugyi-dontesek-kutatas`
  - Represents a Hungarian research landing page about how consumers use and trust AI in financial decisions.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Next-step Destination Mix`, if linked as research
- `GEO Pillar Breakdown`, especially credibility and authority
- `Retrieved Mockup Source Evidence`

### Expected validation signal

- More research-source links.
- Higher credibility / authority score.
- Better answers for AI-trust and financial decision prompts.

---

## R7 — Build decision-guide pages

### Business goal

Help users and AI systems answer decision-oriented questions, not just product-definition questions.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R7",
  "title": "Build decision-guide pages",
  "pillar": "Clarity + Actionability",
  "asset_types": ["decision_guide"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-life-cover-guide`
  - Type: `decision_guide`
  - Mock URL: `https://www.nn.hu/mock/csaladi-eletbiztositas-fedezet`
  - Helps estimate family life insurance cover needs.

- `improved-pension-comparison-guide`
  - Type: `decision_guide`
  - Mock URL: `https://www.nn.hu/mock/nyugdijbiztositas-vagy-onyp`
  - Compares pension insurance and voluntary pension fund options.

### Where it appears in the dashboard

- `Next-step Destination Mix`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially product specificity and actionability
- `Prompt-level Mockup Coverage`

### Expected validation signal

- Better decision-question answers.
- More guide links.
- Higher clarity and actionability scores.

---

## R8 — Build toward Wikipedia authority path

### Business goal

Support long-term entity authority, if enough neutral independent-source evidence exists.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R8",
  "title": "Build toward Wikipedia authority path",
  "pillar": "Authority",
  "asset_types": ["authority_path"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-wikipedia-path`
  - Type: `authority_path`
  - Mock URL: `https://www.nn.hu/mock/wikipedia-authority-path`
  - Explains neutral notability, independent sources and long-term Wikipedia/Wikidata readiness.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially authority/credibility

### Expected validation signal

- Supports long-term authority narrative.
- Should not be treated as quick marketing or guaranteed Wikipedia presence.
- Helps explain source credibility if independent references exist.

---

## R9 — Launch public financial calculators

### Business goal

Turn AI visibility into actionable next steps by giving models concrete NN-owned tools to recommend.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R9",
  "title": "Launch public financial calculators",
  "pillar": "Actionability",
  "asset_types": ["calculator"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-life-calculator`
  - Type: `calculator`
  - Mock URL: `https://www.nn.hu/mock/eletbiztositas-kalkulator`
  - Life insurance cover estimator.

- `improved-pension-gap-calculator`
  - Type: `calculator`
  - Mock URL: `https://www.nn.hu/mock/nyugdijres-kalkulator`
  - Pension gap calculator.

- `improved-tax-calculator`
  - Type: `calculator`
  - Mock URL: `https://www.nn.hu/mock/szja-adokedvezmeny-kalkulator`
  - SZJA tax benefit calculator.

- `improved-health-calculator`
  - Type: `calculator`
  - Mock URL: `https://www.nn.hu/mock/egeszsegbiztositas-kalkulator`
  - Health insurance decision-support calculator.

### Where it appears in the dashboard

- `NN next-step recommendations`
- `Next-step Destination Mix`
- `Prompt-level Mockup Coverage`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially actionability

### Expected validation signal

This is one of the most important recommendations for measurable impact.

Expected effect:

- more explicit `nn.hu` links;
- stronger actionability score;
- more calculator next-step recommendations;
- clearer bridge from AI answer to lead potential.

---

## R10 — Advanced personalization

### Business goal

After the foundation is built, use personalization and advisor handoff to make NN next steps more relevant to the user.

### Where it is defined

`data/recommendations.json`

```json
{
  "id": "R10",
  "title": "Advanced personalization",
  "pillar": "Actionability / conversion",
  "asset_types": ["personalization"]
}
```

### Mockup assets that implement it

`data/corpus_improved.json`

- `improved-personalization`
  - Type: `personalization`
  - Mock URL: `https://www.nn.hu/mock/personalization-pilot`
  - Represents personalized next-best-action logic and advisor handoff.

### Where it appears in the dashboard

- `Actionable Recommendation Coverage`
- `Retrieved Mockup Source Evidence`
- `GEO Pillar Breakdown`, especially actionability
- `Next-step Destination Mix`, if advisor handoff is recommended

### Expected validation signal

- Higher actionability.
- Stronger advisor handoff relevance.
- Better conversion narrative.
- Less important for short-term validation than R1, R5, R6, R7 and R9.

---

## 4. Where the main business claims are implemented

## Claim 1 — NN is already visible, but not actionable enough

Implemented in:

- `data/baseline_visibility.json`
- `static/index.html`
- `static/app.js`
- `static/mockup_only.js`
- `README.md`
- `PROJECT_CONTEXT.md`

Evidence:

```text
NN presence: 64 / 144
Explicit NN cite/link references: 5 / 144
```

Interpretation:

```text
NN is mentioned, but not linked/cited enough.
```

---

## Claim 2 — API should only run the mockup side now

Implemented in:

- `generate_responses.py`
- `geo_demo/server.py`
- `static/mockup_only.js`
- `README.md`

Key behaviour:

```text
default corpus_mode = improved
```

Recommended command:

```powershell
uv run python generate_responses.py --live --models gemini
```

Request count:

```text
48 prompts × 1 corpus mode × 1 model = 48 requests
```

---

## Claim 3 — The strongest impact KPI is link/cite uplift

Implemented in:

- `geo_demo/linking.py`
- `geo_demo/server.py`
- `static/mockup_only.js`
- `static/index.html`

Dashboard fields:

- `NN next-step recommendations`
- `Link / cite uplift vs observed`
- `Prompt-level Mockup Coverage`
- `Next-step Destination Mix`

Baseline comparison:

```text
Observed explicit NN cite/link baseline = 5
Mockup explicit NN link recommendations = calculated from API/mock run
```

---

## Claim 4 — Recommendation mapping is transparent

Implemented in:

- `data/recommendations.json`
- `data/corpus_improved.json`
- `geo_demo/server.py` via `recommendation_coverage()`
- `static/app.js` via `renderRecommendationCoverage()`

Visible dashboard section:

```text
Actionable Recommendation Coverage
```

It shows:

- recommendation ID;
- title;
- horizon;
- pillar;
- priority;
- demo asset signal;
- validation hypothesis;
- expected signal;
- demo asset count.

---

## 5. Files to inspect when debugging

### If the dashboard does not show baseline metrics

Check:

- `data/baseline_visibility.json`
- `geo_demo/data.py` → `load_baseline_visibility()`
- `geo_demo/server.py` → `/api/config`
- `static/app.js` → `renderObservedBaseline()`
- `static/mockup_only.js` → `applyMockupOnlyLabels()`

### If the API still runs both corpora

Check:

- `generate_responses.py` → default `--corpus-mode improved`
- `geo_demo/server.py` → `run_benchmark(..., corpus_mode="improved")`
- `static/mockup_only.js` → patched `runBenchmark()` sends `corpus_mode: "improved"`

### If Gemini returns mock fallback

Check:

- `.env` exists locally
- `.env` is not committed
- `GEMINI_API_KEY` is set
- `GEMINI_MODEL` is set to a valid model, for example `gemini-2.5-flash` or `gemini-2.5-flash-lite`
- dashboard answer badge shows `API - controlled sources`, not `Mock fallback`

### If links are not detected

Check:

- `data/corpus_improved.json` contains `source_url` starting with `https://www.nn.hu`
- `geo_demo/providers.py` includes the instruction to write out relevant NN URLs
- `geo_demo/linking.py` extracts explicit URLs
- generated answer actually contains the URL

---

## 6. Recommended first live run setup

Recommended provider:

```text
Google AI Studio / Gemini API
```

Recommended model:

```text
gemini-2.5-flash
```

or if rate limits are tighter:

```text
gemini-2.5-flash-lite
```

Recommended command:

```powershell
uv run python generate_responses.py --live --models gemini
uv run python dashboard.py --host 127.0.0.1 --port 8765
```

Expected request count:

```text
48 requests
```

Do not use OpenRouter for the first run unless OpenRouter support is added to the code. The current provider implementation directly supports OpenAI, Gemini and Claude APIs, not OpenRouter.

---

## 7. Final interpretation

The project now has a clear implementation chain:

```text
Observed baseline dashboard
→ baseline_visibility.json
→ improved mockup assets
→ Gemini/API mockup-only run
→ dashboard KPI comparison
→ recommendation implementation evidence
```

The most important strategic message is:

> NN is already visible in AI answers. The goal of the recommendations is to make NN more citable, linkable and actionable.

The most important technical message is:

> The project now avoids a second pre-mockup API run. It uses the observed baseline and only calls the model for the mockup/improved corpus.
