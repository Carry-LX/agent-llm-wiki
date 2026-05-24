# Agent 分区初版知识地图

这份总览是基于当前 OneNote `我的笔记本 / Agent` 分区导出的 OCR、图片链接和文本链接整理的第一版人工种子页。它不依赖原来的 OneNote 页面分类，后续可以作为 `wiki_manual/` 中长期保留的理解层。

## 当前材料的主线

这个分区的材料大体围绕一个问题展开：如何把 LLM 从“会回答”推进到“能在工程系统中稳定做事”。其中 RAG、Agent、Prompt、Planning、容错、Text2SQL、微调并不是独立主题，而是同一个系统的不同层。

第一层是知识获取。RAG 材料强调检索不是简单向量相似度，而是要在 GraphRAG、LightRAG、HyDE、向量数据库、chunk 策略和评测之间做取舍。比如 `agent_img_002_001_dcd9267f7f8b` 对比了 GraphRAG 与 LightRAG 的检索机制和适用场景，`agent_img_002_021_9b3378ea7e27` 解释了为什么普通关系型数据库不适合直接承担高维向量相似度搜索。

第二层是任务执行。Agent 材料更关注工具调用循环、文件搜索、子 Agent、状态流转和人机协作边界。`agent_img_010_008_39a6a4c7207f` 展示了 Claude Code 类系统里 Grep、Glob、FileRead、AgentTool 等工具如何服务统一的 LLM 工具循环；`agent_img_009_013_79ba71d907a8` 和 `agent_img_009_014_8bd0eb29ad10` 则指向多 Agent 通讯、leader-worker-verifier 这类更复杂的协作形态。

第三层是过程控制。Planning 页的核心观点是 CoT、Plan、Execute、Observe、Reflection 构成现实 Agent 系统的操作闭环。`agent_img_006_001_8ddd31f50291` 可以作为这个主题的中心证据：没有任务拆解，模型不知道怎么做；没有观察和反思，任务拆对了也跑不稳。

第四层是约束与安全。Prompt、容错、权限材料说明，工程中的 Agent 不能只靠“你是一个智能助手”这类松散提示词，而要明确什么时候必须调用工具、什么时候不能调用、参数如何遵守 schema、失败如何被模型感知。Text2SQL 页里的 `agent_img_004_001_c7a560785213` 是一个很好的安全闭环样例：执行前检查 SELECT、授权、危险关键字和 LIMIT；执行后再检查非空、数值范围、关键实体缺失与历史对比。

第五层是能力训练。微调页的材料显示，Function Calling 或工具调用能力不能只靠少量正常样本，而要覆盖单工具、多工具、并行调用、参数变化、异常恢复、工具结果观察和最终回答。`agent_img_005_002_2a1ff9be530f` 指向 SFT 训练数据扩充流程，`agent_img_005_008_8e11e3ef39a2` 则把 SFT 与 RLHF 的分工区分为“会不会”和“该不该”。

## 第一版 wiki 应该回答的问题

- RAG 系统如何在 GraphRAG、LightRAG、HyDE、向量库和 chunk 策略之间做工程取舍？
- Agent 系统的最小闭环是什么：Prompt、Plan、Tool、Observe、Reflection 分别承担什么责任？
- 什么情况下应该通过 Prompt 约束解决问题，什么情况下必须落到权限、校验和执行器防护？
- Text2SQL 为什么应该被设计成只读工具，并且需要执行前后双重校验？
- Function Calling 微调数据应该覆盖哪些轨迹类型，如何验证提升不是数据泄漏或场景重叠带来的假提升？

## 后续生成规则

后续自动生成 `wiki_generated/` 时，建议把每个结论都落到 evidence_id，不要只生成抽象总结。更高价值的证据优先级应该是：

1. 图片自带的 `source_url`
2. OneNote 图片原图
3. OneNote OCR 文本
4. 页面标题、分区、对象 ID 和时间
5. 自动主题分类结果

这样即使主题分类后面多次重做，原始截图、网页链接和证据链也不会丢。
