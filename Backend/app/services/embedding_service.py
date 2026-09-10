from typing import List
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            if getattr(settings, "USE_LIGHTWEIGHT_EMBEDDINGS", False):
                logger.info("Using lightweight deterministic embeddings as configured.")
                self._model = "fallback"
                return

            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
                self._model = SentenceTransformer(self.model_name)
            except (ImportError, MemoryError, Exception) as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to lightweight embeddings.")
                self._model = "fallback"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of string chunks."""
        self._load_model()
        if not texts:
            return []

        if self._model != "fallback" and hasattr(self._model, "encode"):
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=False, show_progress_bar=False)
                return [list(map(float, emb)) for emb in embeddings]
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")

        # Fallback basic bag-of-words / hash embedding vector if sentence_transformers isn't downloaded yet
        return [self._hash_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * 384

    def _hash_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Deterministic fallback embedding generator."""
        import hashlib
        vec = [0.0] * dim
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0
        # Normalize
        norm = sum(x**2 for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]

embedding_service = EmbeddingService()
