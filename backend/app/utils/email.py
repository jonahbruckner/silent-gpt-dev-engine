import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USERNAME or "no-reply@example.com"


def send_download_email(to_email: str, pack_slug: str, download_url: str) -> None:
    """
    Schickt eine einfache E-Mail mit dem Download-Link für ein gekauftes Pack.
    Wenn SMTP nicht vollständig konfiguriert ist, wird nur geloggt.
    """
    if not (SMTP_HOST and SMTP_PORT and SMTP_USERNAME and SMTP_PASSWORD):
        print(
            "[email] SMTP not fully configured "
            f"(host={SMTP_HOST}, user={SMTP_USERNAME}) – skipping send."
        )
        return

    subject = f"Dein SilentGPT Pack: {pack_slug}"
    body = f"""Hey,

danke für deinen Kauf des Packs "{pack_slug}"!

Hier ist dein persönlicher Download-Link:

{download_url}

Der Link basiert auf deiner Stripe-Session. Falls etwas nicht funktioniert,
melde dich einfach bei mir und ich schicke dir den Download erneut.

Viele Grüße
SilentGPT Dev Engine
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[email] Download email sent to {to_email} for pack={pack_slug}")
    except Exception as exc:
        print(f"[email] Failed to send email to {to_email}: {exc}")
