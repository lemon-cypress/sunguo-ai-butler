from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class MicrosoftAuthError(RuntimeError):
    pass


def device_code_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode"


def token_url(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def post_form(url: str, form: dict, timeout_seconds: int = 30) -> dict:
    body = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise MicrosoftAuthError(f"Microsoft auth HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise MicrosoftAuthError(f"Microsoft auth network error: {error}") from error


def request_device_code(client_id: str, tenant: str, scopes: str) -> dict:
    if not client_id:
        raise MicrosoftAuthError("MICROSOFT_CLIENT_ID is empty.")
    return post_form(
        device_code_url(tenant),
        {
            "client_id": client_id,
            "scope": scopes,
        },
    )


def poll_device_code(client_id: str, tenant: str, device_code: str, interval: int, expires_in: int) -> dict:
    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        try:
            token = post_form(
                token_url(tenant),
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": client_id,
                    "device_code": device_code,
                },
            )
            token["expires_at"] = int(time.time() + int(token.get("expires_in", 3600)) - 60)
            return token
        except MicrosoftAuthError as error:
            message = str(error)
            if "authorization_pending" in message:
                continue
            if "slow_down" in message:
                interval += 5
                continue
            raise
    raise MicrosoftAuthError("Device code expired before authorization completed.")


def save_token(path: Path, token: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def load_token(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def refresh_token(client_id: str, tenant: str, scopes: str, refresh_token_value: str) -> dict:
    token = post_form(
        token_url(tenant),
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "scope": scopes,
            "refresh_token": refresh_token_value,
        },
    )
    token["expires_at"] = int(time.time() + int(token.get("expires_in", 3600)) - 60)
    return token


def get_access_token(client_id: str, tenant: str, scopes: str, token_path: Path) -> str:
    token = load_token(token_path)
    if not token:
        raise MicrosoftAuthError("No Microsoft token found. Run outlook_auth.py first.")

    expires_at = int(token.get("expires_at", 0))
    if expires_at > time.time() and token.get("access_token"):
        return str(token["access_token"])

    refresh_token_value = token.get("refresh_token")
    if not refresh_token_value:
        raise MicrosoftAuthError("Microsoft token expired and has no refresh_token. Run outlook_auth.py again.")

    refreshed = refresh_token(client_id, tenant, scopes, str(refresh_token_value))
    save_token(token_path, refreshed)
    return str(refreshed["access_token"])

