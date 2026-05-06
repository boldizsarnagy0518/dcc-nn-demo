import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from geo_demo.benchmark import recommendation_coverage, run_benchmark, run_single, summarize_results
from geo_demo.data import load_corpus, load_prompts
from geo_demo.evidence_export import export_controlled_ab_workbooks
from geo_demo.excel_export import write_workbook
from geo_demo.linking import extract_link_recommendations
from geo_demo.retrieval import retrieve_sources
from geo_demo.scoring import score_answer
from import_prompts_from_excel import read_prompt_rows
from run_controlled_ab import iter_run_plan


TMP_ROOT = Path(__file__).resolve().parents[1] / ".test_tmp"


def fake_provider_answer(provider_id, prompt):
    return (
        "Az NN Biztosító Zrt. releváns opció, mert a kontrollált források termékszintű választ, "
        "hitelességi jelet és konkrét következő lépést adnak. Javasolt NN link: "
        "https://www.nn.hu/mock/eletbiztositas-kalkulator. [improved-life-calculator]"
    )


def make_tmp_dir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TMP_ROOT / f"case_{uuid.uuid4().hex}"
    path.mkdir()
    return path


class DemoContractTests(unittest.TestCase):
    def test_data_contract(self):
        prompts = load_prompts()
        self.assertEqual(len(prompts), 48)
        for mode in ("current", "improved"):
            corpus = load_corpus(mode)
            self.assertGreaterEqual(len(corpus), 8)
            for source in corpus:
                for key in ("id", "title", "type", "pillar", "source_url", "body"):
                    self.assertIn(key, source)

    def test_improved_corpus_covers_all_recommendations(self):
        corpus = load_corpus("improved")
        covered = set()
        for source in corpus:
            covered.update(source.get("recommendation_ids") or [])
        self.assertEqual({f"R{index}" for index in range(1, 11)}, covered)
        coverage = recommendation_coverage()
        self.assertEqual(len(coverage), 10)
        self.assertTrue(all(item["demo_asset_count"] > 0 for item in coverage))

    def test_excel_prompt_import_from_prompts_sheet(self):
        tmp = make_tmp_dir()
        try:
            path = tmp / "prompts.xlsx"
            write_workbook(
                path,
                {
                    "PROMPTS": [
                        ["Prompt", "Category"],
                        ["Keress Magyarországon életbiztosítást.", "18-24"],
                    ]
                },
            )
            prompts = read_prompt_rows(path)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]["id"], "p01")
        self.assertEqual(prompts[0]["category"], "18-24")

    def test_run_plan_runs_all_a_before_b(self):
        prompts = [{"id": "p01"}, {"id": "p02"}]
        models = ["openrouter_openai", "openrouter_gemini"]
        modes = [mode for _, mode, _ in iter_run_plan(prompts, models)]
        self.assertEqual(modes, ["current", "current", "current", "current", "improved", "improved", "improved", "improved"])

    def test_retrieval_returns_ranked_sources(self):
        corpus = load_corpus("improved")
        sources = retrieve_sources("Mekkora életbiztosítási fedezet kell egy családnak?", corpus, limit=3)
        self.assertEqual(len(sources), 3)
        self.assertIn("fedezet", " ".join(source["title"].lower() for source in sources))

    def test_controlled_ab_benchmark_uses_api_mode_when_live(self):
        with patch("geo_demo.benchmark.call_provider", side_effect=fake_provider_answer):
            results = run_benchmark(prompt_ids=["p01"], models=["openrouter_openai"], corpus_mode="both", use_live=True)
        summary = summarize_results(results)
        self.assertEqual(len(results), 2)
        self.assertEqual([result["corpus_mode"] for result in results], ["current", "improved"])
        self.assertTrue(all(result["provider_mode"] == "api" for result in results))
        self.assertEqual(summary["validation_mode"], "controlled_ab")
        self.assertIn("score_breakdown", summary)
        self.assertIn("prompt_summary", summary)

    def test_scoring_has_expected_breakdown(self):
        sources = load_corpus("improved")[:3]
        answer = (
            "Az NN Biztosító Zrt. konkrét következő lépést ad: kalkulátor és tanácsadó. "
            "Javasolt link: https://www.nn.hu/mock/eletbiztositas-kalkulator. [improved-life-calculator]"
        )
        scores = score_answer(answer, sources)
        self.assertIn("total", scores)
        self.assertGreaterEqual(scores["actionability"], 6)
        self.assertGreaterEqual(scores["nn_link_recommendations"], 1)

    def test_link_recommendation_extraction(self):
        sources = load_corpus("improved")[:5]
        answer = "Menj ide: https://www.nn.hu/mock/eletbiztositas-kalkulator"
        links = extract_link_recommendations(answer, sources)
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0]["url"].startswith("https://www.nn.hu"))

    def test_excel_evidence_export_creates_required_workbooks(self):
        prompt = load_prompts()[0]
        with patch("geo_demo.benchmark.call_provider", side_effect=fake_provider_answer):
            results = [
                run_single(prompt, "current", "openrouter_openai", use_live=True),
                run_single(prompt, "improved", "openrouter_openai", use_live=True),
            ]
        tmp = make_tmp_dir()
        try:
            outputs = export_controlled_ab_workbooks(
                results,
                tmp,
                {
                    "generated_at_utc": "2026-05-05T00:00:00+00:00",
                    "methodology": "controlled A/B validation of recommendation impact",
                },
            )
            for key in ("A_current_outputs", "B_improved_outputs", "AB_summary"):
                self.assertTrue(outputs[key].exists(), key)
                self.assertGreater(outputs[key].stat().st_size, 1000)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
