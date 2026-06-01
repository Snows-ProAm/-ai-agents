"""Check that the Supabase client can connect with your local .env credentials."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from shared.config import get_settings
from shared.supabase_client import get_supabase_client


def main() -> None:
    settings = get_settings()
    supabase = get_supabase_client()

    response = supabase.auth.get_session()

    print(f"Supabase URL loaded: {settings.supabase_url}")
    print("Supabase client created successfully.")
    print(f"Current auth session: {response}")


if __name__ == "__main__":
    main()
