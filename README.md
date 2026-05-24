# Agent 分区 LLM-WIKI

这是从 OneNote `我的笔记本 / Agent` 分区生成的本地知识库最小可用版。

当前版本已经补上 Karpathy LLM-WIKI 风格的维护骨架：`SCHEMA.md` 规定数据层和工作流，`log.md` 记录演化过程，`tools/` 提供 claim 构建、检索和健康检查。

## 使用入口

- 本地网页：`app/index.html`
- 项目维护规则：`AGENTS.md`
- 接手交接说明：`HANDOFF.md`
- LLM-WIKI Schema：`SCHEMA.md`
- 运行日志：`log.md`
- 新增数据指南：`新增数据指南.md`
- 自动 wiki：`wiki_generated/index.md`
- 人工笔记层：`wiki_manual/`
- 维护路线图：`wiki_manual/LLM-WIKI维护路线图.md`
- 观点层：`data/claims.jsonl`
- 原始证据：`raw/assets.jsonl`
- 检索语料：`data/search_corpus.jsonl`
- 外部图谱数据：`data/graph.json`、`data/graph_nodes.jsonl`、`data/graph_edges.jsonl`
- 健康检查报告：`reports/wiki_health_report.md`

网页入口是节点网络视图：左侧可以一键全选/全不选节点类型，也可以只看结构或只看证据；中间画布支持空白拖动、滚轮缩放和拖动节点；右侧以图片为主体，点击图片可放大查看原图。

## Karpathy LLM-WIKI 工作流

这个项目按下面的分层维护：

```text
raw sources
  -> enriched evidence
  -> search corpus / graph
  -> claims
  -> generated wiki + manual wiki
  -> app view / lint report
```

推荐每次新增或整理材料后运行：

```powershell
python .\tools\build_claims_from_corpus.py
python .\tools\lint_agent_wiki.py
```

也可以直接运行派生层重建脚本：

```powershell
& .\tools\rebuild_derived_layers.ps1
```

需要快速查资料时，编辑 `tools/search_agent_wiki.py` 顶部的 `QUERY` 和 `TOP_K`，再运行：

```powershell
python .\tools\search_agent_wiki.py
```

注意：当前 `data/claims.jsonl` 是从现有搜索语料规则抽取出的首版观点层，不等于最终人工审校结论。`confidence=low/medium` 的 claim 后续应优先用视觉模型读图或人工修正。

## 重新同步

在项目根目录运行：

```powershell
& .\tools\rebuild_agent_wiki.ps1
```

也可以分步运行：

```powershell
& .\tools\sync_onenote_agent.ps1
python .\tools\build_agent_wiki.py
```

同步脚本只显式处理 OneNote `我的笔记本 / Agent` 分区。后续扩展到其他分区时，复制脚本或把顶部变量改成新的笔记本、分区即可。

## OCR 富化

`tools/enrich_agent_ocr.py` 会读取 `raw/assets.jsonl`，用本机 `E:\tesseract\tesseract.exe` 对图片重新 OCR，并输出：

- `raw/assets_enriched.jsonl`
- `raw/ocr_cache/*.txt`

生成网页和检索数据时会优先使用 `best_text` / `clean_text`。如果后续接入视觉模型，只需要让模型 OCR 结果写回这些字段，网页、图谱和检索层不需要重做。

## Codex 检索

编辑 `tools/search_agent_wiki.py` 顶部的 `QUERY` 和 `TOP_K`，然后运行：

```powershell
python .\tools\search_agent_wiki.py
```

输出会包含 evidence_id、主题、OneNote 页面、source_url、图片路径和 OCR 片段。

## 健康检查

运行：

```powershell
python .\tools\lint_agent_wiki.py
```

报告会写入 `reports/wiki_health_report.md`，当前重点检查：

- 必需文件和目录是否存在。
- 图谱是否有缺失端点或孤立节点。
- 页面节点是否缺少语义关系。
- source_url 缺失、OneNote 内部来源、重复图片哈希。
- `best_text_source` 分布和 OCR 噪声样例。
- claim 的类型、置信度、来源和 evidence 追溯。

## 分层约定

- `raw/` 是原始层，尽量只追加和重建，不做人工改写。
- `data/claims.jsonl` 是观点层，用来支撑后续更稳定的 wiki synthesis。
- `wiki_generated/` 是自动生成层，可随时覆盖。
- `wiki_manual/` 是人工长期沉淀层，自动脚本不会覆盖。
- `data/` 是检索和网页使用的结构化数据，可由原始层重建。
- `app/` 是本地浏览界面。
- `reports/` 是派生检查报告。
