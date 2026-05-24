from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = "Agent 记忆应该如何分层管理"
TOP_K = 8
SEARCH_CLAIMS_FIRST = True
STOPWORDS = {"agent", "llm", "应该", "如何", "什么", "怎么", "一个", "这个", "那个"}

CLAIMS_PATH = ROOT / "data" / "claims.jsonl"
SEARCH_CORPUS_PATH = ROOT / "data" / "search_corpus.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tokenize(text: str) -> list[str]:
    chunks = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}", text.lower())
    tokens: list[str] = []
    for chunk in chunks:
        if re.fullmatch(r"[\u4e00-\u9fff]{2,}", chunk):
            tokens.extend(chunk[i:i + 1] for i in range(len(chunk)))
            tokens.extend(chunk[i:i + 2] for i in range(max(1, len(chunk) - 1)))
        else:
            tokens.append(chunk)
    return [token for token in tokens if token not in STOPWORDS]


def score_text(query_tokens: set[str], text: str) -> int:
    tokens = tokenize(text)
    if not tokens:
        return 0
    token_set = set(tokens)
    overlap = query_tokens & token_set
    capped_frequency = sum(min(tokens.count(token), 3) for token in overlap)
    return len(overlap) * 20 + capped_frequency


def search_claims(query: str) -> list[tuple[int, dict]]:
    query_tokens = set(tokenize(query))
    results: list[tuple[int, dict]] = []
    for row in read_jsonl(CLAIMS_PATH):
        text = " ".join([
            row.get("claim_text", ""),
            row.get("topic_title", ""),
            " ".join(row.get("evidence_ids", [])),
        ])
        score = score_text(query_tokens, text)
        if score:
            results.append((score, row))
    return sorted(results, key=lambda item: item[0], reverse=True)


def search_corpus(query: str) -> list[tuple[int, dict]]:
    query_tokens = set(tokenize(query))
    results: list[tuple[int, dict]] = []
    for row in read_jsonl(SEARCH_CORPUS_PATH):
        text = " ".join([
            row.get("evidence_label", ""),
            row.get("topic_title", ""),
            row.get("page_title", ""),
            row.get("text", ""),
        ])
        score = score_text(query_tokens, text)
        if score:
            results.append((score, row))
    return sorted(results, key=lambda item: item[0], reverse=True)


def main() -> None:
    if SEARCH_CLAIMS_FIRST:
        claim_results = search_claims(QUERY)[:TOP_K]
        print(f"# Claim results for: {QUERY}")
        for score, row in claim_results:
            evidence_ids = ", ".join(row.get("evidence_ids", []))
            sources = ", ".join(row.get("source_urls", []))
            print(f"\nscore={score} | {row.get('topic_title')} | {evidence_ids}")
            print(row.get("claim_text", ""))
            if sources:
                print(f"source={sources}")

    corpus_results = search_corpus(QUERY)[:TOP_K]
    print(f"\n# Corpus results for: {QUERY}")
    for score, row in corpus_results:
        print(f"\nscore={score} | {row.get('topic_title')} | {row.get('asset_id')}")
        print(row.get("evidence_label", ""))
        print((row.get("text") or "")[:260].replace("\n", " "))
        if row.get("source_url"):
            print(f"source={row.get('source_url')}")


if __name__ == "__main__":
    main()
