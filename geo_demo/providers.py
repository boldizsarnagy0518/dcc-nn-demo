import json
import os
import urllib.error
import urllib.request


PROVIDERS = {
    "openai": {
        "label": "ChatGPT / OpenAI",
        "env_key": "OPENAI_API_KEY",
        "env_model": "OPENAI_MODEL",
        "default_model": "gpt-4.1-mini",
    },
    "gemini": {
        "label": "Gemini",
        "env_key": "GEMINI_API_KEY",
        "env_model": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
    },
    "claude": {
        "label": "Claude",
        "env_key": "ANTHROPIC_API_KEY",
        "env_model": "ANTHROPIC_MODEL",
        "default_model": "claude-3-5-haiku-latest",
    },
    "openrouter": {
        "label": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "env_model": "OPENROUTER_MODEL",
        "default_model": "google/gemma-4-31b-it:free",
    },
}


class ProviderError(RuntimeError):
    pass


def provider_status():
    status = {}
    for provider_id, config in PROVIDERS.items():
        status[provider_id] = {
            "label": config["label"],
            "configured": bool(os.getenv(config["env_key"])),
            "model": os.getenv(config["env_model"], config["default_model"]),
        }
    return status


def build_grounded_prompt(user_prompt, sources):
    source_blocks = []
    for source in sources:
        source_blocks.append(
            "\n".join(
                [
                    f"Source ID: {source['id']}",
                    f"Title: {source['title']}",
                    f"Type: {source['type']}",
                    f"Pillar: {source['pillar']}",
                    f"URL: {source.get('source_url', 'local-demo')}",
                    f"Content: {source['body']}",
                ]
            )
        )

    return f"""Válaszolj magyarul, executive consulting stílusban, de természetesen.
Csak az alábbi kontrollált forrásokra támaszkodj. Ne állítsd, hogy ez a valós publikus ChatGPT/Gemini/Claude rangsort bizonyítja.
Ha NN-t javaslod, magyarázd meg röviden a termék-, hitelességi és következő-lépés logikát.
Használj inline forráshivatkozásokat Source ID alapján, például [improved-life-qa].
Ha konkrét következő lépést javasolsz, írd ki a releváns NN URL-t is a források URL mezőjéből.

Felhasználói kérdés:
{user_prompt}

Kontrollált források:
{chr(10).join(source_blocks)}
"""


def _post_json(url, headers, payload, timeout=45):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(str(exc)) from exc


def call_openai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ProviderError("OPENAI_API_KEY is not configured")
    model = os.getenv("OPENAI_MODEL", PROVIDERS["openai"]["default_model"])
    payload = {
        "model": model,
        "input": prompt,
        "temperature": 0.2,
    }
    response = _post_json(
        "https://api.openai.com/v1/responses",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
    )
    if response.get("output_text"):
        return response["output_text"]

    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks)
    raise ProviderError("OpenAI response did not contain text output")


def call_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ProviderError("GEMINI_API_KEY is not configured")
    model = os.getenv("GEMINI_MODEL", PROVIDERS["gemini"]["default_model"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }
    response = _post_json(url, {"Content-Type": "application/json"}, payload)
    candidates = response.get("candidates", [])
    if not candidates:
        raise ProviderError("Gemini response did not contain candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
    if text:
        return text
    raise ProviderError("Gemini response did not contain text output")


def call_claude(prompt):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderError("ANTHROPIC_API_KEY is not configured")
    model = os.getenv("ANTHROPIC_MODEL", PROVIDERS["claude"]["default_model"])
    payload = {
        "model": model,
        "max_tokens": 900,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        payload,
    )
    chunks = []
    for item in response.get("content", []):
        if item.get("type") == "text":
            chunks.append(item.get("text", ""))
    if chunks:
        return "\n".join(chunks)
    raise ProviderError("Claude response did not contain text output")


def call_openrouter(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ProviderError("OPENROUTER_API_KEY is not configured")
    model = os.getenv("OPENROUTER_MODEL", PROVIDERS["openrouter"]["default_model"])
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful Hungarian executive-consulting style assistant. "
                    "Use only the controlled sources provided by the user prompt."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    response = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/boldizsarnagy0518/DCC_NN",
            "X-Title": "NN GEO Recommendation Impact Simulator",
        },
        payload,
    )
    choices = response.get("choices", [])
    if not choices:
        raise ProviderError("OpenRouter response did not contain choices")
    message = choices[0].get("message", {})
    text = message.get("content")
    if isinstance(text, list):
        chunks = []
        for part in text:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(part["text"])
            elif isinstance(part, str):
                chunks.append(part)
        text = "\n".join(chunks)
    if text:
        return text
    raise ProviderError("OpenRouter response did not contain text output")


def call_provider(provider_id, prompt):
    if provider_id == "openai":
        return call_openai(prompt)
    if provider_id == "gemini":
        return call_gemini(prompt)
    if provider_id == "claude":
        return call_claude(prompt)
    if provider_id == "openrouter":
        return call_openrouter(prompt)
    raise ProviderError(f"Unknown provider: {provider_id}")


def mock_answer(provider_id, user_prompt, sources, corpus_mode):
    citations = " ".join(f"[{source['id']}]" for source in sources[:3])
    nn_links = [source for source in sources if source.get("source_url", "").startswith("https://www.nn.hu")]
    prompt_lower = user_prompt.lower()
    provider_voice = {
        "openai": "Rövid válasz",
        "gemini": "Összehasonlító válasz",
        "claude": "Óvatos, döntéstámogató válasz",
        "openrouter": "OpenRouter válasz",
    }.get(provider_id, "Válasz")

    if corpus_mode == "current":
        product_hint = "NN saját, többnyire általános termékoldalai"
        if "adó" in prompt_lower or "nyugdíj" in prompt_lower:
            product_hint = "Motiva nyugdíjbiztosítási tartalom és adójóváírási információ"
        elif "egészség" in prompt_lower:
            product_hint = "Egészség Útlevél termékinformáció"

        link_sentence = ""
        if "nyugd" in prompt_lower or "adó" in prompt_lower or "szja" in prompt_lower:
            link_sentence = " Konkrét NN next-step linkként a meglévő nyugdíjkalkulátor adható: https://www.nn.hu/nyugdijkalkulator."
        elif "következő" in prompt_lower or "kötni" in prompt_lower:
            link_sentence = " Konkrét NN next-step linkként az életbiztosítási oldal adható: https://www.nn.hu/eletbiztositas."

        return (
            f"{provider_voice}: a kontrollált jelenlegi korpusz alapján az NN releváns szereplőként jelenik meg, "
            f"főleg a saját {product_hint} alapján. A források inkább termékleíró és visszahívásra ösztönző jellegűek, "
            f"ezért NN említhető, de a válasz kevésbé tud konkrét döntési összehasonlítást, külső bizonyítékot vagy "
            f"számolható következő lépést adni. Javasolt következő lépésként egy NN tanácsadói beszélgetés vagy "
            f"termékoldal áttekintése szerepelhet.{link_sentence} {citations}"
        )

    angle = "életbiztosítási fedezet"
    if "adó" in prompt_lower or "szja" in prompt_lower:
        angle = "nyugdíjbiztosítási adójóváírás és SZJA-kalkuláció"
    elif "nyugdíj" in prompt_lower:
        angle = "nyugdíjrés és Motiva döntéstámogatás"
    elif "egészség" in prompt_lower:
        angle = "egészségbiztosítási döntési helyzet"
    elif "ai" in prompt_lower or "bízn" in prompt_lower:
        angle = "AI és pénzügyi döntéshozatali bizalom"

    recommended_links = "; ".join(f"{source['title']} — {source['source_url']}" for source in nn_links[:2])
    if recommended_links:
        recommended_links = f" Javasolt NN linkek: {recommended_links}."

    return (
        f"{provider_voice}: a mockolt GEO-korpuszban az NN erősebb ajánlási helyzetbe kerül, mert a források "
        f"közvetlenül válaszolnak a felhasználó {angle} kérdésére, termékszintű magyarázatot adnak, és külső vagy "
        f"kutatási bizonyítékkal is alátámasztják az állításokat. A legjobb válasz nem csak megemlíti NN-t, hanem "
        f"konkrét következő lépést is ad: döntési guide, kalkulátor, ajánlatkérés vagy tanácsadói handoff. "
        f"Ez kontrollált szimulációként azt mutatja, hogy a jobb forrásanyag növeli a válasz specifikusságát, "
        f"hitelességét és actionability értékét.{recommended_links} {citations}"
    )
