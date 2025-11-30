#!/usr/bin/env python3
"""
Minimal OpenAI Assistant connectivity test.

Uses:
  - OPENAI_API_KEY
  - OPENAI_ASSISTANT_ID

Checks:
  1) Can we reach the OpenAI API and list models?
  2) Can we retrieve the configured assistant?
  3) Can we create a thread and get a short response?
"""

import os
import sys
import time

from openai import OpenAI


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set in the environment.", file=sys.stderr)
        return 1
    if not assistant_id:
        print("ERROR: OPENAI_ASSISTANT_ID is not set in the environment.", file=sys.stderr)
        return 1

    print("✅ Environment variables found:")
    print(f"  OPENAI_API_KEY: ****{api_key[-4:]} (redacted)")
    print(f"  OPENAI_ASSISTANT_ID: {assistant_id}")
    print()

    client = OpenAI(api_key=api_key, timeout=15.0, max_retries=1)

    # 1) List a couple of models
    try:
        print("🔎 Checking model listing...")
        models = client.models.list()
        first_ids = [m.id for m in models.data[:5]]
        print("  ✅ Models reachable. Sample IDs:", ", ".join(first_ids))
    except Exception as e:
        print("  ❌ Failed to list models:", e, file=sys.stderr)
        return 1

    # 2) Retrieve the assistant
    try:
        print("\n🔎 Retrieving assistant...")
        assistant = client.beta.assistants.retrieve(assistant_id)
        print("  ✅ Assistant retrieved.")
        print(f"     ID:    {assistant.id}")
        print(f"     Model: {assistant.model}")
        print(f"     Tools: {[t.get('type') for t in (assistant.tools or [])]}")
    except Exception as e:
        print("  ❌ Failed to retrieve assistant:", e, file=sys.stderr)
        return 1

    # 3) Create a thread and run a very small question
    try:
        print("\n🧵 Creating thread...")
        thread = client.beta.threads.create()
        print(f"  ✅ Thread created: {thread.id}")

        message = "Quick connectivity test. Please reply with a very short confirmation (one sentence)."
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message,
        )

        print("🚀 Starting run...")
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )

        start = time.time()
        max_wait = 60  # seconds

        while True:
            status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            ).status

            print(f"  ⏱️  Status: {status}")
            if status == "completed":
                break
            if status in {"failed", "cancelled", "expired"}:
                print(f"  ❌ Run ended with status: {status}", file=sys.stderr)
                return 1
            if time.time() - start > max_wait:
                print("  ❌ Timed out waiting for run to complete.", file=sys.stderr)
                return 1

            time.sleep(3)

        # Fetch the last message
        print("\n📥 Fetching latest assistant message...")
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            order="desc",
            limit=1,
        )

        if not messages.data:
            print("  ❌ No messages returned.", file=sys.stderr)
            return 1

        msg = messages.data[0]
        parts = []
        for content in msg.content:
            if content.type == "text":
                parts.append(content.text.value)

        response_text = "\n".join(parts).strip()
        if not response_text:
            print("  ❌ Assistant response was empty.", file=sys.stderr)
            return 1

        print("  ✅ Assistant responded:")
        print("--------------------------------------------------")
        print(response_text)
        print("--------------------------------------------------")
        print("\n🎉 OpenAI key + assistant look healthy from this environment.")
        return 0

    except Exception as e:
        print("  ❌ Error during run:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())



