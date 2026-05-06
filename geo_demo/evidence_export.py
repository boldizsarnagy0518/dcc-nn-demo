import json
from pathlib import Path

from .benchmark import domain_from_url, recommendation_coverage, results_to_csv, summarize_results
from .excel_export import write_workbook


OUTPUT_HEADER = [
    "prompt_id",
    "category",
    "prompt",
    "corpus_mode",
    "provider",
    "provider_label",
    "exact_model_id",
    "provider_mode",
    "score_total",
    "mention_quality",
    "product_specificity",
    "credibility",
    "actionability",
    "nn_mentions",
    "explicit_nn_links",
    "nn_link_urls",
    "competitor_mentions",
    "recommendation_ids",
    "retrieved_source_ids",
    "retrieved_source_urls",
    "retrieved_source_domains",
    "answer",
]


def _join(values):
    return "; ".join(str(value) for value in values if value is not None and str(value) != "")


def _result_row(result):
    sources = result.get("retrieved_sources", [])
    link_urls = [item.get("url", "") for item in result.get("link_recommendations", [])]
    source_urls = [source.get("source_url", "") for source in sources]
    source_domains = [domain_from_url(url) for url in source_urls]
    scores = result.get("scores", {})
    return [
        result.get("prompt_id"),
        result.get("category"),
        result.get("prompt"),
        result.get("corpus_mode"),
        result.get("model"),
        result.get("model_label"),
        result.get("exact_model_id"),
        result.get("provider_mode"),
        scores.get("total"),
        scores.get("mention_quality"),
        scores.get("product_specificity"),
        scores.get("credibility"),
        scores.get("actionability"),
        result.get("nn_mentions"),
        len(result.get("link_recommendations", [])),
        _join(link_urls),
        json.dumps(result.get("competitor_mentions", {}), ensure_ascii=False),
        _join(result.get("recommendation_ids", [])),
        _join(source.get("id") for source in sources),
        _join(source_urls),
        _join(source_domains),
        result.get("answer"),
    ]


def output_rows(results):
    rows = [OUTPUT_HEADER]
    rows.extend(_result_row(result) for result in results)
    return rows


def summary_rows(summary):
    return [
        ["metric", "value"],
        ["validation_mode", summary.get("validation_mode")],
        ["current_avg", summary.get("current_avg")],
        ["improved_avg", summary.get("improved_avg")],
        ["delta", summary.get("delta")],
        ["compared_pairs", summary.get("compared_pairs")],
        ["improved_pairs", summary.get("improved_pairs")],
        ["current_nn_mentions", summary.get("current_nn_mentions")],
        ["improved_nn_mentions", summary.get("improved_nn_mentions")],
        ["current_nn_link_recommendations", summary.get("current_nn_link_recommendations")],
        ["improved_nn_link_recommendations", summary.get("improved_nn_link_recommendations")],
        ["link_recommendation_delta", summary.get("link_recommendation_delta")],
    ]


def model_summary_rows(summary):
    rows = [["provider", "current_avg", "improved_avg", "delta"]]
    for model, values in sorted((summary.get("model_summary") or {}).items()):
        rows.append([model, values.get("current"), values.get("improved"), values.get("delta")])
    return rows


def prompt_summary_rows(summary):
    rows = [
        [
            "prompt_id",
            "category",
            "prompt",
            "current_avg",
            "improved_avg",
            "delta",
            "current_mentions",
            "improved_mentions",
            "current_links",
            "improved_links",
        ]
    ]
    for item in summary.get("prompt_summary", []):
        rows.append(
            [
                item.get("prompt_id"),
                item.get("category"),
                item.get("prompt"),
                item.get("current_avg"),
                item.get("improved_avg"),
                item.get("delta"),
                item.get("current_mentions"),
                item.get("improved_mentions"),
                item.get("current_links"),
                item.get("improved_links"),
            ]
        )
    return rows


def recommendation_summary_rows(results):
    recommendations = {item["id"]: item for item in recommendation_coverage()}
    retrievals = {rec_id: {"current": 0, "improved": 0, "prompts": set(), "models": set()} for rec_id in recommendations}

    for result in results:
        mode = result.get("corpus_mode")
        if mode not in {"current", "improved"}:
            continue
        for source in result.get("retrieved_sources", []):
            for rec_id in source.get("recommendation_ids") or []:
                bucket = retrievals.setdefault(rec_id, {"current": 0, "improved": 0, "prompts": set(), "models": set()})
                bucket[mode] += 1
                if mode == "improved":
                    bucket["prompts"].add(result.get("prompt_id"))
                    bucket["models"].add(result.get("model"))

    rows = [
        [
            "recommendation_id",
            "title",
            "pillar",
            "horizon",
            "priority",
            "demo_asset_count",
            "current_retrievals",
            "improved_retrievals",
            "retrieval_delta",
            "improved_prompt_coverage",
            "improved_model_coverage",
        ]
    ]
    for rec_id, rec in sorted(recommendations.items()):
        data = retrievals.get(rec_id, {"current": 0, "improved": 0, "prompts": set(), "models": set()})
        rows.append(
            [
                rec_id,
                rec.get("title"),
                rec.get("pillar"),
                rec.get("horizon"),
                rec.get("priority"),
                rec.get("demo_asset_count"),
                data["current"],
                data["improved"],
                data["improved"] - data["current"],
                len(data["prompts"]),
                len(data["models"]),
            ]
        )
    return rows


def metadata_rows(metadata):
    return [["key", "value"], *[[key, value] for key, value in metadata.items()]]


def export_controlled_ab_workbooks(results, output_dir, metadata):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_results = [result for result in results if result.get("corpus_mode") == "current"]
    improved_results = [result for result in results if result.get("corpus_mode") == "improved"]
    summary = summarize_results(results)

    a_path = write_workbook(
        output_dir / "A_current_outputs.xlsx",
        {
            "Outputs": output_rows(current_results),
            "Run Metadata": metadata_rows(metadata),
        },
    )
    b_path = write_workbook(
        output_dir / "B_improved_outputs.xlsx",
        {
            "Outputs": output_rows(improved_results),
            "Run Metadata": metadata_rows(metadata),
        },
    )
    summary_path = write_workbook(
        output_dir / "AB_summary.xlsx",
        {
            "Executive Summary": summary_rows(summary),
            "Model Summary": model_summary_rows(summary),
            "Prompt Summary": prompt_summary_rows(summary),
            "Recommendation Coverage": recommendation_summary_rows(results),
            "Run Metadata": metadata_rows(metadata),
        },
    )

    (output_dir / "all_results.csv").write_text(results_to_csv(results), encoding="utf-8")
    (output_dir / "all_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "A_current_outputs": a_path,
        "B_improved_outputs": b_path,
        "AB_summary": summary_path,
        "all_results_csv": output_dir / "all_results.csv",
        "all_results_json": output_dir / "all_results.json",
    }


def write_checkpoint_row(path, result):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def load_checkpoint(path):
    path = Path(path)
    if not path.exists():
        return []
    results = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                results.append(json.loads(line))
    return results
