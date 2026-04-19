# services/summarizer.py

from __future__ import annotations

import re
from typing import List, Dict, Any


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple regex.
    """
    if not text or not text.strip():
        return []

    text = text.replace("\n", " ").strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def clean_sentence(sentence: str) -> str:
    """
    Clean sentence spacing.
    """
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence


def score_sentence(sentence: str) -> int:
    """
    Heuristic scoring for extractive summarization.
    Higher score for sentences that look informative.
    """
    score = 0
    s = sentence.lower()

    keywords = [
        "propose", "proposed", "present", "presented", "introduce", "introduced",
        "method", "approach", "model", "framework", "results", "experiment",
        "evaluation", "conclusion", "dataset", "performance", "accuracy",
        "finding", "findings", "analysis", "objective", "aim", "paper",
        "study", "research", "novel", "improve", "improvement", "outperform",
        "limitation", "future work"
    ]

    for word in keywords:
        if word in s:
            score += 2

    word_count = len(sentence.split())

    if 12 <= word_count <= 35:
        score += 3
    elif 8 <= word_count <= 50:
        score += 2

    if any(char.isdigit() for char in sentence):
        score += 1

    if sentence[:1].isupper():
        score += 1

    return score


def rank_sentences(sentences: List[str]) -> List[Dict[str, Any]]:
    """
    Rank sentences by heuristic score.
    """
    ranked = []
    for idx, sentence in enumerate(sentences):
        cleaned = clean_sentence(sentence)
        if cleaned:
            ranked.append({
                "index": idx,
                "sentence": cleaned,
                "score": score_sentence(cleaned)
            })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def summarize_text_short(text: str, max_sentences: int = 3) -> str:
    """
    Generate a short extractive summary.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return "No summary could be generated from the uploaded paper."

    ranked = rank_sentences(sentences)
    top = ranked[:max_sentences]
    top_sorted = sorted(top, key=lambda x: x["index"])

    summary = " ".join(item["sentence"] for item in top_sorted)
    return summary if summary else "No summary could be generated."


def summarize_text_detailed(text: str, max_sentences: int = 6) -> str:
    """
    Generate a longer extractive summary.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return "No detailed summary could be generated from the uploaded paper."

    ranked = rank_sentences(sentences)
    top = ranked[:max_sentences]
    top_sorted = sorted(top, key=lambda x: x["index"])

    summary = " ".join(item["sentence"] for item in top_sorted)
    return summary if summary else "No detailed summary could be generated."


def summarize_text_beginner_friendly(text: str, max_sentences: int = 4) -> str:
    """
    Generate a simplified beginner-friendly summary.
    This is still heuristic, not true LLM rewriting.
    """
    short_summary = summarize_text_short(text, max_sentences=max_sentences)

    if short_summary.startswith("No summary"):
        return short_summary

    return (
        "In simple terms, this paper discusses the following:\n\n"
        f"{short_summary}\n\n"
        "This means the authors are trying to solve a problem, explain their method, "
        "and show the results they achieved."
    )


def extract_key_sections(text: str) -> Dict[str, str]:
    """
    Very lightweight section extraction using keyword matching.
    Falls back gracefully if sections are not clearly found.
    """
    lower_text = text.lower()

    section_keywords = {
        "abstract": ["abstract"],
        "introduction": ["introduction"],
        "methodology": ["method", "methodology", "approach", "framework"],
        "results": ["results", "experiments", "evaluation"],
        "conclusion": ["conclusion", "conclusions", "future work"]
    }

    lines = text.splitlines()
    sections = {
        "abstract": "",
        "introduction": "",
        "methodology": "",
        "results": "",
        "conclusion": ""
    }

    current_section = None

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        line_lower = clean.lower()

        matched_section = None
        for section_name, keywords in section_keywords.items():
            if any(
                line_lower == kw or line_lower.startswith(kw + " ")
                for kw in keywords
            ):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            continue

        if current_section:
            sections[current_section] += clean + " "

    for key in sections:
        sections[key] = sections[key].strip()

    return sections


def generate_paper_summaries(text: str) -> Dict[str, Any]:
    """
    Generate all summary variants and rough section summaries.
    """
    sections = extract_key_sections(text)

    short_summary = summarize_text_short(text, max_sentences=3)
    detailed_summary = summarize_text_detailed(text, max_sentences=6)
    beginner_summary = summarize_text_beginner_friendly(text, max_sentences=4)

    methodology_summary = (
        summarize_text_short(sections["methodology"], max_sentences=2)
        if sections["methodology"] else "Methodology section not clearly identified."
    )

    results_summary = (
        summarize_text_short(sections["results"], max_sentences=2)
        if sections["results"] else "Results section not clearly identified."
    )

    conclusion_summary = (
        summarize_text_short(sections["conclusion"], max_sentences=2)
        if sections["conclusion"] else "Conclusion section not clearly identified."
    )

    return {
        "short_summary": short_summary,
        "detailed_summary": detailed_summary,
        "beginner_friendly_summary": beginner_summary,
        "methodology_summary": methodology_summary,
        "results_summary": results_summary,
        "conclusion_summary": conclusion_summary,
        "sections": sections
    }