from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    openai_api_key: str | None = None


def get_settings() -> Settings:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or None

    missing = [
        name
        for name, value in {
            "SUPABASE_URL": supabase_url,
            "SUPABASE_ANON_KEY": supabase_anon_key,
        }.items()
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s): {joined}")

    return Settings(
        supabase_url=supabase_url,
        supabase_anon_key=supabase_anon_key,
        openai_api_key=openai_api_key,
    )
