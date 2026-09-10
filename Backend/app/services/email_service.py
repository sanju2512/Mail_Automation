import imaplib
import email
import smtplib
import os
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
from app.config.settings import settings
from app.utils.file_utils import sanitize_filename, generate_document_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailService:
    @property
    def imap_server(self) -> str:
        return settings.EMAIL_IMAP_SERVER

    @property
    def imap_port(self) -> int:
        return settings.EMAIL_IMAP_PORT

    @property
    def smtp_server(self) -> str:
        return settings.EMAIL_SMTP_SERVER

    @property
    def smtp_port(self) -> int:
        return settings.EMAIL_SMTP_PORT

    @property
    def user(self) -> Optional[str]:
        return settings.EMAIL_USER

    @property
    def password(self) -> Optional[str]:
        return settings.EMAIL_PASSWORD

    def is_configured(self) -> bool:
        # Support mock mode for testing
        if self.user == "demo@test.com":
            return True
        return bool(self.user and self.password and not self.user.startswith("your_"))

    def check_inbox(self) -> List[Dict[str, Any]]:
        """
        Check email inbox for unread messages containing PDF attachments.
        Downloads attachments into data/input/ and returns metadata.
        Supports mock mode for testing when GMAIL IMAP is not accessible.
        """
        if not self.is_configured():
            logger.info("Email credentials not configured in .env. Skipping live IMAP check.")
            return []

        # DEMO MODE: Return mock emails if user is demo@test.com
        if self.user == "demo@test.com":
            logger.info("Running in DEMO MODE - returning mock emails with sample PDFs")
            return self._mock_check_inbox()

        downloaded_docs: List[Dict[str, Any]] = []

        try:
            import socket
            socket.setdefaulttimeout(30)
            
            logger.info(f"Connecting to IMAP server: {self.imap_server}:{self.imap_port}")
            
            # Try SSL connection first, fall back to plain connection
            try:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            except (socket.timeout, TimeoutError, ConnectionRefusedError) as ssl_error:
                logger.warning(f"SSL connection failed, trying plain IMAP: {ssl_error}")
                # Try plain IMAP on port 143
                mail = imaplib.IMAP4(self.imap_server, 143)
            
            logger.info(f"Logging in as: {self.user}")
            mail.login(self.user, self.password)
            logger.info("Login successful!")
            
            logger.info("Selecting INBOX folder...")
            mail.select("INBOX")
            logger.info("INBOX selected successfully!")

            logger.info("Searching for unread emails...")
            status, messages = mail.search(None, "UNSEEN")
            
            if status != "OK":
                logger.warning(f"Failed to search for unread messages. Status: {status}")
                mail.logout()
                return []
            
            message_ids = messages[0].split() if messages and messages[0] else []
            logger.info(f"Found {len(message_ids)} unread message(s)")
            
            if not message_ids:
                logger.info("No unread emails found in inbox")
                mail.logout()
                return []

            for num in message_ids:
                try:
                    logger.info(f"Processing message {num.decode() if isinstance(num, bytes) else num}...")
                    status, msg_data = mail.fetch(num, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch message {num}")
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            subject_header = msg.get("Subject", "No Subject")
                            decoded_parts = decode_header(subject_header)
                            subject, encoding = decoded_parts[0] if decoded_parts else ("No Subject", "utf-8")
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or "utf-8", errors="ignore")

                            sender = msg.get("From", "Unknown")
                            message_id = msg.get("Message-ID", "")
                            
                            logger.info(f"  From: {sender}, Subject: {subject}")

                            pdf_count = 0
                            for part in msg.walk():
                                if part.get_content_maintype() == "multipart":
                                    continue
                                if part.get("Content-Disposition") is None:
                                    continue

                                filename = part.get_filename()
                                if filename and filename.lower().endswith(".pdf"):
                                    pdf_count += 1
                                    logger.info(f"  Found PDF attachment: {filename}")
                                    
                                    clean_filename = sanitize_filename(filename)
                                    doc_id = generate_document_id("EMAIL-DOC")
                                    target_path = os.path.join(settings.INPUT_DIR, f"{doc_id}_{clean_filename}")

                                    with open(target_path, "wb") as f:
                                        f.write(part.get_payload(decode=True))

                                    logger.info(f"  Saved to: {target_path}")
                                    
                                    downloaded_docs.append({
                                        "document_id": doc_id,
                                        "filename": clean_filename,
                                        "filepath": target_path,
                                        "sender": sender,
                                        "subject": subject,
                                        "message_id": message_id
                                    })
                            
                            if pdf_count == 0:
                                logger.info(f"  No PDF attachments found in this message")
                                
                except Exception as e:
                    logger.error(f"Error processing individual message: {e}", exc_info=True)
                    continue

            mail.logout()
            logger.info(f"IMAP session closed. Total PDFs downloaded: {len(downloaded_docs)}")
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication error (check credentials): {e}", exc_info=True)
        except TimeoutError as e:
            logger.error(f"Connection timeout - IMAP server not responding: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error checking email inbox: {e}", exc_info=True)

        return downloaded_docs

    def _mock_check_inbox(self) -> List[Dict[str, Any]]:
        """Mock email inbox for demo/testing purposes."""
        logger.info("Generating mock emails with sample PDFs...")
        
        # Get existing PDFs from data/input directory
        input_dir = settings.INPUT_DIR
        if not os.path.exists(input_dir):
            os.makedirs(input_dir, exist_ok=True)
            logger.info(f"Created input directory: {input_dir}")
        
        mock_emails = []
        sample_pdfs = [
            {"filename": "sample_employee.pdf", "sender": "hr@company.com", "subject": "Employee Information Form"},
            {"filename": "sample_form.pdf", "sender": "admin@company.com", "subject": "General Registration Form"},
        ]
        
        # Create mock PDFs if they don't exist
        for sample in sample_pdfs:
            # Check if file already exists in input directory
            existing_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
            if any(sample["filename"] in f for f in existing_files):
                # File already exists, use it
                doc_id = generate_document_id("EMAIL-DOC")
                filepath = os.path.join(input_dir, existing_files[0])
                logger.info(f"Using existing PDF: {filepath}")
                mock_emails.append({
                    "document_id": doc_id,
                    "filename": sample["filename"],
                    "filepath": filepath,
                    "sender": sample["sender"],
                    "subject": sample["subject"],
                    "message_id": f"mock-{doc_id}"
                })
            else:
                logger.info(f"Note: Place actual PDF files in {input_dir} for testing")
        
        if not mock_emails:
            logger.info(f"No PDFs found in {input_dir}. To test email functionality:")
            logger.info(f"  1. Place PDF files in: {input_dir}")
            logger.info(f"  2. Call this endpoint again")
        
        return mock_emails

    def send_document_email(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        attachment_path: str
    ) -> bool:
        """Send processed document PDF as an email attachment via SMTP."""
        if not self.is_configured():
            logger.warning(f"Email service not configured. Simulated sending to {recipient_email}")
            return True

        if not os.path.exists(attachment_path):
            logger.error(f"Attachment file not found: {attachment_path}")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.user
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body_text, "plain"))

            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, recipient_email, msg.as_string())
            server.quit()

            logger.info(f"Successfully dispatched email with attachment to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False

email_service = EmailService()
