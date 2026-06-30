from __future__ import annotations

import json
import urllib.error
import urllib.request


DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


class DeepSeekClientError(RuntimeError):
    pass


class DeepSeekQuotaError(DeepSeekClientError):
    pass


def create_chat_completion(api_key: str, model: str, prompt: str) -> str:
    """Call DeepSeek Chat Completions API with only the Python standard library."""
    if not api_key:
        raise DeepSeekClientError("DEEPSEEK_API_KEY is empty.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是松果，一个温柔、阳光、聪明的 AI 私人管家。"},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        DEEPSEEK_CHAT_COMPLETIONS_URL,
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
        if error.code in {402, 429}:
            raise DeepSeekQuotaError(
                f"DeepSeek API 额度、余额或限流不可用。HTTP {error.code}: {detail}"
            ) from error
        raise DeepSeekClientError(f"DeepSeek API HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise DeepSeekClientError(f"DeepSeek API network error: {error}") from error

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise DeepSeekClientError(f"DeepSeek API returned unexpected response: {data}") from error

