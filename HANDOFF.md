# LLM-WIKI 交接说明

更新时间：2026-05-24

本项目是用户的个人 `llm-wiki` 知识库，主题是 Agent / RAG / Claude Code / Text2SQL / Prompt / Memory 等材料。当前工作重点不是继续堆 raw 资料，而是把已有 OneNote 导出的证据层，逐步整理成可维护、可重建、可审校的 LLM-WIKI。

## 项目位置

```text
E:\projects\person
```

## 当前 Git 状态

本项目已初始化为本地 Git 仓库，仅用于本地备份和回退。不要主动 push。

最近提交：

```text
0359e16 清理 Agent 工程模式 claim
4057578 清理 Agent Memory 相关 claim
72092e1 清理 Text2SQL 低置信 claim
b13b4e6 补充 LLM-WIKI 后续优化 backlog
512d8fb 初始化 LLM-WIKI 维护骨架与健康检查工具
```

接手前请先运行：

```powershell
git status --short --branch
```

如果要做阶段性修改，完成后建议本地提交，提交信息用中文。

## 关键入口文件

- `README.md`：项目入口和常用命令。
- `AGENTS.md`：给 Agent 的项目工作约定。
- `SCHEMA.md`：LLM-WIKI 数据层、claim 层、lint 规则。
- `log.md`：已经做过的操作流水。
- `reports/optimization_backlog.md`：后续优化 backlog。
- `reports/wiki_health_report.md`：最近一次健康检查报告。
- `data/claim_overrides.json`：人工审校 claim 覆盖层。
- `data/claims.jsonl`：当前派生出的观点层。
- `wiki_manual/`：人工长期整理页。

## 已完成的工作

### 1. 维护骨架

已新增：

- `AGENTS.md`
- `SCHEMA.md`
- `log.md`
- `.editorconfig`
- `.gitattributes`
- `.gitignore`
- `tools/`
- `reports/`

### 2. 工具链

已新增：

- `tools/build_claims_from_corpus.py`
- `tools/lint_agent_wiki.py`
- `tools/search_agent_wiki.py`
- `tools/enrich_asset_labels.py`
- `tools/enrich_agent_ocr.py`
- `tools/build_agent_wiki.py`
- `tools/rebuild_derived_layers.ps1`
- `tools/rebuild_agent_wiki.ps1`
- `tools/sync_onenote_agent.ps1` (需 OneNote 桌面版)

常用重建命令：

```powershell
& .\tools\rebuild_derived_layers.ps1
```

该命令会：

1. 从 `data/search_corpus.jsonl` 和 `raw/assets_enriched.jsonl` 生成 `data/claims.jsonl`。
2. 运行 `enrich_asset_labels.py` 补全 asset label 和交叉回填 source_url。
3. 生成 `reports/wiki_health_report.md`。

全量重建（需 OneNote 桌面版）：

```powershell
& .\tools\rebuild_agent_wiki.ps1
```

### 3. Text2SQL claim 清理

已完成：

- Text2SQL 从 `8 low` 清理为 `3 high + 5 medium`。
- 两条误归到 Text2SQL 的 Milvus/RAG 性能 claim 已在 claim 层重归到 `RAG 与检索增强`。
- 新增人工页：`wiki_manual/Text2SQL与查询校验审校.md`。

### 4. Agent Memory claim 清理

已完成：

- 新增 13 条 Agent Memory 人工审校 claim。
- Memory 相关证据从 RAG、微调、规划等页面收拢到 `Agent 系统架构`。
- 新增人工页：`wiki_manual/AgentMemory机制审校.md`。

核心结论：

- Memory 不是 Session。
- Memory 是项目级长期外部状态。
- 推荐分为 user / feedback / project / reference 四类。
- 触发策略要平衡成本和覆盖率。
- 后台提取要用 coalescing 避免并发写乱。

### 5. Agent 工程模式 claim 清理

已完成：

- Agent 系统架构低置信 claim 基本清完。
- 新增人工页：`wiki_manual/Agent工程模式审校.md`。

覆盖内容：

- 工具安全默认值。
- 文件编辑前必须读取。
- Prompt 分段注册表与缓存边界。
- `searchHint` / `description` 分工。
- 重试预算、错误分类、指数退避、随机抖动。
- Workflow / Skill 编排。
- 多 Agent 编排模式。
- 长上下文头尾保护与中间摘要。
- badcase 闭环。

### 6. Prompt 约束与上下文设计 claim 清理

已完成：

- Prompt 约束与上下文设计 6 条 low claim 全部清完。
- 2 条误归类重归（训练内存→微调、Workflow→Agent）。
- 新增人工页：`wiki_manual/Prompt约束与上下文设计审校.md`。

覆盖内容：

- 结构化输出六类技术路线全景对比。
- 金融场景三层防幻觉体系（事前约束、事中校验、事后路由）。
- Prompt 架构与缓存（段落注册表、工具调用边界、RAG 专用结构）。
- 提示词+运行时双层防御模式。
- AskUserQuestion 工具三次迭代演进。
- Map-Reduce 长上下文评审。
- MCP 三层结构（角色/能力/协议）。
- Hooks 机制。

### 7. 微调、轨迹与训练数据 claim 清理 + 低置信清零收尾

已完成：

- 微调轨迹 6 条 low、评测集 3 条 low、规划执行 1 条 low 全部清完。
- 新增人工页：`wiki_manual/微调与轨迹与训练数据审校.md`。
- 全局 low 从 11 降到 1（仅剩 Agent 已标记 needs_review 的待复查来源）。

覆盖内容：

- 工具调用评估四维度（选择、参数、顺序、遗忘）与防遗忘策略（30% 通用数据）。
- 训练数据构造：人工标注 + 模型蒸馏组合策略。
- Hermes 双路径自进化：Skill 生成（记笔记）+ RL 训练（练内功）。
- RL 权重内化 vs 上下文工程天花板。
- LLM-as-Planner 自然语言到 PDDL 计划桥接。

**P0 清低置信 claim 已基本完成。全部 8 个主题除 1 条 needs_review 外已清零 low。**

### 8. RAG 与检索增强 claim 清理

已完成：

- RAG 与检索增强 12 条 low claim 全部清完。
- 6 条误归类重归（4 条 Claude Code Memory→Agent、1 条交易问诊 Agent→Agent、1 条采样质检→Prompt）。
- 新增人工页：`wiki_manual/RAG与检索增强审校.md`。

覆盖内容：

- 检索技术（HNSW、IVF、Metadata 过滤、SPLADE、grep vs 向量搜索）。
- Embedding 演进与选型（BGE 优先、业务数据评估）。
- 文档切分（层级划分 + 句子级 overlap）。
- RAG 质量治理五层框架。
- RAG 幻觉来源与 Prompt 矛盾。
- 权限控制三层架构。
- 性能优化（三层缓存、延迟、内存 swap、批量写入抖动）。
- HyDE、Reranker 阈值、GraphRAG 对比、查询路由。

当前 Prompt 约束与上下文设计 claim 分布：

```text
high=0
medium=12
low=0
```

## 当前总体状态

最近一次重建后：

```text
claims=139
health check=0 error / 7 warning
全局 claim 分布：
high=22
medium=116
low=1
```

主题分布大致为：

```text
Agent 系统架构：high=13, medium=40, low=1
RAG 与检索增强：high=0, medium=37, low=0
Prompt 约束与上下文设计：high=0, medium=13, low=0
微调、轨迹与训练数据：high=1, medium=10, low=0
评测集与数据构造：high=5, medium=6, low=0
Text2SQL 与查询校验：high=3, medium=5, low=0
容错、权限与安全边界：high=0, medium=3, low=0
规划、执行与反思：high=0, medium=2, low=0
```

## 还没做的事

### P0：清理低置信 claim（已完成 ✅）

全部 8 个主题的低置信 claim 已清完，仅剩 1 条 Agent 系统架构下已标记 `needs_review` 的待复查来源（只有外部链接无本地材料）。全局 low 从 29→1。

### P1：重写自动主题页摘要区（已完成 ✅）

三个自动主题页 `wiki_generated/Agent_系统架构.md`、`wiki_generated/Text2SQL_与查询校验.md`、`wiki_generated/Prompt_约束与上下文设计.md` 的摘要区已基于 `data/claims.jsonl` 中的 high/medium claim 重写。新版结构：核心判断 → 工程实现/专题展开 → 面试表达 → 支撑 claim → 待确认 → 证据表。OCR 噪声已清除。

### P2：补 source_url / label 字段（部分完成 ✅）

label_title 和 label_summary 已通过新增的 `tools/enrich_asset_labels.py` 全部补全。健康检查 warning 从 7 降到 5。

剩余 5 个 warning 均为硬约束，无法在当前数据下修复：

- 45 条 `search_corpus` 缺 source_url（需 P3 恢复同步链路）。
- 2 条只有 OneNote 内部来源。
- 11 组图片哈希重复（信息性，同一图片跨页面出现）。
- 22 条语料命中 OCR 噪声（需视觉模型重读）。
- 45 条 claim 缺 source_urls（是 source_url 缺失的下游效应）。

`tools/enrich_asset_labels.py` 已内置 source_url 双向回填（asset↔corpus↔claims），P3 恢复链路后运行即可自动传播。

### P3：恢复完整 OneNote 到 app 的重建链路（已完成 ✅）

四个缺失脚本已补回：

- `tools/sync_onenote_agent.ps1`：OneNote COM 同步（需本机 OneNote 桌面版）。
- `tools/enrich_agent_ocr.py`：Tesseract OCR 富化。
- `tools/build_agent_wiki.py`：构建 corpus/图谱/topics/wiki。
- `tools/rebuild_agent_wiki.ps1`：完整管道编排（sync→enrich→build→labels→lint）。

`build_agent_wiki.py` 内置 guard 自动跳过人工审校页（含 `## 核心判断` 标记），P1 页面不会被覆盖。日常维护使用 `rebuild_derived_layers.ps1` 即可。

## 接手建议

如果继续当前路线，建议下一位 AI 按这个顺序做：

1. 运行：

```powershell
git status --short --branch
& .\tools\rebuild_derived_layers.ps1
```

2. 打开：

```text
reports/optimization_backlog.md
reports/wiki_health_report.md
data/claim_overrides.json
```

3. 下一步高价值方向：
   - 用视觉模型重读关键图片，提升 RAG/Prompt 主题的 claim 置信度（当前这两个主题没有 high claim）。
   - 对关键 source_url 做网页正文抓取，写入 best_text（比 OCR 更可靠）。
   - 在 OneNote 桌面版可用时运行 `sync_onenote_agent.ps1` 测试完整同步链路。

## 重要注意事项

- `data/claims.jsonl` 是派生文件，会被脚本重建。
- 人工审校结论必须写到 `data/claim_overrides.json`。
- 自动生成页 `wiki_generated/` 不应手工长期修改。
- 人工长期理解写到 `wiki_manual/`。
- 文件保持 UTF-8 和 LF。
- 用户偏好：脚本顶部显式变量，不喜欢复杂命令行参数。
- Git 只作本地备份，不要主动 push。
