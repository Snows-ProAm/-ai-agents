"""Store simple contact facts from Telegram messages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agents.video_email_request import extract_email_addresses


CONTACT_COMMAND_PATTERN = re.compile(r"\b(?:remember|store|save|add)\b", flags=re.IGNORECASE)
EMAIL_POSSESSIVE_PATTERN = re.compile(
    r"\b(?P<name>[A-Z][A-Z0-9 .'-]{0,80}?)['’]s\s+email\b",
    flags=re.IGNORECASE,
)
EMAIL_LABEL_PATTERN = re.compile(
    r"\b(?:email\s+(?:for|of)|contact\s+for)\s+(?P<name>[A-Z][A-Z0-9 .'-]{0,80})",
    flags=re.IGNORECASE,
)
RELATIONSHIP_NAME_PATTERN = re.compile(
    r"\bmy\s+(?:brother|sister|mum|mom|dad|father|mother|wife|husband|partner|friend)\s+"
    r"(?P<name>[A-Z][A-Z0-9 .'-]{0,80}?)\s+(?:email|contact|address)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ContactMemoryRequest:
    display_name: str
    email_addresses: list[str]
    aliases: list[str]


def maybe_handle_contact_memory(message: str) -> str | None:
    request = parse_contact_memory_request(message)
    if request is None:
        return None

    upsert_contact(request)
    emails = ", ".join(request.email_addresses)
    return f"Stored contact: {request.display_name} ({emails})"


def parse_contact_memory_request(message: str) -> ContactMemoryRequest | None:
    if not CONTACT_COMMAND_PATTERN.search(message):
        return None

    email_addresses = extract_email_addresses(message)
    if not email_addresses:
        return None

    display_name = _extract_contact_name(message)
    if not display_name:
        display_name = email_addresses[0].split("@", 1)[0].replace(".", " ").replace("_", " ").title()

    aliases = _build_aliases(message, display_name)
    return ContactMemoryRequest(
        display_name=display_name,
        email_addresses=email_addresses,
        aliases=aliases,
    )


def upsert_contact(request: ContactMemoryRequest) -> dict[str, Any]:
    from shared.supabase_client import get_supabase_service_client

    supabase = get_supabase_service_client()
    workspace_id = _get_personal_workspace_id(supabase)
    existing = _find_existing_contact(supabase, workspace_id, request)
    payload = {
        "workspace_id": workspace_id,
        "display_name": request.display_name,
        "aliases": request.aliases,
        "email_addresses": request.email_addresses,
        "metadata": {"source": "telegram"},
    }

    if existing:
        response = (
            supabase.table("contacts")
            .update(_merge_contact_payload(existing, payload))
            .eq("id", existing["id"])
            .execute()
        )
    else:
        response = supabase.table("contacts").insert(payload).execute()

    if not response.data:
        raise RuntimeError("Supabase contact write returned no rows.")

    return response.data[0]


def _get_personal_workspace_id(supabase: Any) -> str:
    response = (
        supabase.table("workspaces")
        .select("id")
        .eq("slug", "personal")
        .limit(1)
        .execute()
    )
    if not response.data:
        raise RuntimeError("Missing personal workspace. Run database/agent_platform.sql first.")

    return response.data[0]["id"]


def _find_existing_contact(
    supabase: Any,
    workspace_id: str,
    request: ContactMemoryRequest,
) -> dict[str, Any] | None:
    for email in request.email_addresses:
        response = (
            supabase.table("contacts")
            .select("*")
            .eq("workspace_id", workspace_id)
            .contains("email_addresses", [email])
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]

    response = (
        supabase.table("contacts")
        .select("*")
        .eq("workspace_id", workspace_id)
        .contains("aliases", [request.display_name.lower()])
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _merge_contact_payload(existing: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "display_name": payload["display_name"],
        "aliases": _merge_lists(existing.get("aliases", []), payload["aliases"]),
        "email_addresses": _merge_lists(existing.get("email_addresses", []), payload["email_addresses"]),
        "metadata": {**existing.get("metadata", {}), **payload["metadata"]},
    }


def _merge_lists(first: list[str], second: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in [*first, *second]:
        cleaned = str(value).strip().lower()
        if cleaned and cleaned not in seen:
            merged.append(cleaned)
            seen.add(cleaned)
    return merged


def _extract_contact_name(message: str) -> str:
    for pattern in [EMAIL_POSSESSIVE_PATTERN, RELATIONSHIP_NAME_PATTERN, EMAIL_LABEL_PATTERN]:
        match = pattern.search(message)
        if match:
            return _clean_name(match.group("name"))

    without_email = re.sub(
        r"\b(?:remember|store|save|add)\b",
        "",
        message,
        flags=re.IGNORECASE,
    )
    without_email = re.sub(
        r"\b(?:email|contact|address|is|as|to|for)\b",
        " ",
        without_email,
        flags=re.IGNORECASE,
    )
    without_email = re.sub(r"\S+@\S+", "", without_email)
    return _clean_name(without_email)


def _clean_name(value: str) -> str:
    cleaned = " ".join(value.strip(" .,:;!?").split())
    return cleaned.title() if cleaned else ""


def _build_aliases(message: str, display_name: str) -> list[str]:
    aliases = [display_name.lower()]
    lowered = message.lower()
    relationship_aliases = [
        "brother",
        "sister",
        "mum",
        "mom",
        "dad",
        "father",
        "mother",
        "wife",
        "husband",
        "partner",
        "friend",
    ]
    for alias in relationship_aliases:
        if re.search(rf"\b(?:my\s+)?{re.escape(alias)}\b", lowered):
            aliases.append(alias)
            aliases.append(f"my {alias}")

    return _merge_lists([], aliases)
