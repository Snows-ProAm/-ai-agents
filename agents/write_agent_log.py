"""Insert a test row into the Supabase agent_logs table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from shared.supabase_client import get_supabase_client


DEFAULT_MESSAGE = "Hello from the Python agent workspace."


def build_log_payload(message: str) -> dict[str, str]:
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("Message cannot be empty.")

    return {"message": cleaned}


def insert_agent_log(message: str) -> dict[str, Any]:
    supabase = get_supabase_client()
    payload = build_log_payload(message)

    response = supabase.table("agent_logs").insert(payload).execute()
    if not response.data:
        raise RuntimeError("Supabase insert returned no rows.")

    return response.data[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a row to public.agent_logs.")
    parser.add_argument(
        "message",
        nargs="?",
        default=DEFAULT_MESSAGE,
        help="Message to insert into agent_logs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row = insert_agent_log(args.message)

    print("Inserted agent log:")
    print(f"  id: {row.get('id')}")
    print(f"  message: {row.get('message')}")
    print(f"  created_at: {row.get('created_at')}")


if __name__ == "__main__":
    main()
