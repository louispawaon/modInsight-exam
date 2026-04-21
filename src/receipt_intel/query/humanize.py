from __future__ import annotations

import json

import httpx

HUMANIZE_PROMPT = """You rewrite receipt analytics answers for UI readability.
Rules:
- Keep every numeric value exactly the same.
- Do not invent facts not present in the provided JSON.
- Keep response under 90 words.
- Use plain text only (no markdown).
"""


def humanize_answer_with_ollama(
    *,
    deterministic_answer: str,
    facts: dict,
    base_url: str,
    model: str,
    timeout_s: int,
) -> str | None:
    try:
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": HUMANIZE_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Deterministic answer:\n"
                        f"{deterministic_answer}\n\n"
                        "Grounding facts JSON:\n"
                        f"{json.dumps(facts, ensure_ascii=True)}"
                    ),
                },
            ],
        }
        response = httpx.post(
            f"{base_url.rstrip('/')}/api/chat",
            json=payload,
            timeout=timeout_s,
        )
        response.raise_for_status()
        data = response.json()
        message = data.get("message", {})
        content = message.get("content")
        rewritten = content.strip() if isinstance(content, str) else ""
        return rewritten or None
    except Exception:
        return None
