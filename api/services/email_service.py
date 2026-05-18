"""Email delivery — SMTP (Mailpit in dev) or Resend (prod)."""

import json
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import Settings


def send_magic_link(to_email: str, link: str, settings: Settings) -> None:
    subject = "Sign in to Glintstone"
    body_text = f"Click the link below to sign in (expires in 15 minutes):\n\n{link}"
    body_html = f"""
<p>Click the link below to sign in to Glintstone. The link expires in 15 minutes.</p>
<p><a href="{link}">Sign in to Glintstone</a></p>
<p>If you didn't request this, you can ignore this email.</p>
"""

    if settings.email_backend == "resend":
        _send_via_resend(to_email, subject, body_html, settings)
    else:
        _send_via_smtp(to_email, subject, body_text, body_html, settings)


def _send_via_resend(
    to_email: str, subject: str, body_html: str, settings: Settings
) -> None:
    payload = json.dumps(
        {
            "from": settings.email_from,
            "to": [to_email],
            "subject": subject,
            "html": body_html,
        }
    )
    # Use curl to avoid macOS Python SSL issues with some HTTPS endpoints.
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            "https://api.resend.com/emails",
            "-H",
            "Content-Type: application/json",
            "-H",
            f"Authorization: Bearer {settings.resend_api_key}",
            "-d",
            payload,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Resend delivery failed: {result.stderr}")
    resp = json.loads(result.stdout)
    if "error" in resp:
        raise RuntimeError(f"Resend API error: {resp['error']}")


def _send_via_smtp(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
    settings: Settings,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.sendmail(settings.email_from, to_email, msg.as_string())
