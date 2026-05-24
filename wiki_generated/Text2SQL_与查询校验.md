# Text2SQL 与查询校验

<!-- generated: do not hand-edit this file; put durable notes in ../wiki_manual/ -->

## 自动摘要

围绕 NL2SQL、SQL 生成、执行前校验、执行后校验和 Agent 工具集成的材料集合。

- 证据数量：10 条，其中图片 5 条、文本链接 5 条。
- 涉及 OneNote 页面：Agent, RAG, Text2SQL。
- 关联人工审校页：[Text2SQL与查询校验审校](../wiki_manual/Text2SQL与查询校验审校.md)。

## 核心判断

- **Text2SQL 应作为 Agent 的只读受控工具**：Agent 负责意图判断、歧义澄清和流程调度，Text2SQL 只在条件齐全时被调用，不应独立暴露给用户或自行决定执行时机。`[agent_link_004_001]`
- **校验要分执行前和执行后两层**：执行前检查 SELECT 类型、表授权、危险关键字和自动加 LIMIT；执行后检查非空、数值范围、关键实体缺失和历史对比——发现实体不匹配时应拒绝直接回答并提示补充过滤条件。`[agent_img_004_001]`
- **动态 Schema 裁剪 + 业务术语词典**：通过只注入相关表的 Schema 降低 token 消耗和字段歧义，配合术语词典和澄清机制提升语义理解准确率。`[agent_link_004_002]`
- **执行后闭环迭代**：结果合理性验证 + 日志 + 用户反馈 + few-shot 示例迭代，形成可持续修正的闭环。`[agent_link_004_003]`

## 工程实现

### Agent 工具集成

Text2SQL 在 Agent 系统里的定位是一个只读工具，而非独立的 NL2SQL 问答系统：

- Agent 层职责：意图识别、槽位抽取、歧义澄清、流程调度。
- Text2SQL 层职责：接收确定的查询参数，生成并执行 SQL，返回结果。
- 关键原则：Text2SQL 只在条件齐全时被调用，不自行决定执行时机。

### 执行前后双层校验

**执行前校验**（阻止危险查询）：
- 确认是 SELECT 语句，拒绝 DDL/DML。
- 检查表授权和用户权限。
- 检测危险关键字（DROP、DELETE、INSERT、UPDATE 等）。
- 自动追加 LIMIT 100 防止全表扫描。

**执行后校验**（发现结果异常）：
- 非空检查：结果不应为空。
- 数值范围检查：结果数量级是否在合理范围。
- 关键实体缺失：用户提到的实体名是否出现在结果中。
- 历史对比：与历史同级查询结果偏差是否在阈值内。

### 动态 Schema 裁剪

不做全量 Schema 注入，而是：
1. 根据用户问题涉及的关键词，只注入相关表的结构。
2. 配合业务术语词典（如"销售额"→`sales_amount`）消歧。
3. 当系统对字段映射不确定时，启动澄清对话而非猜测。

### 训练数据构造

- 问答模板 + 变量随机填充 + 大模型问题改写生成训练数据。
- 生成 SQL 时约束模型只使用已知表名和字段名。
- 中文数字转阿拉伯数字（"前五名"→`ORDER BY ... DESC LIMIT 5`）。

### 双向增强数据框架

正向（问题→SQL）+ 逆向（SQL→问题）联合训练。中国电科十所实验：相对 LoRA 微调提升执行准确率 16.3%，相对 few-shot 提示学习提升 35.7%。

对应 evidence：`agent_img_004_001`、`agent_link_004_001-003`、`agent_img_001_004`、`agent_img_002_005`、`agent_link_001_003`。

## 面试表达

- **"Text2SQL 怎么保证安全"** → 不是生成 SQL 就直接执行。执行前检查 SELECT/权限/危险关键字/自动 LIMIT，执行后检查非空/数值范围/实体缺失/历史对比。两层校验缺一不可。
- **"Text2SQL 在 Agent 里怎么定位"** → Text2SQL 是只读工具，Agent 是调度者。意图判断和歧义澄清归 Agent，SQL 生成和执行归 Text2SQL。权限边界清楚，Text2SQL 不自行决定何时执行。
- **"Schema 太大怎么办"** → 动态裁剪：根据问题关键词只注入相关表，配合业务术语词典做列映射，不确定时澄清而非硬猜。

## 支撑 claim（high confidence）

| claim | 领域 |
|---|---|
| Text2SQL 执行前校验 SELECT/权限/LIMIT，执行后校验非空/范围/实体/历史对比 | 安全校验 |
| Text2SQL 实现应通过动态 Schema 裁剪和业务术语词典降低歧义 | 工程实现 |
| Text2SQL 执行后需做结果合理性验证并结合反馈迭代形成闭环 | 质量迭代 |

## 待确认

本主题当前无待确认 claim（low=0）。

## 来源链接

- https://mp.weixin.qq.com/s/KG-0kV7cLunKL8GJwu_FCg
- https://mp.weixin.qq.com/s/i9L-II6miRrQ1em3O3UFnw
- https://pdf.hanspub.org/csa_1543666.pdf

## 证据表

| evidence_id | 类型 | OneNote 页面 | 原链接 | 图片 | 摘要片段 |
|---|---|---|---|---|---|
| agent_img_001_004_90500f357b93 | onenote_image | Agent |  | [image](../raw/images/agent_img_001_004_90500f357b93.png) | Text2SQL 训练数据由问答模板、变量随机填充和大模型问题改写构造，生成 SQL 时约束模型只使用已知表名和字段名。 |
| agent_img_002_005_90500f357b93 | onenote_image | RAG |  | [image](../raw/images/agent_img_002_005_90500f357b93.png) | 同上：同一张图片同时出现在 Agent 和 RAG 页面。 |
| agent_img_004_001_c7a560785213 | onenote_image | Text2SQL |  | [image](../raw/images/agent_img_004_001_c7a560785213.png) | 执行前后双层校验：SELECT/无危险关键字/LIMIT 100 通过后执行；结果做非空/数值范围/关键实体缺失/历史对比。 |
| agent_link_004_001_a434e04af222 | onenote_text_link | Text2SQL | OneNote 内部链接 |  | Text2SQL 作为 Agent 的只读工具，Agent 负责意图判断、歧义澄清和流程调度。 |
| agent_link_004_002_1309c6f76a59 | onenote_text_link | Text2SQL | [source](https://mp.weixin.qq.com/s/KG-0kV7cLunKL8GJwu_FCg) |  | 动态 Schema 裁剪降低 token 和歧义，业务术语词典和澄清机制提升理解准确率。 |
| agent_img_002_027_e76d357cd694 | onenote_image | RAG | [source](https://mp.weixin.qq.com/s/i9L-II6miRrQ1em3O3UFnw) | [image](../raw/images/agent_img_002_027_e76d357cd694.png) | Milvus 内存不足导致 swap 使查询延迟从 20ms 飙升到 2s+（已重归 RAG 与检索增强主题）。 |
| agent_img_002_026_f9760a189147 | onenote_image | RAG | [source](https://mp.weixin.qq.com/s/i9L-II6miRrQ1em3O3UFnw) | [image](../raw/images/agent_img_002_026_f9760a189147.png) | 批量写入改到业务低峰期、Segment 合并静默完成（已重归 RAG 与检索增强主题）。 |
| agent_link_004_003_efdfe5a416f4 | onenote_text_link | Text2SQL | [source](https://mp.weixin.qq.com/s/KG-0kV7cLunKL8GJwu_FCg) |  | 执行后结果合理性验证，结合日志和用户反馈持续优化 few-shot 示例。 |
| agent_link_001_003_4eea312600bf | onenote_text_link | Agent | [source](https://pdf.hanspub.org/csa_1543666.pdf) |  | 双向增强框架（问题→SQL 正向 + SQL→问题逆向），准确率提升 16.3%（vs LoRA）和 35.7%（vs few-shot）。 |
| agent_link_002_002_299ba7379201 | onenote_text_link | RAG | [source](https://pdf.hanspub.org/csa_1543666.pdf) |  | 与 agent_link_001_003 同一来源，出现在 RAG 页面。 |

## 后续人工补充建议

- 将稳定理解写入 `wiki_manual/`，不要直接修改本文件。
- 已有关联审校页：[Text2SQL与查询校验审校](../wiki_manual/Text2SQL与查询校验审校.md)。
- 对关键 source_url 可后续增加网页正文抓取，形成比截图 OCR 更高层的证据。

_Updated at 2026-05-23_
