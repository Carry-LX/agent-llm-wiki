# Agent 系统的 Feature Flag 管控：让 Agent 行为可运行时调控

## 核心观点

**不要把所有 Agent 行为都写死在代码里。** Agent 里很多东西应该做成"运行时可控开关"，尤其是：模型选择、工具是否开放、Prompt 版本、MCP Server 是否启用、安全策略、灰度实验、紧急回滚。

---

## 例子 1：新工具先接进去，但不要立刻全量开放

假设你做了一个 Agent，可以调用数据库工具：

```ts
tools = [
  searchDocs,
  callApi,
  queryDatabase
]
```

`queryDatabase` 很危险，可能查错、慢、权限复杂。不要一上线就让所有用户都能用：

```ts
if (growthbook.isOn("agent_enable_database_tool")) {
  tools.push(queryDatabase)
}
```

GrowthBook 里控制：

```json
{
  "agent_enable_database_tool": false
}
```

一开始先关着。然后可以改成只给内部员工开，再逐步放量 5%、10%...

这个场景下，Feature Flag 的意义是：**工具代码已经部署好了，但是否让 Agent 使用这个工具，由运行时配置决定。** 这对 Agent 特别重要，因为 Agent 的行为不是固定 UI，而是会根据工具能力改变推理路径。

---

## 例子 2：Prompt 改版不要直接覆盖旧 Prompt

Agent 系统里经常要改系统提示词：

```ts
const systemPromptV2 = `
你是一个客服 Agent。
回答前先判断用户意图。
如果涉及退款，优先调用 refund_policy 工具。
`
```

不要直接替换旧 Prompt，用 flag：

```ts
const usePromptV2 = growthbook.isOn("agent_prompt_v2")
const systemPrompt = usePromptV2 ? systemPromptV2 : systemPromptV1
```

这样你可以让 10% 用户先用新版 Prompt。为什么这很有用？因为 Prompt 改动经常会带来副作用：回答变长、工具调用次数增加、误触发工具、成本升高、安全性变差、用户满意度下降。如果直接全量上线，出问题很难判断是不是 Prompt 改坏了。

用 Feature Flag 后，你可以比较：

```text
Prompt V1：工具调用率 20%，平均成本 0.03 美元
Prompt V2：工具调用率 45%，平均成本 0.08 美元
```

如果 V2 成本暴涨，就把 flag 关掉，不需要重新发布代码。

---

## 例子 3：模型路由用运行时 Flag 控制

比如你的 Agent 有两个模型：便宜模型 `fast_model` 和贵模型 `reasoning_model`。你想测试复杂问题是否要切到贵模型：

```ts
const model = growthbook.isOn("agent_use_reasoning_model")
  ? "reasoning_model"
  : "fast_model"
```

或者更细粒度：

```ts
if (
  growthbook.isOn("agent_complex_task_reasoning_model") &&
  task.complexity > 0.8
) {
  model = "reasoning_model"
} else {
  model = "fast_model"
}
```

这在 Agent 系统里非常实用。因为模型选择会直接影响回答质量、响应速度、推理能力、调用成本、失败率。你不应该每次为了改模型路由都重新发版。更好的方式是后台一开，复杂任务走强模型；发现成本太高，就关掉。

---

## 例子 4：MCP Server 灰度接入

假设你的 Agent 可以连新的 MCP Server：

```text
github_mcp
notion_mcp
company_docs_mcp
database_mcp
```

新 MCP Server 经常有问题：连接超时、返回格式不稳定、权限边界不清楚、工具描述写得不好导致模型乱调用。不要直接放进 tools 列表：

```ts
const tools = [searchDocs, callApi]

if (growthbook.isOn("agent_enable_notion_mcp")) {
  tools.push(...notionMcpTools)
}
```

这样做的好处是：当 Notion MCP 出问题时，你不用删代码、不用重新部署，只要把 `agent_enable_notion_mcp` 设为 false。Agent 立刻不再看到这批工具。这叫 **kill switch**（紧急关闭开关）。Agent 系统里 kill switch 很重要，因为工具一旦暴露给模型，模型可能主动调用它。

---

## 例子 5：不同用户看到不同 Agent 能力

比如你做的是企业 Agent。免费用户只能文档问答和简单总结，高级用户可以联网搜索、数据库查询、代码执行、批量自动化。这可以用运行时 Feature Flag 控制：

```ts
const userAttributes = {
  plan: user.plan,
  orgId: user.orgId,
  role: user.role
}

growthbook.setAttributes(userAttributes)

if (growthbook.isOn("agent_enable_code_interpreter")) {
  tools.push(codeInterpreter)
}
```

GrowthBook 后台规则：`plan == "enterprise"` 才开启 `agent_enable_code_interpreter`。这样你不用在代码里写死一堆 `if (user.plan === "enterprise")`，而是把"谁能用什么能力"放到配置系统里管理。

---

## 例子 6：安全策略可以动态收紧

Agent 系统里可能有一个风险判断模块：

```ts
const riskLevel = classifyRisk(userMessage)

if (riskLevel === "high") {
  block()
}
```

但你可能想临时加强策略，比如最近发现 Agent 容易误调用某个工具。可以做一个 flag：

```ts
const strictToolSafety = growthbook.isOn("agent_strict_tool_safety")

if (strictToolSafety && toolCall.riskLevel >= "medium") {
  requireConfirmation()
}
```

平时 `agent_strict_tool_safety: false`，出问题时设为 `true`。效果就是：原本中风险工具可以直接调用，现在中风险工具必须用户确认。这不需要重新发版。对于 Agent 来说，这类开关非常关键，因为 Agent 的行为是动态生成的，不像传统按钮那么可控。

---

## 例子 7：控制 Agent 是否自动执行，还是只给建议

比如你有一个邮件 Agent。行为风险分等级：

```text
低风险：只生成文字
中风险：创建草稿
高风险：直接发送
```

用 flag 控制：

```ts
if (growthbook.isOn("agent_auto_create_email_draft")) {
  createGmailDraft(email)
} else {
  returnDraftText(email)
}

if (growthbook.isOn("agent_auto_send_email")) {
  sendEmail(email)
} else {
  askUserToConfirm(email)
}
```

不要把高风险行为一开始就写死。应该用 Feature Flag 慢慢放开。

---

## 例子 8：记忆功能是否启用

Agent 可能有 Memory 功能：记住用户偏好、记住项目上下文、记住历史任务。但记忆功能很容易出问题：记错东西、记了不该记的内容、污染后续回答、引起隐私问题。所以可以这样：

```ts
if (growthbook.isOn("agent_enable_memory_write")) {
  memory.save(extractedPreference)
}
```

或者更细粒度：

```ts
if (growthbook.isOn("agent_enable_project_memory")) {
  memory.saveProjectContext(projectId, summary)
}

if (growthbook.isOn("agent_enable_user_preference_memory")) {
  memory.saveUserPreference(userId, preference)
}
```

这样你可以只先开放项目记忆，不开放个人偏好记忆。

---

## 运行时 Flag vs 构建时 Flag

### 用 GrowthBook 运行时 Flag（控制行为）

适合控制的场景：这个功能今天开不开、给哪些用户开、给多少比例用户开、出问题能不能马上关、能不能做 A/B 测试。

比如：是否启用新 Prompt、是否启用某个工具、是否使用某个模型、是否开启 MCP Server、是否允许自动执行、是否开启记忆、是否开启更严格安全策略。

### 用构建时 Flag（控制代码是否进产物）

适合控制的场景：这段代码要不要进入最终构建产物、某个依赖要不要被打包、某个内部功能要不要存在于生产版本、开源版和企业版是否使用不同代码。

比如：内部调试面板、企业专属模块、实验性本地功能、大型依赖模块。

### 判断标准

- 运行时 Flag：控制"这个功能今天开不开"
- 构建时 Flag：控制"这段代码要不要进最终产物"

### 实战案例：Claude Code 的两套 Feature Flag 机制

Claude Code 自身就同时使用了两套 Flag 机制，是理解两者差异的最佳例证：

| 维度 | 构建时 `feature()` | 运行时 GrowthBook `tengu_*` |
| --- | --- | --- |
| **解析时机** | Bun 打包时 | 会话启动时从 GrowthBook 拉取 |
| **影响范围** | 代码是否存在于 bundle | 代码逻辑的运行时分支 |
| **修改方式** | 需要重新构建和发布 | 服务端配置即时生效 |
| **典型用途** | 实验性功能的完整模块树消除 | A/B 测试、渐进灰度 |
| **示例** | `feature('KAIROS')` | `tengu_ultrathink_enabled` |

关键区别：

- **`feature('KAIROS')`**：这是构建时 flag。如果 KAIROS 功能（某个实验性子系统）还不想让任何用户看到，<strong>整个 Kairos 模块的代码都不会被打进 bundle</strong>。用户机器上的二进制文件里根本没有这段代码——不是"关着"，是"不存在"。这对实验性功能的安全隔离至关重要：未完成的功能不仅不能运行，甚至不应该可被逆向工程发现。

- **`tengu_ultrathink_enabled`**：这是运行时 flag。ultrathink 的代码已经在所有用户的 bundle 里了，但<strong>只有在 GrowthBook 后台对特定用户群体开启后才会生效</strong>。这意味着你可以今天给 1% 用户开 ultrathink，明天看数据，后天提升到 10%——全程不需要用户更新客户端，也不需要发新版本。

两者的分工非常清晰：

```text
构建时 feature('X')：决定模块 X 的代码进不进 bundle
    ↓ 如果进了 bundle
运行时 tengu_X：决定模块 X 对谁生效、什么时候生效
```

这跟前面讲的判断标准完全一致：<strong>担心代码泄露出实验功能 → 构建时干掉；想灰度放量、随时回滚 → 运行时控制。</strong>真正的工程实践里两者经常同时存在——先用构建时 flag 把半成品藏起来，等模块稳定后再放开构建时 flag、用运行时 flag 做渐进灰度。

---

## 完整示例：企业知识库 Agent

假设你做一个"企业知识库 Agent"，它有这些能力：文档搜索、MCP 工具调用、数据库查询、新版 Prompt、复杂问题走强模型、自动生成 Jira ticket。

比较合理的写法：

```ts
const tools = [docSearch]

if (growthbook.isOn("agent_enable_mcp_tools")) {
  tools.push(...mcpTools)
}

if (growthbook.isOn("agent_enable_database_query")) {
  tools.push(queryDatabase)
}

if (growthbook.isOn("agent_enable_jira_create")) {
  tools.push(createJiraTicket)
}

const systemPrompt = growthbook.isOn("agent_prompt_v2")
  ? promptV2
  : promptV1

const model = growthbook.isOn("agent_use_reasoning_model")
  ? "strong-model"
  : "fast-model"
```

这样上线的时候你可以按顺序开：

```text
第一天：只开新版 Prompt 给内部员工
第二天：开放 MCP 工具给 5% 用户
第三天：开放强模型路由给复杂问题
第四天：开放 Jira 创建工具，但必须用户确认
发现数据库工具有问题：马上关闭 agent_enable_database_query
```

---

## 一句话总结

在 Agent 系统里，Feature Flag 最有用的地方不是普通 UI 开关，而是控制这些高风险、动态、难预测的东西：模型怎么选、Prompt 用哪个版本、工具是否暴露给模型、MCP Server 是否启用、是否允许自动执行、是否启用记忆、安全策略是否收紧、新能力是否灰度开放。

**凡是"上线后可能想马上关掉、只给部分用户试、或者需要 A/B 对比"的 Agent 行为，都适合用 GrowthBook 这种运行时 Feature Flag 控制。** 不是为了"架构好看"，而是为了控制 Agent 的不确定性。
