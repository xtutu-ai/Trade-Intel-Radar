from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)


class MailSender:
    def __init__(self, host: str, port: int, user: str, password: str, mail_from: str, mail_to: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.mail_from = mail_from or user
        self.mail_to = mail_to

    def configured(self) -> bool:
        return bool(self.host and self.port and self.user and self.password and self.mail_from and self.mail_to)

    def send_html(self, subject: str, html: str) -> None:
        if not self.configured():
            log.warning("SMTP is not configured; skip sending email")
            return
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.mail_from
        msg["To"] = self.mail_to
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.mail_from, [x.strip() for x in self.mail_to.split(",")], msg.as_string())
        log.info("Email sent to %s", self.mail_to)
