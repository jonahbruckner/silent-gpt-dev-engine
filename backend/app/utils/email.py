import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def _build_smtp_client() -> Optional[smtplib.SMTP]:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

    if not host:
        return None

    client = smtplib.SMTP(host, port, timeout=30)
    if use_tls:
        client.starttls()
    if username and password:
        client.login(username, password)
    return client


def send_download_email(to_email: str, pack_slug: str, download_url: str) -> None:
    """
    Sends a simple email with the download URL for a purchased pack.
    If SMTP is not configured, this function simply logs and returns.
    """
    from_email = os.environ.get("SMTP_FROM", "no-reply@example.com")

    client = _build_smtp_client()
    if client is None:
        print("[email] SMTP not configured, skipping email send.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"Dein Download-Link für {pack_slug}"
    msg["From"] = from_email
    msg["To"] = to_email

    body = (
        f"Hey,\n\n"
        f"danke für deinen Kauf des Packs '{pack_slug}'.\n\n"
        f"Hier ist dein persönlicher Download-Link:\n\n"
        f"{download_url}\n\n"
        f"Falls du Fragen hast oder irgendetwas nicht funktioniert, "
        f"antworte einfach auf diese E-Mail.\n\n"
        f"Viele Grüße\n"
        f"SilentGPT Dev Engine"
    )
    msg.set_content(body)

    try:
        client.send_message(msg)
        print(f"[email] Download email sent to {to_email}")
    finally:
        try:
            client.quit()
        except Exception:
            pass
