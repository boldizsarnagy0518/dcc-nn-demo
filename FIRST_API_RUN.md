# First API Run Guide

## Recommended provider for the first run

Use **Google AI Studio / Gemini API** for the first live validation run.

Reason:

- The current code already has a native Gemini provider.
- No OpenRouter provider is implemented yet.
- The project now runs mockup-only validation by default, so a full Gemini-only run is only 48 requests.
- Gemini 2.5 Flash / Flash-Lite are suitable for low-cost POC validation.

## Prompt source

The prompt set is stored in:

```text
data/prompts.json
```

It has now been updated from the uploaded Excel benchmark file:

```text
n8n_DCC.xlsx
```

Source sheet and column:

```text
Sheet: PROMPTS
Prompt column: A
Header row: row 1
Prompt rows: row 2 onward
```

Column B is imported as the prompt category / segment. In the uploaded Excel this is mainly the age group, for example `18–24`, `25–34`, `35–44`, etc.

The current `data/prompts.json` contains 48 prompts.

To regenerate `data/prompts.json` from an Excel file later, place the Excel file locally and run:

```powershell
uv run python import_prompts_from_excel.py path\to\n8n_DCC.xlsx
```

Optional explicit version:

```powershell
uv run python import_prompts_from_excel.py path\to\n8n_DCC.xlsx --sheet PROMPTS --prompt-col A --category-col B --output data/prompts.json
```

## Why not OpenRouter first?

OpenRouter can be useful later, but it is not the best first-run option in the current codebase.

Current limitation:

```text
geo_demo/providers.py supports: OpenAI, Gemini, Claude
geo_demo/providers.py does not yet support: OpenRouter
```

To use OpenRouter, a new provider wrapper would need to be added.

Also, OpenRouter free models have free-tier request limits. This can still be useful for small tests, but it is not as clean as using the already implemented Gemini provider.

## Request count

The project now uses the uploaded Excel/HTML dashboard as the observed pre-mockup baseline.

The API run only tests the mockup / improved corpus.

Therefore:

```text
48 prompts × 1 corpus mode × 1 model = 48 requests
```

Not:

```text
48 prompts × 2 corpus modes × 1 model = 96 requests
```

The old controlled A/B mode still exists, but it is optional.

## Setup steps

### 1. Create `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

### 2. Fill only Gemini first

Recommended first setup:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini

GEMINI_API_KEY=your_google_ai_studio_key_here
GEMINI_MODEL=gemini-2.5-flash

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

If you want the cheapest / fastest variant and quality is acceptable, you can try:

```text
GEMINI_MODEL=gemini-2.5-flash-lite
```

If you use a model with strict per-minute limits, run with a delay. For example:

```powershell
uv run python generate_responses.py --live --models gemini --delay-seconds 7
```

### 3. Run the live validation

```powershell
uv run python generate_responses.py --live --models gemini --delay-seconds 7
```

This writes:

```text
results/latest_results.json
results/latest_results.csv
```

These files are intentionally ignored by git.

### 4. Start the dashboard

```powershell
uv run python dashboard.py --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## What to check after running

In the answer cards, check the badge.

Good:

```text
API - controlled sources
```

Bad for validation:

```text
Mock fallback
```

If you see `Mock fallback`, the API call failed. The dashboard still works, but those answers should not be treated as live LLM validation evidence.

## Optional: old controlled A/B mode

If you want to run the old current-vs-improved setup, use:

```powershell
uv run python generate_responses.py --live --models gemini --corpus-mode both
```

That will require:

```text
48 prompts × 2 corpus modes × 1 model = 96 requests
```

For the current project story, this is not necessary because the pre-mockup baseline already comes from the uploaded manual benchmark.

## Suggested first-run interpretation

Use this wording when explaining the result:

```text
The observed baseline comes from the 48-prompt manual benchmark. The live API run only tests the recommendation mockup assets. This keeps cost low while still validating whether the proposed assets can make AI-style answers more citable, linkable and actionable.
```
