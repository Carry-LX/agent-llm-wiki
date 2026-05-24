# RAGAS评估与Doc2Query

<!-- generated increment: Codex 直接读图生成；未使用 OneNote OCR -->

## 页面摘要

该页该页包含 5 张关于 RAGAS / RAG 评估的图片证据，主要覆盖 Doc2Query 反向 HyDE、RAGAS 总体框架、检索指标、生成指标和噪声敏感度。

## 证据

### Doc2Query反向HyDE索引

- evidence_id: `agent_img_011_001_6650821467a8`
- source: https://www.bestblogs.dev/article/1eeddb21?entry=explore_card&from=%2Fexplore
- image: [raw/images/agent_img_011_001_6650821467a8.png](../raw/images/agent_img_011_001_6650821467a8.png)
- keywords: Doc2Query, 反向HyDE, RAG检索, 虚构问题, 离线索引

反向 HyDE（Doc2Query）用于 RAG 检索增强：针对每个 chunk 离线生成可能的用户问题，再把这些 question 与原始 chunk 关联建索引。相比在线 HyDE，它把生成成本放到离线阶段，不影响实时调用 RT。示例中，差旅报销制度文本可生成“出差去二线城市住酒店一天能报销多少钱”“出差回来后最晚什么时候报销”“报销差旅费需要什么类型的发票”等虚构问题，从而提升用户自然问法和知识库 chunk 的匹配能力。

### RAGAS评估维度框架

- evidence_id: `agent_img_011_002_cfe257f566f0`
- source: https://www.bestblogs.dev/article/1eeddb21?entry=explore_card&from=%2Fexplore
- image: [raw/images/agent_img_011_002_cfe257f566f0.png](../raw/images/agent_img_011_002_cfe257f566f0.png)
- keywords: RAGAS, RAG评估, LLM-as-a-Judge, faithfulness, context precision, context recall

RAGAS 是一种 RAG 自动评估框架，使用 LLM-as-a-Judge 评估 RAG 系统表现。它把评估拆成两个维度：生成维度关注 faithfulness 和 answer relevancy，衡量回答是否忠实于检索上下文、是否回答了用户问题；检索维度关注 context precision 和 context recall，衡量检索上下文的信噪比以及是否召回了回答所需信息。

### RAGAS检索指标公式

- evidence_id: `agent_img_011_003_654cba106462`
- source: https://www.bestblogs.dev/article/1eeddb21?entry=explore_card&from=%2Fexplore
- image: [raw/images/agent_img_011_003_654cba106462.png](../raw/images/agent_img_011_003_654cba106462.png)
- keywords: Context Precision, Context Recall, RAGAS, 检索评估, Claims

RAGAS 检索指标包括 Context Precision 和 Context Recall。Context Precision 衡量检索结果排序质量：相关 chunk 是否排在不相关 chunk 前面，公式可写为 Context Precision@K = sum(Precision@k × v_k) / top K 中相关项数量，Precision@k = TP@k/(TP@k+FP@k)。Context Recall 衡量召回完整性：把参考答案拆成 claims，判断每个事实点是否能从 retrieved contexts 找到出处，公式为 supported claims / total claims。

### RAGAS生成指标公式

- evidence_id: `agent_img_011_004_9524de954860`
- source: https://www.bestblogs.dev/article/1eeddb21?entry=explore_card&from=%2Fexplore
- image: [raw/images/agent_img_011_004_9524de954860.png](../raw/images/agent_img_011_004_9524de954860.png)
- keywords: Faithfulness, Answer Relevancy, RAGAS, 生成评估, 余弦相似度

RAGAS 生成指标包括 Faithfulness 和 Answer Relevancy。Faithfulness 衡量回答中 claims 是否被 retrieved contexts 支持，公式为 supported response claims / total response claims。Answer Relevancy 衡量回答和用户输入之间的相关性：先基于 response 生成若干合成问题，再计算这些问题 embedding 与原始 user_input embedding 的余弦相似度并取平均。

### RAGAS噪声敏感度指标

- evidence_id: `agent_img_011_005_b52c9cc953fe`
- source: https://www.bestblogs.dev/article/1eeddb21?entry=explore_card&from=%2Fexplore
- image: [raw/images/agent_img_011_005_b52c9cc953fe.png](../raw/images/agent_img_011_005_b52c9cc953fe.png)
- keywords: Noise Sensitivity, RAGAS, 噪声敏感度, 相关噪声, 无关噪声

RAGAS 的 Noise Sensitivity 衡量 RAG 系统在检索上下文含噪声时生成错误回答的频率，分数越低越好。它分为相关上下文噪声敏感度和不相关上下文噪声敏感度：前者看相关文档中的多余信息是否被错误写入回答，后者看不相关文档是否带偏模型。计算时审查 response 中每个 claim，结合 reference 和 retrieved_contexts 判断 claim 是否正确以及错误是否可归因于噪声上下文。


_Generated at 2026-05-19T02:41:18.695Z_
