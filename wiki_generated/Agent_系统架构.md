# Agent 系统架构

<!-- generated: do not hand-edit this file; put durable notes in ../wiki_manual/ -->

## 自动摘要

围绕工具调用、执行链路、状态管理、观测反馈和 Agent 项目工程化的材料集合。

- 证据数量：54 条，其中图片 43 条、文本链接 11 条。
- 涉及 OneNote 页面：Agent, Claude code, RAG, 微调, 杂项。
- 关联人工审校页：[Agent工程模式审校](../wiki_manual/Agent工程模式审校.md)、[AgentMemory机制审校](../wiki_manual/AgentMemory机制审校.md)。

## 核心判断

- **安全默认值 > 默认允许**：Agent 工具系统应采用安全默认值，工具构建时默认假设最危险的情形，由开发者显式声明并发安全、只读等属性。`[agent_img_010_004]`
- **文件编辑前必须读取**：这不是提示词建议，而是运行时硬约束——工具执行时检查对话历史中是否存在对应 Read 调用。`[agent_img_010_030]`
- **Prompt 分段注册表 + 缓存边界**：稳定内容（身份、安全规则、工具原则、输出格式、错误处理）放前缀；动态内容（时间、状态、检索结果、工具结果）放缓存边界之后。`[agent_img_010_027][agent_img_010_026]`
- **重试需要预算 + 分类 + 抖动**：不同错误码不应统一重试，过载时应减少请求，写操作需考虑幂等性，指数退避须加随机抖动。`[agent_img_010_029][agent_img_010_028]`
- **Memory ≠ Session**：Session 是一次会话的聊天日志，Memory 是项目级长期笔记，从对话中提炼出可复用的信息。应按 user/feedback/project/reference 四类分层，分别管理加载时机、优先级和时效性。`[agent_img_010_016][agent_img_010_020]`
- **Memory 应基于文件系统而非向量库**：MEMORY.md 索引 + 子 Markdown 文件的结构可读、可编辑、可审计，比黑盒向量检索更适合偏好类记忆的长期维护。`[agent_img_010_017][agent_link_010_001]`
- **Badcase 闭环可将准确率从 76% 提升到 89%**：三路收集（用户反馈、客服工单、自动检测）+ 四分类（检索失败、幻觉、路由错误、知识缺失）+ 原 case 验证 + 全量回归 + 灰度发布。`[agent_img_002_006]`

## Memory 系统设计

### 四类记忆与检索策略

| 类型 | 内容 | 加载时机 | 检索策略 |
|---|---|---|---|
| user | 用户角色、身份、长期偏好 | 会话开始全量加载 | 直接注入 system prompt |
| feedback | 用户反馈的规则和偏好 | 执行操作前检索 | 最高优先级约束当前行为 |
| project | 项目状态、决策、截止日期 | 按任务相关性检索 | 先检查绝对时效 |
| reference | 外部系统引用、链接 | 仅按需检索 | 需要外部信息时触发 |

### 记忆提取触发策略

成本和覆盖率之间的权衡：
- 规则驱动触发：可预测但不够灵活。
- LLM 自主触发：更灵活但成本高、不确定性大。
- 工程实践：后台异步触发，用 ADD/UPDATE/DELETE/NOOP 处理提取结果。

### 并发控制

后台记忆提取需合并并发请求：同一时间只运行一个提取任务，运行期间新请求只标记 dirty，当前任务结束后根据 watermark 统一扫描新增消息。

### 不应进入 Memory 的内容

可从代码或 git 历史恢复的实现细节不应写入 Memory。应保存无法从当前状态自动推导出的关键决策：用户偏好、方案选择原因、bug 根因。

对应 evidence：`agent_img_010_012-022`、`agent_img_010_013-019`、`agent_link_010_001-004`、`agent_img_002_009`、`agent_img_001_008`。

## 工具安全与设计

### 安全默认值

工具构建的默认假设应偏向最危险情形。工具开发者必须显式声明：
- 并发安全属性。
- 只读/读写属性。
- 输入感知的权限控制（如 Bash 中 `ls` vs `rm` 的安全属性完全不同）。

### 搜索提示与描述的分离

- `searchHint`：给 ToolSearch 匹配用的短能力标签。
- `description`：工具已加载后给模型理解参数和调用边界的正式说明。

### 延迟加载

工具数量超过阈值时，不应将所有完整 schema 发送给模型。核心工具完整加载，其余标记为 deferred 并仅暴露"工具名 + 延迟加载标记"。模型通过 ToolSearch 按需获取。

### Grep 封装优于 Raw Shell

Claude Code 将 Grep 封装成带结构化参数的专用工具，LLM 不需要解析原始 shell 输出，减少出错概率且系统更容易控制信息量。

对应 evidence：`agent_img_010_004`、`agent_img_010_003`、`agent_img_010_002`、`agent_img_010_009`、`agent_img_010_010`、`agent_img_001_016`。

## Prompt 架构与缓存

### 分段注册表

系统 Prompt 不应是巨大字符串，而应拆成有名称、可定位、可标注缓存属性的段落注册表。

**稳定前缀（可缓存）**：Agent 身份、安全规则、工具使用原则、输出格式、错误处理规则。

**动态边界后（不可缓存）**：当前时间、用户状态、会话变量、检索结果、工具调用结果、动态工具列表。

动态内容放入缓存边界后时，应要求调用者说明为什么必须每轮重算。

### 会话中途不切模型

Prompt 缓存是模型唯一的。中途切换模型会破坏已建立的缓存。确实需要切换时用 Subagent。

对应 evidence：`agent_img_010_026-027`、`agent_img_010_007`、`agent_img_010_024`。

## 多 Agent 编排

### 四种模式

| 模式 | 适合场景 | 主要风险 |
|---|---|---|
| 顺序管道 | 强依赖步骤 | 前序错误传递 |
| Map-Reduce | 并行任务 | 汇总和冲突裁定困难 |
| 层级嵌套 | 深层复杂任务 | 必须限制深度 |
| 路由分发 | 请求类型多样 | 路由错误放大 |

### AgentTeam vs Task 派发

Task 派发是主 Agent 发指令、子 Agent 执行并返回结果的单向交互。AgentTeam 是持续协作，Leader-Worker-Verifier 需要解决任务分解、子任务调度、失败处理、并行结果合并和矛盾结论裁定。

### 多 Agent 协作成本

三类单 Agent 不会遇到的成本：交接成本（信息从上一个 Agent 能懂翻译成下一个 Agent 能用）、共享上下文聚合成本、并行结果合并与冲突裁定成本。

对应 evidence：`agent_img_009_011-014`、`agent_img_001_020`。

## 上下文管理

### 头部保护、尾部保护、中间摘要

- 头部保护：保留系统指令和初始任务定义。
- 尾部保护：保留最近几轮对话维持短期连贯性。
- 中间摘要：对冗长工具调用过程和推理步骤裁剪并生成摘要。

### 工具结果大小控制

两层限制：先限制单个工具结果，再限制同一条消息里多个工具结果的总大小，防止上下文窗口被撑爆。

对应 evidence：`agent_img_009_008`、`agent_img_010_001`、`agent_img_010_025`。

## Workflow 与 Skill

### Workflow 是上下文封装的基本单位

Workflow 包含特定业务的上下文和对通用 Skill 的执行编排。复杂任务不应由单个 Skill 完成（会导致复杂度过高、多 Skill 执行准确率低、编写耗时高），应拆分为多个单一职责 Skill 并用 Workflow 编排。

### Agent 轨迹结构

标准 Agent 轨迹应包含：用户问题 → 模型思考 → 工具调用 → 工具观察结果 → 最终回答。工具返回内容属于外部 observation，不应和模型内部推理或最终回答混在一起。

### Skill 沉淀机制

Hermes Agent 通过 _skill_nudge_interval 计数器在连续 N 轮对话后自动提醒 Agent 整理经验为 Skill。积累的 Skill 让 Agent 下次遇到类似问题时直接复用而非从零探索。

对应 evidence：`agent_img_001_014-015`、`agent_img_001_013`、`agent_img_005_001`、`agent_img_009_005-006`。

## 重试与错误处理

### 重试六要素

1. **预算**：总重试次数、特定错误码单独次数、等待上限。
2. **分类**：429、529、408、409、401、403、5xx 语义不同。
3. **过载降载**：过载时减少请求，不是所有请求一起重试。
4. **幂等性**：涉及写文件、调用工具或提交变更时考虑重复执行副作用。
5. **可观测性**：每次 query/success/error 打事件。
6. **用户体验**：等待期间让用户看到状态。

### 指数退避 + 随机抖动

固定退避时间点（500ms、1s、2s、4s）会让大量客户端在相同时间点集体重试，进一步放大后端压力。应加入随机抖动分散重试时间。

对应 evidence：`agent_img_010_029`、`agent_img_010_028`。

## Badcase 闭环

三路收集（用户反馈 + 客服工单 + 自动检测）→ 四分类（检索失败/幻觉生成/路由错误/知识缺失）→ 按类分配修复 → 原 case 验证 → 全量回归（确认核心指标退化不超过 2%）→ 灰度发布（10% 起步）。实践表明可将准确率从 76% 提升到 89%。

对应 evidence：`agent_img_002_006`、`agent_img_001_005`、`agent_link_001_004`。

## 面试表达

- **"Agent 的工具安全怎么做"** → 安全默认值 + 输入感知的权限控制 + 文件编辑前读取的硬约束 + 工具参数类型/范围校验。
- **"Agent 怎么记住用户偏好"** → Memory 不是把所有东西塞向量库。按 user/feedback/project/reference 四类分层，文件系统索引，分别管理加载时机和时效。
- **"多 Agent 怎么编排"** → 四种模式选型（管道/Map-Reduce/层级/路由），要解决的不只是任务拆分还有交接成本、并行合并和冲突裁定。
- **"RAG 系统上线后答案不对怎么处理"** → Badcase 闭环：三路收集 + 四分类 + 原 case 修复 + 全量回归 + 灰度发布。6 个月准确率 76%→89%。
- **"重试怎么做"** → 不是失败就重试。需要预算、错误分类、过载降载、幂等性、可观测性、随机抖动。

对应 evidence：`agent_img_010_004`、`agent_img_010_020`、`agent_img_010_029`、`agent_img_009_011`、`agent_img_002_006`。

## 支撑 claim（high confidence）

| claim | 领域 |
|---|---|
| Agent 工具系统应采用安全默认值，由开发者显式声明并发安全和只读属性 | 工具安全 |
| 文件编辑工具应强制编辑前读取，运行时检查对话历史中是否存在 Read 调用 | 工具安全 |
| Prompt 缓存设计应把稳定内容放前缀、动态内容放边界后 | Prompt 架构 |
| 系统 Prompt 应拆成有名称、可定位、可缓存标注的段落注册表 | Prompt 架构 |
| Agent 重试需要预算、错误分类、过载降载、幂等性和可观测性 | 重试 |
| Agent Memory 按 user/feedback/project/reference 四类分层，分别管理加载时机、优先级和时效性 | Memory |
| 四类 Memory 应采用不同检索策略 | Memory |
| Memory 可用 MEMORY.md 索引 + 子文件结构，文件 ID 使用稳定哈希 | Memory |
| 记忆提取触发策略应在成本和覆盖率间平衡，采用后台异步 + 合并并发 | Memory |
| Badcase 闭环三路收集 + 四分类 + 全量回归 + 灰度发布，准确率 76%→89% | Badcase |
| Agent Memory 是除知识库之外的第二检索源，两路检索结果共同进入回答生成 | Memory |
| 把异构信息混入无分类向量库会导致时效不同的信息难以清理 | Memory |

## 待确认

| claim | 原因 |
|---|---|
| agent_link_001_001：只有外部链接和重复 URL | 无本地材料可审校，已标记 needs_review |

## 来源链接

- https://developer.aliyun.com/article/1675940
- https://developer.aliyun.com/article/1714754?spm=a2c6h.24874632.expert-profile.22.16451bb6I2z2HU
- https://developer.aliyun.com/article/1732681?spm=a2c6h.24874632.expert-profile.13.16451bb6uGrOtt
- https://mp.weixin.qq.com/s/8bI19Vfn-5Kqpwp0Yg1kdg
- https://mp.weixin.qq.com/s/BEUadA_OwAVpL1srTmdbxQ
- https://mp.weixin.qq.com/s/F2QU3cSO7sOW9ZPVAEkt_w
- https://mp.weixin.qq.com/s/Rjm4kpKifyVyH27k_FWStQ
- https://mp.weixin.qq.com/s/TYNg6RT79DHW8n8LxP8Rag
- https://mp.weixin.qq.com/s/dDczjoNM3URc8ExcJL1hPg
- https://mp.weixin.qq.com/s/vOh3qVl9jStG8MSPSnF6jw
- https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490229&idx=1&sn=1bfab0f67ac2cdc8d9ee687fb189908e
- https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490253&idx=1&sn=673f4845b0501552126cc02c0725dd66
- https://www.bestblogs.dev/article/5c79977a
- https://www.bestblogs.dev/article/f0deaa0c?entry=explore_card&from=%2Fexplore
- https://www.doubao.com/thread/w4f9e93dc6a8ca880
- https://zhanghandong.github.io/harness-engineering-from-cc-to-ai-coding/part1/ch02.html

## 证据表

| evidence_id | 类型 | OneNote 页面 | 原链接 | 图片 | 摘要片段 |
|---|---|---|---|---|---|
| agent_img_009_013_79ba71d907a8 | onenote_image | 杂项 | [source](https://www.bestblogs.dev/article/f0deaa0c) | [image](../raw/images/agent_img_009_013_79ba71d907a8.png) | Agent 间通讯复用用户操作能力：用户在前端可以给 Agent 发指令、启动新 Agent、中止任务、总结进展。 |
| agent_img_010_008_39a6a4c7207f | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s/dDczjoNM3URc8ExcJL1hPg) | [image](../raw/images/agent_img_010_008_39a6a4c7207f.png) | Explore 类型子 Agent 只配备搜索和读取工具（Grep、Glob、Read），不能编辑、执行命令或嵌套启动新 Agent。 |
| agent_img_009_006_406455c22467 | onenote_image | 杂项 | [source](https://developer.aliyun.com/article/1732681) | [image](../raw/images/agent_img_009_006_406455c22467.png) | _skill_nudge_interval=10 表示 Agent 连续 10 轮无 Skill 变更时系统提醒整理经验。 |
| agent_img_009_012_b07abd5153e2 | onenote_image | 杂项 | [source](https://www.bestblogs.dev/article/f0deaa0c) | [image](../raw/images/agent_img_009_012_b07abd5153e2.png) | 多 Agent 协作成本：交接翻译成本、共享上下文聚合成本、并行结果合并与冲突裁定成本。 |
| agent_img_009_014_8bd0eb29ad10 | onenote_image | 杂项 | [source](https://www.bestblogs.dev/article/f0deaa0c) | [image](../raw/images/agent_img_009_014_8bd0eb29ad10.png) | AgentTeam vs Task 派发：AgentTeam 是持续协作，Task 派发是单向指令-返回。 |
| agent_img_010_002_059f630d18fa | onenote_image | Claude code | [source](https://zhanghandong.github.io/harness-engineering-from-cc-to-ai-coding/part1/ch02.html) | [image](../raw/images/agent_img_010_002_059f630d18fa.png) | 工具延迟加载：核心工具完整加载，deferred 工具初始只暴露工具名。 |
| agent_img_010_004_7748829a7526 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_004_7748829a7526.png) | 工具安全默认值：默认假设最危险情形，开发者显式声明并发安全和只读属性。 |
| agent_img_010_027_8cb3c4541134 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_027_8cb3c4541134.png) | 动态 Prompt 内容应放在缓存边界之后，要求调用者说明为什么必须每轮重算。 |
| agent_img_010_007_6a0c1a08f3ce | onenote_image | Claude code | [source](https://www.bestblogs.dev/article/5c79977a) | [image](../raw/images/agent_img_010_007_6a0c1a08f3ce.png) | 会话中途不切换模型：Prompt 缓存是模型唯一的，切换会破坏缓存。 |
| agent_img_001_020_34269172aa96 | onenote_image | Agent | [source](https://mp.weixin.qq.com/s/BEUadA_OwAVpL1srTmdbxQ) | [image](../raw/images/agent_img_001_020_34269172aa96.png) | Supervisor 模式是生产环境最主流的 Multi-Agent 架构，决策权和执行权分离。 |
| agent_img_010_009_fc55588560a1 | onenote_image | Claude code | [source](https://zhanghandong.github.io/harness-engineering-from-cc-to-ai-coding/part1/ch02.html) | [image](../raw/images/agent_img_010_009_fc55588560a1.png) | ToolSearch 按需加载：模型通过搜索工具名和描述来发现并加载延迟工具。 |
| agent_img_010_018_b5f17153c5f1 | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490253) | [image](../raw/images/agent_img_010_018_b5f17153c5f1.png) | 记忆提取用 ADD/UPDATE/DELETE/NOOP 处理结果，后台异步触发。 |
| agent_img_005_007_16a0017a3bf3 | onenote_image | 微调 | [source](https://mp.weixin.qq.com/s/vOh3qVl9jStG8MSPSnF6jw) | [image](../raw/images/agent_img_005_007_16a0017a3bf3.png) | 工具调用训练数据需覆盖单工具、多工具并行、多轮对话、失败重试等场景。 |
| agent_img_009_005_9da3fe710b2a | onenote_image | 杂项 | [source](https://developer.aliyun.com/article/1732681) | [image](../raw/images/agent_img_009_005_9da3fe710b2a.png) | Hermes 动态 Skill 沉淀：复盘复杂任务，提炼成可复用 Skill。 |
| agent_img_009_011_f3f3422d45ce | onenote_image | 杂项 | | [image](../raw/images/agent_img_009_011_f3f3422d45ce.png) | 多 Agent 四种编排模式：顺序管道、Map-Reduce、层级嵌套、路由分发。 |
| agent_img_005_001_bad29a1acc99 | onenote_image | 微调 | | [image](../raw/images/agent_img_005_001_bad29a1acc99.png) | Agent 轨迹结构：用户问题→思考→工具调用→观察→最终回答。 |
| agent_img_010_025_fa1c65c42292 | onenote_image | Claude code | [source](https://zhanghandong.github.io/harness-engineering-from-cc-to-ai-coding/part1/ch02.html) | [image](../raw/images/agent_img_010_025_fa1c65c42292.png) | queryLoop 用分层恢复避免无限循环。 |
| agent_img_010_001_e39c23430755 | onenote_image | Claude code | [source](https://zhanghandong.github.io/harness-engineering-from-cc-to-ai-coding/part1/ch02.html) | [image](../raw/images/agent_img_010_001_e39c23430755.png) | 工具结果两层大小控制：先限制单个结果，再限制同消息多结果总大小。 |
| agent_img_010_024_4ec2339a3a62 | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s/TYNg6RT79DHW8n8LxP8Rag) | [image](../raw/images/agent_img_010_024_4ec2339a3a62.png) | Claude Code system_prompt 构建顺序：核心指令→环境→工具→摘要策略→Memory。 |
| agent_img_010_026_92e884da861b | onenote_image | Claude code | | [image](../raw/images/agent_img_010_026_92e884da861b.png) | 缓存命中率监控设计：稳定前缀可缓存，动态内容放缓存边界后。 |
| agent_img_010_020_b527d8b886ff | onenote_image | Claude code | | [image](../raw/images/agent_img_010_020_b527d8b886ff.png) | Agent Memory 应被设计为需要主动管理的系统，按四类分层。 |
| agent_img_009_008_71cb71df22d7 | onenote_image | 杂项 | | [image](../raw/images/agent_img_009_008_71cb71df22d7.png) | 上下文压缩：头部保护、尾部保护、中间摘要策略。 |
| agent_img_010_029_ea01ad355cb5 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_029_ea01ad355cb5.png) | 重试机制六要素：预算、分类、过载降载、幂等性、可观测性、用户体验。 |
| agent_img_001_016_55162987dd1e | onenote_image | Agent | | [image](../raw/images/agent_img_001_016_55162987dd1e.png) | 工具参数类型/范围校验，拦截因幻觉产生的错误工具调用。 |
| agent_img_010_010_900f839d220c | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s/dDczjoNM3URc8ExcJL1hPg) | [image](../raw/images/agent_img_010_010_900f839d220c.png) | Claude Code vs Codex 搜索工具封装对比：封装 Grep 为结构化工具。 |
| agent_img_010_003_df2c941682fd | onenote_image | Claude code | | [image](../raw/images/agent_img_010_003_df2c941682fd.png) | searchHint（短能力标签）和 description（正式调用说明）的分工。 |
| agent_img_010_030_907dbaa011f8 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_030_907dbaa011f8.png) | FileEditTool：编辑前必须读取——运行时硬约束。 |
| agent_img_002_020_2223a2a396de | onenote_image | RAG | [source](https://mp.weixin.qq.com/s/8bI19Vfn-5Kqpwp0Yg1kdg) | [image](../raw/images/agent_img_002_020_2223a2a396de.png) | MCP 两种通信方式：stdio（本地）和 Streamable HTTP（远程）。 |
| agent_img_001_005_ce1638579d53 | onenote_image | Agent | | [image](../raw/images/agent_img_001_005_ce1638579d53.png) | Badcase 闭环将准确率从 76% 提升到 89%。 |
| agent_img_001_015_5be324090a5c | onenote_image | Agent | | [image](../raw/images/agent_img_001_015_5be324090a5c.png) | Workflow 封装业务上下文和 Skills 执行编排。 |
| agent_img_010_019_209453d6a810 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_019_209453d6a810.png) | 后台记忆提取并发控制：同一时间只运行一个提取任务，新请求标记 dirty。 |
| agent_link_001_004_b0fd20db1549 | onenote_text_link | Agent | [source](https://mp.weixin.qq.com/s/F2QU3cSO7sOW9ZPVAEkt_w) | | RAG/Agent 系统 badcase 闭环：收集、分类、修复验证和回归测试。 |
| agent_link_001_005_2da27c38a6fa | onenote_text_link | Agent | [source](https://developer.aliyun.com/article/1714754) | | 交易领域问诊 Agent 案例：问题定位、流程调度和反馈闭环纳入工程化。 |
| agent_img_010_017_51c9eb8de69e | onenote_image | Claude code | [source](https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490229) | [image](../raw/images/agent_img_010_017_51c9eb8de69e.png) | MEMORY.md 索引 + 子文件结构，文件 ID 使用稳定哈希。 |
| agent_img_010_016_10147080437a | onenote_image | Claude code | | [image](../raw/images/agent_img_010_016_10147080437a.png) | Session vs Memory：Session 是聊天日志，Memory 是项目级长期笔记。 |
| agent_img_010_028_deae5c10a6f8 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_028_deae5c10a6f8.png) | 指数退避 + 随机抖动，避免大量客户端同时重试。 |
| agent_link_001_001_ab0d3f31e5b4 | onenote_text_link | Agent | [source](https://www.doubao.com/thread/w4f9e93dc6a8ca880) | | 待复查来源，无本地材料可审校。 |
| agent_link_001_002_3aa486062719 | onenote_text_link | Agent | [source](https://mp.weixin.qq.com/s/Rjm4kpKifyVyH27k_FWStQ) | | 文档切分：层级划分 + 句子级 overlap（已重归 RAG 与检索增强）。 |
| agent_link_001_006_14131c3a0a2a | onenote_text_link | Agent | [source](https://developer.aliyun.com/article/1675940) | | 意图识别和槽位抽取放在 Agent 调度前置层。 |
| agent_link_010_002_008f43b1ea20 | onenote_text_link | Claude code | [source](https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490253) | | 记忆提取触发策略：成本和覆盖率权衡，后台异步触发。 |
| agent_img_010_021_b3c82f1477b0 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_021_b3c82f1477b0.png) | 四类分层降低记忆库规模并提高高优先级记忆的稳定影响。 |
| agent_img_010_022_c5deb2fdfd12 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_022_c5deb2fdfd12.png) | 四类 Memory 不同检索策略：全量注入、操作前检索、任务相关性检索、按需检索。 |
| agent_img_010_012_450cba6d1d68 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_012_450cba6d1d68.png) | Memory 不保存可从代码/git 恢复的实现细节，只保存关键决策。 |
| agent_img_010_013_a7f193bf605f | onenote_image | Claude code | | [image](../raw/images/agent_img_010_013_a7f193bf605f.png) | 项目级 Memory 目录组织：MEMORY.md 入口索引 + 子文件按需读取。 |
| agent_img_010_014_190a24782f95 | onenote_image | Claude code | | [image](../raw/images/agent_img_010_014_190a24782f95.png) | 用户角色类 Memory 示例：数据科学家→关注可复现、指标口径、边界条件。 |
| agent_img_010_015_8da4dcbcb47c | onenote_image | Claude code | | [image](../raw/images/agent_img_010_015_8da4dcbcb47c.png) | MEMORY.md 是记忆目录，列出有哪些记忆及在哪个子文件。 |
| agent_img_002_009_cd3df81953ab | onenote_image | RAG | | [image](../raw/images/agent_img_002_009_cd3df81953ab.png) | Agent Memory 是知识库之外的第二检索源。 |
| agent_img_001_008_cd3df81953ab | onenote_image | Agent | | [image](../raw/images/agent_img_001_008_cd3df81953ab.png) | Agent Memory 知识库+记忆库两路检索共同进入回答。 |
| agent_img_002_006_ce1638579d53 | onenote_image | RAG | | [image](../raw/images/agent_img_002_006_ce1638579d53.png) | Badcase 闭环：三路收集 + 四分类 + 全量回归 + 灰度发布。 |
| agent_img_001_013_803b291fe2c9 | onenote_image | Agent | | [image](../raw/images/agent_img_001_013_803b291fe2c9.png) | 复杂任务用 Workflow 编排多个单一职责 Skill。 |
| agent_img_001_014_65226eff0183 | onenote_image | Agent | | [image](../raw/images/agent_img_001_014_65226eff0183.png) | Workflow 是上下文封装的基本单位。 |
| agent_link_010_001_bf6562fce929 | onenote_text_link | Claude code | [source](https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490229) | | 用户偏好记忆通过文件系统（MEMORY.md）而非向量库持久化。 |
| agent_link_010_003_11ca96cf6d58 | onenote_text_link | Claude code | [source](https://mp.weixin.qq.com/s?__biz=MzkzMDIwMzg1Mw==&mid=2247490260) | | 异构信息混入无分类向量库导致时效不同信息难以清理。 |
| agent_link_010_004_dd778098aff4 | onenote_text_link | Claude code | [source](https://mp.weixin.qq.com/s/jS4jCo1is3ZluX_hno7arA) | | Claude Code Memory 自动记录到 MEMORY.md，使用者应定期清理。 |
| agent_link_002_004_a6f5c9c86dbe | onenote_text_link | RAG | [source](https://developer.aliyun.com/article/1714754) | | 交易领域问诊 Agent 落地案例。 |

## 后续人工补充建议

- 将稳定理解写入 `wiki_manual/`，不要直接修改本文件。
- 已有关联审校页：[Agent工程模式审校](../wiki_manual/Agent工程模式审校.md)、[AgentMemory机制审校](../wiki_manual/AgentMemory机制审校.md)。
- 对关键 source_url 可后续增加网页正文抓取，形成比截图 OCR 更高层的证据。

_Updated at 2026-05-23_
