# services/llm_answer.py

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return Groq(api_key=api_key)


def trim_chat_history(
    chat_history: Optional[List[Dict[str, Any]]],
    max_messages: int = 6
) -> List[Dict[str, str]]:
    """
    Keep only the most recent chat messages and only user/assistant roles.
    """
    if not chat_history:
        return []

    cleaned = []
    for msg in chat_history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in {"user", "assistant"} and content:
            cleaned.append({
                "role": role,
                "content": content
            })

    return cleaned[-max_messages:]


def build_messages(
    question: str,
    context: str,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, str]]:
    """
    Build messages for conversational RAG.
    """
    system_prompt = (
        "You are a helpful AI research paper assistant for students.\n"
        "Use previous chat messages for conversational continuity.\n"
        "Use the provided paper context for factual grounding.\n"
        "If the user asks follow-up questions like 'that', 'it', 'they', "
        "'this model', 'the second one', or 'which one performed better', "
        "resolve them using the recent chat history.\n"
        "Answer naturally like a chatbot, not like a template.\n"
        "Use only the paper context for factual claims.\n"
        "If the answer is not clearly present in the context, say: "
        "'I could not find that clearly in the uploaded paper.'\n"
        "Do not invent facts.\n"
        "Keep answers clear, student-friendly, and concise unless the user asks for detail."
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]

    # Add recent conversation memory
    recent_history = trim_chat_history(chat_history, max_messages=6)
    messages.extend(recent_history)

    # Add grounded current request
    user_prompt = f"""
Paper Context:
{context}

Current User Question:
{question}

Instructions:
- Use the recent conversation to understand follow-up references.
- Use only the paper context for facts.
- If this is a summary/explanation question, synthesize naturally.
- If this is a factual question, answer directly.
- If the answer is unclear from context, say so honestly.
"""

    messages.append({"role": "user", "content": user_prompt.strip()})
    return messages


def generate_llm_answer(
    question: str,
    context: str,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 700,
) -> str:
    """
    Generate an answer from Groq using conversational history + retrieved context.
    """
    if not context or not context.strip():
        return "I could not find enough relevant context in the uploaded paper."

    client = get_groq_client()

    messages = build_messages(
        question=question,
        context=context,
        chat_history=chat_history
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()