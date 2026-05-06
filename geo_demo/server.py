import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .benchmark import recommendation_coverage, results_to_csv, run_benchmark, summarize_results
from .data import (
    STATIC_DIR,
    corpus_modes,
    load_baseline_visibility,
    load_corpus,
    load_original_analysis_summary,
    load_prompts,
)
from .env import load_dotenv
from .providers import (
    PROVIDERS,
    ProviderError,
    provider_status,
)
from .results import load_latest_results


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
                    "original_analysis": load_original_analysis_summary(),
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
