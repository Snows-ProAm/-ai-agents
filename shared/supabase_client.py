from __future__ import annotations

from supabase import Client, create_client

from shared.config import get_settings


def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_service_client() -> Client:
    settings = get_settings()
    if not settings.supabase_service_role_key:
        raise RuntimeError("Missing required environment variable: SUPABASE_SERVICE_ROLE_KEY")

    return create_client(settings.supabase_url, settings.supabase_service_role_key)
