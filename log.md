# LLM-WIKI 运行日志

## 2026-06-07 新增人工笔记：Qwen 模型演进技术总结

- 操作：新增 `wiki_manual/Qwen模型演进技术总结.md`（来源：丁师兄大模型 2026-06-04，授权自自动学习机知乎），拆为 3 个证据节点——架构与预训练演进（GQA→QK-Norm→混合注意力→解耦Harness-Verifier）、后训练技术演进（DPO+GRPO→Thinking Budget+蒸馏→异步RL→跨框架RL+反作弊）、Agent与RL基础设施演进（通用RL→Agent专项RL→自进化体系）。覆盖 Qwen 2.5/3/3.5/3.6/3.7 五个版本。10 张图片已同步至 raw/images/。
- 操作：manifest.js 新增 3 个节点 + 3 条边，连接 topic_finetuning_trajectories 和 topic_agent_architecture。

## 2026-05-25 新增人工笔记：LLM 推理机制

- 操作：新增 `wiki_manual/LLM推理机制.md`，解释 LLM Prefill/Decode 两阶段工作原理、KV Cache 作用、资源需求差异及混跑干扰问题。
- 操作：新增 `wiki_manual/PD分离的工程挑战.md`，拆为 3 个证据节点——KV Cache 传输瓶颈、负载不均衡与调度、显存碎片与性能敏感性。含面试回答框架和 Llama-3.1-70B 定量数据。
- 操作：新增 `wiki_manual/ClaudeCode的JSON输出机制.md`，拆为 2 个证据节点——JSON 通道机制（text_delta vs input_json_delta）、空壳工具校验（Ajv + Stop 钩子）。覆盖 outputFormat/SyntheticOutputTool/Stop hook 源码级分析。
- 操作：新增 `wiki_manual/ClaudeCode为何放弃RAG.md`（来源：丁师兄大模型 2026-05-28），拆为 2 个证据节点——代码场景下 RAG 为何失效（embedding 语义漂移/乘法效应/索引时效性）、Agentic Search 架构取舍（无状态设计/Everything is the Model/混合方案）。含面试三层回答框架。
- 操作：新增 `wiki_manual/Agent死循环与兜底机制.md`（来源：吴师兄学大模型 2026-05-29），拆为 2 个证据节点——死循环四种成因（工具调用循环/目标漂移/自我怀疑/幻觉性进展）、四层兜底机制（max_iterations/step budget/循环检测/人工 escalation）。含 7 条生产 Checklist、Claude Code 对照分析、三段式面试回答。3 张图片已同步至 raw/images/。
- 操作：新增 `wiki_manual/TMIC_AI小新Agent设计方法论.md`（个人体系化总结），拆为 3 个证据节点——上下文工程三层优化（Skills vs RAG/业务模块识别/参数预取）、多轮方向控制（TodoList 锚定 + Tree Action 编排剥离）、可迁移四阶段框架（上下文加载→规划→执行→分析输出）。核心信念：基模推理能力已足够，全部工程精力让模型在正确时刻看到正确信息。
- 操作：TMIC 文章追加"SubAgent 角色定义"感悟，新增节点 `manual_subagent_role_definition`——Agent=规划者、SubAgent=执行者，能力集合从角色定义推导而非做减法。
- 操作：TMIC 文章追加"DeepAgent 三层基础设施"感悟，新增 2 个节点——三层架构（上下文工程→行为约束→持续进化）+ RAG 软约束与评估闭环飞轮（RAG是唯一可精准干预而不产生副作用的入口，五步闭环构成免疫系统，数据回流驱动自进化）。

## 2026-05-25 文档整合

- 操作：融合 AGENTS.md + SCHEMA.md → README.md，删除新增数据指南.md、维护路线图.md、optimization_backlog.md，精简 HANDOFF.md。
- 结果：.md 文件从 28 个精简到 23 个，入口文件 README.md 成为唯一项目说明和约定来源。

## 2026-05-24 项目迁移

- 操作：将项目从 `C:\Users\李鑫\Documents\Codex\2026-05-18\codex-onenote\llm_wiki_agent` 迁移至 `E:\projects\person`。
- 更新：`last_sync_manifest.json` 中的 output_root。
- 验证：全部 6 个 Python 脚本编译通过，lint 0 errors，search 正常。
- 旧位置保留原文件，新位置重新 init git。

## 2026-05-20

- 操作：根据 Karpathy LLM-WIKI 思路补项目维护骨架。
- 输入：现有 `raw/`、`data/`、`wiki_generated/`、`wiki_manual/`、`app/`。
- 输出：新增 `AGENTS.md`、`SCHEMA.md`、`tools/`、`reports/`。
- 判断：当前库已经有 raw/wiki/data/app 分层和图谱关系，但缺少 schema、log、lint、claim 层和可重复工具链。
- 风险：首轮不重写历史 OCR 内容，只先建立检查与派生层，避免污染原始材料。

## 2026-05-20 首版 claims 和 lint

- 操作：从 `data/search_corpus.jsonl` 规则抽取首版 `data/claims.jsonl`。
- 输出：139 条 claim，覆盖现有可检索语料中的主要 evidence。
- 操作：运行 `python tools/lint_agent_wiki.py`。
- 输出：`reports/wiki_health_report.md`，当前 0 个 error、7 个 warning。
- 主要 warning：45 条语料缺 source_url，134 条 enriched asset 缺 `label_title` 和 `label_summary`，22 条语料命中疑似 OCR 噪声，11 组图片哈希存在重复引用。
- 风险：首版 claim 仍来自 OCR/搜索语料，不是最终高置信知识结论；后续应优先用视觉模型重读高价值图片。

## 2026-05-20 本地备份与整体 backlog

- 操作：初始化 Git 仓库并创建初始本地提交。
- 提交：`512d8fb 初始化 LLM-WIKI 维护骨架与健康检查工具`。
- 规模：292 个文件，约 41 MB。
- 操作：补 `.editorconfig`、`.gitattributes`、`.gitignore`，固定 UTF-8、LF 和临时文件忽略规则。
- 操作：新增 `reports/optimization_backlog.md`，把后续优化拆成 P0-P3。
- 判断：当前结构层稳定，后续主攻证据可信度、低置信 claim、来源缺口、重复图片和完整重建链路。

## 2026-05-20 Text2SQL claim 审校

- 操作：新增 `data/claim_overrides.json`，作为可重建的人工审校覆盖层。
- 操作：更新 `tools/build_claims_from_corpus.py`，生成 `data/claims.jsonl` 时自动套用 override。
- 输出：Text2SQL 主题 claim 从 `8 low` 变为 `3 high + 5 medium`。
- 调整：两条 Milvus/RAG 性能 claim 在 claim 层重归到 `RAG 与检索增强`。
- 输出：新增 `wiki_manual/Text2SQL与查询校验审校.md`，作为替代旧 OCR 摘要的人工阅读入口。
- 验证：`python -m py_compile tools/build_claims_from_corpus.py tools/lint_agent_wiki.py tools/search_agent_wiki.py` 通过；`tools/rebuild_derived_layers.ps1` 通过，健康检查仍为 0 error。

## 2026-05-20 Agent Memory claim 审校

- 操作：继续扩展 `data/claim_overrides.json`，新增 Agent Memory 相关人工审校 claim。
- 范围：`agent_img_002_009`、`agent_img_001_008`、`agent_img_010_012` 到 `agent_img_010_022` 等 Memory 证据。
- 输出：新增 `wiki_manual/AgentMemory机制审校.md`。
- 结果：全局 claim 置信度从 `high=8, medium=76, low=55` 变为 `high=15, medium=77, low=47`。
- 判断：Memory 证据应归入 Agent 系统架构主题，而不是分散在 RAG、微调、规划等自动分类页里。

## 2026-05-23 Agent 工程模式 claim 审校

- 操作：继续扩展 `data/claim_overrides.json`，清理 Agent 系统架构剩余 low claim。
- 范围：工具安全默认值、Prompt 分段注册表与缓存边界、重试预算与抖动、文件编辑前读取、Workflow/Skill 编排、多 Agent 编排、上下文压缩、badcase 闭环。
- 输出：新增 `wiki_manual/Agent工程模式审校.md`。
- 结果：Agent 系统架构 low claim 从 19 条降到 1 条；全局分布变为 `high=20, medium=90, low=29`。
- 判断：剩余 Agent low claim 只有重复 URL，已标记 `needs_review`，不进入核心摘要。

## 2026-05-23 Prompt 约束与上下文设计 claim 审校

- 操作：继续扩展 `data/claim_overrides.json`，清理 Prompt 约束与上下文设计的 6 条 low claim。
- 范围：模型训练内存误归类、结构化输出技术路线、金融三层防幻觉体系、Workflow 上下文封装、Claude Code 双层防御。
- 调整：`agent_img_009_002_7af3c22a8eaf` 重归到微调、轨迹与训练数据；`agent_img_001_014_65226eff0183` 重归到 Agent 系统架构。
- 输出：新增 `wiki_manual/Prompt约束与上下文设计审校.md`，覆盖结构化输出、Prompt 架构与缓存、双层防御、AskUserQuestion 演进、Map-Reduce 长上下文、MCP 三层结构、Hooks 机制。
- 结果：Prompt 约束与上下文设计 low claim 从 6 条降到 0 条；全局分布变为 `high=20, medium=96, low=23`。

## 2026-05-23 RAG 与检索增强 claim 审校

- 操作：继续扩展 `data/claim_overrides.json`，清理 RAG 与检索增强的 12 条 low claim。
- 范围：HNSW 算法理解、RAG 质量治理五层框架、RAG Prompt 根本矛盾、文档切分最佳实践、动态 RAG 质量评估、文本生成流水线、Claude Code Memory 面试题、badcase 闭环。
- 调整：6 条重归类（4 条 Claude Code Memory 和 badcase 闭环→Agent 系统架构，1 条交易问诊 Agent→Agent，1 条采样质检→Prompt 约束与上下文设计）。
- 输出：新增 `wiki_manual/RAG与检索增强审校.md`，覆盖检索技术、Embedding、文档切分、质量治理、RAG 幻觉、权限控制、性能优化、HyDE、Reranker 和 GraphRAG 对比。
- 结果：RAG 与检索增强 low 从 12 降到 0；全局分布变为 `high=21, medium=107, low=11`。

## 2026-05-23 微调、轨迹与训练数据 claim 审校

- 操作：继续扩展 `data/claim_overrides.json`，清理微调轨迹（6 low）、评测集（3 low）和规划执行（1 low）的剩余 low claim。
- 范围：工具调用评估四维度、人工标注+蒸馏组合策略、Hermes 双路径自进化、RL 权重内化、LLM-as-Planner、FAQ 语义匹配、文档切分标题层级识别。
- 调整：2 条文档切分→RAG、2 条 FAQ 匹配→RAG、1 条复杂任务 Workflow→Agent。
- 输出：新增 `wiki_manual/微调与轨迹与训练数据审校.md`，覆盖微调评估、数据构造、Agent 自进化和 RL 训练闭环。
- 结果：全局 low 从 11 降到 1（仅剩 Agent 已标记 needs_review 的待复查来源）；全局分布变为 `high=22, medium=116, low=1`。P0 清低置信 claim 基本完成。

## 2026-05-24 P3：恢复完整 OneNote 到 app 的重建链路

- 操作：补回 README 中提到但缺失的四个脚本。
- 新增：
  - `tools/sync_onenote_agent.ps1`：通过 OneNote COM 导出页面 XML、提取图片和文本链接，生成 `raw/assets.jsonl` 和 `raw/onenote_pages.jsonl`。
  - `tools/enrich_agent_ocr.py`：对图片运行 tesseract OCR，生成 `raw/assets_enriched.jsonl` 和 `raw/ocr_cache/*.txt`。
  - `tools/build_agent_wiki.py`：从 enriched assets 生成 `data/search_corpus.jsonl`、图谱、`data/topics.json` 和 `wiki_generated/*.md`（自动跳过已含「## 核心判断」的人工审校页）。
  - `tools/rebuild_agent_wiki.ps1`：完整管道编排——sync → enrich → build → labels → lint。
- 调整：
  - `tools/rebuild_derived_layers.ps1` 新增 enrich_asset_labels 步骤。
  - `build_agent_wiki.py` 内置跳过人工审校页的 guard，P1 重写的三个页面不会被自动生成覆盖。
- 验证：`build_agent_wiki.py` 成功生成 139 条 corpus、275 节点、509 边。健康检查 0 errors。
- 注意：`sync_onenote_agent.ps1` 依赖本机 OneNote 桌面版 COM 对象，无法在无 OneNote 环境下测试。现有数据可继续通过 `rebuild_derived_layers.ps1` 维护。

## 2026-05-23 P2：补 source_url / label 字段

- 操作：新增 `tools/enrich_asset_labels.py`，自动为 `raw/assets_enriched.jsonl` 补全 label_title 和 label_summary。
- 同时新增 source_url 双向回填（asset↔corpus↔claims）和 OCR 噪声标记功能，供后续 P3 恢复同步链路后自动生效。
- 结果：健康检查 warning 从 7 降到 5。label_title（134→0）和 label_summary（134→0）已清零。
- 剩余 5 个 warning 均属硬约束：source_url 缺失（45+2）、图片哈希重复（11）、OCR 噪声（22）、claim 缺 source_urls（45）。这些无法在当前数据下修复，需 P3 恢复同步链路或视觉模型重读关键图片。

## 2026-05-23 P1：重写自动主题页摘要区

- 操作：基于 `data/claims.jsonl` 中的 high/medium claim 重写三个自动主题页的摘要区。
- 范围：`wiki_generated/Agent_系统架构.md`、`wiki_generated/Text2SQL_与查询校验.md`、`wiki_generated/Prompt_约束与上下文设计.md`。
- 新版结构：核心判断 → 工程实现/专题展开 → 面试表达 → 支撑 claim → 待确认 → 证据表。
- 主要改进：原"关键要点"区直接截 OCR 噪声（如"上玉文没有约束好""注意万不集中"），新版全部基于审校后的 claim 文本重写。
- 结果：三个页面摘要区不再有 OCR 噪声，核心判断可直接用于面试表达和知识复用。

## 2026-05-23 交接文档

- 操作：新增 `HANDOFF.md`。
- 目的：给后续接手的 AI 提供单一入口，说明已完成事项、当前状态、未完成 backlog、推荐下一步和注意事项。
- 下一步推荐：优先处理 `Prompt 约束与上下文设计` 的 6 条 low claim。
