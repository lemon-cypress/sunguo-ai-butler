from __future__ import annotations

import sys

from config import get_settings
from ms_graph_auth import MicrosoftAuthError, poll_device_code, request_device_code, save_token


def looks_like_client_id(value: str) -> bool:
    if not value:
        return False
    if "@" in value:
        return False
    parts = value.split("-")
    return len(parts) == 5 and all(parts)


def configure_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    configure_output()
    settings = get_settings()

    if not looks_like_client_id(settings.microsoft_client_id):
        print("MICROSOFT_CLIENT_ID 看起来不对。")
        print("")
        print("这里不能填 Outlook 邮箱。")
        print("它必须是 Microsoft Entra / Azure App Registration 里的 Application (client) ID。")
        print("格式通常像这样：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        print("")
        print("请先在 Azure / Microsoft Entra 创建应用注册，然后把 Application (client) ID 填进 .env。")
        return

    try:
        print(f"Microsoft tenant: {settings.microsoft_tenant}")
        print(f"Microsoft scopes: {settings.microsoft_scopes}")
        print("")
        device = request_device_code(
            settings.microsoft_client_id,
            settings.microsoft_tenant,
            settings.microsoft_scopes,
        )
    except MicrosoftAuthError as error:
        print(f"获取 Microsoft 设备码失败：{error}")
        return

    print("请用浏览器打开下面的网址并输入验证码：")
    print(device.get("verification_uri") or device.get("verification_url"))
    print("")
    print(f"验证码：{device.get('user_code')}")
    print("")
    if device.get("message"):
        print(device["message"])
        print("")
    print("等待你完成 Microsoft 登录授权...")

    try:
        token = poll_device_code(
            settings.microsoft_client_id,
            settings.microsoft_tenant,
            str(device["device_code"]),
            int(device.get("interval", 5)),
            int(device.get("expires_in", 900)),
        )
    except MicrosoftAuthError as error:
        print(f"Microsoft 授权失败：{error}")
        return

    save_token(settings.microsoft_token_path, token)
    print("Microsoft 授权成功，token 已保存到本地：")
    print(settings.microsoft_token_path)
    print("这个文件不要上传 GitHub。")


if __name__ == "__main__":
    main()
