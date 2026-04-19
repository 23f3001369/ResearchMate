# services/topic_extractor.py

from __future__ import annotations

import re
from typing import List


VALID_SECTION_KEYWORDS = {
    "abstract",
    "introduction",
    "related work",
    "related works",
    "literature review",
    "background",
    "methodology",
    "methods",
    "method",
    "materials and methods",
    "experimental setup",
    "experiments",
    "results",
    "discussion",
    "analysis",
    "conclusion",
    "conclusions",
    "future work",
    "limitations",
    "references",
    "outcomes",
}


NOISE_PATTERNS = [
    r"^page\s+\d+$",
    r"^page\s+\d+\s+of\s+\d+$",
    r"^\d+$",
    r"^minimum[: ]",
    r"^maximum[: ]",
    r"^mean[: ]",
    r"^std[: ]",
    r"^recall[: ]",
    r"^precision[: ]",
    r"^f-score[: ]",
    r"^specificity[: ]",
    r"^sensitivity[: ]",
    r"^accuracy[: ]",
    r"^confusion matrix",
    r"^kharagpur, india$",
    r"^medium[,!”\"]*$",
]


ROMAN_SECTION_RE = re.compile(
    r"^(?P<num>[IVXLC]+)\.?\s+(?P<title>[A-Z][A-Z \-&/()]+)$"
)

NUMERIC_SECTION_RE = re.compile(
    r"^(?P<num>\d+(\.\d+)*)\.?\s+(?P<title>[A-Z][A-Za-z0-9 \-&/()]+)$"
)

LETTER_SUBSECTION_RE = re.compile(
    r"^(?P<num>[A-Z])\.\s+(?P<title>[A-Z][A-Za-z0-9 \-&/()]+)$"
)


def clean_line(line: str) -> str:
    line = line.replace("ﬁ", "fi").replace("ﬂ", "fl")
    line = re.sub(r"\s+", " ", line).strip()
    return line.strip("-–—:;. ")


def is_noise(line: str) -> bool:
    low = clean_line(line).lower()

    if not low:
        return True

    for pattern in NOISE_PATTERNS:
        if re.match(pattern, low):
            return True

    if sum(ch.isdigit() for ch in low) >= 3:
        return True
    if "%" in low:
        return True
    if ":" in low and len(low.split()) <= 4:
        return True

    if "et al" in low:
        return True
    if "doi" in low:
        return True
    if "http" in low or "www." in low:
        return True
    if "downloaded on" in low or "authorized licensed use" in low:
        return True
    if "ieee" in low and len(low.split()) > 3:
        return True

    return False


def looks_like_plain_section_title(title: str) -> bool:
    low = clean_line(title).lower()

    if low in VALID_SECTION_KEYWORDS:
        return True

    strong_words = [
        "introduction", "method", "methodology", "results", "discussion",
        "conclusion", "references", "analysis", "experiment", "background",
        "related work", "literature review", "future work", "limitations",
        "outcomes",
    ]
    return any(word in low for word in strong_words)


def extract_heading_text(line: str) -> str | None:
    line = clean_line(line)
    if not line or is_noise(line):
        return None

    low = line.lower()

    if low in VALID_SECTION_KEYWORDS:
        return line.title()

    m = ROMAN_SECTION_RE.match(line)
    if m:
        title = clean_line(m.group("title"))
        if looks_like_plain_section_title(title):
            return f"{m.group('num')}. {title.title()}"

    m = NUMERIC_SECTION_RE.match(line)
    if m:
        title = clean_line(m.group("title"))
        if looks_like_plain_section_title(title):
            return f"{m.group('num')} {title.title()}"

    m = LETTER_SUBSECTION_RE.match(line)
    if m:
        title = clean_line(m.group("title"))
        allowed_subsections = {
            "dataset",
            "experimental setup",
            "results",
            "discussion",
            "conclusion",
            "performance analysis",
            "evaluation metrics",
        }
        if title.lower() in allowed_subsections:
            return f"{m.group('num')}. {title.title()}"

    if line.isupper() and 1 <= len(line.split()) <= 4:
        if looks_like_plain_section_title(line):
            return line.title()

    return None


def extract_topics_from_text(text: str) -> List[str]:
    if not text:
        return ["Full Paper"]

    lines = text.splitlines()
    topics: List[str] = []

    for raw in lines:
        heading = extract_heading_text(raw)
        if heading:
            topics.append(heading)

    seen = set()
    final_topics = ["Full Paper"]
    for topic in topics:
        key = topic.lower()
        if key not in seen:
            final_topics.append(topic)
            seen.add(key)

    return final_topics


def normalize_for_match(s: str) -> str:
    s = clean_line(s).lower()
    s = re.sub(r"^[ivxlc]+\.\s*", "", s)
    s = re.sub(r"^\d+(\.\d+)*\s*", "", s)
    s = re.sub(r"^[a-z]\.\s*", "", s)
    return s.strip()


def get_topic_content(text: str, selected_topic: str) -> str:
    if not text:
        return ""

    if not selected_topic or selected_topic == "Full Paper":
        return text[:12000]

    lines = text.splitlines()
    target = normalize_for_match(selected_topic)

    start_idx = None
    for i, raw in enumerate(lines):
        heading = extract_heading_text(raw)
        if heading and normalize_for_match(heading) == target:
            start_idx = i
            break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        next_heading = extract_heading_text(lines[j])
        if next_heading:
            end_idx = j
            break

    section_text = "\n".join(lines[start_idx:end_idx]).strip()
    return section_text[:12000] if section_text else ""