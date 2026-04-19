# services/embeddings.py

from __future__ import annotations

from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Load and cache the sentence-transformer model.

    Args:
        model_name: Hugging Face / sentence-transformers model name

    Returns:
        SentenceTransformer model instance
    """
    global _model

    if _model is None:
        _model = SentenceTransformer(model_name)

    return _model


def embed_texts(
    texts: List[str],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = 32,
    normalize_embeddings: bool = True
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of input texts
        model_name: Embedding model name
        batch_size: Batch size for encoding
        normalize_embeddings: Whether to L2-normalize vectors

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    model = load_embedding_model(model_name)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=normalize_embeddings
    )

    return embeddings.tolist()


def embed_single_text(
    text: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    normalize_embeddings: bool = True
) -> List[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Input text
        model_name: Embedding model name
        normalize_embeddings: Whether to L2-normalize vector

    Returns:
        Embedding vector as list[float]
    """
    if not text or not text.strip():
        return []

    model = load_embedding_model(model_name)

    embedding = model.encode(
        text,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=normalize_embeddings
    )

    return embedding.tolist()


def embed_chunk_documents(
    chunk_docs: List[Dict[str, Any]],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = 32,
    normalize_embeddings: bool = True
) -> List[Dict[str, Any]]:
    """
    Add embeddings to structured chunk documents.

    Input:
        [
            {
                "chunk_id": "chunk_0",
                "text": "...",
                "source": "paper.pdf",
                "word_count": 180
            }
        ]

    Output:
        [
            {
                "chunk_id": "chunk_0",
                "text": "...",
                "source": "paper.pdf",
                "word_count": 180,
                "embedding": [...]
            }
        ]
    """
    if not chunk_docs:
        return []

    texts = [doc["text"] for doc in chunk_docs]
    embeddings = embed_texts(
        texts=texts,
        model_name=model_name,
        batch_size=batch_size,
        normalize_embeddings=normalize_embeddings
    )

    embedded_docs = []
    for doc, emb in zip(chunk_docs, embeddings):
        new_doc = dict(doc)
        new_doc["embedding"] = emb
        embedded_docs.append(new_doc)

    return embedded_docs


def get_embedding_dimension(
    model_name: str = DEFAULT_EMBEDDING_MODEL
) -> int:
    """
    Return embedding dimension for the loaded model.
    """
    model = load_embedding_model(model_name)
    sample_embedding = model.encode(
        "test",
        show_progress_bar=False,
        convert_to_numpy=True
    )
    return int(sample_embedding.shape[0])