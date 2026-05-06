import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from geo_demo.benchmark import run_single
from geo_demo.env import load_dotenv
from geo_demo.evidence_export import export_controlled_ab_workbooks, load_checkpoint, write_checkpoint_row
from geo_demo.providers import PROVIDERS, ProviderError
from import_prompts_from_excel import read_prompt_rows


DEFAULT_MODELS = ["openrouter_openai", "openrouter_gemini", "openrouter_claude"]
EXPECTED_PROMPT_COUNT = 48
DEFAULT_EXCEL_CANDIDATES = [
    Path(r"C:\Users\Boldizsár Nagy\Downloads\n8n_DCC.xlsx"),
    Path("data/n8n_DCC.xlsx"),
    Path("n8n_DCC.xlsx"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run controlled A/B validation for NN GEO recommendations and export Excel evidence files."
    )
    parser.add_argument(
        "excel_path",
        nargs="?",
        help="Path to n8n_DCC.xlsx. If omitted, common local locations are checked.",
    )
    parser.add_argument("--sheet", default="PROMPTS", help="Prompt worksheet name. Default: PROMPTS.")
    parser.add_argument("--prompt-col", default="A", help="Prompt column. Default: A.")
    parser.add_argument("--category-col", default="B", help="Category/segment column. Default: B.")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="Comma-separated provider ids.")
    parser.add_argument("--delay-seconds", type=float, default=0, help="Optional delay between provider calls.")
    parser.add_argument(
        "--output-dir",
        help="Output folder. Default: results/controlled_ab_<UTC timestamp>.",
    )
    parser.add_argument(
        "--limit-prompts",
        type=int,
        default=None,
        help="Optional smoke-test limit. Full evidence runs should omit this.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing checkpoint.jsonl in the output folder.",
    )
    return parser.parse_args()


def resolve_excel_path(value):
    if value:
        path = Path(value)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")
        return path

    for candidate in DEFAULT_EXCEL_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "n8n_DCC.xlsx was not found. Pass the Excel path explicitly, for example: "
        "python run_controlled_ab.py \"C:\\Users\\...\\Downloads\\n8n_DCC.xlsx\""
    )


def load_excel_prompts(excel_path, sheet, prompt_col, category_col, limit=None):
    prompts = read_prompt_rows(excel_path, sheet_name=sheet, prompt_col=prompt_col.upper(), category_col=category_col.upper())
    if limit is not None:
        prompts = prompts[:limit]
    if limit is None and len(prompts) != EXPECTED_PROMPT_COUNT:
        raise ValueError(f"Expected {EXPECTED_PROMPT_COUNT} prompts, got {len(prompts)} from {excel_path}")
    return prompts


def parse_models(value):
    models = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [model for model in models if model not in PROVIDERS]
    if unknown:
        raise ValueError(f"Unknown provider id(s): {', '.join(unknown)}")
    return models


def require_configured_providers(models):
    missing = []
    for model in models:
        env_key = PROVIDERS[model]["env_key"]
        if not os.getenv(env_key):
            missing.append(f"{model} ({env_key})")
    if missing:
        raise RuntimeError(
            "Evidence mode requires live provider API keys and does not use mock fallback. Missing: "
            + ", ".join(missing)
        )


def default_output_dir():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"controlled_ab_{stamp}"


def result_key(result):
    return (result.get("prompt_id"), result.get("corpus_mode"), result.get("model"))


def checkpoint_index(results):
    indexed = {}
    for result in results:
        if result.get("provider_mode") != "api":
            raise ValueError("Checkpoint contains non-API rows. Evidence run cannot resume from mock/fallback data.")
        indexed[result_key(result)] = result
    return indexed


def iter_run_plan(prompts, models):
    for corpus_mode in ("current", "improved"):
        for prompt in prompts:
            for model in models:
                yield prompt, corpus_mode, model


def run_controlled_ab(prompts, models, output_dir, delay_seconds=0, resume=True):
    output_dir = Path(output_dir)
    checkpoint_path = output_dir / "checkpoint.jsonl"
    indexed = checkpoint_index(load_checkpoint(checkpoint_path)) if resume else {}
    total = len(prompts) * len(models) * 2
    completed = len(indexed)

    for prompt, corpus_mode, model in iter_run_plan(prompts, models):
        key = (prompt["id"], corpus_mode, model)
        if key in indexed:
            print(f"[skip {completed}/{total}] {model} | {corpus_mode} | {prompt['id']} already checkpointed")
            continue

        done_number = completed + 1
        print(f"[{done_number}/{total}] {model} | {corpus_mode} | {prompt['id']}")
        try:
            result = run_single(prompt, corpus_mode, model, use_live=True)
        except ProviderError:
            print("Provider call failed. Checkpoint is preserved; rerun with the same --output-dir to resume.")
            raise
        indexed[key] = result
        write_checkpoint_row(checkpoint_path, result)
        completed += 1

        if completed < total and delay_seconds > 0:
            time.sleep(delay_seconds)

    ordered = []
    for prompt, corpus_mode, model in iter_run_plan(prompts, models):
        ordered.append(indexed[(prompt["id"], corpus_mode, model)])
    return ordered


def main():
    load_dotenv()
    args = parse_args()
    excel_path = resolve_excel_path(args.excel_path)
    models = parse_models(args.models)
    require_configured_providers(models)

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    prompts = load_excel_prompts(
        excel_path,
        sheet=args.sheet,
        prompt_col=args.prompt_col,
        category_col=args.category_col,
        limit=args.limit_prompts,
    )

    print(f"Excel prompt source: {excel_path}")
    print(f"Prompts: {len(prompts)}")
    print(f"Models: {', '.join(models)}")
    print(f"Output folder: {output_dir}")
    print(f"Planned calls: {len(prompts) * len(models) * 2}")

    results = run_controlled_ab(
        prompts=prompts,
        models=models,
        output_dir=output_dir,
        delay_seconds=args.delay_seconds,
        resume=not args.no_resume,
    )

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "excel_path": str(excel_path),
        "prompt_count": len(prompts),
        "models": ", ".join(models),
        "run_shape": "A=current corpus, then B=current+recommendation/mockup corpus",
        "methodology": "controlled A/B validation of recommendation impact; no live web browsing",
        "mock_fallback": "disabled",
    }
    outputs = export_controlled_ab_workbooks(results, output_dir, metadata)

    print(json.dumps({key: str(path) for key, path in outputs.items()}, ensure_ascii=False, indent=2))
    print("Controlled A/B evidence export completed.")


if __name__ == "__main__":
    main()
