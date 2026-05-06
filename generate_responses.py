import argparse
import json
import time
from datetime import datetime, timezone

from geo_demo.data import RESULTS_DIR, load_prompts
from geo_demo.env import load_dotenv
from geo_demo.providers import PROVIDERS
from geo_demo.benchmark import results_to_csv, run_benchmark, summarize_results


def parse_args():
    parser = argparse.ArgumentParser(description="Generate NN GEO recommendation mockup validation responses.")
    parser.add_argument("--live", action="store_true", help="Use provider APIs when keys are configured.")
    parser.add_argument("--models", default=",".join(PROVIDERS), help="Comma-separated model ids.")
    parser.add_argument(
        "--corpus-mode",
        default="improved",
        choices=["improved", "current", "both"],
        help=(
            "Which source environment to run. Default is improved/mockup-only because the "
            "pre-mockup baseline is imported from the manual Excel/HTML benchmark."
        ),
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0,
        help=(
            "Optional delay between provider calls. Useful for free-tier rate limits, "
            "for example Gemini API RPM limits. Recommended: 5 for Flash-Lite, 7 for Flash."
        ),
    )
    parser.add_argument("--output", default=str(RESULTS_DIR / "latest_results.json"))
    parser.add_argument("--csv-output", default=str(RESULTS_DIR / "latest_results.csv"))
    return parser.parse_args()


def planned_request_count(models, corpus_mode):
    corpus_count = 2 if corpus_mode == "both" else 1
    return len(load_prompts()) * len(models) * corpus_count


def run_benchmark_with_optional_delay(models, corpus_mode, use_live, delay_seconds):
    if not use_live or delay_seconds <= 0:
        return run_benchmark(models=models, corpus_mode=corpus_mode, use_live=use_live)

    prompts = load_prompts()
    results = []
    total = planned_request_count(models, corpus_mode)
    done = 0
    corpus_modes = ["current", "improved"] if corpus_mode == "both" else [corpus_mode]

    for prompt in prompts:
        for mode in corpus_modes:
            for model in models:
                done += 1
                print(f"[{done}/{total}] Running {model} | {mode} | {prompt['id']}...")
                results.extend(
                    run_benchmark(
                        prompt_ids=[prompt["id"]],
                        models=[model],
                        corpus_mode=mode,
                        use_live=use_live,
                    )
                )
                if done < total:
                    print(f"Waiting {delay_seconds:g}s to avoid provider rate limits...")
                    time.sleep(delay_seconds)
    return results


def main():
    load_dotenv()
    args = parse_args()
    models = [item.strip() for item in args.models.split(",") if item.strip()]

    request_count = planned_request_count(models, args.corpus_mode)
    print(f"Planned provider calls: {request_count}")
    print(f"Delay between calls: {args.delay_seconds:g}s")

    results = run_benchmark_with_optional_delay(
        models=models,
        corpus_mode=args.corpus_mode,
        use_live=args.live,
        delay_seconds=args.delay_seconds,
    )
    summary = summarize_results(results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "use_live": args.live,
        "models": models,
        "corpus_mode": args.corpus_mode,
        "delay_seconds": args.delay_seconds,
        "baseline_source": "observed_manual_excel_html_benchmark",
        "results": results,
        "summary": summary,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    with open(args.csv_output, "w", encoding="utf-8", newline="") as handle:
        handle.write(results_to_csv(results))

    print(f"Wrote {len(results)} results to {args.output}")
    print(f"Wrote CSV export to {args.csv_output}")
    print(f"Corpus mode: {args.corpus_mode}")
    print(f"Mockup answer quality score: {summary['improved_avg']}")
    print(f"Mockup prompts with NN mentions: {summary['improved_prompts_with_nn_mentions']}")
    print(f"Mockup prompts with NN links: {summary['improved_prompts_with_nn_links']}")
    print(f"Mockup NN link recommendations: {summary['improved_nn_link_recommendations']}")

    if args.corpus_mode == "both":
        print(f"Controlled A/B score: {summary['current_avg']} -> {summary['improved_avg']} ({summary['delta']:+})")
    else:
        print("Observed pre-mockup baseline comes from data/baseline_visibility.json, not from a second API run.")


if __name__ == "__main__":
    main()
