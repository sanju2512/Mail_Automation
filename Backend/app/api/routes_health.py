from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config.settings import settings
from app.models.database import get_db
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Check API server, SQLite database, and Groq API key configuration status."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    groq_configured = bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"))

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version="1.0.0",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database_connected=db_connected,
        groq_configured=groq_configured
    )
