import requests


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
OPENALEX_AUTHORS_URL = "https://api.openalex.org/authors"


def _reconstruct_abstract(inverted_index):
    word_positions = []

    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    word_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in word_positions)


def _format_openalex_results(results):
    papers = []

    for item in results:
        title = item.get("title", "No title")

        authorships = item.get("authorships", [])
        authors = ", ".join(
            author.get("author", {}).get("display_name", "")
            for author in authorships
            if author.get("author", {}).get("display_name")
        )

        abstract = "Abstract not available"
        if item.get("abstract_inverted_index"):
            abstract = _reconstruct_abstract(item["abstract_inverted_index"])

        year = item.get("publication_year", "N/A")

        url = ""
        primary_location = item.get("primary_location")
        if primary_location and primary_location.get("landing_page_url"):
            url = primary_location["landing_page_url"]
        elif item.get("id"):
            url = item["id"]

        papers.append({
            "title": title,
            "authors": authors if authors else "N/A",
            "year": year,
            "abstract": abstract,
            "url": url
        })

    return papers


def _search_author_id(author_name):
    if not author_name or not author_name.strip():
        return None

    params = {
        "search": author_name.strip(),
        "per-page": 1
    }

    response = requests.get(OPENALEX_AUTHORS_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    return results[0].get("id")


def search_papers(topic="", author_name="", limit=10):
    """
    Supports:
    - topic only
    - author only
    - topic + author
    """
    topic = (topic or "").strip()
    author_name = (author_name or "").strip()

    if not topic and not author_name:
        return []

    params = {
        "per-page": limit
    }

    filters = []

    # Topic search
    if topic:
        params["search"] = topic

    # Author filter
    if author_name:
        author_id = _search_author_id(author_name)
        if not author_id:
            return []
        filters.append(f"author.id:{author_id}")

    if filters:
        params["filter"] = ",".join(filters)

    response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    return _format_openalex_results(results)


# Optional backward-compatible wrappers
def search_papers_by_topic(topic, limit=10):
    return search_papers(topic=topic, author_name="", limit=limit)


def search_papers_by_author(author_name, limit=10):
    return search_papers(topic="", author_name=author_name, limit=limit)