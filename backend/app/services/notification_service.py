import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_FROM_EMAIL)


def send_email_notification(to_email: str | Iterable[str], subject: str, body: str, html: bool = True) -> bool:
    recipients = [to_email] if isinstance(to_email, str) else [e for e in to_email if e]
    if not recipients:
        return False
    if not smtp_configured():
        logger.info("[Notification] SMTP not configured. Skipped email to %s: %s", recipients, subject)
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.warning("[Notification] Failed to send email to %s: %s", recipients, e)
        return False
