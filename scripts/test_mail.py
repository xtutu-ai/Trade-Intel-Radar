from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.report.mail_sender import MailSender


settings = Settings()
sender = MailSender(
    host=settings.env("SMTP_HOST"),
    port=settings.int_env("SMTP_PORT", 587),
    user=settings.env("SMTP_USER"),
    password=settings.env("SMTP_PASSWORD"),
    mail_from=settings.env("MAIL_FROM"),
    mail_to=settings.env("MAIL_TO"),
)

if not sender.configured():
    print("SMTP not configured. Fill SMTP_* and MAIL_* in .env")
    raise SystemExit(1)

sender.send_html("Trade-Intel-Radar SMTP Test", "<h1>SMTP OK</h1><p>This is a test email.</p>")
print("mail sent")
