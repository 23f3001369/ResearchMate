# services/chunking.py

from __future__ import annotations

import re
from typing import List, Dict, Any


def normalize_text(text: str) -> str:
    """
    Normalize text before chunking.
    """
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs using double newlines.
    """
    text = normalize_text(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def split_long_paragraph(paragraph: str, max_words: int = 200) -> List[str]:
    """
    Split a long paragraph into smaller chunks by sentence boundaries.
    Falls back to word-based splitting if needed.
    """
    paragraph = paragraph.strip()
    if not paragraph:
        return []

    words = paragraph.split()
    if len(words) <= max_words:
        return [paragraph]

    # Sentence-based split
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks = []
    current_chunk = []

    for sentence in sentences:
        sentence_words = sentence.split()

        if len(current_chunk) + len(sentence_words) <= max_words:
            current_chunk.extend(sentence_words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = sentence_words

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Fallback if sentence split failed badly
    final_chunks = []
    for chunk in chunks:
        chunk_words = chunk.split()
        if len(chunk_words) <= max_words:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(chunk_words), max_words):
                final_chunks.append(" ".join(chunk_words[i:i + max_words]))

    return final_chunks


def chunk_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 40
) -> List[str]:
    """
    Chunk text into overlapping word-based chunks while trying to respect paragraph structure.

    Args:
        text: Full document text
        chunk_size: Max words per chunk
        overlap: Number of words overlapped between consecutive chunks

    Returns:
        List[str]: list of text chunks
    """
    text = normalize_text(text)
    if not text:
        return []

    paragraphs = split_into_paragraphs(text)

    prepared_parts = []
    for para in paragraphs:
        para_words = para.split()
        if len(para_words) <= chunk_size:
            prepared_parts.append(para)
        else:
            prepared_parts.extend(split_long_paragraph(para, max_words=chunk_size))

    all_words = []
    for part in prepared_parts:
        all_words.extend(part.split())
        all_words.append("\nPARA_BREAK\n")

    chunks = []
    current_words = []
    i = 0

    filtered_words = [w for w in all_words if w != "\nPARA_BREAK\n"]

    while i < len(filtered_words):
        chunk_words = filtered_words[i:i + chunk_size]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)

        if i + chunk_size >= len(filtered_words):
            break

        i += max(1, chunk_size - overlap)

    return chunks


def create_chunk_documents(
    text: str,
    source_name: str = "uploaded_paper.pdf",
    chunk_size: int = 200,
    overlap: int = 40
) -> List[Dict[str, Any]]:
    """
    Create structured chunk documents with metadata.

    Returns:
        [
            {
                "chunk_id": "chunk_0",
                "text": "...",
                "source": "uploaded_paper.pdf",
                "word_count": 187
            },
            ...
        ]
    """
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    documents = []
    for idx, chunk in enumerate(chunks):
        documents.append({
            "chunk_id": f"chunk_{idx}",
            "text": chunk,
            "source": source_name,
            "word_count": len(chunk.split())
        })

    return documents