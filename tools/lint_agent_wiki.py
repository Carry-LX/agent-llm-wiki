from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "wiki_health_report.md"
FAIL_ON_ERRORS = False

REQUIRED_PATHS = [
    "README.md",
    "SCHEMA.md",
    "AGENTS.md",
    "log.md",
    "raw/assets_enriched.jsonl",
    "raw/onenote_pages.jsonl",
    "data/search_corpus.jsonl",
    "data/graph_nodes.jsonl",
    "data/graph_edges.jsonl",
    "data/topics.json",
    "wiki_generated/index.md",
    "wiki_manual",
    "app/index.html",
]

SUSPICIOUS_TEXT_PATTERNS = [
    "暴万",
    "余弱",
    "履盖",
    "氵",
    "扌",
    "宀",
    "�",
    "AINE",
    "Witte Ata",
]


def read_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    rows: list[dict] = []
    if not path.exists():
        return rows, [f"missing file: {path}"]
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(ROOT)}:{line_no}: {exc}")
    return rows, errors


def image_hash_from_path(image_path: str) -> str:
    name = Path(image_path or "").stem
    match = re.search(r"_([0-9a-f]{12})$", name)
    return match.group(1) if match else ""


def markdown_table(rows: list[tuple[str, int]]) -> list[str]:
    if not rows:
        return ["无"]
    lines = ["| 项 | 数量 |", "|---|---:|"]
    for name, count in rows:
        label = name if name else "<missing>"
        lines.append(f"| {label} | {count} |")
    return lines


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"缺少必需路径：`{rel}`")

    nodes, node_errors = read_jsonl(ROOT / "data" / "graph_nodes.jsonl")
    edges, edge_errors = read_jsonl(ROOT / "data" / "graph_edges.jsonl")
    corpus, corpus_errors = read_jsonl(ROOT / "data" / "search_corpus.jsonl")
    assets, asset_errors = read_jsonl(ROOT / "raw" / "assets_enriched.jsonl")
    claims, claim_errors = read_jsonl(ROOT / "data" / "claims.jsonl")
    errors.extend(node_errors + edge_errors + corpus_errors + asset_errors)
    if claim_errors and not (ROOT / "data" / "claims.jsonl").exists():
        warnings.append("缺少 `data/claims.jsonl`，自动摘要仍会过度依赖 OCR 或搜索语料。")
    else:
        errors.extend(claim_errors)

    node_ids = {row.get("id") for row in nodes if row.get("id")}
    missing_edge_endpoints = [
        edge for edge in edges
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids
    ]
    if missing_edge_endpoints:
        errors.append(f"图谱存在 {len(missing_edge_endpoints)} 条边引用了不存在的节点。")

    degree = defaultdict(int)
    for edge in edges:
        degree[edge.get("source")] += 1
        degree[edge.get("target")] += 1
    zero_degree_nodes = [node for node in nodes if degree[node.get("id")] == 0]
    if zero_degree_nodes:
        warnings.append(f"存在 {len(zero_degree_nodes)} 个孤立节点。")

    page_relation_map: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        page_relation_map[edge.get("source")].add(edge.get("relation", ""))
        page_relation_map[edge.get("target")].add(edge.get("relation", ""))
    weak_pages = []
    for node in nodes:
        if node.get("type") != "page":
            continue
        relations = page_relation_map.get(node.get("id"), set())
        semantic_relations = relations - {"contains_page", ""}
        if not semantic_relations:
            weak_pages.append(node)
    if weak_pages:
        warnings.append(f"存在 {len(weak_pages)} 个页面节点缺少语义关系。")

    source_url_missing = sum(1 for row in corpus if not row.get("source_url"))
    onenote_source = sum(1 for row in corpus if str(row.get("source_url", "")).startswith("onenote:"))
    if source_url_missing:
        warnings.append(f"`data/search_corpus.jsonl` 中 {source_url_missing} 条记录缺少 source_url。")
    if onenote_source:
        warnings.append(f"`data/search_corpus.jsonl` 中 {onenote_source} 条记录只有 OneNote 内部来源。")

    hash_groups: dict[str, list[str]] = defaultdict(list)
    for row in corpus:
        image_hash = image_hash_from_path(row.get("image_path", ""))
        if image_hash:
            hash_groups[image_hash].append(row.get("asset_id", ""))
    duplicate_hash_groups = {k: v for k, v in hash_groups.items() if len(set(v)) > 1}
    if duplicate_hash_groups:
        warnings.append(f"存在 {len(duplicate_hash_groups)} 组图片哈希被多个 asset_id 引用，需要确认去重语义。")

    best_text_source_counts = Counter(row.get("best_text_source", "<missing>") for row in assets)
    label_title_missing = sum(1 for row in assets if not row.get("label_title"))
    label_summary_missing = sum(1 for row in assets if not row.get("label_summary"))
    if label_title_missing:
        warnings.append(f"`raw/assets_enriched.jsonl` 中 {label_title_missing} 条记录缺少 label_title。")
    if label_summary_missing:
        warnings.append(f"`raw/assets_enriched.jsonl` 中 {label_summary_missing} 条记录缺少 label_summary。")

    suspicious_rows = []
    for row in corpus:
        text = row.get("text") or ""
        hits = [pattern for pattern in SUSPICIOUS_TEXT_PATTERNS if pattern in text]
        if hits:
            suspicious_rows.append((row.get("asset_id", ""), row.get("topic_title", ""), ",".join(hits)))
    if suspicious_rows:
        warnings.append(f"搜索语料中 {len(suspicious_rows)} 条记录命中疑似 OCR 噪声模式。")

    claim_source_missing = sum(1 for row in claims if not row.get("source_urls"))
    claim_evidence_missing = sum(1 for row in claims if not row.get("evidence_ids"))
    claim_type_counts = Counter(row.get("claim_type", "<missing>") for row in claims)
    claim_confidence_counts = Counter(row.get("confidence", "<missing>") for row in claims)
    if claims and claim_source_missing:
        warnings.append(f"`data/claims.jsonl` 中 {claim_source_missing} 条 claim 缺少 source_urls。")
    if claims and claim_evidence_missing:
        errors.append(f"`data/claims.jsonl` 中 {claim_evidence_missing} 条 claim 缺少 evidence_ids。")

    node_type_counts = Counter(row.get("type", "<missing>") for row in nodes)
    edge_relation_counts = Counter(row.get("relation", "<missing>") for row in edges)

    notes.append(f"节点：{len(nodes)}；边：{len(edges)}；搜索语料：{len(corpus)}；资产：{len(assets)}；claims：{len(claims)}。")
    notes.append(f"报告生成时间：{datetime.now(timezone.utc).isoformat()}。")

    lines: list[str] = []
    lines.append("# LLM-WIKI 健康检查报告")
    lines.append("")
    lines.extend(f"- {note}" for note in notes)
    lines.append("")
    lines.append("## 结论")
    if errors:
        lines.append(f"- ERROR：{len(errors)} 项，需要优先修复。")
    else:
        lines.append("- ERROR：0 项。")
    if warnings:
        lines.append(f"- WARN：{len(warnings)} 项，建议纳入后续清理。")
    else:
        lines.append("- WARN：0 项。")
    lines.append("")
    lines.append("## Errors")
    lines.extend(f"- {item}" for item in errors) if errors else lines.append("- 无")
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- 无")
    lines.append("")
    lines.append("## 节点类型")
    lines.extend(markdown_table(node_type_counts.most_common()))
    lines.append("")
    lines.append("## 边关系")
    lines.extend(markdown_table(edge_relation_counts.most_common()))
    lines.append("")
    lines.append("## best_text_source 分布")
    lines.extend(markdown_table(best_text_source_counts.most_common()))
    lines.append("")
    lines.append("## claim 类型")
    lines.extend(markdown_table(claim_type_counts.most_common()))
    lines.append("")
    lines.append("## claim 置信度")
    lines.extend(markdown_table(claim_confidence_counts.most_common()))
    lines.append("")
    lines.append("## OCR 噪声样例")
    if suspicious_rows:
        lines.append("| asset_id | topic | 命中模式 |")
        lines.append("|---|---|---|")
        for asset_id, topic, hits in suspicious_rows[:30]:
            lines.append(f"| {asset_id} | {topic} | {hits} |")
    else:
        lines.append("- 未命中疑似 OCR 噪声模式。")
    lines.append("")
    lines.append("## 重复图片哈希样例")
    if duplicate_hash_groups:
        lines.append("| image_hash | asset_ids |")
        lines.append("|---|---|")
        for image_hash, asset_ids in list(duplicate_hash_groups.items())[:30]:
            lines.append(f"| {image_hash} | {', '.join(sorted(set(asset_ids)))} |")
    else:
        lines.append("- 未发现重复图片哈希组。")
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    print(f"wrote report to {REPORT_PATH}")
    print(f"errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors and FAIL_ON_ERRORS else 0


if __name__ == "__main__":
    raise SystemExit(main())
