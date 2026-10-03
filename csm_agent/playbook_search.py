"""Playbook search: exact key match first, keyword search as a fallback.

Keys are the same names the risk and opportunity rules return (e.g.
"download_drop"), so the agent can go straight from a reason to the matching
advice. Free-text questions ("champion left?") fall back to keyword search.
"""

import re

MAX_KEYWORD_RESULTS = 2

# Common words that should not count as a keyword match.
_STOPWORDS = {
    "the", "and", "for", "what", "when", "how", "should", "with", "our",
    "they", "their", "this", "that", "from", "about", "does", "can", "you",
    "who", "has", "have", "are", "was", "were", "doing", "account",
}


def search_sections(query: str, sections: list[dict]) -> dict:
    """Returns {"match_type": "key" | "keyword" | "none", "sections": [...]}."""
    tokens = [t for t in re.split(r"[\s,]+", query.lower()) if t]

    # 1. Exact key match (one or more keys, e.g. "download_drop, renewal_soon")
    by_key = [s for s in sections if any(t in s["keys"] for t in tokens)]
    if by_key:
        return {"match_type": "key", "sections": _public(by_key)}

    # 2. Keyword fallback: a word in the title counts double
    words = [w for w in re.findall(r"[a-z]+", query.lower())
             if len(w) >= 3 and w not in _STOPWORDS]
    scored = []
    for section in sections:
        title, content = section["title"].lower(), section["content"].lower()
        score = sum(2 * (w in title) + (w in content) for w in words)
        if score:
            scored.append((score, section))
    scored.sort(key=lambda pair: pair[0], reverse=True)  # stable: ties keep file order
    if scored:
        top = [section for _, section in scored[:MAX_KEYWORD_RESULTS]]
        return {"match_type": "keyword", "sections": _public(top)}

    return {"match_type": "none", "sections": []}


def _public(sections: list[dict]) -> list[dict]:
    return [{"title": s["title"], "content": s["content"]} for s in sections]
