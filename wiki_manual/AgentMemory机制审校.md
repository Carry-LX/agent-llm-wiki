# Agent Memory 机制审校

这页整理 Agent Memory 相关证据，目标是把分散在 RAG、Claude Code、微调和规划页面里的材料合成一个稳定理解层。当前结论来自 `data/claim_overrides.json` 的人工审校 claim，优先级高于自动页里的 OCR 摘要。

## 核心判断

Agent Memory 不是一次会话的聊天记录，也不是把所有历史内容丢进同一个向量库。它更像一个外部状态系统：把长期有复用价值的信息按类型、时效和优先级管理，在合适时机注入或检索。

最重要的设计分界是：

- `Session`：一次会话的聊天日志，记录用户说了什么、模型答了什么、工具调用了什么。
- `Memory`：项目级长期笔记，从一次或多次对话中提炼出以后还会复用的信息。

对应证据：`agent_img_010_016_10147080437a`。

## 四类记忆

推荐把 Memory 分成四类：

| 类型 | 内容 | 使用策略 |
|---|---|---|
| user | 用户身份、长期偏好、稳定工作方式 | 会话开始全量加载，直接注入 system prompt |
| feedback | 用户纠正、行为规范、禁用做法 | 执行操作前检索，最高优先级约束当前行为 |
| project | 项目状态、截止日期、当前架构演进 | 按任务相关性检索，先检查绝对时效，过期则忽略 |
| reference | 外部系统位置、文档、issue、dashboard | 需要外部信息时按需检索，找到位置后跳转查询 |

如果把这些都混进无分类向量库，会带来三个问题：时效不同的信息难清理，过期信息继续污染上下文，检索噪声变大。分层后，反馈规则可以稳定影响行为，项目状态可以自动过期，外部引用不必每轮加载。

对应证据：`agent_img_010_020_b527d8b886ff`、`agent_img_010_021_b3c82f1477b0`、`agent_img_010_022_c5deb2fdfd12`。

## 文件组织

项目级 Memory 可以采用“索引 + 子文件”的组织方式：

```text
memory/
  MEMORY.md
  user_role_data_scientist.md
  user_pref_deep_explanation.md
  feedback_no_mock_database.md
  feedback_no_fake_business_data.md
  project_release_freeze_20260507.md
  project_ingest_refactor.md
  reference_linear_ingest_bug.md
  reference_sentry_dashboard.md
```

`MEMORY.md` 不需要承载全部细节。它更像目录，告诉模型有哪些记忆、每条记忆大概是什么、详细内容应该读哪个子文件。子文件保存具体规则、偏好、项目状态或引用位置。

记忆文件 ID 应使用稳定哈希，例如 SHA-256 截断，而不是依赖 Python 运行时的 `hash()`，否则跨进程或跨环境可能不稳定。

对应证据：`agent_img_010_013_a7f193bf605f`、`agent_img_010_015_8da4dcbcb47c`、`agent_img_010_017_51c9eb8de69e`。

## 触发策略

记忆提取有成本，每次触发通常意味着额外 LLM 调用。因此触发策略的核心不是“越频繁越好”，而是在成本和覆盖率之间取平衡。

常见策略：

- 规则驱动：例如消息数量超过阈值、重要性积分超过阈值。优点是可预测，缺点是不够灵活。
- LLM 自主驱动：让模型判断何时读写记忆。优点是灵活，缺点是成本高、行为更不确定。
- 后台异步策略：主对话不阻塞，每 N 条消息或任务完成后异步扫描新增内容。

提取结果建议设计成四类操作：`ADD`、`UPDATE`、`DELETE`、`NOOP`。`NOOP` 很重要，它表示没有值得写入的新信息，避免把无价值内容持续塞进记忆库。

对应证据：`agent_img_010_018_b5f17153c5f1`。

## 并发控制

后台记忆提取不能无限并发。一个稳妥做法是 coalescing：

- `_running`：当前是否已有提取任务在运行。
- `_dirty`：运行期间是否又来了新的提取请求。
- `_watermark`：上次提取处理到第几条消息。
- 互斥锁：保证这些状态不会被多个异步任务同时改乱。

如果正在提取时又来了新请求，不新开任务，只把 `_dirty` 标成 true；当前任务结束后，再根据 `_watermark` 统一扫描新增消息。

对应证据：`agent_img_010_019_209453d6a810`。

## 什么不该进 Memory

Memory 应保留无法从当前状态自动推导出的关键决策，不应该保存代码和 git 历史里已经能恢复的实现细节。

适合进入 Memory：

- 用户偏好方案 A 而不是方案 B。
- 某个 bug 的根因是竞态条件。
- 用户明确纠正过“不要 mock 数据库”。
- 项目当前冻结窗口或架构迁移状态。

不适合进入 Memory：

- 某个 bug 具体改了哪几行代码。
- 当前仓库里已经存在的函数签名。
- 可以通过搜索代码或 git log 得到的信息。

对应证据：`agent_img_010_012_450cba6d1d68`。

## 可复用回答

面试或方案说明可以这样说：

```text
我不会把 Agent Memory 设计成一个不断追加的向量库。Session 只是一次会话日志，Memory 是项目级长期状态。我们把记忆分成 user、feedback、project、reference 四类：user 类会话开始全量加载，feedback 类执行前检索且最高优先级，project 类按任务相关性检索并检查绝对时效，reference 类只在需要外部信息时按需检索。写入侧采用后台异步提取，结果用 ADD、UPDATE、DELETE、NOOP 表示，并用 coalescing 合并并发提取请求，避免阻塞主对话和重复写入。
```

## 本轮审校结果

- 新增 13 条 Agent Memory 人工审校 claim。
- 全局 low claim 从 55 降到 47，high claim 从 8 升到 15。
- Memory 相关证据从 RAG、微调、规划等页面收拢到 `Agent 系统架构` 主题。
- 后续应让自动页基于 claim 层重写摘要区，减少 OCR 原文直接进入核心要点。
