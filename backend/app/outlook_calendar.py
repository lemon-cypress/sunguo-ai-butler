from __future__ import annotations

import json
import sys

from config import get_settings
from outlook_graph import get_today_outlook_or_error


def configure_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    configure_output()
    settings = get_settings()
    outlook, error = get_today_outlook_or_error(settings)
    if error:
        print("读取 Outlook 日历失败：")
        print(error)
        print("")
        print("如果还没有授权，请先运行：")
        print("python .\\backend\\app\\outlook_auth.py")
        return

    print(json.dumps(outlook, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

