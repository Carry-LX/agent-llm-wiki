# LLM-WIKI Schema

本文件规定这个知识库的长期结构。它的作用类似 Karpathy LLM-WIKI 中的 schema：告诉后续 Agent 如何 ingest、query、lint 和维护 wiki。

## 核心对象

### Raw asset

位置：`raw/assets_enriched.jsonl`

每条 raw asset 表示 OneNote 中的一个原始对象，常见类型是图片或文本链接。建议字段：

```json
{
  "schema_version": 1,
  "asset_id": "agent_img_002_021_9b3378ea7e27",
  "asset_type": "onenote_image",
  "page_title": "RAG",
  "source_url": "https://example.com",
  "image_path": "raw/images/example.png",
  "image_sha256": "...",
  "best_text": "...",
  "best_text_source": "codex_vision_model",
  "label_title": "向量数据库支撑高维相似度检索",
  "label_summary": "一句话说明该证据支撑的观点",
  "label_keywords": ["RAG", "向量数据库"],
  "label_model": "codex_vision_model",
  "label_generated_at": "2026-05-20T12:00:00Z"
}
```

`best_text_source` 的可信度排序：

1. `codex_vision_model`
2. `human_manual`
3. `source_article_text`
4. `tesseract_chi_sim_eng`
5. `onenote_ocr_cleaned`
6. `anchor_text`

### Claim

位置：`data/claims.jsonl`

claim 是从证据中抽取出的可引用观点。wiki 摘要应优先基于 claim，而不是直接截取 OCR 文本。

```json
{
  "claim_id": "claim_agent_img_002_021_9b3378ea7e27_001",
  "claim_type": "engineering_judgment",
  "claim_text": "高维向量相似度搜索不适合依赖 B-tree，应使用专门向量索引或向量数据库。",
  "topic_id": "rag_and_retrieval",
  "topic_title": "RAG 与检索增强",
  "evidence_ids": ["agent_img_002_021_9b3378ea7e27"],
  "source_urls": ["https://example.com"],
  "confidence": "medium",
  "extraction_method": "codex_vision_model",
  "status": "active"
}
```

claim 类型建议：

- `definition`：定义或概念解释。
- `engineering_judgment`：工程取舍和推荐做法。
- `risk`：风险、失败模式、安全边界。
- `workflow`：流程、步骤、闭环。
- `metric`：评估指标或量化口径。
- `comparison`：方案对比。
- `example`：案例、样例、面试表达。

### Topic page

位置：`wiki_generated/*.md` 或 `wiki_manual/*.md`

自动主题页建议包含：

1. 核心结论。
2. 工程取舍。
3. 常见误区。
4. 支撑 claims。
5. 原始 evidence 表。
6. 待人工确认项。

### Log entry

位置：`log.md`

每次重要变更追加一段：

```markdown
## 2026-05-20

- 操作：新增 claims 层和 lint 工具。
- 输入：`data/search_corpus.jsonl`、`raw/assets_enriched.jsonl`。
- 输出：`data/claims.jsonl`、`reports/wiki_health_report.md`。
- 风险：首版 claims 是规则抽取，后续要用视觉模型或人工审校提升置信度。
```

## Ingest 规则

- 新增图片必须优先由视觉模型直接读图，不能把 OneNote OCR 或本地 OCR 当作主要内容来源。
- 如果只是历史数据补救，可以保留 Tesseract 文本，但生成 claim 时将 `confidence` 降为 `low` 或 `medium`。
- source_url 为空时，claim 仍可保留，但 lint 应提示缺来源。
- 重复图片以 `image_sha256` 去重；重复出现的位置作为引用位置，而不是新证据本体。

## Query 规则

- 回答问题时优先检索 `data/claims.jsonl`。
- claim 不足时再回落到 `data/search_corpus.jsonl`。
- 回答中尽量带 evidence_id，方便回查图片或来源。
- 如果回答过程中形成了稳定新判断，应追加到 `wiki_manual/` 或重新生成 `data/claims.jsonl`。

## Lint 规则

`tools/lint_agent_wiki.py` 至少检查：

- 必需目录和文件是否存在。
- 图谱边的端点是否都存在。
- 是否存在孤立节点。
- 页面节点是否只有目录关系，没有语义关系。
- source_url 缺失、OneNote 内部链接、重复 asset。
- `best_text_source` 的分布，以及 OCR 主导比例。
- enriched asset 是否缺 `label_title`、`label_summary`、`label_keywords`。
- claims 是否存在，是否能追溯 evidence 和 source。

## 生成页规则

- 不把 OCR 原文直接当作“关键要点”。
- 自动摘要应基于 claims 聚合，必要时保留低置信提示。
- 每个结论后标 evidence_id。
- 乱码、重复段、无法解释的片段应进入待人工确认，而不是进入核心结论。
