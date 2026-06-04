# Claude Code 为什么放弃 RAG

> 来源：[丁师兄大模型](https://mp.weixin.qq.com/s/db6dPnpD_22uyuuMpQUjKw)，2026-05-28

Anthropic 工程师 Boris 在 2025 年 5 月的 Latent Space 播客中明确表示，Claude Code 早期试过 RAG（本地向量数据库 + embedding 检索），但效果不行，最终切换到了"agentic search"——让模型自己调用 grep、glob、find 等 Linux 命令实时搜索代码。Boris 原话："it outperformed everything, by a lot"。

---

## 1. 代码场景下 RAG 的三个根本缺陷

### 问题一：Embedding 对代码标识符近乎失效

`getUserById` 和 `deleteUserById` 在向量空间里距离非常近（共享大量 token），但功能完全相反——一个是查询，一个是删除。

代码是结构化的精确标识符，函数名、类名、变量名本身就是最好的检索关键词。精确匹配（grep 搜 `processPayment`）天然比语义匹配（embedding 近似搜索）更可靠，不存在语义漂移。

### 问题二：RAG 管线的乘法效应

整个 RAG 链路：文档切分 → embedding 生成 → 向量检索 → 重排序 → 最终生成。每个环节即使做到 90% 准确率，五个环节乘下来只剩不到 60%。

而且出错时调试是噩梦——你不知道是 chunk 切得不好、还是 embedding 质量有问题、还是 rerank 模型偏了。grep 失败的原因只有一个：关键词没匹配上。这种确定性在工程上价值巨大。

### 问题三：索引时效性

代码仓库变化极快，上午建的索引下午可能就过时了。频繁重建索引计算开销巨大，不重建则索引与实际代码漂移。grep 每次实时搜索，拿到的永远是当前最新状态，不存在同步问题。

---

## 2. 架构哲学：无状态设计与"Everything is the Model"

Claude Code 的设计遵循经典的**无状态设计**原则——从 Unix 管道到 REST API 到 Serverless，这条线在计算机科学里反复被验证过。

- **零配置**：用户 clone 完代码就能直接用，不需要等几分钟构建 embedding。
- **零运维**：没有"索引卡住了""缓存损坏了"这种问题。
- **Everything is the Model**：尽量让模型本身驱动决策，而不是在模型外面搭复杂的工程管线。模型每变强一分，整个系统自动变好一分——这就是 Rich Sutton 的 Bitter Lesson 在工程上的体现。
- **安全性**：embedding 本身有信息泄露风险（学术研究已证明可从 embedding 反推原始内容），grep 完全在本地执行，从架构上杜绝这个问题。

---

## 3. 辩证看待：这不是银弹

Claude Code 的方案也有明显代价：

- **Token 消耗巨大**：每次搜索都是实时执行，模型要列目录、读文件、做多轮探索。Milvus 团队公开批评这是在"烧 token"。
- **概念搜索有短板**：想找"所有跟权限校验相关的逻辑"，grep 不一定能覆盖所有变体写法。

业界共识正在走向**混合方案**：精确搜索（grep）处理标识符级别查找，语义检索（向量）处理概念级别探索，两者互补。Claude Code 选了极简那一端，Cursor 选了向量索引那一端，未来大概率在中间收敛。

---

## 4. 深度延伸：重新理解"Everything is the Model"

"Everything is the Model"有一个容易被误读的版本：

> "模型越来越强，外围工程（harness）越来越不重要。"

这个理解把 harness 当成了模型的**替身**——因为模型不够强，才需要 harness 来补。模型强了，harness 就可以退场。

但 Claude Code 的实践揭示的正好相反：

**harness 不是模型的替身，是模型的放大器。**

grep 本身没有任何智能。让 grep 变强大的是模型知道用它搜什么、读完结果后知道怎么判断相关性、搜不到时知道换什么关键词——这些是模型的能力，但 grep 这个工具把这些能力**释放**了出来。

换句话说：

> 模型每变强一分，好的 harness 让它再强十分。模型每变弱一分，harness 把它能做的事尽可能兜住。

这不是"模型替代 harness"，而是"模型 × harness"的乘法关系。Claude Code 选择极简的 harness（几个 Linux 命令），不是因为 harness 不重要，恰恰是因为**harness 的设计目标就是只做模型做不了的事**——精确字符串匹配（grep）和文件系统访问（glob/find）——然后把剩下的全部交给模型。每一层不必要的外围工程，都是对模型能力的压制，而不是补充。

这其实也是对 Bitter Lesson 的更深一层理解：Rich Sutton 说的"利用算力而非人类知识"，在工程层面不是"把所有东西都塞进模型参数里"，而是"让模型成为决策中枢，让 harness 成为模型手和眼的延伸"。harness 做得越少、越透明、越可组合，模型的能力就越能完整地传递到任务上。随着模型变强，好的 harness 的价值不是递减，而是**递增**——因为同一个工具在更强的模型手里，能完成更复杂的任务。



面试官问"Claude Code 为什么放弃 RAG"，三层结构：

**技术事实层**（讲清楚 RAG 的缺陷）：
> "代码场景下 embedding 对标识符近乎失效——`getUserById` 和 `deleteUserById` 向量距离很近但语义相反。整个 RAG 管线的乘法效应让准确率断崖下跌，而且索引时效性跟不上代码变更速度。"

**架构哲学层**（拔高）：
> "这背后是无状态设计哲学——零配置、零运维、'everything is the model'。每层工程管线都是复杂度负债，模型自身变强才是长期杠杆。"

**辩证层**（不说死）：
> "代价是 token 消耗大、概念级搜索有短板。业界正在走向精确搜索加语义检索的混合方案，Claude Code 和 Cursor 代表了光谱的两端。"
