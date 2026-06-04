# Agent 分区 LLM-WIKI

这是从 OneNote `我的笔记本 / Agent` 分区生成的本地个人知识库，主题覆盖 Agent 架构、RAG 与检索增强、Prompt 工程、Text2SQL、Memory、微调与训练数据、评测集、容错与权限。

当前版本已按 Karpathy LLM-WIKI 风格建立维护骨架：分层数据约定、claim 观点层、可重复工具链、健康检查和人工审校覆盖层。

## 使用入口

- 本地网页：`app/index.html`（节点网络视图，支持搜索、图谱浏览、图片放大）
- 项目工作约定：本文件
- 交接说明：`HANDOFF.md`
- 运行日志：`log.md`
- 自动 wiki：`wiki_generated/index.md`
- 人工笔记：`wiki_manual/`
- 精品感悟：`wiki_html/`（精品文章的深度感悟与设计方法论，HTML 长文呈现）
- 健康报告：`reports/wiki_health_report.md`

## 数据分层

项目按以下分层维护，下层作为上层的可信源：

```text
raw/ 原始层
  → data/ 结构化中间层（图谱、检索语料、claim 观点层）
  → wiki_generated/ 自动 wiki + wiki_manual/ 人工长期理解
  → app/ 本地浏览界面
  → reports/ 派生检查报告
```

各层职责：

| 层 | 目录 | 是否手工改 | 用途 |
|---|---|---|---|
| 原始层 | `raw/images/` | 可以追加 | 存图片原件 |
| 原始层 | `raw/assets.jsonl` | 不推荐 | OneNote 图片资产原始记录 |
| 原始层 | `raw/assets_enriched.jsonl` | 不推荐 | 大模型读图后的证据文本、描述和标签 |
| 原始层 | `raw/onenote_pages.jsonl` | 不推荐 | OneNote 页面元信息 |
| 中间层 | `data/topics.json` | 临时可改 | 主题列表和统计 |
| 中间层 | `data/graph.json` | 临时可改 | 图谱总数据 |
| 中间层 | `data/graph_nodes.jsonl` | 临时可改 | 图谱节点 |
| 中间层 | `data/graph_edges.jsonl` | 临时可改 | 图谱关系 |
| 中间层 | `data/search_corpus.jsonl` | 临时可改 | 搜索语料 |
| 中间层 | `data/claims.jsonl` | 派生文件 | 观点层（会被重建） |
| 中间层 | `data/claim_overrides.json` | 推荐 | 人工审校覆盖（不会被覆盖） |
| Wiki | `wiki_generated/` | 不推荐 | 自动生成主题页 |
| Wiki | `wiki_manual/` | 推荐 | 人工长期整理 |
| 展示 | `app/wiki_data.json` | 临时可改 | 网页数据 |
| 展示 | `app/wiki_data.js` | 临时可改 | 网页 JS 数据 |
| 展示 | `app/index.html` | 可以改 | 网页界面 |

## 核心对象与 Schema

### Raw Asset（原始证据）

位置：`raw/assets_enriched.jsonl`。每条表示 OneNote 中的一个图片对象：

```json
{
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
  "label_keywords": ["RAG", "向量数据库"]
}
```

`best_text_source` 可信度排序：`codex_vision_model` > `human_manual` > `source_article_text` > `tesseract_chi_sim_eng` > `onenote_ocr_cleaned` > `anchor_text`。

### Claim（观点）

位置：`data/claims.jsonl`。从证据中抽取的可引用观点，wiki 摘要应优先基于 claim：

```json
{
  "claim_id": "claim_agent_img_002_021_001",
  "claim_type": "engineering_judgment",
  "claim_text": "高维向量相似度搜索不适合依赖 B-tree，应使用专门向量索引。",
  "topic_id": "rag_and_retrieval",
  "evidence_ids": ["agent_img_002_021_9b3378ea7e27"],
  "source_urls": ["https://example.com"],
  "confidence": "medium",
  "extraction_method": "codex_vision_model",
  "status": "active"
}
```

claim 类型：`definition`（定义）、`engineering_judgment`（工程取舍）、`risk`（风险边界）、`workflow`（流程步骤）、`metric`（评估指标）、`comparison`（方案对比）、`example`（案例样例）。

人工审校结论写入 `data/claim_overrides.json`，重建 `claims.jsonl` 时自动套用。

### 图谱关系

建图时区分四类关系，避免做成"页面目录图"：

1. **来源关系**：`contains_evidence`，表示证据来自哪个 OneNote 页面。
2. **主题关系**：`supported_by`，表示证据属于哪个知识主题。
3. **概念关系**：`explained_by`，表示证据解释了某个抽象概念。
4. **跨页语义关系**：`semantic_evidence`，表示证据虽来自别的页面，但内容上属于当前主题。

## 常用命令

### 日常维护（推荐）

```powershell
& .\tools\rebuild_derived_layers.ps1
```

这条命令会：重建 claims → 补全 asset label → 生成健康报告。

### 全量重建（需 OneNote 桌面版）

```powershell
& .\tools\rebuild_agent_wiki.ps1
```

完整管道：sync OneNote → OCR 富化 → build wiki → labels → lint。

### 检索

编辑 `tools/search_agent_wiki.py` 顶部的 `QUERY` 和 `TOP_K`，然后：

```powershell
python .\tools\search_agent_wiki.py
```

### 健康检查

```powershell
python .\tools\lint_agent_wiki.py
```

报告写入 `reports/wiki_health_report.md`，检查：图谱断边/孤点、页面节点缺语义关系、source_url 缺失、OCR 噪声、label 缺字段、claim 追溯等。

## 工作约定

- 文件保存为 UTF-8，换行使用 LF。
- 不直接改 `raw/` 里的原始材料，除非执行同步流程。
- 不直接手改 `wiki_generated/` 作为长期结果；长期理解写入 `wiki_manual/`。
- 新增 `wiki_manual/*.md` 时，必须同步更新 `wiki_manual/manifest.js` 的 `nodes` 和 `edges`（设置 `window.__MANUAL_MANIFEST__` 全局变量），否则 HTML 图谱中不会显示。节点 `id` 统一用 `manual_` 前缀，`type` 统一用 `manual_note`，边用 `manual_enrichment` 关系连到已有 `topic_*` 节点。
- <strong>⚠️ 新增知识后，除更新 manifest.js 节点外，还必须重建文档版本：</strong>运行 `python tools/build_wiki_content.py` 将 `wiki_manual/*.md` 和 `wiki_generated/*.md` 重新编译到 `app/wiki_content.js`。Wiki 系统有两套展示方式（图谱节点 + 文档列表），仅更新其中一套会导致另一套看不到新增内容。
- 人工审校结论写入 `data/claim_overrides.json`，不直接改 `data/claims.jsonl`。
- 每次结构性修改后运行 lint 并查看健康报告。
- 脚本优先使用文件顶部显式变量，不使用复杂命令行参数。
- Git 仅作本地备份，不主动 push。
- `wiki_html/` 存放精品文章读后的深度感悟与设计方法论，以 HTML 长文形式呈现。与 `wiki_manual/` 的区别：`wiki_manual/` 是 Markdown 笔记，侧重知识点备忘与审校；`wiki_html/` 是排版后的 HTML 文章，侧重可读性与体系化表达，适合分享和反复阅读。

## 质量红线

- 关键结论必须能追溯到 evidence_id、source_url 或原始图片。
- 新增图片必须由视觉模型直接读图，不以 OneNote OCR 或本地 OCR 作为主要内容来源。
- OCR 文本不能直接当作高置信结论，尤其是含乱码、重复段、错别字时。
- 同一张图片在多个 OneNote 页面出现时，应以 `image_sha256` 去重。
- 页面归属关系不能替代语义关系；短标题页要补主题、概念、跨页证据关系。
- 新增数据流程失败时，不推进同步水位。

## 新增数据

### 推荐方式：从 OneNote 正规新增

1. 在 OneNote `我的笔记本 / Agent` 分区新增材料。
2. 运行 `& .\tools\rebuild_agent_wiki.ps1` 全量重建。
3. 检查 `app/index.html` 确认新证据可见。

### 人工笔记

写到 `wiki_manual/` 下，适合：面试回答模板、技术判断总结、多篇材料融合后的观点、不希望被自动覆盖的内容。

### 精品感悟

写到 `wiki_html/` 下，适合：精品文章读后深度感悟、设计方法论提炼、工程实践复盘。以 HTML 长文排版，侧重可读性和体系化表达，区别于 `wiki_manual/` 的知识点备忘风格。

### 临时手工新增

改 `app/wiki_data.json` 和 `app/wiki_data.js`（两者保持同步），在 `graph.nodes` 中加节点、`graph.edges` 中加关系。注意下次重新生成会被覆盖。

### 增量同步水位

同步脚本以 `raw/last_sync_manifest.json` 的 `generated_at_utc` 为水位，向前回看 5 分钟找候选页面，通过 `page_id` + `onenote_object_id` + `image_sha256` 三级判断新增/变更/重复。只有全部输出文件成功写入后才推进水位。

## 当前状态

- claims：139 条（high=22, medium=116, low=1）
- 健康检查：0 errors / 5 warnings
- 主题：8 个，全部完成低置信清零
- 工具链：9 个脚本，均可正常运行
- 3 个自动主题页摘要区已基于 claim 重写，不再含 OCR 噪声
