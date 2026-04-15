from __future__ import annotations

import argparse

from openai import OpenAI


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a local OpenAI-compatible vLLM endpoint")
    parser.add_argument("--base-url", default="http://localhost:8002/v1", help="OpenAI-compatible base URL")
    parser.add_argument("--model", default="qwen35b", help="Served model name")
    parser.add_argument("--prompt", default="Say ping only.", help="User prompt to send")
    parser.add_argument("--max-tokens", type=int, default=64, help="Max completion tokens")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key="EMPTY")

    print(f"base_url={args.base_url}")
    print(f"model={args.model}")

    models = client.models.list()
    print("available_models=", [m.id for m in models.data])

    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        temperature=0,
        max_tokens=args.max_tokens,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            }
        },
    )

    print(response.choices[0].message.content.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
