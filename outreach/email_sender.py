import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_NAME, DRAFTS_DIR
from outreach.tracker import ApplicationTracker

class EmailDispatcher:
    """Manages email composition, PDF attachment, and sending to HR or portal mailboxes
    with built-in Safe Review Mode and dispatch auditing."""

    def __init__(self):
        self.tracker = ApplicationTracker()

    def build_email_message(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        sender_email: Optional[str] = None,
        sender_display_name: Optional[str] = None,
        attachments: Optional[List[Path]] = None
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        s_email = sender_email or os.getenv("SMTP_USER", SMTP_USER) or "candidate@engineering-talent.com"
        s_name = sender_display_name or os.getenv("SENDER_NAME", SENDER_NAME)

        msg["From"] = f"{s_name} <{s_email}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)

        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if attachments:
            for filepath in attachments:
                if filepath and filepath.exists():
                    with open(filepath, "rb") as f:
                        part = MIMEApplication(f.read(), Name=filepath.name)
                        part["Content-Disposition"] = f'attachment; filename="{filepath.name}"'
                        msg.attach(part)

        return msg

    def send_or_draft_application(
        self,
        job_title: str,
        company: str,
        location: str,
        recipient_email: str,
        subject: str,
        body_text: str,
        cv_pdf_path: Optional[Path] = None,
        cover_letter_pdf_path: Optional[Path] = None,
        force_live_send: bool = False
    ) -> Dict[str, Any]:
        """Dispatches email to HR or saves to drafts depending on Safe Mode / credentials."""
        attachments = [p for p in [cv_pdf_path, cover_letter_pdf_path] if p and p.exists()]
        msg = self.build_email_message(
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            attachments=attachments
        )

        user = os.getenv("SMTP_USER", SMTP_USER)
        pwd = os.getenv("SMTP_PASSWORD", SMTP_PASSWORD)
        host = os.getenv("SMTP_HOST", SMTP_HOST)
        port = int(os.getenv("SMTP_PORT", str(SMTP_PORT)))

        can_send_live = bool(user and pwd and force_live_send)

        if can_send_live:
            try:
                server = smtplib.SMTP(host, port, timeout=15)
                server.starttls()
                server.login(user, pwd)
                server.send_message(msg)
                server.quit()

                # Track in DB
                app_id = self.tracker.add_application(
                    job_title=job_title,
                    company=company,
                    location=location,
                    hr_email=recipient_email,
                    status="Sent",
                    cv_pdf_path=str(cv_pdf_path) if cv_pdf_path else "",
                    cover_letter_pdf_path=str(cover_letter_pdf_path) if cover_letter_pdf_path else "",
                    email_subject=subject,
                    notes="Sent live via SMTP."
                )

                return {
                    "success": True,
                    "mode": "LIVE_SENT",
                    "app_id": app_id,
                    "message": f"Successfully emailed application to {recipient_email}!"
                }
            except Exception as e:
                print(f"SMTP error, falling back to draft: {e}")

        # Safe Mode or Draft Generation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"draft_{company}_{job_title}_{timestamp}.eml".replace(" ", "_").replace("/", "-")
        eml_path = DRAFTS_DIR / safe_filename

        with open(eml_path, "wb") as f:
            f.write(msg.as_bytes())

        app_id = self.tracker.add_application(
            job_title=job_title,
            company=company,
            location=location,
            hr_email=recipient_email,
            status="Drafted",
            cv_pdf_path=str(cv_pdf_path) if cv_pdf_path else "",
            cover_letter_pdf_path=str(cover_letter_pdf_path) if cover_letter_pdf_path else "",
            email_subject=subject,
            notes=f"Saved to draft EML: {safe_filename}. Ready for review or 1-click dispatch."
        )

        return {
            "success": True,
            "mode": "DRAFT_SAVED",
            "app_id": app_id,
            "draft_file": str(eml_path),
            "message": f"Application prepared in Safe Draft mode. Saved to: {safe_filename}"
        }
