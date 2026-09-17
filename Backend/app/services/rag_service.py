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
        self.client = None
        self.collection = None
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure ChromaDB client and collection are properly initialized."""
        if self.collection is not None:
            return self.collection
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            count = self.collection.count()
            logger.info(f"Initialized ChromaDB at {self.persist_dir}, items in collection: {count}")
            return self.collection
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB PersistentClient: {e}")
            self.client = None
            self.collection = None
            return None

    def chunk_text(self, text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
        """Split document text into overlapping chunks by words for optimal embedding representation."""
        if not text or not text.strip():
            return []

        words = text.split()
        if not words:
            return []

        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks: List[str] = []
        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            chunk = words[i:i + chunk_size]
            if chunk:
                chunks.append(" ".join(chunk))
            if i + chunk_size >= len(words):
                break

        return chunks

    def ingest_pdf(self, file_path: str, document_type: str = "policy") -> Dict[str, Any]:
        """Extract, chunk, embed, and store a knowledge base PDF into ChromaDB."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Knowledge PDF not found: {file_path}")

        coll = self._ensure_collection()
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

        if coll is not None:
            coll.add(
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
        """Perform semantic similarity search in ChromaDB with robust fallback."""
        coll = self._ensure_collection()
        k = top_k or settings.RAG_TOP_K
        if coll is None:
            return []

        try:
            total_items = coll.count()
        except Exception:
            total_items = 0

        if total_items == 0:
            return []

        query_embedding = embedding_service.embed_query(query)
        where_clause = {"document_type": document_type} if document_type else None

        results = None
        try:
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=min(k, total_items),
                where=where_clause
            )
        except Exception as e:
            logger.warning(f"ChromaDB filtered query failed: {e}. Trying unrestricted query.")
            try:
                results = coll.query(
                    query_embeddings=[query_embedding],
                    n_results=min(k, total_items)
                )
            except Exception as ex:
                logger.error(f"ChromaDB search query failed completely: {ex}")

        search_results: List[Dict[str, Any]] = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                score = round(max(0.0, 1.0 - float(dist)), 4)
                search_results.append({
                    "text": doc_text,
                    "source": (meta or {}).get("source", "knowledge_base"),
                    "page": (meta or {}).get("page", 1),
                    "document_type": (meta or {}).get("document_type", "unknown"),
                    "score": score,
                    "metadata": meta or {}
                })

        # Fallback: If similarity search returned 0 items but collection has items, fetch direct entries
        if not search_results and total_items > 0:
            try:
                fallback_data = coll.get(limit=min(k, total_items))
                if fallback_data and fallback_data.get("documents"):
                    for d_text, d_meta in zip(fallback_data["documents"], fallback_data.get("metadatas") or [{}] * len(fallback_data["documents"])):
                        search_results.append({
                            "text": d_text,
                            "source": (d_meta or {}).get("source", "knowledge_base"),
                            "page": (d_meta or {}).get("page", 1),
                            "document_type": (d_meta or {}).get("document_type", "unknown"),
                            "score": 0.8,
                            "metadata": d_meta or {}
                        })
            except Exception as e:
                logger.warning(f"Fallback get from ChromaDB collection failed: {e}")

        return search_results

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all knowledge base documents in the knowledge base directory with stats."""
        kb_dir = settings.KNOWLEDGE_BASE_DIR
        if not os.path.exists(kb_dir):
            return []

        coll = self._ensure_collection()
        docs = []
        for fname in os.listdir(kb_dir):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(kb_dir, fname)
                try:
                    stat = os.stat(fpath)
                    # Count chunks in ChromaDB for this document
                    chunk_count = 0
                    if coll is not None:
                        try:
                            # query chunks matching source
                            res = coll.get(where={"source": fname})
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
        coll = self._ensure_collection()
        
        # Remove from ChromaDB collection
        if coll is not None:
            try:
                coll.delete(where={"source": clean_name})
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

