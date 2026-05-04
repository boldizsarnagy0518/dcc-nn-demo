# First API Run Guide

## Recommended provider logic

The project supports four providers:

```text
openai
 gemini
claude
openrouter
```

For normal use, Gemini is still the cleanest direct provider. If your Gemini daily quota is exhausted, OpenRouter can be used as a temporary free-model test route.

## Prompt source

The prompt set is stored in:

```text
data/prompts.json
```

It has been updated from the uploaded Excel benchmark file:

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

## Request count

The project uses the uploaded Excel/HTML dashboard as the observed pre-mockup baseline.

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

### 2A. Gemini setup

```text
GEMINI_API_KEY=your_google_ai_studio_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Run:

```powershell
uv run python generate_responses.py --live --models gemini --delay-seconds 7
```

### 2B. OpenRouter free-model setup

Use this when Gemini quota is exhausted or when you want to test an OpenRouter free model.

```text
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```

OpenRouter uses one API key for all OpenRouter models. The model ID controls which model is used.

For a quick smoke test with OpenRouter, run one selected prompt from the dashboard UI, or temporarily run a small subset if you add prompt filtering later.

For the full 48-prompt run:

```powershell
uv run python generate_responses.py --live --models openrouter --delay-seconds 4
```

Reason for delay:

```text
OpenRouter free models are often around 20 requests/minute.
60 / 20 = 3 seconds/request, so 4 seconds gives a small buffer.
```

Important free-tier warning:

```text
48 requests is very close to a 50/day free limit.
```

So only run the full benchmark when the 1-prompt smoke test works.

## Start the dashboard

```powershell
uv run python dashboard.py --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## What to check after running

In the answer cards, check the provider badge.

Good:

```text
API - controlled sources
```

Bad for validation:

```text
Mock fallback
```

The latest code no longer uses API fallback in live mode. If an API call fails, the run should error instead of silently producing a fallback answer.

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
