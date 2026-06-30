from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qa_builder import answer_question, load_latest_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="围绕最新早报追问松果")
    parser.add_argument("question", nargs="*", help="要问松果的问题")
    parser.add_argument("--mock", action="store_true", help="读取今天的 mock 输出包")
    parser.add_argument("--bundle", help="指定 output_bundle.json 路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON，方便前端或测试读取")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = input("你想问松果什么？").strip()

    project_root = Path(__file__).resolve().parents[2]
    if args.bundle:
        bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8-sig"))
    elif args.mock:
        bundle = load_latest_bundle(project_root / "demos" / "mock")
    else:
        bundle = load_latest_bundle(project_root / "demos")

    result = answer_question(bundle, question)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"松果：{result['answer']}")
    for item in result.get("details", []):
        print(f"- {item}")
    if result.get("suggested_questions"):
        print("你还可以追问：")
        for item in result["suggested_questions"][:4]:
            print(f"- {item}")
    print(f"来源：{result.get('source', 'unknown')}")


if __name__ == "__main__":
    main()
