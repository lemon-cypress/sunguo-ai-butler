from __future__ import annotations

import json
import urllib.error
import urllib.request


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class OpenAIClientError(RuntimeError):
    pass


class OpenAIQuotaError(OpenAIClientError):
    pass


def create_response(api_key: str, model: str, prompt: str) -> str:
    """Call OpenAI Responses API with only the Python standard library."""
    if not api_key:
        raise OpenAIClientError("OPENAI_API_KEY is empty.")

    payload = {
        "model": model,
        "input": prompt,
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "medium"},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if error.code == 429 and "insufficient_quota" in detail:
            raise OpenAIQuotaError(
                "OpenAI API 额度不足或账单未开通。请检查 Billing、Usage 和 Limits 后再试。"
            ) from error
        raise OpenAIClientError(f"OpenAI API HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise OpenAIClientError(f"OpenAI API network error: {error}") from error

    text = extract_output_text(data)
    if not text:
        raise OpenAIClientError("OpenAI API returned no output text.")
    return text


def extract_output_text(response_data: dict) -> str:
    """Extract text from a Responses API response."""
    direct = response_data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    chunks: list[str] = []
    for item in response_data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()
