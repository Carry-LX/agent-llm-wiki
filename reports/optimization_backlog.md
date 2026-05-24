# LLM-WIKI 后续优化 Backlog

生成时间：2026-05-20

这份 backlog 基于 `reports/wiki_health_report.md`、`data/claims.jsonl`、`data/search_corpus.jsonl` 和图谱结构统计整理。当前图谱结构没有硬错误，优化重点应从“能展示”转向“结论可信、可复用、可持续重建”。

## 当前整体判断

- 已有 152 个图谱节点、614 条边、139 条 asset、139 条 claim。
- 健康检查 0 个 error，说明结构没有断边、孤点等硬问题。
- 健康检查 7 个 warning，主要集中在来源缺失、OCR 噪声、历史 asset 缺少结构化标签。
- 当前 claim 层是规则抽取种子层，适合检索和定位，不适合直接当成最终高置信总结。

## 优先级 P0：补高价值证据的视觉理解

目标：减少 OCR 噪声进入核心结论。

当前 `best_text_source` 分布：

| source | 数量 |
|---|---:|
| tesseract_chi_sim_eng | 114 |
| anchor_text | 18 |
| codex_vision_model | 5 |
| onenote_ocr_cleaned | 2 |

建议先处理：

- `reports/wiki_health_report.md` 中 OCR 噪声样例列出的 22 条 evidence。
- 缺 source_url 但出现在核心主题页的 evidence。
- Agent Memory、Tool Use、Text2SQL、RAG 评估这几类能沉淀成长期方法论的截图。

完成标准：

- 对重点 evidence 补 `best_text_source=codex_vision_model`。
- 补 `label_title`、`label_summary`、`label_keywords`。
- 对应 claim 的 `confidence` 至少提升到 `medium`，关键结论提升到 `high`。

## 优先级 P1：清理低置信 claim

当前 claim 置信度：

| confidence | 数量 |
|---|---:|
| high | 22 |
| medium | 116 |
| low | 1 |

P0 清低置信 claim 基本完成。剩余 1 条 low 为 Agent 系统架构下已标记 needs_review 的待复查来源（只有外部链接无本地材料）。

按主题看：

| 主题 | 总数 | high | medium | low |
|---|---:|---:|---:|---:|
| Agent 系统架构 | 54 | 13 | 40 | 1 |
| RAG 与检索增强 | 37 | 0 | 37 | 0 |
| Prompt 约束与上下文设计 | 13 | 0 | 13 | 0 |
| 微调、轨迹与训练数据 | 11 | 1 | 10 | 0 |
| 评测集与数据构造 | 11 | 5 | 6 | 0 |
| Text2SQL 与查询校验 | 8 | 3 | 5 | 0 |
| 容错、权限与安全边界 | 3 | 0 | 3 | 0 |
| 规划、执行与反思 | 2 | 0 | 2 | 0 |

建议处理顺序：

1. ~~Agent 系统架构~~：已完成，low=1（剩余为 needs_review 标记）。
2. ~~Text2SQL 与查询校验~~：已完成，low=0。
3. ~~Prompt 约束与上下文设计~~：已完成，low=0。

完成标准：

- 低置信 claim 不直接进入自动主题页核心摘要。
- 每条低置信 claim 要么被视觉模型重读，要么被人工改写，要么标记为 `status=needs_review`。

## 优先级 P1：补来源缺口（label 部分已修复 ✅，source_url 待 P3）

label_title/label_summary 已通过 `tools/enrich_asset_labels.py` 全部补全（134→0，134→0）。健康检查 warning 从 7 降到 5。

source_url 缺口无法在当前数据下修复——45 条缺失的 source_url 在 assets_enriched 和 search_corpus 中同时缺失，没有交叉回填来源。需要 P3 恢复 OneNote 同步链路后重新抓取外链。新增的 enrich 脚本已内置 source_url 双向回填逻辑，P3 恢复 URL 后运行即可自动传播到 corpus 和 claims。

## 优先级 P2：处理重复图片哈希

健康报告发现 11 组图片哈希对应多个 asset_id。多数是同一张图同时出现在 Agent 和 RAG 页面。

建议：

- 保留 raw asset 的多处出现。
- 在 graph 层以 `asset_imgsha_*` 为去重证据节点。
- 在 claim 层合并重复证据，把多个 asset_id 放入同一个 `evidence_ids` 数组。

完成标准：

- 同一张图不在同一主题摘要中重复出现。
- app 右侧详情能显示“出现于多个 OneNote 页面”。

## 优先级 P2：重写自动主题页摘要区（已完成 ✅）

三个自动主题页摘要区已基于 `data/claims.jsonl` 中的 high/medium claim 重写：

- `wiki_generated/Agent_系统架构.md`
- `wiki_generated/Text2SQL_与查询校验.md`
- `wiki_generated/Prompt_约束与上下文设计.md`

新版结构：核心判断 → 工程实现/专题展开 → 面试表达 → 支撑 claim → 待确认 → 证据表。OCR 噪声已从摘要区清除。

## 优先级 P3：恢复完整生成链路（已完成 ✅）

四个缺失脚本已补回：

- `tools/sync_onenote_agent.ps1`：OneNote COM 同步（依赖 OneNote 桌面版）。
- `tools/enrich_agent_ocr.py`：Tesseract OCR 富化。
- `tools/build_agent_wiki.py`：构建 corpus/图谱/topics/wiki 页面（自动跳过人工审校页）。
- `tools/rebuild_agent_wiki.ps1`：完整管道编排。

现有数据可通过 `rebuild_derived_layers.ps1` 维护。`sync_onenote_agent.ps1` 需 OneNote 桌面版才能运行，无法在当前环境下端到端测试，但逻辑已基于现有数据结构（assets.jsonl、onenote_pages.jsonl、page_xml）验算。

## 下一步建议

最小高收益路线：

1. ~~先处理 Text2SQL 的 8 条低置信 claim，因为数量小、主题边界清楚。~~ 已完成：Text2SQL claim 变为 `3 high + 5 medium`。
2. ~~再处理 Agent Memory 相关 evidence，因为它和 Karpathy LLM-WIKI / agent memory 理论关系最强。~~ 已完成首轮：新增 13 条 Memory 审校 claim，并补 `wiki_manual/AgentMemory机制审校.md`。
3. 最后重写 `wiki_generated/Agent_系统架构.md` 和 `wiki_generated/Text2SQL_与查询校验.md` 的摘要区。

## 2026-05-20 进展：Text2SQL claim 清理

本轮新增 `data/claim_overrides.json`，并让 `tools/build_claims_from_corpus.py` 在生成 claim 时自动套用人工审校覆盖。

处理结果：

- Text2SQL 主题下的 claim 从 `8 low` 清理为 `3 high + 5 medium`。
- `agent_img_004_001_c7a560785213` 被整理为执行前/执行后双校验核心证据。
- `agent_img_001_004_90500f357b93` 和 `agent_img_002_005_90500f357b93` 被整理为 Text2SQL 数据构造证据。
- `agent_img_002_026_f9760a189147` 和 `agent_img_002_027_e76d357cd694` 在 claim 层重归到 RAG 与检索增强，避免继续污染 Text2SQL 主题结论。
- 新增 `wiki_manual/Text2SQL与查询校验审校.md` 作为人工审校阅读入口。

## 2026-05-20 进展：Agent Memory claim 清理

本轮继续使用 `data/claim_overrides.json`，把分散在 RAG、Claude Code、微调和规划页面里的 Memory 证据统一审校到 Agent 系统架构主题。

处理结果：

- 新增 13 条 Memory 审校 claim。
- 全局 claim 置信度从 `high=8, medium=76, low=55` 变为 `high=15, medium=77, low=47`。
- Agent 系统架构 claim 增至 48 条，其中 `high=7, medium=22, low=19`。
- 形成 `wiki_manual/AgentMemory机制审校.md`，覆盖 Session vs Memory、四类记忆、目录结构、触发策略、并发控制和不该进入 Memory 的内容。

## 2026-05-23 进展：Agent 工程模式 claim 清理

本轮继续清理 Agent 系统架构中剩余的 low claim，重点覆盖工具安全、Prompt 架构、重试、文件编辑、Workflow、多 Agent、上下文压缩和 badcase 闭环。

处理结果：

- Agent 系统架构 low claim 从 19 条降到 1 条。
- 全局 claim 分布变为 `high=20, medium=90, low=29`。
- 剩余 Agent low claim 是只有重复 URL 的待复查来源，已标记 `needs_review`，不应进入核心摘要。
- 误归到 Agent 的文档切分证据已在 claim 层重归到 `RAG 与检索增强`。
- 新增 `wiki_manual/Agent工程模式审校.md` 作为人工阅读入口。

## 2026-05-23 进展：Prompt 约束与上下文设计 claim 清理

本轮继续使用 `data/claim_overrides.json`，清理 Prompt 约束与上下文设计的 6 条 low claim。

处理结果：

- Prompt 约束与上下文设计 low claim 从 6 条降到 0 条。
- 全局分布变为 `high=20, medium=96, low=23`。
- 当前剩余 low 集中在 RAG 与检索增强（12）、微调轨迹（6）、评测集（3）和 Agent（1，已标记 needs_review）。
- `agent_img_009_002_7af3c22a8eaf`（训练内存估算）重归到微调、轨迹与训练数据。
- `agent_img_001_014_65226eff0183`（Workflow 上下文封装）重归到 Agent 系统架构。
- 新增 `wiki_manual/Prompt约束与上下文设计审校.md`，覆盖结构化输出、Prompt 架构与缓存、双层防御、AskUserQuestion 演进、Map-Reduce 长上下文、MCP 三层结构、Hooks 机制。

## 2026-05-23 进展：RAG 与检索增强 claim 清理

本轮继续使用 `data/claim_overrides.json`，清理 RAG 与检索增强的 12 条 low claim。

处理结果：

- RAG 与检索增强 low claim 从 12 条降到 0 条。
- 全局分布变为 `high=21, medium=107, low=11`。
- 当前剩余 low 集中在微调轨迹（6）、评测集（3）、Agent（1，needs_review）和规划执行（1）。
- 6 条证据重归类：4 条 Claude Code Memory 面试题→Agent 系统架构、1 条交易问诊 Agent→Agent、1 条文本生成采样→Prompt 约束与上下文设计。
- 新增 `wiki_manual/RAG与检索增强审校.md`，覆盖检索技术、Embedding 演进与选型、文档切分、RAG 质量治理五层框架、RAG 幻觉与 Prompt 矛盾、权限控制、性能优化（缓存/延迟/内存/写入）、HyDE/Reranker/GraphRAG/查询路由。

## 2026-05-23 进展：微调、轨迹与训练数据 claim 清理 + 低置信清零收尾

本轮清理了微调轨迹（6 low）、评测集（3 low）和规划执行（1 low），完成 P0 清低置信 claim 收尾。

处理结果：

- 全局 low 从 11 降到 1（仅剩 Agent 已标记 needs_review 的待复查来源，无本地材料可审校）。
- 全局分布变为 `high=22, medium=116, low=1`。
- 重归类：2 条文档切分标题层级识别→RAG、2 条 FAQ 语义匹配→RAG、1 条复杂任务 Workflow→Agent。
- 微调主题：工具调用评估四维度（含防遗忘 30% 通用数据策略）、人工标注+蒸馏组合数据构造、Hermes 双路径自进化、RL 权重内化。
- 规划主题：LLM-as-Planner 自然语言到 PDDL 计划桥接。
- 新增 `wiki_manual/微调与轨迹与训练数据审校.md`。
- **P0 清低置信 claim 已基本完成**，所有 8 个主题除 1 条 needs_review 外已清零 low。
