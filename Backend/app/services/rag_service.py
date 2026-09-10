import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config.settings import settings
from app.services.embedding_service import embedding_service
from app.services.pdf_service import PDFService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RAGService:
    COLLECTION_NAME = "document_knowledge_base"

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized ChromaDB at {self.persist_dir}, items in collection: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB PersistentClient: {e}")
            self.client = None
            self.collection = None

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split document text into overlapping chunks by words/sentences."""
        if not text:
            return []
        
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for para in paragraphs:
            words = para.split()
            if not words:
                continue

            if current_len + len(words) > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                # retain overlap words
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else []
                current_chunk = overlap_words + words
                current_len = len(current_chunk)
            else:
                current_chunk.extend(words)
                current_len += len(words)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def ingest_pdf(self, file_path: str, document_type: str = "policy") -> Dict[str, Any]:
        """Extract, chunk, embed, and store a knowledge base PDF into ChromaDB."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Knowledge PDF not found: {file_path}")

        extracted = PDFService.extract_text(file_path)
        full_text = extracted.get("full_text", "")
        filename = os.path.basename(file_path)

        if not full_text.strip():
            logger.warning(f"No extractable text found in knowledge document: {file_path}")
            return {"filename": filename, "chunks_indexed": 0, "status": "empty_document"}

        chunks = self.chunk_text(full_text)
        if not chunks:
            return {"filename": filename, "chunks_indexed": 0, "status": "no_chunks"}

        embeddings = embedding_service.embed_texts(chunks)
        ids = [f"{filename}-chunk-{uuid.uuid4().hex[:8]}" for _ in chunks]
        metadatas = [
            {
                "source": filename,
                "document_type": document_type,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]

        if self.collection:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            logger.info(f"Successfully ingested {len(chunks)} chunks from {filename} into ChromaDB")

        return {
            "filename": filename,
            "chunks_indexed": len(chunks),
            "status": "success"
        }

    def search(self, query: str, top_k: Optional[int] = None, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic similarity search in ChromaDB for query context."""
        k = top_k or settings.RAG_TOP_K
        if not self.collection or self.collection.count() == 0:
            return []

        query_embedding = embedding_service.embed_query(query)
        where_clause = {"document_type": document_type} if document_type else None

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self.collection.count()),
                where=where_clause
            )
        except Exception as e:
            logger.error(f"ChromaDB search query failed: {e}")
            return []

        search_results: List[Dict[str, Any]] = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Cosine distance to similarity score
                score = round(max(0.0, 1.0 - float(dist)), 4)
                search_results.append({
                    "text": doc_text,
                    "source": meta.get("source", "knowledge_base"),
                    "page": meta.get("page", 1),
                    "document_type": meta.get("document_type", "unknown"),
                    "score": score,
                    "metadata": meta
                })

        return search_results

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all knowledge base documents in the knowledge base directory with stats."""
        kb_dir = settings.KNOWLEDGE_BASE_DIR
        if not os.path.exists(kb_dir):
            return []

        docs = []
        for fname in os.listdir(kb_dir):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(kb_dir, fname)
                try:
                    stat = os.stat(fpath)
                    # Count chunks in ChromaDB for this document
                    chunk_count = 0
                    if self.collection:
                        try:
                            # query chunks matching source
                            res = self.collection.get(where={"source": fname})
                            chunk_count = len(res.get("ids", []))
                        except Exception:
                            chunk_count = 0

                    docs.append({
                        "filename": fname,
                        "file_size_bytes": stat.st_size,
                        "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified_at": stat.st_mtime,
                        "chunks_indexed": chunk_count
                    })
                except Exception as e:
                    logger.warning(f"Failed to read file stats for {fname}: {e}")

        # Sort newest first
        docs.sort(key=lambda x: x["modified_at"], reverse=True)
        return docs

    def delete_document(self, filename: str) -> bool:
        """Delete a document file from knowledge_base and remove its chunks from ChromaDB."""
        clean_name = os.path.basename(filename)
        fpath = os.path.join(settings.KNOWLEDGE_BASE_DIR, clean_name)
        
        # Remove from ChromaDB collection
        if self.collection:
            try:
                self.collection.delete(where={"source": clean_name})
                logger.info(f"Removed chunks for {clean_name} from ChromaDB")
            except Exception as e:
                logger.error(f"Error removing chunks for {clean_name} from ChromaDB: {e}")

        # Remove physical file
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                logger.info(f"Deleted knowledge base file: {fpath}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete file {fpath}: {e}")
                return False
        return True

rag_service = RAGService()

