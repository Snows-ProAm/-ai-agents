"""Shared parsing helpers for video email requests."""

from __future__ import annotations

import re
from dataclasses import dataclass


EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", flags=re.IGNORECASE)


@dataclass(frozen=True)
class VideoEmailRequest:
    query: str
    recipients: list[str]


def extract_email_addresses(value: str) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()
    for match in EMAIL_PATTERN.finditer(value):
        address = match.group(0).strip().lower()
        if address not in seen:
            addresses.append(address)
            seen.add(address)
    return addresses
