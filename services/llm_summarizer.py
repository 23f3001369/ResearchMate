# services/llm_summarizer.py

from __future__ import annotations

import os
from typing import Dict, Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return Groq(api_key=api_key)


def build_summary_prompt(text: str, topic_name: str = "Full Paper") -> str:
    return f"""
You are a helpful AI research paper assistant for students.

Summarize ONLY the selected topic/section below.

Selected Topic:
{topic_name}

Return output in exactly this format:

Summary:
Write one clear summary of the selected topic/section in 1–3 paragraphs.

Key Points:
- Bullet point 1
- Bullet point 2
- Bullet point 3
- Bullet point 4
- Bullet point 5

Rules:
- Focus only on the selected topic/section.
- If the selected topic is "Full Paper", summarize the overall paper.
- Do not drift into a generic whole-paper summary when a specific topic is selected.
- Do not invent facts.
- Keep the summary concise and informative.
- Do not create extra sections.

Selected Topic Text:
{text}
""".strip()


def generate_summary_from_text(
    text: str,
    topic_name: str = "Full Paper",
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 700
) -> str:
    if not text or not text.strip():
        return "No content available for summarization."

    client = get_groq_client()
    prompt = build_summary_prompt(text, topic_name=topic_name)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You summarize research papers clearly and accurately for students. "
                    "When a specific topic is selected, focus only on that topic."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content.strip()


def generate_summary_sections(
    text: str,
    topic_name: str = "Full Paper",
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    summary_text = generate_summary_from_text(
        text=text,
        topic_name=topic_name,
        model=model
    )
    return {
        "full_summary": summary_text
    }