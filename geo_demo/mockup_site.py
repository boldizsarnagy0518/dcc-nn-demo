import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class MockupHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.description = ""
        self.visible_parts = []
        self.ld_json_blocks = []
        self._in_title = False
        self._skip_depth = 0
        self._in_ld_json = False
        self._current_ld_json = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
            return
        if tag == "meta" and attrs_dict.get("name", "").lower() == "description":
            self.description = attrs_dict.get("content", "")
            return
        if tag == "script" and attrs_dict.get("type", "").lower() == "application/ld+json":
            self._in_ld_json = True
            self._current_ld_json = []
            return
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
            return
        if tag == "script" and self._in_ld_json:
            raw = "".join(self._current_ld_json).strip()
            if raw:
                self.ld_json_blocks.append(raw)
            self._in_ld_json = False
            self._current_ld_json = []
            return
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_ld_json:
            self._current_ld_json.append(data)
            return
        if self._in_title:
            self.title_parts.append(text)
            return
        if not self._skip_depth:
            self.visible_parts.append(text)


def _collapse_text(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def _strip_tags(fragment):
    without_scripts = re.sub(r"<(script|style|noscript|svg)[\s\S]*?</\1>", " ", fragment, flags=re.IGNORECASE)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return _collapse_text(without_tags)


def _extract_page_section(raw_html, page_id):
    pattern = re.compile(
        rf'<section\s+[^>]*(?:id="{re.escape(page_id)}"|data-page="{re.escape(page_id)}")[^>]*>([\s\S]*?)(?=\n\s*</section>\s*\n\s*<section\s+id=|\n\s*</main>|$)',
        flags=re.IGNORECASE,
    )
    match = pattern.search(raw_html)
    return _strip_tags(match.group(1)) if match else ""


def _parse_ld_json_summary(blocks):
    summaries = []
    for block in blocks:
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            kind = item.get("@type", "JSON-LD")
            if kind == "Organization":
                same_as = ", ".join(item.get("sameAs", [])[:5])
                summaries.append(
                    {
                        "id": "mockup-site-organization-jsonld",
                        "title": "NN Biztosító Organization JSON-LD és metaazonosítók",
                        "type": "entity",
                        "pillar": "Credibility",
                        "status": "mockup_site_evidence",
                        "source_url": "https://www.nn.hu/mock/entity-schema",
                        "tags": ["Organization JSON-LD", "sameAs", "NN Biztosító Zrt.", "metaadat"],
                        "recommendation_ids": ["R2", "R3"],
                        "body": _collapse_text(
                            "A mockup Organization JSON-LD blokkot tartalmaz az NN Biztosító Zrt. névvel, "
                            f"parentOrganization mezővel és sameAs hivatkozásokkal. SameAs példák: {same_as}."
                        ),
                    }
                )
            elif kind == "FAQPage":
                questions = []
                for entry in item.get("mainEntity", []):
                    if isinstance(entry, dict) and entry.get("name"):
                        questions.append(entry["name"])
                summaries.append(
                    {
                        "id": "mockup-site-faq-jsonld",
                        "title": "FAQPage JSON-LD természetes nyelvű biztosítási kérdésekkel",
                        "type": "product_qa",
                        "pillar": "Clarity",
                        "status": "mockup_site_evidence",
                        "source_url": "https://www.nn.hu/mock/faq-jsonld",
                        "tags": ["FAQPage", "kérdés-válasz", "életbiztosítás", "nyugdíjbiztosítás"],
                        "recommendation_ids": ["R1", "R3", "R7"],
                        "body": _collapse_text(
                            "A mockup FAQPage JSON-LD blokkot használ, amely ügyfélkérdésként írja le a fontos "
                            f"biztosítási témákat. Példakérdések: {'; '.join(questions[:6])}."
                        ),
                    }
                )
    return summaries


def load_mockup_site_sources(root):
    path = Path(root) / "nn_actionable_site" / "index.html"
    if not path.exists():
        return []

    raw_html = path.read_text(encoding="utf-8")
    parser = MockupHTMLParser()
    parser.feed(raw_html)

    title = _collapse_text(" ".join(parser.title_parts))
    description = _collapse_text(parser.description)
    visible_text = _collapse_text(" ".join(parser.visible_parts))

    sources = [
        {
            "id": "mockup-site-meta",
            "title": "Mockup oldal meta title és meta description",
            "type": "technical_hygiene",
            "pillar": "Discoverability",
            "status": "mockup_site_evidence",
            "source_url": "https://www.nn.hu/mock/meta",
            "tags": ["meta title", "meta description", "strukturált oldal", "NN"],
            "recommendation_ids": ["R3"],
            "body": _collapse_text(f"Title: {title}. Meta description: {description}."),
        },
        {
            "id": "mockup-site-visible-content",
            "title": "NN actionable mockup látható ügyféloldali tartalom",
            "type": "decision_guide",
            "pillar": "Actionability",
            "status": "mockup_site_evidence",
            "source_url": "https://www.nn.hu/mock/actionable-site",
            "tags": ["mockup", "ügyféloldal", "következő lépés", "NN"],
            "recommendation_ids": ["R1", "R7", "R9", "R10"],
            "body": visible_text[:2400],
        },
        {
            "id": "mockup-site-ab-evidence-workflow",
            "title": "Controlled A/B evidence workflow és mérési logika",
            "type": "dashboard",
            "pillar": "Measurement",
            "status": "mockup_site_evidence",
            "source_url": "local-controlled-ab-workflow",
            "tags": ["controlled A/B", "48 prompt", "három modell", "Excel evidence"],
            "recommendation_ids": ["R4"],
            "body": (
                "A controlled A/B workflow ugyanazt a 48 promptot futtatja le current és improved forráskörnyezetben, "
                "három modellre bontva. A mérés prompt-, modell- és recommendation-szinten mutatja, hogyan változik "
                "az NN említés, az explicit NN link, a hitelesség és a következő lépés."
            ),
        },
    ]

    section_specs = [
        ("calculators", "mockup-site-calculators", "Mockup kalkulátorok és next-step utak", "calculator", "Actionability", ["R9", "R10"]),
        ("pages", "mockup-site-conversational-pages", "Átírt kérdésalapú termékoldalak", "product_qa", "Clarity", ["R1", "R7"]),
        ("trust", "mockup-site-trust-evidence", "Bizalmi háttér, külső bizonyíték és kutatási assetek", "third_party", "Credibility", ["R2", "R5", "R6", "R8"]),
    ]
    for page_id, source_id, source_title, source_type, pillar, recommendation_ids in section_specs:
        body = _extract_page_section(raw_html, page_id)
        if body:
            sources.append(
                {
                    "id": source_id,
                    "title": source_title,
                    "type": source_type,
                    "pillar": pillar,
                    "status": "mockup_site_evidence",
                    "source_url": f"https://www.nn.hu/mock/{page_id}",
                    "tags": [page_id, "mockup", "NN", pillar],
                    "recommendation_ids": recommendation_ids,
                    "body": body[:2400],
                }
            )

    sources.extend(_parse_ld_json_summary(parser.ld_json_blocks))
    return sources
