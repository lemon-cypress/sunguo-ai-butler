from __future__ import annotations

import json
import urllib.error
import urllib.request


DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


class DeepSeekClientError(RuntimeError):
    pass


class DeepSeekQuotaError(DeepSeekClientError):
    pass


def create_chat_completion(api_key: str, model: str, prompt: str, json_mode: bool = False) -> str:
    """Call DeepSeek Chat Completions API with only the Python standard library."""
    if not api_key:
        raise DeepSeekClientError("DEEPSEEK_API_KEY is empty.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是松果，一个温柔、阳光、聪明、可靠的 AI 私人管家。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2500,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
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
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if error.code in {402, 429}:
            raise DeepSeekQuotaError(f"DeepSeek quota, balance, or rate limit unavailable. HTTP {error.code}: {detail}") from error
        raise DeepSeekClientError(f"DeepSeek API HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise DeepSeekClientError(f"DeepSeek API network error: {error}") from error
    except TimeoutError as error:
        raise DeepSeekClientError("DeepSeek API timed out while reading the response.") from error

    try:
        content = data["choices"][0]["message"]["content"].strip()
        if not content:
            raise DeepSeekClientError(f"DeepSeek API returned empty content: {data}")
        return content
    except (KeyError, IndexError, TypeError) as error:
        raise DeepSeekClientError(f"DeepSeek API returned unexpected response: {data}") from error
