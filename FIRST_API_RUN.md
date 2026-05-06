# First Controlled A/B Evidence Run

Use this guide for the first real evidence run. The default setup now uses OpenRouter.

## 1. Check Prompt Source

The input is the Excel file:

```text
n8n_DCC.xlsx
```

Expected source:

```text
Sheet: PROMPTS
Prompt column: A
Category column: B
Expected prompts: 48
```

## 2. Configure OpenRouter

Create `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill:

```text
OPENROUTER_API_KEY=...
OPENROUTER_OPENAI_MODEL=openai/gpt-5.2
OPENROUTER_GEMINI_MODEL=google/gemini-3-pro-preview
OPENROUTER_CLAUDE_MODEL=anthropic/claude-sonnet-4.6
```

If OpenRouter shows a slightly different current model slug, update the relevant value in `.env`.

## 3. Smoke Test

Run one prompt first:

```powershell
python run_controlled_ab.py "C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx" --limit-prompts 1
```

This should make 6 calls:

```text
1 prompt x 2 corpus modes x 3 model-family routes
```

## 4. Full Run

The full evidence run is:

```text
48 prompts x 2 corpus modes x 3 model-family routes = 288 provider calls
```

Run:

```powershell
python run_controlled_ab.py "C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx" --delay-seconds 2
```

If a provider fails, rerun with the same output folder:

```powershell
python run_controlled_ab.py "C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx" --output-dir results\controlled_ab_<timestamp> --delay-seconds 2
```

The runner resumes from `checkpoint.jsonl`.

## 5. Interpretation

Use this wording:

```text
The original live benchmark identified the visibility and citation gap. The controlled A/B validation uses OpenRouter-hosted access to GPT, Gemini and Claude model families to isolate whether the recommended NN assets can improve AI-style answer quality, citation readiness and next-step actionability.
```

Do not say:

```text
This proves NN will rank higher in public ChatGPT, Gemini or Claude.
```
