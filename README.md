# NN GEO Controlled A/B Evidence Pipeline

This repository supports the NN Hungary GenAI visibility / GEO case with two artifacts:

1. **Controlled A/B evidence pipeline**  
   Runs the same 48 Excel prompts against current NN/current-like sources and improved mockup sources, then exports client-facing Excel evidence.

2. **Clickable NN mockup site**  
   A Vercel-ready static mockup in `nn_actionable_site/` that shows how the actionable recommendations could look to an NN customer.

The main proof point is:

```text
Controlled A/B validation of recommendation impact.
```

It does not claim to prove live public ChatGPT, Gemini or Claude rankings.

## Methodology

The recommended evidence run is:

```text
A = current NN/current-like corpus
B = current corpus + actionable recommendation/mockup corpus + parsed mockup HTML signals
```

Run shape:

```text
48 prompts x 2 corpus modes x 3 model-family routes = 288 provider calls
```

The default run uses OpenRouter model-family aliases:

```text
openrouter_openai   -> OpenRouter-hosted GPT route
openrouter_gemini   -> OpenRouter-hosted Gemini route
openrouter_claude   -> OpenRouter-hosted Claude route
```

This keeps setup simple: one OpenRouter API key, three configured model IDs.

## Setup

Create `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill this:

```text
OPENROUTER_API_KEY=...
OPENROUTER_OPENAI_MODEL=openai/gpt-5.2
OPENROUTER_GEMINI_MODEL=google/gemini-3-pro-preview
OPENROUTER_CLAUDE_MODEL=anthropic/claude-sonnet-4.6
```

The exact model IDs can be changed if OpenRouter lists a slightly different/current model slug.

## Run Controlled A/B

The runner reads prompts directly from the Excel `PROMPTS` sheet.

Smoke test first:

```powershell
python run_controlled_ab.py "C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx" --limit-prompts 1
```

This runs:

```text
1 prompt x 2 corpus modes x 3 model-family routes = 6 calls
```

Full run:

```powershell
python run_controlled_ab.py "C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx" --delay-seconds 2
```

If the Excel file is in a known local location, the path can be omitted:

```powershell
python run_controlled_ab.py --delay-seconds 2
```

Evidence mode uses live API calls only. There is no mock fallback. If a provider call fails, the checkpoint remains and the run can be resumed with the same `--output-dir`.

## Outputs

Each run creates:

```text
results/controlled_ab_<timestamp>/
  checkpoint.jsonl
  all_results.json
  all_results.csv
  A_current_outputs.xlsx
  B_improved_outputs.xlsx
  AB_summary.xlsx
```

The Excel files contain prompt text, model route, exact model ID, answer text, retrieved evidence, NN links, competitor mentions, recommendation IDs and score breakdowns.

## Static Mockup Site

The clickable customer-facing mockup is in:

```text
nn_actionable_site/
```

The root `vercel.json` routes a Vercel deployment to this static site. Use it for QR-code demos and jury/client walkthroughs.

See:

```text
VERCEL_DEPLOYMENT_GUIDE.md
```

## Tests

```powershell
python -m compileall -q geo_demo tests run_controlled_ab.py
python -m unittest discover -s tests
```

## Recommended Presentation Wording

```text
The original live benchmark identified the visibility and citation gap. The controlled A/B validation uses OpenRouter-hosted access to GPT, Gemini and Claude model families to isolate whether the recommended NN assets can improve AI-style answer quality, citation readiness and next-step actionability.
```
