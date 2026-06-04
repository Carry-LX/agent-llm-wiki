# Claude Code JSON 输出的通道机制

Claude Code 是 Anthropic 官方的 AI 编程工具，它内部也需要让模型输出 JSON。翻了源码后发现，它通过把文本包成工具，然后用工具的协议来约束输出合法的 JSON。

核心思路：SDK 在运行时根据你的 Schema 动态创建一个空壳工具，它不会执行任何实际操作，唯一的作用就是接收模型的输出数据。关键在于：模型一旦走了工具调用的路径，数据就从文本通道切换到了专用通道，格式保障从"靠 prompt 约束"变成了"靠协议保证"。

---

## 1. 模型输出文本和工具参数，走的是不同的路

Claude API 返回的内容不是一整段文本，而是分成了不同类型的"区块"。看源码里的流式处理部分（`claude.ts`）：

```typescript
// 模型返回的内容分成不同类型的区块
case 'content_block_start':
  switch (part.content_block.type) {
    case 'tool_use':                    // 工具调用区块
      contentBlocks[part.index] = {
        ...part.content_block,
        input: '',                      // 工具参数，初始化为空字符串
      }
      break
    case 'text':                        // 文本区块
      contentBlocks[part.index] = {
        ...part.content_block,
        text: '',                       // 文字内容，初始化为空字符串
      }
      break
  }
```

文本区块和工具调用区块从一开始就是分开的。模型说的"废话"和你要的 JSON 数据不会混在一起。

再看数据怎么流入这两种区块：

```typescript
// 两种区块的数据流入通道也完全不同
case 'content_block_delta':
  switch (delta.type) {
    case 'input_json_delta':            // JSON 碎片，只能流入工具调用区块
      contentBlock.input += delta.partial_json
      break
    case 'text_delta':                  // 文本碎片，只能流入文本区块
      contentBlock.text += delta.text
      break
  }
```

> **关键：工具参数通过 `input_json_delta` 专用通道传输，每次传一小段 JSON 碎片（`partial_json`）。这些碎片拼在一起，就是完整的工具参数 JSON。**

---

## 2. 拼完后还要过 JSON.parse 这道关

碎片拼完之后，还要过一道关——`JSON.parse`。如果解析失败，参数会变成空对象 `{}`，绝不会把一段残缺的文本当作 JSON 传给下游（`messages.ts`）：

```typescript
// 工具参数拼完后，必须通过 JSON.parse 这道关
case 'tool_use': {
  let normalizedInput
  if (typeof contentBlock.input === 'string') {
    const parsed = safeParseJSON(contentBlock.input)  // 必须是合法 JSON
    normalizedInput = parsed ?? {}                     // 解析失败就变成空对象
  }
  return { ...contentBlock, input: normalizedInput }   // 下游拿到的一定是 JS 对象
}
```

整个链条：**API 服务端把工具参数拆成 JSON 碎片 → 通过专用通道传输 → 客户端拼起来 → JSON.parse 验证 → 传给下游代码**。这个过程中没有模型"自由发挥"的空间——要么输出合法 JSON，要么变成空对象触发重试。

---

## 3. 怎么把文本输出也走工具通道？——空壳工具

上面说的是工具调用的天然通道。那怎么让普通文本也享受这种格式保障？

答案就是传入 `outputFormat` 参数。你定义 schema 并传入，SDK 会在运行时动态创建一个空壳工具，把你的 schema 当作这个工具的参数定义，塞进发给 API 的工具列表里。模型看到工具列表里多了一个叫 `StructuredOutput` 的工具，就会通过"调用工具"的方式输出数据——自然而然地走上了 `tool_use` 区块这条路。

两种方式的区别：

| | 老办法（纯 prompt） | 新办法（outputFormat） |
|---|---|---|
| 输出通道 | `text_delta` | `input_json_delta` |
| 格式保障 | 靠 prompt 约束 | 靠协议保证 |
| JSON 解析 | 需要自己从文本里提取 | API 层自动拼接 |
| 校验 | 自己写 | SDK 内置 Ajv |

---

## 4. 格式合法之后，还要校验内容

格式合法不代表内容正确——模型可能输出了一个完全不相关的结构，比如你要 `tasks` 字段，它给了一个 `result` 字段。

所以 Claude Code 在空壳工具里还加了一层校验（`SyntheticOutputTool.ts`）：

```typescript
// 创建空壳工具时，会把你定义的 JSON Schema 编译成校验函数
const ajv = new Ajv({ allErrors: true })
const validateSchema = ajv.compile(jsonSchema)    // jsonSchema 就是你定义的格式

// 模型调用工具时，先校验再返回
async call(input) {
  const isValid = validateSchema(input)
  if (!isValid) {
    // 校验失败：把具体错误告诉模型，让它改
    const errors = validateSchema.errors
      ?.map(e => `${e.instancePath || 'root'}: ${e.message}`)
      .join(', ')
    throw new Error(`Output does not match required schema: ${errors}`)
    // 这个错误会变成 tool_result 返回给模型，模型看到后会重试
  }
  return {
    data: 'Structured output provided successfully',
    structured_output: input,
  }
}
```

模型如果输出不符合 schema，会看到类似"缺少必填字段 tasks"这样的错误信息，然后重新输出。

---

## 5. 如果模型压根不调用空壳工具呢？

模型可能直接在文本里写了结果就想收工。Claude Code 用 Stop 钩子解决了这个问题（`hookHelpers.ts`）：

```typescript
// 注册一个"停止检查"：每次模型想结束对话，都会触发这个检查
addFunctionHook(
  setAppState, sessionId,
  'Stop',                                                          // 在模型停止时触发
  '',
  messages => hasSuccessfulToolCall(messages, 'StructuredOutput'),  // 检查：调用过空壳工具吗？
  'You MUST call the StructuredOutput tool to complete this request. Call this tool now.',
  { timeout: 5000 },
)
```

逻辑很直白：模型每次说"我说完了"，系统就去消息记录里找——你成功调用过 `StructuredOutput` 这个工具吗？没有？拒绝让你停下来，把"你必须调用 StructuredOutput 工具"发回去。模型被迫继续。

这个过程最多重复 5 次，5 次之后还不行才报错放弃。

---

## 6. 完整机制串起来

```text
用户定义 schema + outputFormat
  → SDK 动态创建空壳工具（SyntheticOutputTool）
  → 模型被引导通过工具调用输出数据
  → 数据走 input_json_delta 专用通道（协议层保障）
  → 客户端拼接 JSON 碎片 + JSON.parse 验证
  → Ajv schema 校验内容结构
  → 校验失败 → 错误信息返回模型 → 重试
  → Stop 钩子：不调用空壳工具就不让结束
  → 最终输出：合法的、符合 schema 的 JS 对象
```

---

## 7. 实践：只用改两处

定义你要的 JSON 格式：

```typescript
const schema = {
  type: "object",
  properties: {
    tasks: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          steps: { type: "string" },
          type: { type: "string", enum: ["ui", "api"] },
        },
        required: ["name", "steps", "type"],
      },
    },
  },
  required: ["tasks"],
};
```

调用时加一个参数：

```typescript
const options = {
  ...原来的参数,
  outputFormat: { type: "json_schema", schema },
};

const { structuredOutput } = await callAgent(task, options);

if (structuredOutput) {
  parsed = structuredOutput;  // 直接用，不需要 JSON.parse
}
```

原来四层策略链的代码没删，留着兜底。但正常情况下走的是工具调用路径，那四层根本不会被触发。

---

## 一句话总结

> **SDK 根据你的 Schema 动态创建空壳工具，模型被迫通过调用这个工具来输出数据，数据就从文本通道切换到了工具调用专用通道——这条通道在协议层面保证 JSON 格式合法，再加上 Schema 校验保证内容正确，不调用工具就不让结束。**
