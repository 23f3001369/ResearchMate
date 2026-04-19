# # services/qa_engine.py

# from __future__ import annotations

# import re
# from typing import List, Dict, Any, Tuple

# from services.embeddings import embed_single_text
# from services.vectordb import search_similar_chunks


# def normalize_text(text: str) -> str:
#     if not text:
#         return ""
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()


# def split_into_sentences(text: str) -> List[str]:
#     if not text:
#         return []
#     text = normalize_text(text)
#     sentences = re.split(r'(?<=[.!?])\s+', text)
#     return [s.strip() for s in sentences if s.strip()]


# def extract_keywords(question: str) -> List[str]:
#     """
#     Extract useful keywords from the question.
#     """
#     stopwords = {
#         "the", "is", "of", "a", "an", "and", "or", "to", "in", "on", "for",
#         "what", "which", "who", "whom", "when", "where", "why", "how", "did",
#         "does", "do", "was", "were", "are", "be", "been", "being", "that",
#         "this", "these", "those", "with", "by", "from", "as", "at", "it",
#         "its", "their", "his", "her", "about", "based", "paper", "research",
#         "proposed", "model", "achieved"
#     }

#     words = re.findall(r"[a-zA-Z0-9.%+-]+", question.lower())
#     keywords = [w for w in words if w not in stopwords and len(w) > 2]
#     return keywords


# def keyword_overlap_score(question: str, text: str) -> int:
#     """
#     Simple keyword overlap score for reranking.
#     """
#     q_keywords = extract_keywords(question)
#     text_lower = text.lower()

#     score = 0
#     for kw in q_keywords:
#         if kw in text_lower:
#             score += 2

#     # Bonus for percentage if question hints at performance metrics
#     metric_words = ["accuracy", "precision", "recall", "f1", "score", "auc", "sensitivity", "specificity"]
#     if any(m in question.lower() for m in metric_words):
#         if "%" in text or re.search(r"\b\d+(\.\d+)?\b", text):
#             score += 3

#     return score


# def sentence_relevance_score(question: str, sentence: str) -> int:
#     """
#     Score a sentence for direct answerability.
#     """
#     score = keyword_overlap_score(question, sentence)

#     q_lower = question.lower()
#     s_lower = sentence.lower()

#     if "accuracy" in q_lower and "accuracy" in s_lower:
#         score += 4

#     if any(word in q_lower for word in ["achieved", "result", "performance"]):
#         if any(word in s_lower for word in ["achieved", "result", "accuracy", "performance"]):
#             score += 2

#     if "%" in sentence:
#         score += 3

#     if 6 <= len(sentence.split()) <= 35:
#         score += 2

#     return score


# def rerank_chunks(question: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Rerank retrieved chunks using keyword overlap in addition to embedding retrieval.
#     """
#     reranked = []

#     for chunk in chunks:
#         text = chunk.get("text", "")
#         distance = chunk.get("distance", 9999.0)

#         overlap = keyword_overlap_score(question, text)

#         # Lower distance is better, so subtract a scaled version
#         combined_score = overlap - (distance * 2)

#         new_chunk = dict(chunk)
#         new_chunk["keyword_score"] = overlap
#         new_chunk["combined_score"] = combined_score
#         reranked.append(new_chunk)

#     reranked.sort(key=lambda x: x["combined_score"], reverse=True)
#     return reranked


# def find_best_answer_sentence(question: str, chunks: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any] | None]:
#     """
#     Find the single most relevant sentence from retrieved chunks.
#     """
#     best_sentence = ""
#     best_chunk = None
#     best_score = float("-inf")

#     for chunk in chunks:
#         text = chunk.get("text", "")
#         sentences = split_into_sentences(text)

#         for sentence in sentences:
#             score = sentence_relevance_score(question, sentence)
#             if score > best_score:
#                 best_score = score
#                 best_sentence = sentence
#                 best_chunk = chunk

#     return best_sentence, best_chunk


# def build_context_from_chunks(
#     retrieved_chunks: List[Dict[str, Any]],
#     max_chars: int = 2500
# ) -> str:
#     """
#     Build compact context from top reranked chunks.
#     """
#     if not retrieved_chunks:
#         return ""

#     context_parts = []
#     total_chars = 0

#     for idx, chunk in enumerate(retrieved_chunks, start=1):
#         text = normalize_text(chunk.get("text", ""))
#         if not text:
#             continue

#         block = f"[Chunk {idx}] {text}\n"
#         if total_chars + len(block) > max_chars:
#             break

#         context_parts.append(block)
#         total_chars += len(block)

#     return "\n".join(context_parts).strip()


# def retrieve_relevant_chunks(question: str, top_k: int = 8) -> List[Dict[str, Any]]:
#     """
#     Embed question and retrieve chunks from ChromaDB.
#     """
#     if not question or not question.strip():
#         return []

#     query_embedding = embed_single_text(question)
#     if not query_embedding:
#         return []

#     chunks = search_similar_chunks(
#         query_embedding=query_embedding,
#         top_k=top_k
#     )
#     return chunks


# def format_answer(question: str, best_sentence: str, best_chunk: Dict[str, Any] | None) -> str:
#     """
#     Format a cleaner final answer.
#     """
#     if not best_sentence:
#         return "I could not find a precise answer in the uploaded paper."

#     q_lower = question.lower()

#     if "accuracy" in q_lower:
#         percent_match = re.search(r"\b\d+(\.\d+)?%", best_sentence)
#         if percent_match:
#             return f"The proposed model achieved an accuracy of **{percent_match.group(0)}**.\n\nSupporting sentence: {best_sentence}"

#     return f"According to the paper, {best_sentence}"


# def is_metadata_question(question):
#     q = question.lower()

#     metadata_patterns = [
#         "how many pages",
#         "number of pages",
#         "total pages",
#         "how long is this paper",
#         "how many authors",
#         "document title"
#     ]

#     return any(p in q for p in metadata_patterns)


# def is_summary_question(question):
#     q = question.lower()

#     summary_patterns = [
#         "what is this paper about",
#         "major topics",
#         "main topics",
#         "what topics are covered",
#         "summarize",
#         "explain the paper",
#         "what does this paper discuss",
#         "methodology",
#         "main idea"
#     ]

#     return any(p in q for p in summary_patterns)


# def answer_question(question):

#     # ROUTE 1 — Metadata questions
#     if is_metadata_question(question):

#         page_count = None

#         try:
#             import streamlit as st
#             page_count = st.session_state["pdf_data"]["page_count"]
#         except:
#             pass

#         if page_count:
#             return {
#                 "answer": f"This document has {page_count} pages.",
#                 "retrieved_chunks": [],
#                 "context":""
#             }


#     # ROUTE 2 — Summary questions
#     if is_summary_question(question):

#         try:
#             import streamlit as st
#             summaries = st.session_state["summaries"]

#             return {
#                 "answer":
#                     f"""Major topics covered in this paper:

#                     1. {summaries["short_summary"]}

#                     Methodology:
#                     {summaries["methodology_summary"]}

#                     Results:
#                     {summaries["results_summary"]}

#                     Conclusion:
#                     {summaries["conclusion_summary"]}
#                     """,
#                                     "retrieved_chunks": [],
#                                     "context":""
#                                 }

#         except:
#             pass


#     # ROUTE 3 — Existing retrieval logic
#     retrieved_chunks = retrieve_relevant_chunks(question)

#     reranked_chunks = rerank_chunks(question,retrieved_chunks)

#     best_sentence,best_chunk = find_best_answer_sentence(
#         question,
#         reranked_chunks
#     )

#     context = build_context_from_chunks(
#         reranked_chunks[:4]
#     )

#     answer = format_answer(
#         question,
#         best_sentence,
#         best_chunk
#     )

#     return {
#         "answer":answer,
#         "retrieved_chunks":reranked_chunks[:5],
#         "context":context
#     }


# services/qa_engine.py

# services/qa_engine.py

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional

import streamlit as st

from services.embeddings import embed_single_text
from services.vectordb import search_similar_chunks
from services.llm_answer import generate_llm_answer


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def build_context_from_chunks(
    retrieved_chunks: List[Dict[str, Any]],
    max_chars: int = 5000
) -> str:
    """
    Build a compact context string from retrieved chunks.
    """
    if not retrieved_chunks:
        return ""

    context_parts = []
    total_chars = 0

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        text = normalize_text(chunk.get("text", ""))
        if not text:
            continue

        block = f"[Chunk {idx}]\n{text}\n"
        if total_chars + len(block) > max_chars:
            break

        context_parts.append(block)
        total_chars += len(block)

    return "\n".join(context_parts).strip()


def is_metadata_question(question: str) -> bool:
    q = question.lower()
    patterns = [
        "how many pages",
        "number of pages",
        "total pages",
        "how long is this paper",
        "how many authors",
        "document title",
        "paper title",
        "file name",
        "filename",
    ]
    return any(p in q for p in patterns)


def answer_metadata_question(question: str) -> Optional[str]:
    q = question.lower()
    pdf_data = st.session_state.get("pdf_data", {})

    if "page" in q and pdf_data.get("page_count") is not None:
        return f"This document has {pdf_data['page_count']} pages."

    if any(x in q for x in ["title", "file name", "filename"]) and pdf_data.get("file_name"):
        return f"The uploaded file name is {pdf_data['file_name']}."

    return None


def retrieve_relevant_chunks(question: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Embed question and retrieve most relevant chunks from ChromaDB.
    """
    if not question or not question.strip():
        return []

    query_embedding = embed_single_text(question)
    if not query_embedding:
        return []

    return search_similar_chunks(
        query_embedding=query_embedding,
        top_k=top_k
    )


def answer_question(
    question: str,
    top_k: int = 6,
    max_context_chars: int = 5000
) -> Dict[str, Any]:
    """
    Conversational RAG:
    - direct metadata answers when possible
    - otherwise retrieve chunks
    - send question + context + recent chat history to Groq
    """
    # Route metadata questions directly
    if is_metadata_question(question):
        metadata_answer = answer_metadata_question(question)
        if metadata_answer:
            return {
                "question": question,
                "answer": metadata_answer,
                "context": "",
                "retrieved_chunks": []
            }

    # Retrieve local context
    retrieved_chunks = retrieve_relevant_chunks(question=question, top_k=top_k)
    context = build_context_from_chunks(
        retrieved_chunks=retrieved_chunks,
        max_chars=max_context_chars
    )

    # Use recent chat history for follow-up references
    chat_history = st.session_state.get("chat_history", [])

    answer = generate_llm_answer(
        question=question,
        context=context,
        chat_history=chat_history
    )

    return {
        "question": question,
        "answer": answer,
        "context": context,
        "retrieved_chunks": retrieved_chunks
    }