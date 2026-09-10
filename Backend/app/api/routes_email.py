from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.agents.email_agent import email_agent
from app.models.schemas import EmailCheckResponse
from app.services.email_service import email_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/email", tags=["Email Automation"])

@router.post("/check", response_model=EmailCheckResponse)
def check_email_inbox(db: Session = Depends(get_db)):
    """
    Check configured email inbox for new incoming PDF attachments and automatically ingest them.
    """
    res = email_agent.check_and_ingest(db=db)
    return EmailCheckResponse(
        status=res["status"],
        emails_processed=res["emails_processed"],
        documents_detected=res["documents_detected"],
        message=res["message"]
    )

@router.get("/test", response_model=dict)
def test_email_connection():
    """
    Test email connection and return diagnostic information.
    Useful for debugging email configuration issues.
    """
    if not email_service.is_configured():
        return {
            "status": "not_configured",
            "message": "Email service is not configured. Please set EMAIL_USER and EMAIL_PASSWORD in .env",
            "user": email_service.user,
            "imap_server": email_service.imap_server,
            "imap_port": email_service.imap_port
        }
    
    try:
        import imaplib
        import socket
        
        socket.setdefaulttimeout(30)
        
        logger.info(f"[TEST] Attempting to connect to {email_service.imap_server}:{email_service.imap_port}")
        
        # Try SSL connection first
        try:
            mail = imaplib.IMAP4_SSL(email_service.imap_server, email_service.imap_port)
            logger.info("[TEST] SSL connection successful!")
        except (socket.timeout, TimeoutError, ConnectionRefusedError) as e:
            logger.warning(f"[TEST] SSL connection failed, trying plain IMAP on port 143: {e}")
            # Fallback to plain IMAP
            mail = imaplib.IMAP4(email_service.imap_server, 143)
            logger.info("[TEST] Plain IMAP connection successful!")
        
        logger.info(f"[TEST] Attempting to login as {email_service.user}")
        mail.login(email_service.user, email_service.password)
        logger.info("[TEST] Login successful!")
        
        # Try to select INBOX
        status, mailbox_list = mail.list()
        logger.info(f"[TEST] Available mailboxes: {mailbox_list}")
        
        mail.select("INBOX")
        status, messages = mail.search(None, "ALL")
        
        total_emails = len(messages[0].split()) if messages and messages[0] else 0
        
        status_unread, unread_messages = mail.search(None, "UNSEEN")
        unread_count = len(unread_messages[0].split()) if unread_messages and unread_messages[0] else 0
        
        mail.logout()
        
        return {
            "status": "connected",
            "message": "Email service is working correctly!",
            "user": email_service.user,
            "imap_server": email_service.imap_server,
            "imap_port": email_service.imap_port,
            "total_emails": total_emails,
            "unread_emails": unread_count,
            "connection": "SUCCESS"
        }
        
    except imaplib.IMAP4.error as e:
        logger.error(f"[TEST] IMAP error: {e}", exc_info=True)
        return {
            "status": "auth_failed",
            "message": f"Authentication failed. Check your email credentials. Gmail users: Use App Passwords, not your regular password.",
            "error": str(e),
            "user": email_service.user,
            "imap_server": email_service.imap_server,
            "imap_port": email_service.imap_port,
            "connection": "FAILED"
        }
    except TimeoutError as e:
        logger.error(f"[TEST] Timeout: {e}", exc_info=True)
        return {
            "status": "timeout",
            "message": "Connection timeout. The IMAP server is not responding. Check your internet connection.",
            "error": str(e),
            "user": email_service.user,
            "imap_server": email_service.imap_server,
            "imap_port": email_service.imap_port,
            "connection": "TIMEOUT"
        }
    except Exception as e:
        logger.error(f"[TEST] Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "An unexpected error occurred while testing email connection.",
            "error": str(e),
            "user": email_service.user,
            "imap_server": email_service.imap_server,
            "imap_port": email_service.imap_port,
            "connection": "FAILED"
        }

