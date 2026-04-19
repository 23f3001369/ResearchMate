# services/vectordb.py

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.api.models.Collection import Collection


CHROMA_DIR = Path("data/chroma_db")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "research_paper_chunks"


def get_chroma_client(persist_directory: str = str(CHROMA_DIR)) -> chromadb.PersistentClient:
    """
    Create or return a persistent Chroma client.
    """
    return chromadb.PersistentClient(path=persist_directory)


def get_or_create_collection(
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR)
) -> Collection:
    """
    Get or create a Chroma collection.
    """
    client = get_chroma_client(persist_directory)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def reset_collection(
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR)
) -> Collection:
    """
    Delete and recreate a collection.
    Useful when uploading a new paper and replacing previous chunks.
    """
    client = get_chroma_client(persist_directory)

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    return client.get_or_create_collection(name=collection_name)


def store_embedded_documents(
    embedded_docs: List[Dict[str, Any]],
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR),
    reset: bool = True
) -> int:
    """
    Store embedded chunk documents in Chroma.

    Each doc is expected to contain:
        {
            "chunk_id": "chunk_0",
            "text": "...",
            "source": "paper.pdf",
            "word_count": 180,
            "embedding": [...]
        }

    Returns:
        int: number of stored documents
    """
    if not embedded_docs:
        return 0

    collection = (
        reset_collection(collection_name, persist_directory)
        if reset
        else get_or_create_collection(collection_name, persist_directory)
    )

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for doc in embedded_docs:
        ids.append(doc["chunk_id"])
        documents.append(doc["text"])
        embeddings.append(doc["embedding"])
        metadatas.append({
            "source": str(doc.get("source", "unknown")),
            "word_count": int(doc.get("word_count", 0))
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(ids)


def search_similar_chunks(
    query_embedding: List[float],
    top_k: int = 5,
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR)
) -> List[Dict[str, Any]]:
    """
    Search top-k most similar chunks using a query embedding.

    Returns:
        [
            {
                "chunk_id": "chunk_0",
                "text": "...",
                "metadata": {...},
                "distance": 0.23
            }
        ]
    """
    if not query_embedding:
        return []

    collection = get_or_create_collection(collection_name, persist_directory)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        output.append({
            "chunk_id": chunk_id,
            "text": text,
            "metadata": metadata,
            "distance": distance
        })

    return output


def get_collection_count(
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR)
) -> int:
    """
    Return number of documents in the collection.
    """
    collection = get_or_create_collection(collection_name, persist_directory)
    return collection.count()


def peek_collection(
    limit: int = 5,
    collection_name: str = COLLECTION_NAME,
    persist_directory: str = str(CHROMA_DIR)
) -> Dict[str, Any]:
    """
    Inspect a few stored items from the collection.
    """
    collection = get_or_create_collection(collection_name, persist_directory)
    return collection.peek(limit=limit)