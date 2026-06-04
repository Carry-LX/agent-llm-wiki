"""
Search the LLM-WIKI by keywords and return matched nodes with full content.

Usage:
    python tools/search_wiki.py "keyword1 keyword2 keyword3"
    python tools/search_wiki.py --keywords "keyword1 keyword2" --top 3

The script searches two node indexes:
  1. wiki_manual/manifest.json — 26 manually curated nodes (title + description + keywords)
  2. app/wiki_data.json — 119 evidence/topic nodes (title + text/description)

For each matched node, it reads the full content from the source file and collects
associated image paths. Output is JSON to stdout.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

MANIFEST_JS_PATH = ROOT / "wiki_manual" / "manifest.js"
WIKI_DATA_PATH = ROOT / "app" / "wiki_data.json"
WIKI_GENERATED_DIR = ROOT / "wiki_generated"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_manifest_js() -> dict:
    """Parse manifest.js — a JS file that sets window.__MANUAL_MANIFEST__ = {...};"""
    raw = _read_file(MANIFEST_JS_PATH)
    if raw is None:
        return {"nodes": [], "edges": []}

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return {"nodes": [], "edges": []}
    json_str = raw[start:end + 1]

    # Remove JavaScript trailing commas before } or ]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"nodes": [], "edges": []}


def _read_file(path: Path) -> Optional[str]:
    """Read a file, return contents or None."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _strip_html(html: str) -> str:
    """Crude HTML → plain text."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#?\w+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_images_from_html(html: str) -> list[dict]:
    """Extract <img> tags from HTML, return [{path, alt}]."""
    images: list[dict] = []
    for m in re.finditer(r'<img[^>]*src="([^"]+)"[^>]*(?:alt="([^"]*)")?[^>]*>', html, re.IGNORECASE):
        path = m.group(1)
        alt = m.group(2) or ""
        # Resolve relative paths (images/xxx → wiki_html/images/xxx)
        if path.startswith("images/"):
            path = "wiki_html/" + path
        images.append({"path": path, "alt": alt.strip()})
    return images


def _extract_images_from_md(md: str) -> list[dict]:
    """Extract ![alt](path) from markdown."""
    images: list[dict] = []
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", md):
        images.append({"path": m.group(2), "alt": m.group(1).strip()})
    return images


def _score_text(text: str, keywords: list[str]) -> tuple[int, list[str]]:
    """Count keyword occurrences in text. Returns (score, [matched_keywords])."""
    if not text:
        return 0, []
    text_lower = text.lower()
    score = 0
    matched: list[str] = []
    for kw in keywords:
        kw_lower = kw.lower()
        count = text_lower.count(kw_lower)
        if count > 0:
            score += count
            matched.append(kw)
    return score, matched


# ---------------------------------------------------------------------------
# node-level content readers
# ---------------------------------------------------------------------------

def _read_manual_node_content(node: dict) -> tuple[str, list[dict]]:
    """Read full content and images for a manual node (from manifest.json)."""
    md_path = node.get("md_path", "")
    if not md_path:
        return "", []

    filepath = ROOT / md_path
    raw = _read_file(filepath)
    if raw is None:
        return "", []

    images: list[dict] = []

    # Direct image_path from manifest
    direct_img = node.get("image_path", "")
    if direct_img:
        images.append({"path": direct_img, "alt": node.get("title", "")})

    if md_path.endswith(".html"):
        content = _strip_html(raw)
        images.extend(_extract_images_from_html(raw))
    else:
        content = raw
        images.extend(_extract_images_from_md(raw))

    # Deduplicate images
    seen: set[str] = set()
    deduped: list[dict] = []
    for img in images:
        if img["path"] not in seen:
            seen.add(img["path"])
            deduped.append(img)

    return content, deduped


def _read_evidence_node_content(node: dict) -> tuple[str, list[dict]]:
    """Read content for an evidence node (from wiki_data.json)."""
    text = node.get("text", "") or ""
    images: list[dict] = []
    img_path = node.get("image_path", "")
    if img_path:
        images.append({"path": img_path, "alt": node.get("title", "")})
    return text, images


def _read_topic_node_content(node: dict) -> tuple[str, list[dict]]:
    """Read content for a topic node — find corresponding wiki_generated page."""
    title = node.get("title", "")
    # Try to find a wiki_generated page matching the topic title
    # Topic titles are like "RAG 与检索增强", wiki_generated filenames are like "RAG_与检索增强.md"
    candidates = list(WIKI_GENERATED_DIR.glob("*.md"))
    best: Optional[Path] = None
    for cand in candidates:
        if title in cand.stem or cand.stem in title:
            best = cand
            break
    if best is None and candidates:
        # Fuzzy: pick the one with most character overlap
        title_chars = set(title.replace(" ", ""))
        scored = []
        for cand in candidates:
            stem_chars = set(cand.stem.replace("_", "").replace(" ", ""))
            overlap = len(title_chars & stem_chars)
            scored.append((overlap, cand))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored and scored[0][0] > 2:
            best = scored[0][1]

    if best:
        raw = _read_file(best)
        if raw:
            images = _extract_images_from_md(raw)
            return raw, images

    # Fallback: use description as content
    return node.get("description", "") or "", []


# ---------------------------------------------------------------------------
# search engines
# ---------------------------------------------------------------------------

def search_manifest(keywords: list[str]) -> list[dict]:
    """Search manifest.js manual nodes."""
    manifest = _load_manifest_js()
    results: list[dict] = []

    for node in manifest.get("nodes", []):
        total_score = 0
        matched_on: dict[str, bool] = {}
        matched_kws: set[str] = set()

        # Title (weight ×3)
        s, m = _score_text(node.get("title", ""), keywords)
        if s > 0:
            total_score += s * 3
            matched_on["title"] = True
            matched_kws.update(m)

        # Description (weight ×2)
        s, m = _score_text(node.get("description", ""), keywords)
        if s > 0:
            total_score += s * 2
            matched_on["description"] = True
            matched_kws.update(m)

        # Keywords (weight ×2 — user-tagged, high signal)
        kw_str = " ".join(node.get("keywords", []))
        s, m = _score_text(kw_str, keywords)
        if s > 0:
            total_score += s * 2
            matched_on["keywords"] = True
            matched_kws.update(m)

        if total_score > 0:
            content, images = _read_manual_node_content(node)
            results.append({
                "node_id": node.get("id", ""),
                "type": node.get("type", "manual_note"),
                "title": node.get("title", ""),
                "description": node.get("description", ""),
                "keywords": node.get("keywords", []),
                "score": total_score,
                "matched_on": matched_on,
                "matched_keywords": sorted(matched_kws),
                "source_file": node.get("md_path", ""),
                "source_url": node.get("source_url", ""),
                "content": content,
                "images": images,
            })

    return results


def search_wiki_data(keywords: list[str]) -> list[dict]:
    """Search wiki_data.json evidence and topic nodes."""
    wiki_data = _load_json(WIKI_DATA_PATH)
    results: list[dict] = []

    for node in wiki_data.get("graph", {}).get("nodes", []):
        node_type = node.get("type", "")
        total_score = 0
        matched_on: dict[str, bool] = {}
        matched_kws: set[str] = set()

        if node_type == "evidence":
            # Title (weight ×3)
            s, m = _score_text(node.get("title", ""), keywords)
            if s > 0:
                total_score += s * 3
                matched_on["title"] = True
                matched_kws.update(m)
            # Text (weight ×1)
            s, m = _score_text(node.get("text", ""), keywords)
            if s > 0:
                total_score += s * 1
                matched_on["text"] = True
                matched_kws.update(m)
            # evidence_label (weight ×2)
            s, m = _score_text(node.get("evidence_label", ""), keywords)
            if s > 0:
                total_score += s * 2
                matched_on["label"] = True
                matched_kws.update(m)

            if total_score > 0:
                content, images = _read_evidence_node_content(node)
                results.append({
                    "node_id": node.get("id", ""),
                    "type": "evidence",
                    "title": node.get("evidence_label") or node.get("title", ""),
                    "description": "",
                    "keywords": [],
                    "score": total_score,
                    "matched_on": matched_on,
                    "matched_keywords": sorted(matched_kws),
                    "source_file": "",  # evidence nodes have inline text, no separate file
                    "source_url": node.get("source_url", ""),
                    "page_title": node.get("page_title", ""),
                    "content": content,
                    "images": images,
                })

        elif node_type == "topic":
            # Title (weight ×3)
            s, m = _score_text(node.get("title", ""), keywords)
            if s > 0:
                total_score += s * 3
                matched_on["title"] = True
                matched_kws.update(m)
            # Description (weight ×2)
            s, m = _score_text(node.get("description", ""), keywords)
            if s > 0:
                total_score += s * 2
                matched_on["description"] = True
                matched_kws.update(m)

            if total_score > 0:
                content, images = _read_topic_node_content(node)
                results.append({
                    "node_id": node.get("id", ""),
                    "type": "topic",
                    "title": node.get("title", ""),
                    "description": node.get("description", ""),
                    "keywords": [],
                    "score": total_score,
                    "matched_on": matched_on,
                    "matched_keywords": sorted(matched_kws),
                    "source_file": "",
                    "source_url": "",
                    "content": content,
                    "images": images,
                })

    return results


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def search(keywords: list[str], top: int = 3) -> list[dict]:
    """Run search across all node indexes, return top results with full content."""
    manual_results = search_manifest(keywords)
    data_results = search_wiki_data(keywords)

    all_results = manual_results + data_results
    all_results.sort(key=lambda r: r["score"], reverse=True)

    return all_results[:top]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Search LLM-WIKI by keywords")
    parser.add_argument(
        "keywords",
        nargs="*",
        help="Keywords to search for (space-separated). E.g.: Agent 死循环 兜底 deadloop",
    )
    parser.add_argument(
        "--keywords", "-k",
        dest="keywords_str",
        help="Comma or space-separated keywords (alternative to positional).",
    )
    parser.add_argument(
        "--file", "-f",
        help="Read keywords from a UTF-8 text file (one per line, or space-separated). "
             "Use this to avoid Windows command-line encoding issues with Chinese.",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=3,
        help="Max results to return (default: 3).",
    )
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="Only return node metadata, skip reading full content.",
    )

    args = parser.parse_args()

    # Collect keywords
    kw_list: list[str] = list(args.keywords)

    if args.keywords_str:
        extra = re.split(r"[,\s]+", args.keywords_str.strip())
        kw_list.extend(k for k in extra if k)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            file_text = f.read()
        extra = re.split(r"[,\n\s]+", file_text.strip())
        kw_list.extend(k for k in extra if k)

    if not kw_list:
        print(json.dumps({"error": "No keywords provided. Usage: python search_wiki.py keyword1 keyword2 ..."}, ensure_ascii=False))
        sys.exit(1)

    results = search(kw_list, top=args.top)

    if args.no_content:
        for r in results:
            r.pop("content", None)
            r.pop("images", None)

    output = {
        "query": " ".join(kw_list),
        "total_hits": len(results),
        "results": results,
    }
    # Use ASCII-safe encoding to avoid Windows console GBK issues
    json_text = json.dumps(output, ensure_ascii=False, indent=2)
    try:
        print(json_text)
    except UnicodeEncodeError:
        # Fallback: encode non-ASCII as \\uXXXX
        print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
