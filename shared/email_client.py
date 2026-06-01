"""Small Gmail SMTP helper."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_gmail_message(
    *,
    gmail_address: str,
    gmail_app_password: str,
    to_email: str,
    subject: str,
    body: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> None:
    message = EmailMessage()
    message["From"] = gmail_address
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(message)
