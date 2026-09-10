# ⚡ Agentic Document Automation System

An enterprise-grade, end-to-end **Agentic AI Document Automation Platform** powered by **FastAPI**, **GroqCloud (Qwen LLM)**, **ChromaDB (RAG)**, **PyMuPDF**, **SQLite + SQLAlchemy**, and a responsive real-time web dashboard.

---

## 🏛️ System Architecture

```
                         ┌─────────────────────┐
                         │      EMAIL INBOX     │
                         └──────────┬──────────┘
                                    │ PDF Attachment
                                    ▼
                         ┌─────────────────────┐
                         │     EMAIL AGENT      │
                         │ Detect / Download    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   DOCUMENT INPUT     │
                         │ PDF Upload / Email   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   PDF PROCESSOR      │
                         │ Text Extraction      │
                         └──────────┬──────────┘
                                    │ Extracted Text
                    ┌───────────────┴────────────────┐
                    │                                │
                    ▼                                ▼
          ┌──────────────────┐             ┌──────────────────┐
          │   RAG RETRIEVER  │             │  DOCUMENT AGENT  │
          │ ChromaDB Vector  │             │ Classification   │
          │ Embeddings       │             │ Required Schema  │
          └────────┬─────────┘             └────────┬─────────┘
                   │                                │
                   └──────────────┬─────────────────┘
                                  ▼
                       ┌─────────────────────┐
                       │   GROQCLOUD QWEN    │
                       │        LLM          │
                       │ Reasoning & Extract │
                       └──────────┬──────────┘
                                  │ Structured JSON
                                  ▼
                       ┌─────────────────────┐
                       │  VALIDATION AGENT   │
                       │ Deterministic Check │
                       └──────────┬──────────┘
                                  │
                         ┌────────┴─────────┐
                         │                  │
                       ERROR               VALID
                         │                  │
                         ▼                  ▼
                ┌────────────────┐  ┌──────────────────┐
                │  ERROR AGENT   │  │ GENERATION AGENT │
                │ Explain Error  │  │ Populate Fields  │
                │ Suggest Action │  │ Build Output PDF │
                └────────────────┘  └────────┬─────────┘
                                             │
                                             ▼
                                  ┌────────────────────┐
                                  │ GENERATED DOCUMENT │
                                  │ Save & Send Email  │
                                  └────────────────────┘
```

---

## 🚀 Key Features

1. **Deterministic + Agentic Hybrid**: Deterministic PyMuPDF extraction, regex/field validation, and template rendering combined with GroqCloud Qwen LLM for deep document understanding and semantic reasoning.
2. **Context-Augmented RAG**: ChromaDB vector store ingests organizational policies/handbooks and injects relevant business rules dynamically into the LLM prompt.
3. **Multi-Agent State Machine**: Complete state tracking across `RECEIVED` → `TEXT_EXTRACTED` → `UNDERSTANDING` → `RETRIEVING` → `EXTRACTING` → `VALIDATING` → `GENERATING` → `COMPLETED` / `INVALID`.
4. **Resilient Validation & Error Remediation**: Fails early on missing mandatory fields or invalid data without hallucinating corrections, producing actionable user remediation instructions.
5. **Interactive Frontend Dashboard**: Real-time pipeline visualizer, drag-and-drop document uploader, live extracted fields table, validation reports, and document download/email dispatch.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI + Uvicorn |
| **LLM Provider** | GroqCloud |
| **LLM Model** | Qwen 2.5 (Configurable in `.env`) |
| **Vector DB / RAG** | ChromaDB + Sentence Transformers |
| **PDF Extraction** | PyMuPDF (`fitz`) |
| **Document Generation**| ReportLab / Python-docx |
| **Database** | SQLite + SQLAlchemy ORM |
| **Frontend** | HTML5, Vanilla CSS3, JavaScript (ES6+) |
| **Containerization** | Docker + Docker Compose |

---

## 📦 Installation & Setup

### 1. Clone & Environment Configuration
```bash
# Clone or navigate to the repository
cd mail-automation

# Copy environment variables
cp .env.example .env
```

Ensure your `.env` contains your active Groq API Key:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen-2.5-32b
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Sample Documents (Optional)
```bash
python create_samples.py
```

### 4. Run the Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open your browser at `http://127.0.0.1:8000` to access the interactive web dashboard.
Interactive Swagger API docs are available at `http://127.0.0.1:8000/docs`.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest tests/ -v
```

---

## 🐳 Running with Docker

```bash
docker-compose up --build -d
```
The dashboard will be available at `http://localhost:8000`.

---

## 📡 API Reference Summary

- `GET /health` - System health, DB connection, and Groq status
- `POST /documents/upload` - Upload and extract text from a PDF
- `GET /documents/` - List all tracked documents
- `GET /documents/{id}` - View full metadata, extracted fields, and audit trail
- `POST /documents/{id}/process` - Execute end-to-end multi-agent pipeline
- `GET /documents/{id}/download` - Download verified output document
- `POST /documents/{id}/send` - Dispatch generated document to recipient email
- `POST /rag/ingest` - Ingest reference policy PDF into ChromaDB
- `GET /rag/search` - Semantic similarity search in knowledge base
- `POST /email/check` - Check inbox for unread PDF attachments
- `POST /llm/test` - Direct GroqCloud Qwen LLM prompt testing
