# Prompt 约束与上下文设计

<!-- generated: do not hand-edit this file; put durable notes in ../wiki_manual/ -->

## 自动摘要

围绕 System Prompt 架构、结构化输出约束、工具调用边界、上下文管理策略和 MCP/Hooks 机制的材料集合。

- 证据数量：14 条，均为图片证据。
- 涉及 OneNote 页面：Agent, Claude code, RAG, 提示词, 杂项。
- 关联人工审校页：[Prompt约束与上下文设计审校](../wiki_manual/Prompt约束与上下文设计审校.md)。

## 核心判断

- **提示词 + 运行时双层防御优于单纯 Prompt 或单纯工具校验**：Prompt 层告诉模型规则（如"编辑前先读取文件"），运行时层在工具执行时真正检查前提条件是否满足（检查对话历史中有没有 Read 调用）。两层各管一摊、互相兜底。`[agent_img_010_031]`
- **结构化输出选型是合规性-成本-供应商锁定的三角权衡**：六类技术路线（Prompt 引导、输出后校验、约束解码、监督微调、RL 强化、接口化 API）的合规强度和工程成本差异巨大，金融等高合规场景应走向约束解码或接口化能力，低风险场景 Prompt 引导即可。`[agent_img_009_009][agent_img_009_010]`
- **金融 RAG 应采用三层防幻觉体系**：事前结构化输出约束（JSON 字段类型/值域，数字从原文抽取而非推算）、事中引用一致性校验（NLI 逐句比对原文）、事后置信度分级路由人工复核。`[agent_img_001_017]`
- **上下文超长时用 Map-Reduce 拆分处理**：大 MR 或大规则集会稀释模型注意力导致漏召，将长上下文拆为"拆分—处理—合并"三段流水线可缓解注意力衰减问题。`[agent_img_009_003]`

## 结构化输出

### 六类技术路线对比

| 路线 | 原理 | 优势 | 局限 |
|---|---|---|---|
| Prompt 引导 | 自然语言描述输出格式 | 零成本、快速部署 | 无法保证 100% 格式合规 |
| 输出后校验 | 解析输出后正则/JSON Schema 校验 | 事后保障、不依赖模型能力 | 治标不治本，坏输出已产生 |
| 约束解码 | 逐 token 限制合法候选集 | 可 100% 语法合规 | 推理开销大、实现复杂 |
| 监督微调 | 训练数据中固化输出格式 | 永久改变行为、稳定 | 有 plateau 现象、需要大量标注 |
| RL 强化 | 以格式合规为 reward 信号训练 | 可突破 SFT 高原 | 训练成本高、reward hacking 风险 |
| 接口化 API | API 参数直接强制 JSON Schema | 端到端类型安全 | 依赖特定供应商 |

选型建议：金融等高合规场景优先考虑约束解码或接口化 API；低风险场景 Prompt 引导+输出后校验即可。

### 金融三层防幻觉

1. **事前约束**：强制 JSON 格式，每个字段有严格类型和值域约束。数字字段直接从 RAG 原文抽取而非模型推算。
2. **事中校验**：NLI 模型逐句比对生成内容与原始文档，声明级溯源验证。
3. **事后路由**：低置信案例强制路由人工复核，沉淀为难例数据集持续迭代。

## Prompt 架构与缓存

- **分段注册表**：System Prompt 应拆成有名称、可定位的段落，而非一大段文本。
- **稳定前缀（可缓存）**：Agent 身份、安全规则、工具使用原则、输出格式。
- **动态边界后（不可缓存）**：当前时间、用户状态、工具调用结果、检索结果。
- **Memory 注入位置**：在 system prompt 前部注入，位于核心指令之后、CLAUDE.md 之前。

## 工具调用边界

- **Prompt 层面明确工具能力边界**：不要让模型猜测工具能做什么，应在 prompt 中描述清楚每个工具的职责和不适合场景。
- **Hooks 适合轻量阻断和自动化**：当前支持的 Hook 点包括 PreToolUse、PostToolUse、PostToolUseFailure 等，适合在工具调用前后做权限控制、日志记录和结果校验，不适合需要大量上下文的复杂语义判断——后者该用 Skill 或 Subagent。
- **AskUserQuestion 工具演进**：第一版在现有工具上加参数（污染工具职责）、第二版用特殊格式标记（解析脆弱）、第三版独立为专用工具（职责清晰、UI 可定制）。

## MCP 三层架构

MCP 不是 Client+Server 二元结构，而是三层：

| 层 | 内容 | 职责 |
|---|---|---|
| 角色层 | Host / Client / Server | 角色定位、会话、权限边界 |
| 能力层 | Tools / Resources / Prompts | 暴露什么能力、发现与描述解析 |
| 协议层 | JSON-RPC 2.0 + stdio / Streamable HTTP | 通信方式 |

应用层与协议层应有清晰的防腐层，避免协议变更影响业务逻辑。

对应 evidence：`agent_img_010_031`、`agent_img_009_009-010`、`agent_img_001_017`、`agent_img_009_003`、`agent_img_010_023`、`agent_img_007_001`、`agent_img_010_005-006`、`agent_img_002_018-019`、`agent_img_001_019`。

## 面试表达

- **"结构化输出怎么做"** → 不是"写好 Prompt 就行"。六条技术路线（Prompt 引导→输出校验→约束解码→微调→RL→接口化 API），合规强度和成本递增。金融场景走约束解码或接口化，低风险场景 Prompt+校验即可。
- **"怎么防止 Agent 幻觉"** → 三层体系：事前结构化约束（字段类型/值域/原文抽取禁止推算）、事中 NLI 逐句溯源校验、事后低置信路由人工复核。
- **"Agent 怎么在中途问用户问题"** → 不要给已有工具加参数（污染职责），做成独立的 AskUserQuestion 工具。这样职责清晰、UI 可定制、不破坏现有工具语义。
- **"MCP 是什么"** → 三层：角色层（Host/Client/Server）决定谁跟谁通信、能力层（Tools/Resources/Prompts）暴露什么、协议层（JSON-RPC 2.0 + stdio/HTTP）怎么通信。最大误区是把 MCP 当 Client+Server 二元结构。

## 支撑 claim（medium confidence）

| claim | 领域 |
|---|---|
| 结构化输出六类技术路线，从 Prompt 引导到接口化 API，合规强度和成本递增 | 结构化输出 |
| 金融 RAG 三层防幻觉：事前约束（结构化输出）、事中校验（NLI 溯源）、事后路由（人工复核） | 防幻觉 |
| 双层防御：提示词层告知规则 + 运行时层检查前提条件 | 工程实现 |
| MCP 三层结构（角色/能力/协议），不应简化为 Client+Server 二元 | MCP |
| AskUserQuestion 应独立为专用工具而非嵌入已有工具 | 工具设计 |
| Hooks 适合轻量阻断和自动化，不适合复杂语义判断 | 架构边界 |
| Map-Reduce 拆分处理可缓解长上下文中模型注意力衰减 | 上下文管理 |
| RAG 专用 Prompt 应区分角色定义和检索片段引用规则 | Prompt 设计 |

## 待确认

本主题当前无待确认 claim（low=0），但所有 13 条 claim 均为 medium 置信度。主要原因是该主题证据全为截图 OCR 提取，无文本链接可直接引用，提升置信度需要视觉模型重读关键图片。

## 来源链接

- https://mp.weixin.qq.com/s/8GKYJtG3SZDA_8KTN55ThQ
- https://mp.weixin.qq.com/s/8bI19Vfn-5Kqpwp0Yg1kdg
- https://mp.weixin.qq.com/s/TYNg6RT79DHW8n8LxP8Rag
- https://mp.weixin.qq.com/s/uU5Q8K2hYpqsc0PDxoyFUQ
- https://www.bestblogs.dev/article/288cbab6
- https://www.bestblogs.dev/article/5c79977a

## 证据表

| evidence_id | 类型 | OneNote 页面 | 原链接 | 图片 | 摘要片段 |
|---|---|---|---|---|---|
| agent_img_007_001_e34249d9df55 | onenote_image | 提示词 | [source](https://mp.weixin.qq.com/s/uU5Q8K2hYpqsc0PDxoyFUQ) | [image](../raw/images/agent_img_007_001_e34249d9df55.png) | Prompt 要明确工具调用边界：错误的 System Prompt 只告诉模型"你可以使用以下工具"而不约束何时不该用。 |
| agent_img_009_002_7af3c22a8eaf | onenote_image | 杂项 |  | [image](../raw/images/agent_img_009_002_7af3c22a8eaf.png) | 训练内存估算：梯度、优化器状态等（已重归微调、轨迹与训练数据主题）。 |
| agent_img_010_023_d582b70d06a2 | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s/TYNg6RT79DHW8n8LxP8Rag) | [image](../raw/images/agent_img_010_023_d582b70d06a2.png) | Memory 注入在 system prompt 的第十段，在 CLAUDE.md 之前。 |
| agent_img_009_003_61e2922ef802 | onenote_image | 杂项 | [source](https://www.bestblogs.dev/article/288cbab6) | [image](../raw/images/agent_img_009_003_61e2922ef802.png) | Map-Reduce 长上下文处理：大 MR 或大规则集导致注意力稀释，采用拆分—处理—合并流水线。 |
| agent_img_010_005_772065f10bc8 | onenote_image | Claude code | [source](https://www.bestblogs.dev/article/5c79977a) | [image](../raw/images/agent_img_010_005_772065f10bc8.png) | AskUserQuestion 三次迭代：给 Bash 加参数→特殊格式标记→独立专用工具。 |
| agent_img_001_019_e69b9d279a6c | onenote_image | Agent | [source](https://mp.weixin.qq.com/s/8GKYJtG3SZDA_8KTN55ThQ) | [image](../raw/images/agent_img_001_019_e69b9d279a6c.png) | RAG 专用 Prompt 结构：角色定义、参考文档、格式化检索片段、回答规则。 |
| agent_img_002_018_21ba6bfa8425 | onenote_image | RAG | [source](https://mp.weixin.qq.com/s/8bI19Vfn-5Kqpwp0Yg1kdg) | [image](../raw/images/agent_img_002_018_21ba6bfa8425.png) | MCP 三层面试表达：角色层（Host/Client/Server）、能力层（Tools/Resources/Prompts）、协议层。 |
| agent_img_010_006_91f3a9315fd6 | onenote_image | Claude code | [source](https://www.bestblogs.dev/article/5c79977a) | [image](../raw/images/agent_img_010_006_91f3a9315fd6.png) | Hooks 适合轻量阻断，不适合需要大量上下文理解的复杂判断（该用 Skill 或 Subagent）。 |
| agent_img_001_017_29006a1055a1 | onenote_image | Agent |  | [image](../raw/images/agent_img_001_017_29006a1055a1.png) | 金融三层防幻觉：结构化输出约束（事前）、引用一致性校验（事中）、置信度分级路由（事后）。 |
| agent_img_009_010_1123d496a7e0 | onenote_image | 杂项 |  | [image](../raw/images/agent_img_009_010_1123d496a7e0.jpg) | 结构化输出六类技术路线对比表：原理、典型应用、优势、局限。 |
| agent_img_001_014_65226eff0183 | onenote_image | Agent |  | [image](../raw/images/agent_img_001_014_65226eff0183.png) | Workflow 是上下文封装的基本单位（已重归 Agent 系统架构主题）。 |
| agent_img_002_019_6a3f08dd5a27 | onenote_image | RAG | [source](https://mp.weixin.qq.com/s/8bI19Vfn-5Kqpwp0Yg1kdg) | [image](../raw/images/agent_img_002_019_6a3f08dd5a27.png) | MCP 三层结构与已有标准的互补关系。 |
| agent_img_009_009_fd719d4b2dcf | onenote_image | 杂项 |  | [image](../raw/images/agent_img_009_009_fd719d4b2dcf.png) | 结构化输出技术从 Prompt 引导到接口化能力的演进全景。 |
| agent_img_010_031_94b80bbf7ca5 | onenote_image | Claude code |  | [image](../raw/images/agent_img_010_031_94b80bbf7ca5.png) | 双层防御：提示词层告知规则 + 运行时层检查前提条件。 |

## 后续人工补充建议

- 将稳定理解写入 `wiki_manual/`，不要直接修改本文件。
- 已有关联审校页：[Prompt约束与上下文设计审校](../wiki_manual/Prompt约束与上下文设计审校.md)。
- 本主题全部为图片证据无文本链接源，提升 claim 置信度需要视觉模型重读关键图片。

_Updated at 2026-05-23_
