from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH_CORPUS_PATH = ROOT / "data" / "search_corpus.jsonl"
ENRICHED_ASSETS_PATH = ROOT / "raw" / "assets_enriched.jsonl"
CLAIM_OVERRIDES_PATH = ROOT / "data" / "claim_overrides.json"
CLAIMS_PATH = ROOT / "data" / "claims.jsonl"
MAX_TEXT_CHARS = 220


WORKFLOW_WORDS = ("流程", "步骤", "闭环", "链路", "Pipeline", "Plan", "Execute", "Observe")
RISK_WORDS = ("风险", "失败", "幻觉", "权限", "安全", "容错", "危险", "校验", "拒答")
METRIC_WORDS = ("评估", "指标", "Recall", "Precision", "Faithfulness", "RAGAS", "测试集")
COMPARISON_WORDS = ("对比", "区别", "取舍", "优劣", "GraphRAG", "LightRAG", "PathRAG")
DEFINITION_WORDS = ("是什么", "定义", "本质", "原理", "机制")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} is not valid JSONL: {exc}") from exc
    return rows


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace(" | ", " ")
    return text


def first_useful_span(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    pieces = re.split(r"(?<=[。！？!?])\s+|[。\n]", text)
    candidates = [p.strip(" ：:;；,，|") for p in pieces if len(p.strip()) >= 18]
    if not candidates:
        return text[:MAX_TEXT_CHARS].strip()
    chosen = candidates[0]
    if len(chosen) < 60 and len(candidates) > 1:
        chosen = f"{chosen}。{candidates[1]}"
    return chosen[:MAX_TEXT_CHARS].strip()


def classify_claim_type(label: str, text: str) -> str:
    blob = f"{label} {text}"
    if any(word in blob for word in METRIC_WORDS):
        return "metric"
    if any(word in blob for word in RISK_WORDS):
        return "risk"
    if any(word in blob for word in COMPARISON_WORDS):
        return "comparison"
    if any(word in blob for word in WORKFLOW_WORDS):
        return "workflow"
    if any(word in blob for word in DEFINITION_WORDS):
        return "definition"
    return "engineering_judgment"


def confidence_from_source(best_text_source: str, source_url: str) -> str:
    if best_text_source in {"codex_vision_model", "human_manual", "source_article_text"}:
        return "high" if source_url else "medium"
    if best_text_source in {"tesseract_chi_sim_eng", "onenote_ocr_cleaned"}:
        return "medium" if source_url else "low"
    return "low"


def stable_claim_id(asset_id: str, text: str) -> str:
    digest = hashlib.sha1(f"{asset_id}|{text}".encode("utf-8")).hexdigest()[:10]
    safe_asset = re.sub(r"[^A-Za-z0-9_]+", "_", asset_id)
    return f"claim_{safe_asset}_{digest}"


def main() -> None:
    corpus_rows = read_jsonl(SEARCH_CORPUS_PATH)
    assets = read_jsonl(ENRICHED_ASSETS_PATH)
    overrides = read_json(CLAIM_OVERRIDES_PATH)
    asset_by_id = {row.get("asset_id"): row for row in assets if row.get("asset_id")}

    claims_by_key: OrderedDict[str, dict] = OrderedDict()
    generated_at = datetime.now(timezone.utc).isoformat()

    for row in corpus_rows:
        asset_id = row.get("asset_id") or row.get("evidence_id")
        if not asset_id:
            continue

        asset = asset_by_id.get(asset_id, {})
        label = row.get("evidence_label") or asset.get("label_title") or asset_id
        source_url = row.get("source_url") or asset.get("source_url") or ""
        best_text_source = asset.get("best_text_source") or "search_corpus"
        text = row.get("text") or asset.get("best_text") or ""
        span = first_useful_span(text)
        if not span:
            continue

        if label and label not in span:
            claim_text = f"{label}：{span}"
        else:
            claim_text = span

        claim_id = stable_claim_id(asset_id, claim_text)
        key = f"{asset_id}|{claim_text}"
        if key in claims_by_key:
            continue

        claim = {
            "claim_id": claim_id,
            "claim_type": classify_claim_type(label, claim_text),
            "claim_text": claim_text,
            "topic_id": row.get("topic_id") or "",
            "topic_title": row.get("topic_title") or "",
            "evidence_ids": [asset_id],
            "source_urls": [source_url] if source_url else [],
            "image_paths": [row.get("image_path")] if row.get("image_path") else [],
            "page_titles": [row.get("page_title")] if row.get("page_title") else [],
            "confidence": confidence_from_source(best_text_source, source_url),
            "extraction_method": f"rule_seed_from_{best_text_source}",
            "status": "active",
            "generated_at": generated_at,
        }
        override = overrides.get(asset_id)
        if override:
            claim.update(override)
            claim["override_applied"] = True
            claim["override_source"] = str(CLAIM_OVERRIDES_PATH.relative_to(ROOT))
        claims_by_key[key] = claim

    write_jsonl(CLAIMS_PATH, list(claims_by_key.values()))
    print(f"wrote {len(claims_by_key)} claims to {CLAIMS_PATH}")


if __name__ == "__main__":
    main()
