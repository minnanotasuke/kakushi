"""End-to-end demo: mask → OpenAI → unmask.

If OPENAI_API_KEY is set in the environment, this script makes a real call to
gpt-4o-mini and shows you exactly what bytes go out, what comes back, and how
it gets restored. If the key is missing, it dry-runs (prints the request that
would be sent and a fake reply).

Usage:
    .venv/bin/python examples/openai_demo.py
"""

import argparse
import os
import sys
from pathlib import Path

# Run from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kakushi import mask, unmask  # noqa: E402


SAMPLE = """田中太郎様

いつもお世話になっております。
株式会社山田商事の件で、¥1,500,000の見積書を tanaka@example.co.jp にお送りいたしました。
ご確認のほど、よろしくお願いいたします。

電話: 090-1234-5678
担当: 佐藤花子
"""

SYSTEM = "あなたは丁寧な日本語ビジネス文を整えるアシスタントです。"
USER_INSTRUCTION = "以下のメールをより丁寧に整え、件名も提案してください:\n\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't call OpenAI; print a fake reply (default if no API key).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ORIGINAL (never leaves your server)")
    print("=" * 60)
    print(SAMPLE)

    masked, mapping = mask(SAMPLE, dictionary={"株式会社山田商事": "取引先A"})

    print("=" * 60)
    print(f"MASKED (sent to LLM)  —  mapping size: {len(mapping)}")
    print("=" * 60)
    print(masked)

    api_key = None if args.dry_run else os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("=" * 60)
        print("DRY RUN  —  OPENAI_API_KEY not set")
        print("=" * 60)
        fake_reply = (
            "件名: 見積書送付のご確認\n\n"
            + masked.replace("お送りいたしました", "ご確認いただけますと幸いです")
        )
        print(fake_reply)
        print()
        print("=" * 60)
        print("RESTORED (returned to user)")
        print("=" * 60)
        print(unmask(fake_reply, mapping))
        return

    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("openai package not installed. pip install openai")
        return

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_INSTRUCTION + masked},
        ],
    )
    reply_masked = response.choices[0].message.content or ""

    print("=" * 60)
    print("LLM REPLY (still masked)")
    print("=" * 60)
    print(reply_masked)

    print("=" * 60)
    print("RESTORED (returned to user)")
    print("=" * 60)
    print(unmask(reply_masked, mapping))


if __name__ == "__main__":
    main()
