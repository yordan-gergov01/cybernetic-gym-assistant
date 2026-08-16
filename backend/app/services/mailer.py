"""Outgoing email. Currently one message: the password-reset link.

Plain SMTP rather than a provider SDK - it is the one interface every mail service
speaks, so the project can point at Gmail, Mailgun or a company server by changing
`.env` and nothing else.

With no SMTP host configured the link is written to the log at WARNING instead. That is
the honest fallback for a project without a mail provider: the flow keeps working for
whoever can read the log, and nobody is told an email was sent when it was not.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(message: EmailMessage) -> None:
    """Blocking SMTP call. Runs in a thread - see `send_password_reset`."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_password_reset(email: str, link: str, valid_minutes: int) -> bool:
    """Send the reset link. Returns whether it actually went out.

    A failure here is never raised at the caller: the endpoint must answer the same way
    whether or not the address exists, and a 500 would tell an attacker which addresses
    are registered. It is logged with the link so a reset is still possible.
    """
    if not settings.smtp_configured:
        logger.warning(
            "SMTP is not configured; the password reset link for %s was not sent: %s", email, link
        )
        return False

    message = EmailMessage()
    message["Subject"] = "Смяна на паролата"
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message.set_content(
        "Здравей,\n\n"
        "Заявена е смяна на паролата за профила ти в Cybernetic Gym Assistant.\n"
        f"Отвори този линк, за да зададеш нова парола:\n\n{link}\n\n"
        f"Линкът важи {valid_minutes} минути и може да се използва само веднъж.\n"
        "Ако не си заявявал смяна, просто изтрий това писмо - паролата ти остава същата.\n"
    )

    try:
        await asyncio.to_thread(_send, message)
        return True
    except (smtplib.SMTPException, OSError):
        logger.error("Could not send the password reset email to %s", email, exc_info=True)
        return False
