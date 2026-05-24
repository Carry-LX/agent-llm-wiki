# Agent 工作约定

这个目录是个人 LLM-WIKI 知识库。默认目标不是把资料简单堆进 RAG，而是把 OneNote 原始材料持续编译成可阅读、可检索、可检查的 wiki。

## 基本原则

- 文件保存为 UTF-8，换行使用 LF。
- 不直接改 `raw/` 里的原始材料，除非是在执行明确的同步流程。
- 不直接手改 `wiki_generated/` 作为长期结果；长期理解写入 `wiki_manual/`，自动结果由工具重建。
- `data/claims.jsonl` 是从证据抽取出的观点层，优先用于生成 wiki 摘要和回答问题。
- 每次结构性修改后运行 `python tools/lint_agent_wiki.py`，并查看 `reports/wiki_health_report.md`。
- 项目里的脚本优先使用文件顶部显式变量，不使用复杂命令行参数。

## 推荐工作流

1. 新增或同步 OneNote 原始材料到 `raw/`。
2. 对新增图片做视觉理解，写入 `raw/assets_enriched.jsonl`。
3. 从 enriched asset 重建 `data/search_corpus.jsonl`、图谱和 wiki。
4. 运行 `python tools/build_claims_from_corpus.py` 生成观点层。
5. 运行 `python tools/lint_agent_wiki.py` 检查结构、来源、重复和 OCR 风险。
6. 把重要人工判断写入 `wiki_manual/`。
7. 在 `log.md` 追加本次变化。

## 分层职责

- `raw/`：原始证据层，保存 OneNote 页面、图片、OCR 缓存、同步水位。
- `data/`：结构化中间层，保存图谱、搜索语料、观点层、标签缓存。
- `wiki_generated/`：自动 wiki 层，可重建。
- `wiki_manual/`：人工长期理解层，不被自动覆盖。
- `app/`：本地浏览界面。
- `tools/`：可重复工具链。
- `reports/`：检查报告和派生诊断结果。

## 质量红线

- 关键结论必须能追溯到 evidence_id、source_url 或原始图片。
- OCR 文本不能直接当作高置信结论，尤其是含乱码、重复段、错别字时。
- 同一张图片在多个 OneNote 页面出现时，应区分原始引用和去重证据。
- 页面归属关系不能替代语义关系；短标题页要补主题、概念、跨页证据关系。
- 新增数据流程失败时，不推进 `raw/last_sync_manifest.json` 的水位。
