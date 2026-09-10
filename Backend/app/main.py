import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.config.logging_config import setup_logging
from app.models.database import init_db
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router
from app.api.routes_rag import router as rag_router
from app.api.routes_email import router as email_router
from app.api.routes_jobs import router as jobs_router
from app.models.schemas import LLMTestRequest, LLMTestResponse
from app.services.llm_service import llm_service
from app.utils.logger import get_logger

# Initialize structured logging
setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
logger = get_logger("app.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Agentic Document Automation System...")
    init_db()
    settings.ensure_directories()
    logger.info("Database and storage directories successfully initialized.")
    yield

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Agentic Document Automation API powered by GroqCloud Qwen LLM, ChromaDB RAG, and FastAPI",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Include API Routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(email_router)
app.include_router(jobs_router)

# Direct LLM Test Endpoint (Phase 3 Requirement)
@app.post("/llm/test", response_model=LLMTestResponse, tags=["LLM"])
def test_llm_connection(payload: LLMTestRequest):
    """Test GroqCloud Qwen LLM integration with an arbitrary prompt."""
    try:
        messages = [
            {"role": "system", "content": "You are an AI assistant in an Agentic Document Automation pipeline."},
            {"role": "user", "content": payload.message}
        ]
        response_text = llm_service.generate(messages, max_tokens=500)
        return LLMTestResponse(
            status="success",
            response=response_text,
            model=settings.GROQ_MODEL
        )
    except Exception as e:
        logger.error(f"LLM test request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse

# Explicit Root Route serving Dashboard index.html
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/", tags=["Dashboard"])
def serve_dashboard():
    """Serve the frontend dashboard index.html."""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(status_code=404, content={"detail": "Frontend dashboard not found."})

# Mount CSS and JS static subdirectories
if (frontend_dir / "css").exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
if (frontend_dir / "js").exists():
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")

