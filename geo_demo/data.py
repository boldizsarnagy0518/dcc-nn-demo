import json
from pathlib import Path

from .mockup_site import load_mockup_site_sources


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATIC_DIR = ROOT / "static"
RESULTS_DIR = ROOT / "results"


def load_json(name):
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dedupe_sources(sources):
    deduped = []
    seen = set()
    for source in sources:
        source_id = source.get("id")
        if not source_id or source_id in seen:
            continue
        deduped.append(source)
        seen.add(source_id)
    return deduped


def load_prompts():
    return load_json("prompts.json")


def load_recommendations():
    return load_json("recommendations.json")


def load_baseline_visibility():
    return load_json("baseline_visibility.json")


def load_original_analysis_summary():
    return load_json("original_analysis_summary.json")


def load_corpus_file(mode):
    if mode not in {"current", "improved"}:
        raise ValueError(f"Unknown corpus mode: {mode}")
    return load_json(f"corpus_{mode}.json")


def load_corpus(mode):
    if mode == "current":
        return load_corpus_file("current")
    if mode == "improved":
        return _dedupe_sources(
            [
                *load_corpus_file("current"),
                *load_corpus_file("improved"),
                *load_mockup_site_sources(ROOT),
            ]
        )
    raise ValueError(f"Unknown corpus mode: {mode}")


def corpus_modes():
    return {
        "current": {
            "label": "Current corpus",
            "description": "Today-like NN/public content with generic product pages and weaker external proof.",
        },
        "improved": {
            "label": "Improved A/B corpus",
            "description": "Current NN/current-like content plus mocked GEO assets based on the actionable recommendations.",
        },
    }
