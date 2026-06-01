from __future__ import annotations

from supabase import Client, create_client

from shared.config import get_settings


def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)
