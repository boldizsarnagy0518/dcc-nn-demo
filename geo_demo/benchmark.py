import csv
import io
import json
import os
import re
from urllib.parse import urlparse

from .data import load_baseline_visibility, load_corpus, load_prompts, load_recommendations
from .linking import count_nn_mentions, extract_link_recommendations
from .providers import PROVIDERS, build_grounded_prompt, call_provider, mock_answer
from .retrieval import retrieve_sources
from .scoring import score_answer


COMPETITORS = ("UNIQA", "Generali", "Allianz", "Groupama")


def provider_model_id(provider_id):
    config = PROVIDERS[provider_id]
    return os.getenv(config["env_model"], config["default_model"])


def compact_source(source):
    return {
        "id": source["id"],
        "title": source["title"],
        "type": source["type"],
        "pillar": source["pillar"],
        "status": source.get("status", "unknown"),
        "source_url": source.get("source_url", "local-demo"),
        "recommendation_ids": source.get("recommendation_ids", []),
        "body": source["body"],
    }


def domain_from_url(url):
    parsed = urlparse(url or "")
    if parsed.netloc:
        return parsed.netloc.lower()
    return "local-demo"


def count_competitor_mentions(answer):
    mentions = {}
    for competitor in COMPETITORS:
        pattern = rf"\b{re.escape(competitor)}\b"
        mentions[competitor] = len(re.findall(pattern, answer or "", flags=re.IGNORECASE))
    return mentions


def recommendation_ids_from_sources(sources):
    ids = set()
    for source in sources:
        ids.update(source.get("recommendation_ids") or [])
    return sorted(ids)


def recommendation_coverage():
    recommendations = load_recommendations()
    improved_sources = load_corpus("improved")
    source_type_counts = {}
    recommendation_asset_counts = {}

    for source in improved_sources:
        source_type = source.get("type")
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        for rec_id in source.get("recommendation_ids") or []:
            recommendation_asset_counts[rec_id] = recommendation_asset_counts.get(rec_id, 0) + 1

    enriched = []
    for rec in recommendations:
        asset_count = recommendation_asset_counts.get(rec["id"], 0)
        if not asset_count:
            for asset_type in rec.get("asset_types", []):
                if asset_type == "dashboard":
                    asset_count += 1
                else:
                    asset_count += source_type_counts.get(asset_type, 0)
        item = dict(rec)
        item["demo_asset_count"] = asset_count
        enriched.append(item)
    return enriched


def run_single(prompt_item, corpus_mode, provider_id, use_live=False):
    corpus = load_corpus(corpus_mode)
    sources = retrieve_sources(prompt_item["prompt"], corpus, limit=5)
    grounded_prompt = build_grounded_prompt(prompt_item["prompt"], sources)

    if use_live:
        answer = call_provider(provider_id, grounded_prompt)
        provider_mode = "api"
        run_mode = "api_controlled_sources"
    else:
        answer = mock_answer(provider_id, prompt_item["prompt"], sources, corpus_mode)
        provider_mode = "mock"
        run_mode = "local_mock"

    compact_sources = [compact_source(source) for source in sources]
    return {
        "prompt_id": prompt_item["id"],
        "prompt": prompt_item["prompt"],
        "category": prompt_item["category"],
        "model": provider_id,
        "model_label": PROVIDERS[provider_id]["label"],
        "exact_model_id": provider_model_id(provider_id),
        "provider_mode": provider_mode,
        "run_mode": run_mode,
        "corpus_mode": corpus_mode,
        "answer": answer,
        "citations": [source["id"] for source in sources],
        "nn_mentions": count_nn_mentions(answer),
        "competitor_mentions": count_competitor_mentions(answer),
        "link_recommendations": extract_link_recommendations(answer, sources),
        "retrieved_sources": compact_sources,
        "recommendation_ids": recommendation_ids_from_sources(compact_sources),
        "scores": score_answer(answer, sources),
        "error": None,
    }


def run_benchmark(prompt_ids=None, corpus_mode="improved", models=None, use_live=False):
    prompts = load_prompts()
    prompt_lookup = {prompt["id"]: prompt for prompt in prompts}
    if prompt_ids:
        selected_prompts = [prompt_lookup[prompt_id] for prompt_id in prompt_ids if prompt_id in prompt_lookup]
    else:
        selected_prompts = prompts

    selected_models = models or list(PROVIDERS)
    modes = ["current", "improved"] if corpus_mode == "both" else [corpus_mode]

    results = []
    for prompt_item in selected_prompts:
        for mode in modes:
            for provider_id in selected_models:
                if provider_id in PROVIDERS:
                    results.append(run_single(prompt_item, mode, provider_id, use_live=use_live))
    return results


def summarize_results(results):
    baseline = load_baseline_visibility()
    by_mode = {"current": [], "improved": []}
    score_keys = ("mention_quality", "product_specificity", "credibility", "actionability")
    score_breakdown = {
        "current": {key: [] for key in score_keys},
        "improved": {key: [] for key in score_keys},
    }
    links_by_mode = {"current": 0, "improved": 0}
    linked_answers_by_mode = {"current": 0, "improved": 0}
    mentions_by_mode = {"current": 0, "improved": 0}
    prompts_by_mode = {"current": set(), "improved": set()}
    mention_prompts_by_mode = {"current": set(), "improved": set()}
    link_prompts_by_mode = {"current": set(), "improved": set()}
    source_type_mix = {"current": {}, "improved": {}}
    source_domain_mix = {"current": {}, "improved": {}}
    next_step_mix = {"current": {}, "improved": {}}
    competitor_mentions = {"current": {name: 0 for name in COMPETITORS}, "improved": {name: 0 for name in COMPETITORS}}
    recommendation_mix = {"current": {}, "improved": {}}
    by_model = {}
    prompt_deltas = {}
    prompt_summary = {}
    for result in results:
        total = result["scores"]["total"]
        mode = result["corpus_mode"]
        prompt_id = result["prompt_id"]
        prompts_by_mode.setdefault(mode, set()).add(prompt_id)
        by_mode.setdefault(mode, []).append(total)
        for key in score_keys:
            score_breakdown.setdefault(mode, {}).setdefault(key, []).append(result["scores"].get(key, 0))
        link_count = len(result.get("link_recommendations", []))
        links_by_mode[mode] = links_by_mode.get(mode, 0) + link_count
        linked_answers_by_mode[mode] = linked_answers_by_mode.get(mode, 0) + (1 if link_count else 0)
        for link in result.get("link_recommendations", []):
            link_type = link.get("type") or "unknown"
            next_step_mix.setdefault(mode, {})[link_type] = next_step_mix.setdefault(mode, {}).get(link_type, 0) + 1
        for source in result.get("retrieved_sources", []):
            source_type = source.get("type") or "unknown"
            source_type_mix.setdefault(mode, {})[source_type] = source_type_mix.setdefault(mode, {}).get(source_type, 0) + 1
            domain = domain_from_url(source.get("source_url"))
            source_domain_mix.setdefault(mode, {})[domain] = source_domain_mix.setdefault(mode, {}).get(domain, 0) + 1
            for rec_id in source.get("recommendation_ids") or []:
                recommendation_mix.setdefault(mode, {})[rec_id] = recommendation_mix.setdefault(mode, {}).get(rec_id, 0) + 1
        for competitor, count in result.get("competitor_mentions", {}).items():
            competitor_mentions.setdefault(mode, {}).setdefault(competitor, 0)
            competitor_mentions[mode][competitor] += count
        mention_count = result.get("nn_mentions", 0)
        mentions_by_mode[mode] = mentions_by_mode.get(mode, 0) + mention_count
        if mention_count:
            mention_prompts_by_mode.setdefault(mode, set()).add(prompt_id)
        if link_count:
            link_prompts_by_mode.setdefault(mode, set()).add(prompt_id)
        by_model.setdefault(result["model"], {}).setdefault(mode, []).append(total)
        key = (result["prompt_id"], result["model"])
        prompt_deltas.setdefault(key, {})[mode] = total
        prompt_row = prompt_summary.setdefault(
            prompt_id,
            {
                "prompt_id": prompt_id,
                "category": result["category"],
                "prompt": result["prompt"],
                "current_scores": [],
                "improved_scores": [],
                "current_mentions": 0,
                "improved_mentions": 0,
                "current_links": 0,
                "improved_links": 0,
                "current_linked_models": 0,
                "improved_linked_models": 0,
            },
        )
        prompt_row[f"{mode}_scores"].append(total)
        prompt_row[f"{mode}_mentions"] += mention_count
        prompt_row[f"{mode}_links"] += link_count
        if link_count:
            prompt_row[f"{mode}_linked_models"] += 1

    def avg(values):
        return round(sum(values) / len(values), 1) if values else 0

    current_avg = avg(by_mode.get("current", []))
    improved_avg = avg(by_mode.get("improved", []))
    has_current = bool(by_mode.get("current"))
    has_improved = bool(by_mode.get("improved"))
    validation_mode = "controlled_ab" if has_current and has_improved else "mockup_only"

    improved_pairs = 0
    compared_pairs = 0
    for pair in prompt_deltas.values():
        if "current" in pair and "improved" in pair:
            compared_pairs += 1
            if pair["improved"] > pair["current"]:
                improved_pairs += 1

    model_summary = {}
    for model, modes in by_model.items():
        model_summary[model] = {
            "current": avg(modes.get("current", [])),
            "improved": avg(modes.get("improved", [])),
            "delta": round(avg(modes.get("improved", [])) - avg(modes.get("current", [])), 1) if has_current else None,
        }

    breakdown_summary = {}
    for key in score_keys:
        current_score = avg(score_breakdown["current"].get(key, []))
        improved_score = avg(score_breakdown["improved"].get(key, []))
        breakdown_summary[key] = {
            "current": current_score,
            "improved": improved_score,
            "delta": round(improved_score - current_score, 1) if has_current else None,
        }

    prompt_rows = []
    for row in prompt_summary.values():
        current_score = avg(row.pop("current_scores"))
        improved_score = avg(row.pop("improved_scores"))
        row["current_avg"] = current_score
        row["improved_avg"] = improved_score
        row["delta"] = round(improved_score - current_score, 1) if current_score else None
        prompt_rows.append(row)
    prompt_rows.sort(key=lambda item: item["prompt_id"])

    baseline_links = baseline.get("baseline_explicit_nn_link_references", 0)
    baseline_presence = baseline.get("nn_presence_total", 0)

    return {
        "validation_mode": validation_mode,
        "observed_baseline": baseline,
        "current_avg": current_avg,
        "improved_avg": improved_avg,
        "delta": round(improved_avg - current_avg, 1) if has_current else None,
        "improved_pairs": improved_pairs,
        "compared_pairs": compared_pairs,
        "model_summary": model_summary,
        "score_breakdown": breakdown_summary,
        "source_type_mix": source_type_mix,
        "source_domain_mix": source_domain_mix,
        "next_step_mix": next_step_mix,
        "competitor_mentions": competitor_mentions,
        "recommendation_mix": recommendation_mix,
        "prompt_summary": prompt_rows,
        "current_nn_mentions": mentions_by_mode.get("current", 0),
        "improved_nn_mentions": mentions_by_mode.get("improved", 0),
        "current_total_prompts": len(prompts_by_mode.get("current", set())),
        "improved_total_prompts": len(prompts_by_mode.get("improved", set())),
        "current_prompts_with_nn_mentions": len(mention_prompts_by_mode.get("current", set())),
        "improved_prompts_with_nn_mentions": len(mention_prompts_by_mode.get("improved", set())),
        "current_prompts_with_nn_links": len(link_prompts_by_mode.get("current", set())),
        "improved_prompts_with_nn_links": len(link_prompts_by_mode.get("improved", set())),
        "current_nn_link_recommendations": links_by_mode.get("current", 0),
        "improved_nn_link_recommendations": links_by_mode.get("improved", 0),
        "link_recommendation_delta": links_by_mode.get("improved", 0) - links_by_mode.get("current", 0) if has_current else None,
        "current_linked_answers": linked_answers_by_mode.get("current", 0),
        "improved_linked_answers": linked_answers_by_mode.get("improved", 0),
        "observed_baseline_nn_presence": baseline_presence,
        "observed_baseline_nn_links": baseline_links,
        "mockup_vs_observed_link_delta": links_by_mode.get("improved", 0) - baseline_links,
        "mockup_vs_observed_presence_delta": mentions_by_mode.get("improved", 0) - baseline_presence,
    }


def results_to_csv(results):
    output = io.StringIO()
    fieldnames = [
        "prompt_id",
        "category",
        "model",
        "model_label",
        "exact_model_id",
        "provider_mode",
        "corpus_mode",
        "score_total",
        "mention_quality",
        "product_specificity",
        "credibility",
        "actionability",
        "nn_mentions",
        "nn_link_recommendations",
        "competitor_mentions",
        "recommendation_ids",
        "source_ids",
        "source_domains",
        "source_urls",
        "answer",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        sources = result.get("retrieved_sources", [])
        writer.writerow(
            {
                "prompt_id": result.get("prompt_id"),
                "category": result.get("category"),
                "model": result.get("model"),
                "model_label": result.get("model_label"),
                "exact_model_id": result.get("exact_model_id"),
                "provider_mode": result.get("provider_mode"),
                "corpus_mode": result.get("corpus_mode"),
                "score_total": result.get("scores", {}).get("total"),
                "mention_quality": result.get("scores", {}).get("mention_quality"),
                "product_specificity": result.get("scores", {}).get("product_specificity"),
                "credibility": result.get("scores", {}).get("credibility"),
                "actionability": result.get("scores", {}).get("actionability"),
                "nn_mentions": result.get("nn_mentions"),
                "nn_link_recommendations": len(result.get("link_recommendations", [])),
                "competitor_mentions": json.dumps(result.get("competitor_mentions", {}), ensure_ascii=False),
                "recommendation_ids": ";".join(result.get("recommendation_ids", [])),
                "source_ids": ";".join(source.get("id", "") for source in sources),
                "source_domains": ";".join(domain_from_url(source.get("source_url")) for source in sources),
                "source_urls": ";".join(source.get("source_url", "") for source in sources),
                "answer": result.get("answer"),
            }
        )
    return output.getvalue()
