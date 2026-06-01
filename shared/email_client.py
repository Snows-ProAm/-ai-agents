"""Small Gmail SMTP helper."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def send_gmail_message(
    *,
    gmail_address: str,
    gmail_app_password: str,
    to_email: str | list[str],
    subject: str,
    body: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> None:
    recipients = _normalize_recipients(to_email)
    message = EmailMessage()
    message["From"] = gmail_address
    message["To"] = ", ".join(formataddr(("", recipient)) for recipient in recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(message, to_addrs=recipients)


def _normalize_recipients(to_email: str | list[str]) -> list[str]:
    values = [to_email] if isinstance(to_email, str) else to_email
    recipients: list[str] = []
    for value in values:
        recipients.extend(part.strip() for part in value.split(",") if part.strip())
    if not recipients:
        raise ValueError("At least one recipient email address is required.")
    return recipients
