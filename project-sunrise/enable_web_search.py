#!/usr/bin/env python3
"""
Enable Web Search for an existing OpenAI Assistant and verify.

Usage:
  OPENAI_API_KEY=sk-... python3 enable_web_search.py --assistant-id asst_XXX --model gpt-4.1
"""

import os
import sys
import argparse
from openai import OpenAI


def main() -> None:
    parser = argparse.ArgumentParser(description="Enable Web Search on an Assistant")
    parser.add_argument("--assistant-id", required=True, help="Assistant ID (e.g., asst_XXXXX)")
    parser.add_argument("--model", default="gpt-4.1", help="Model to set (default: gpt-4.1)")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Retrieve current assistant
    try:
        assistant = client.beta.assistants.retrieve(args.assistant_id)
    except Exception as e:
        print(f"Error retrieving assistant: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Current model: {assistant.model}")
    current_tools = list(assistant.tools or [])
    has_web = any((t or {}).get("type") == "web_search" for t in current_tools)
    print(f"Web Search present before update: {has_web}")

    if not has_web:
        current_tools.append({"type": "web_search"})

    # Update assistant (model + tools)
    try:
        client.beta.assistants.update(
            args.assistant_id,
            model=args.model,
            tools=current_tools,
        )
    except Exception as e:
        print(f"Error updating assistant: {e}", file=sys.stderr)
        sys.exit(1)

    # Verify
    after = client.beta.assistants.retrieve(args.assistant_id)
    tools_after = after.tools or []
    has_web_after = any((t or {}).get("type") == "web_search" for t in tools_after)

    print("\n=== Verification ===")
    print(f"Assistant ID: {after.id}")
    print(f"Model:        {after.model}")
    print("Tools:")
    for t in tools_after:
        print(f"  - {t.get('type')}")
    print(f"\nWeb Search enabled: {has_web_after}")

    if not has_web_after:
        print("Warning: Web Search still not enabled. Your account/org may not have access.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()


