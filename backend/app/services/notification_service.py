import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

from app.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return settings.is_smtp_configured


def send_email_notification(to_email: str | Iterable[str], subject: str, body: str, html: bool = True) -> bool:
    recipients = [to_email] if isinstance(to_email, str) else [e for e in to_email if e]
    if not recipients:
        return False
    if not smtp_configured():
        logger.info("[Notification] SMTP not configured. Skipped email to %s: %s", recipients, subject)
        return False
    host = settings.resolved_smtp_host
    port = settings.SMTP_PORT
    user = settings.resolved_smtp_user
    password = settings.resolved_smtp_password
    from_email = settings.resolved_smtp_from_email
    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))
        with smtplib.SMTP(host, port, timeout=12) as server:
            server.starttls()
            if password:
                server.login(user, password)
            server.send_message(msg)
        logger.info("[Notification] Successfully delivered email to %s via %s:%s", recipients, host, port)
        return True
    except Exception as e:
        logger.warning("[Notification] Failed to send email to %s: %s", recipients, e)
        return False
