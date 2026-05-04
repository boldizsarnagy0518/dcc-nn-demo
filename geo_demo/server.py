import argparse
import csv
import io
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .data import STATIC_DIR, corpus_modes, load_baseline_visibility, load_corpus, load_prompts, load_recommendations
from .env import load_dotenv
from .providers import (
    PROVIDERS,
    ProviderError,
    build_grounded_prompt,
    call_provider,
    mock_answer,
    provider_status,
)
from .linking import count_nn_mentions, extract_link_recommendations
from .retrieval import retrieve_sources
from .results import load_latest_results
from .scoring import score_answer


COMPETITORS = ("UNIQA", "Generali", "Allianz", "Groupama")


def json_response(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, body, content_type="text/plain; charset=utf-8", status=200):
    payload = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def read_request_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)


def compact_source(source):
    return {
        "id": source["id"],
        "title": source["title"],
        "type": source["type"],
        "pillar": source["pillar"],
        "status": source.get("status", "unknown"),
        "source_url": source.get("source_url", "local-demo"),
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


def recommendation_coverage():
    recommendations = load_recommendations()
    improved_sources = load_corpus("improved")
    source_type_counts = {}
    for source in improved_sources:
        source_type = source.get("type")
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

    enriched = []
    for rec in recommendations:
        asset_count = 0
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

    return {
        "prompt_id": prompt_item["id"],
        "prompt": prompt_item["prompt"],
        "category": prompt_item["category"],
        "model": provider_id,
        "model_label": PROVIDERS[provider_id]["label"],
        "provider_mode": provider_mode,
        "run_mode": run_mode,
        "corpus_mode": corpus_mode,
        "answer": answer,
        "citations": [source["id"] for source in sources],
        "nn_mentions": count_nn_mentions(answer),
        "competitor_mentions": count_competitor_mentions(answer),
        "link_recommendations": extract_link_recommendations(answer, sources),
        "retrieved_sources": [compact_source(source) for source in sources],
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
        "source_ids",
        "source_domains",
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
                "source_ids": ";".join(source.get("id", "") for source in sources),
                "source_domains": ";".join(domain_from_url(source.get("source_url")) for source in sources),
                "answer": result.get("answer"),
            }
        )
    return output.getvalue()


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "NNGEODemo/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            json_response(
                self,
                {
                    "prompts": load_prompts(),
                    "recommendations": recommendation_coverage(),
                    "baseline_visibility": load_baseline_visibility(),
                    "providers": provider_status(),
                    "corpus_modes": corpus_modes(),
                },
            )
            return

        if parsed.path == "/api/sources":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["improved"])[0]
            try:
                json_response(self, {"mode": mode, "sources": load_corpus(mode)})
            except ValueError as exc:
                json_response(self, {"error": str(exc)}, status=400)
            return

        if parsed.path == "/api/cached":
            latest = load_latest_results()
            if latest:
                json_response(
                    self,
                    {
                        "results": latest["results"],
                        "summary": latest["summary"],
                        "cached": True,
                        "generated_at": latest.get("generated_at"),
                        "source": "results/latest_results.json",
                    },
                )
                return
            results = run_benchmark(use_live=False, corpus_mode="improved")
            json_response(
                self,
                {
                    "results": results,
                    "summary": summarize_results(results),
                    "cached": True,
                    "source": "local-mock-generated",
                },
            )
            return

        if parsed.path == "/api/export.csv":
            latest = load_latest_results()
            results = latest["results"] if latest else run_benchmark(use_live=False, corpus_mode="improved")
            text_response(self, results_to_csv(results), content_type="text/csv; charset=utf-8")
            return

        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            json_response(self, {"error": "Not found"}, status=404)
            return

        try:
            payload = read_request_json(self)
            prompt_ids = payload.get("prompt_ids")
            if payload.get("prompt_id"):
                prompt_ids = [payload["prompt_id"]]
            corpus_mode = payload.get("corpus_mode", "improved")
            models = payload.get("models") or list(PROVIDERS)
            use_live = bool(payload.get("use_live", False))
            results = run_benchmark(prompt_ids=prompt_ids, corpus_mode=corpus_mode, models=models, use_live=use_live)
            json_response(
                self,
                {
                    "results": results,
                    "summary": summarize_results(results),
                    "cached": not use_live,
                    "provider_status": provider_status(),
                },
            )
        except ProviderError as exc:
            json_response(self, {"error": str(exc), "type": "provider_error"}, status=502)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            json_response(self, {"error": str(exc)}, status=400)

    def serve_static(self, request_path):
        if request_path in {"", "/"}:
            path = STATIC_DIR / "index.html"
        else:
            relative = request_path.lstrip("/")
            path = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in path.parents and path != STATIC_DIR.resolve():
                json_response(self, {"error": "Invalid path"}, status=400)
                return

        if not path.exists() or not path.is_file():
            json_response(self, {"error": "Not found"}, status=404)
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    parser = argparse.ArgumentParser(description="Run the NN GEO recommendation impact simulator dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()

    load_dotenv()

    if not Path(STATIC_DIR / "index.html").exists():
        raise SystemExit("static/index.html not found")

    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"NN GEO recommendation impact simulator running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()
