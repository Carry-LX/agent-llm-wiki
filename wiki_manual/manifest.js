// 人工笔记图节点清单。每次新增 wiki_manual/*.md 时，必须在此文件中追加对应条目。
// 此文件由 app/index.html 通过 <script> 标签加载（不用 XHR，因为 file:// 下同步 XHR 被 Chrome 阻止）。
window.__MANUAL_MANIFEST__ = {
  "nodes": [
    {
      "id": "manual_opencli_browser_agent",
      "type": "source",
      "title": "OpenCLI 浏览器操控 Agent",
      "description": "让 Agent 通过登录态 Chrome 操控任意网站：CLI + Daemon + Extension 三层架构，100+ 站点适配器，19 条 browser 原语，4 个 AI Agent Skill。",
      "source_url": "https://github.com/jackwener/OpenCLI",
      "md_path": "wiki_manual/OpenCLI浏览器操控Agent.md",
      "keywords": ["OpenCLI", "browser", "agent", "chrome", "automation", "CDP", "skill"]
    },
    {
      "id": "manual_sft_rl_dip_recover",
      "type": "source",
      "title": "SFT 后 RL 训练性能先降后升机制",
      "description": "RL 初期因 SFT/RL 目标函数不可解耦致性能下降，后期通过权重矩阵奇异向量方向重构和奖励方差隐式正则化恢复泛化。含 Llama-3.2、Qwen3、华为2026 论文实验证据和面试回答模板。",
      "source_url": "https://mp.weixin.qq.com/s/e0XjEwut35Xv1empaPCSiA",
      "md_path": "wiki_manual/SFT后RL训练性能先降后升机制.md",
      "keywords": ["SFT", "RL", "RLHF", "RLVR", "catastrophic forgetting", "post-training", "singular vectors", "implicit regularization", "面试"]
    },
    {
      "id": "manual_llm_no_dropout",
      "type": "source",
      "title": "大模型为什么不使用 Dropout",
      "description": "单轮预训练几乎不存在过拟合、海量数据本身就是最强正则化、Dropout 拖慢训练效率三个核心原因，以及不同位置的 Dropout 处理策略差异和微调阶段的例外情况。含面试回答框架。",
      "source_url": "https://mp.weixin.qq.com/s/4zsfMwseLn6tw09p0EAJKQ",
      "md_path": "wiki_manual/大模型为什么不使用Dropout.md",
      "keywords": ["Dropout", "regularization", "pretraining", "overfitting", "single-epoch", "LLM", "GPT-3", "LLaMA", "面试"]
    },
    {
      "id": "manual_sft_grpo_subjective_pitfalls",
      "type": "source",
      "title": "SFT + GRPO 在主观推理任务中的实战反思",
      "description": "假推理链的事后合理化陷阱、GRPO 在非客观领域的 Rubric 与 Judge 双重失效（Goodhart 定律、有损投影、精度累积放大），以及 DPO vs GRPO 的场景选择策略。",
      "source_url": "https://mp.weixin.qq.com/s/oEtubrxnJSVL8zTY3mwbbg",
      "md_path": "wiki_manual/SFT+GRPO主观推理任务实战反思.md",
      "keywords": ["SFT", "GRPO", "DPO", "RL", "reasoning", "Rubric", "Judge", "Goodhart", "subjective", "对齐", "微调"]
    },
    {
      "id": "manual_llm_inference",
      "type": "manual_note",
      "title": "LLM 推理机制",
      "description": "Prefill（并行处理 prompt，计算密集型）与 Decode（逐 token 生成，内存密集型）两阶段的工作原理、KV Cache 的作用，以及两者混跑时的资源抢占问题。",
      "md_path": "wiki_manual/LLM推理机制.md",
      "keywords": ["Prefill", "Decode", "KV Cache", "推理", "GPU", "显存带宽", "计算密集型", "内存密集型"]
    },
    {
      "id": "manual_pd_kv_transfer",
      "type": "manual_note",
      "title": "PD 分离的 KV Cache 传输瓶颈",
      "description": "Llama-3.1-70B 单请求 KV Cache 约 1.34GB，TTFT 500ms 内留给传输仅约 300ms。10GbE 需 1s+ 不可用，25GbE 勉强，InfiniBand HDR/NVLink 才是生产级方案。传输开销超过分离收益则架构白搭。",
      "md_path": "wiki_manual/PD分离的工程挑战.md",
      "keywords": ["PD分离", "KV Cache", "Prefill", "Decode", "Llama-3.1", "InfiniBand", "NVLink", "TTFT", "网络传输"]
    },
    {
      "id": "manual_pd_load_schedule",
      "type": "manual_note",
      "title": "PD 分离的负载不均衡与调度",
      "description": "短 prompt 长输出需 1P3D，长上下文需 3P1D，静态配置在动态流量下产生资源浪费。PD 分离后调度需实时决策 Prefill/Decode 实例分配和 KV Cache 路由，生产者-消费者同步产生气泡。Mooncake 用三层集群架构应对。",
      "md_path": "wiki_manual/PD分离的工程挑战.md",
      "keywords": ["PD分离", "负载均衡", "调度", "Mooncake", "DistServe", "P:D比例", "气泡", "弹性伸缩"]
    },
    {
      "id": "manual_pd_memory_sensitivity",
      "type": "manual_note",
      "title": "PD 分离的显存碎片与性能敏感性",
      "description": "Prefill 并发生成 KV Cache 致显存飙升，Decode 保留全部生成中请求的 Cache 且随长度增长。PagedAttention 缓解碎片化但跨节点管理更复杂。P:D 比例性能曲线随 workload 交叉，瓶颈切换是突变而非平滑，业务变化大时可能断崖下跌。",
      "md_path": "wiki_manual/PD分离的工程挑战.md",
      "keywords": ["PD分离", "显存管理", "PagedAttention", "OOM", "碎片化", "P:D比例", "性能敏感性", "workload"]
    },
    {
      "id": "manual_json_channel",
      "type": "manual_note",
      "title": "Claude Code JSON 输出的通道机制",
      "description": "Claude API 将 text_delta 和 input_json_delta 分成不同通道，工具调用参数通过专用 JSON 通道传输，经 JSON.parse 验证。SDK 通过 outputFormat 动态创建空壳工具，把普通文本输出也导向工具通道，从协议层保证 JSON 格式合法。",
      "md_path": "wiki_manual/ClaudeCode的JSON输出机制.md",
      "keywords": ["Claude Code", "JSON", "tool_use", "input_json_delta", "outputFormat", "流式处理", "content_block"]
    },
    {
      "id": "manual_json_validation",
      "type": "manual_note",
      "title": "空壳工具 + Schema 校验 + Stop 钩子",
      "description": "SDK 用 Ajv 编译用户 schema 为校验函数，模型调用空壳工具时实时校验；失败则把具体错误返回模型重试。Stop 钩子在模型想结束时检查是否已调用 StructuredOutput 工具，未调用则拒绝停止（最多重试 5 次）。双层保障：协议层保证 JSON 合法 + 校验层保证内容符合 schema。",
      "md_path": "wiki_manual/ClaudeCode的JSON输出机制.md",
      "keywords": ["SyntheticOutputTool", "Ajv", "schema", "Stop hook", "structuredOutput", "校验", "重试", "空壳工具"]
    },
    {
      "id": "manual_rag_code_failure",
      "type": "manual_note",
      "title": "代码场景下 RAG 为何失效",
      "description": "embedding 对代码标识符近乎失效（getUserById vs deleteUserById 向量距离近但语义相反）；RAG 管线五个环节各 90% 准确率相乘仅剩 60%；索引时效性跟不上代码变更速度。grep 精确匹配天然比语义检索更适合代码场景。",
      "source_url": "https://mp.weixin.qq.com/s/db6dPnpD_22uyuuMpQUjKw",
      "md_path": "wiki_manual/ClaudeCode为何放弃RAG.md",
      "keywords": ["RAG", "Claude Code", "grep", "embedding", "代码检索", "语义漂移", "乘法效应", "索引时效性"]
    },
    {
      "id": "manual_agentic_search_philosophy",
      "type": "manual_note",
      "title": "从 RAG 到 Agentic Search 的架构取舍",
      "description": "Claude Code 选择无状态设计：零配置、零运维，模型自己调 grep/glob/find。'Everything is the model' 常被误解为'模型强了 harness 就不需要了'，但真相是 harness 是模型的放大器——模型每强一分，好的 harness 让它再强十分。harness 的设计目标不是替代模型，而是只做模型做不了的事（精确匹配、文件访问），剩下的全部交给模型。随着模型变强，同一 harness 的价值是递增而非递减。代价是 token 大、概念搜索有短板，业界趋向 grep+向量混合方案。",
      "source_url": "https://mp.weixin.qq.com/s/db6dPnpD_22uyuuMpQUjKw",
      "md_path": "wiki_manual/ClaudeCode为何放弃RAG.md",
      "keywords": ["Claude Code", "Agentic Search", "grep", "无状态", "Bitter Lesson", "harness", "放大器", "混合方案", "Cursor", "Milvus"]
    },
    {
      "id": "manual_agent_deadloop_causes",
      "type": "manual_note",
      "title": "Agent 死循环的四种成因",
      "description": "工具调用循环（反复同工具微调参数不收敛）、目标漂移（子目标替代主目标永不交付）、自我怀疑循环（反复 review/polish 同义替换）、幻觉性进展（同义词游戏走 8 步等于 1 步）。先诊断成因再选兜底机制，否则兜底一定打偏。",
      "source_url": "https://mp.weixin.qq.com/s/WufLje1K1q7q_ZqXVQftDw",
      "image_path": "raw/images/agent_deadloop_causes.png",
      "md_path": "wiki_manual/Agent死循环与兜底机制.md",
      "keywords": ["Agent", "死循环", "工具调用循环", "目标漂移", "自我怀疑", "幻觉性进展", "兜底", "生产级"]
    },
    {
      "id": "manual_agent_four_layer_defense",
      "type": "manual_note",
      "title": "生产级 Agent 四层兜底机制",
      "description": "四层叠加：max_iterations 硬上限止损、step budget 面向成本控制、循环检测 (tool+input 指纹 hash) 主动识别、人工 escalation (飞书/Slack webhook) 最后闸门。核心洞察：让概率模型自己判断'何时停下'是把工程问题甩给概率分布——99%能停，1%就足以让账单爆炸。止损逻辑必须是确定性的外部机制，不能依赖模型自觉。附 7 条生产 Checklist 和三段式面试回答框架。",
      "source_url": "https://mp.weixin.qq.com/s/WufLje1K1q7q_ZqXVQftDw",
      "image_path": "raw/images/agent_deadloop_defense.png",
      "md_path": "wiki_manual/Agent死循环与兜底机制.md",
      "keywords": ["Agent", "兜底", "max_iterations", "step budget", "循环检测", "escalation", "recursion_limit", "checklist", "面试"]
    },
    {
      "id": "manual_context_engineering",
      "type": "manual_note",
      "title": "Agent 上下文工程：Skills/RAG/前置过滤",
      "description": "TMIC AI 小新的基石信念：基模推理能力已足够强，Agent 失败绝大多数是因为上下文不对——要么信息太多淹没了关键信号，要么不够导致依据缺失。Skills（手写业务规则，约束行为边界）与 RAG（历史案例检索，提供参考模板）互补注入私有知识。业务模块识别用小步骤换高密度上下文：工具集从全量过滤到 10-20 个，Skills/RAG 只注入相关模块。全局参数一次性并行预取，不让 Agent 为拿通用参数多走 LLM 往返。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["Agent", "上下文工程", "Skills", "RAG", "业务识别", "预取", "基模", "CLAUDE.md"]
    },
    {
      "id": "manual_todolist_tree_action",
      "type": "manual_note",
      "title": "多轮 Agent 的方向控制：TodoList + Tree Action",
      "description": "TodoList 解决 ReAct 原生缺陷：每一步只看当前状态、第4步忘了第1步为什么取那个数据。首轮生成完整执行计划，之后每轮带着计划思考——'我在计划的哪个位置？还剩什么？'。Tree Action 把编排逻辑从大模型剥离：Planning 单轮输出带依赖关系的多 Action（'B 依赖 A 的输出'），系统按层级自动执行，依赖间参数传递用小模型做机械映射。实测 Planning 平均次数从 3.20 降到 2.44。省的不是执行时间，是大模型重复推理次数。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["Agent", "TodoList", "Tree Action", "ReAct", "多轮", "方向感", "小模型", "依赖编排", "SubAgent"]
    },
    {
      "id": "manual_agent_four_stage_framework",
      "type": "manual_note",
      "title": "可迁移的 Agent 四阶段设计框架",
      "description": "阶段1 上下文加载（业务识别→过滤工具/Skills/RAG→预取参数）；阶段2 规划（TodoList 锚定全局方向）；阶段3 执行（Tree Action 批量编排+小模型串联+SubAgent 并行委托）；阶段4 分析与输出（独立分析节点，流式输出不阻塞主流程）。核心原则：相信基模推理能力，全部工程精力投入到'让基模在每一刻看到的上下文是对的、够的、不冗余的'。所有组件都是这句话的不同实现方式。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["Agent", "框架", "四阶段", "上下文加载", "Planning", "Tree Action", "SubAgent", "流式输出", "可迁移"]
    },
    {
      "id": "manual_subagent_role_definition",
      "type": "manual_note",
      "title": "SubAgent 优化的本质：角色定义而非性能调优",
      "description": "初版 SubAgent 被设计成'缩小版 Agent'，照搬 TodoList+Planning+Analysis，耗时 103 秒。真正的优化不是技术手段，而是纠正角色认知——Agent 是规划者，SubAgent 是执行者，不是同一角色的不同尺寸。执行者只需 3 个能力：理解任务、调工具、返回结果。规划、分解、衍生子代理、生成报告不属于它。能力集合应从角色定义推导，而非从 Agent 做减法。'因为慢所以砍'下次还会砍错；'因为不属于执行者所以不该有'，新增能力时也有了判断标准。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["SubAgent", "角色定义", "规划者", "执行者", "能力边界", "103秒", "做减法", "认知升级"]
    },
    {
      "id": "manual_deepagent_three_tiers",
      "type": "manual_note",
      "title": "DeepAgent 的三层基础设施：上下文 → 约束 → 进化",
      "description": "七个技术点不是'架构的七个零件'而是三个层次：上下文工程（Summary不是清垃圾是做编辑——把上下文当工作台面而非存储空间，异步化让基础设施不打断使用者；职责分离不为了架构好看——组件存在的理由不是技术先进而是这个职责缺人干）；行为约束（RAG+Skills）；持续进化（评估闭环+数据回流）。三层缺一不可：能干活→干对活→越干越好。代码让AI能跑，评估让AI能持续跑对，RAG让AI能越跑越好。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["DeepAgent", "基础设施", "上下文工程", "Summary", "异步", "职责分离", "三层架构", "持续进化"]
    },
    {
      "id": "manual_rag_soft_constraint_flywheel",
      "type": "manual_note",
      "title": "RAG 是软约束：从评估闭环到自进化飞轮",
      "description": "RAG在DeepAgent中的角色不是知识库而是'软约束'——不告诉AI必须怎么做，而是告诉它'历史上类似问题我们是这样做的'，减少从零规划从而减少发散。更深一层：RAG是DeepAgent时代唯一可精准干预而不产生副作用的入口（Prompt/Skills影响面太大）。五步闭环（用例收集→批量执行→模型评测→人工复核→数据回流）构成免疫系统：Workflow是死的、DeepAgent是活的，没有持续评估你不知道它什么时候变差。数据回流是最关键一环：评估不只是发现问题，高质量案例自动入库RAG → Planning更稳 → 评估更高 → 发现更多好案例——正向飞轮。",
      "source_url": "",
      "md_path": "wiki_manual/TMIC_AI小新Agent设计方法论.md",
      "keywords": ["RAG", "软约束", "评估闭环", "数据回流", "自进化", "飞轮", "免疫系统", "DeepAgent", "纠偏"]
    },
    {
      "id": "manual_three_lang_stack",
      "type": "manual_note",
      "title": "AI 工程的三语言栈：Python、TypeScript、Go 各占一角",
      "description": "从真实 AI 系统的三层架构出发：Python 统治训练与建模（生态锁定），TypeScript 统治 Agent 编排与应用层（异步流式+类型安全+Web 原生），Go 统治推理基础设施与中间件（高并发+低延迟+单二进制）。深度展开 TS 原生异步 vs Python 后装异步的根本差异，以及 JSON Schema vs Agent Tool Schema 全解析——为什么 TypeScript 的类型系统是 Agent 工具定义的「单一事实来源」。含对比表、面试考察点、角色学习建议。",
      "source_url": "",
      "md_path": "wiki_html/AI工程三语言栈.html",
      "keywords": ["Python", "TypeScript", "Go", "Agent", "MCP", "推理", "goroutine", "AsyncGenerator", "三语言栈", "面试", "架构"]
    },
    {
      "id": "manual_tmic_methodology_html",
      "type": "manual_note",
      "title": "TMIC AI 小新 Agent 设计方法论（HTML 长文版）",
      "description": "九章系统讲解 TMIC 团队从 Workflow 到 Agent 的架构演进全貌。与 Markdown 版的知识点备忘不同，HTML 版以学术论文式排版完整呈现：Skills+RAG 私有知识注入、业务模块上下文过滤、参数预加载、TodoList 方向控制、Tree Action 批量编排与小模型参数传递、SubAgent 角色优化（103s→20s）、Summary 异步化、四阶段设计框架。适合反复阅读和分享。",
      "source_url": "https://mp.weixin.qq.com/s/XOejVumoe_-0v62i-FWUAg",
      "md_path": "wiki_html/TMIC-Agent设计方法论.html",
      "keywords": ["Agent", "上下文工程", "Skills", "RAG", "Tree Action", "TodoList", "SubAgent", "TMIC", "设计方法论", "四阶段", "架构演进"]
    },
    {
      "id": "manual_agent_tool_failure",
      "type": "manual_note",
      "title": "Agent 工具调用失败处理：从 try/except 到让模型自己想办法",
      "description": "传统 try/except 只保证程序不崩，Agent 的容错需要模型知道失败并自主决策。从 OpenClaw/Hermes/Claude Code 工程实践提炼：三种失败分类（临时性/确定性/循环）→ 统一错误格式（情报层）→ System Prompt 规则（决策层）→ 循环检测（硬约束层）→ 透明降级。核心洞察：把运维经验编码进工具返回结构，把失败当作观察还给 LLM。含面试三层回答框架。",
      "source_url": "https://mp.weixin.qq.com/s/nvZE1pOGPIH2sJP4yJQxjA",
      "md_path": "wiki_html/Agent工具调用失败处理.html",
      "keywords": ["Agent", "容错", "try/except", "工具调用", "失败处理", "循环检测", "降级", "硬约束", "情报层", "ReAct", "Claude Code", "面试"]
    },
    {
      "id": "manual_ws_vs_sse",
      "type": "manual_note",
      "title": "WebSocket vs SSE：Agent 通信协议选型深度对比",
      "description": "为什么 OpenAI/Anthropic 的流式 API 全用 SSE 而非 WebSocket？从 HTTP 本质讲起：SSE 是 HTTP 原生特性（巧用长连接），WebSocket 是独立协议（Upgrade 握手升级）。逐层拆解 SSE 消息格式与 EventSource API、WebSocket 全双工模型、各自的三个致命局限（SSE：连接数上限/纯文本/双通道；WS：有状态扩容难/代理拦截/无请求响应配对），AI 场景选型框架，MCP 选择 Streamable HTTP 的原因。含 10 张原理图。",
      "source_url": "https://mp.weixin.qq.com/s/MYv0xZKFHAdtkF-Yy2gyEw",
      "md_path": "wiki_html/WebSocket_vs_SSE通信协议对比.html",
      "keywords": ["WebSocket", "SSE", "EventSource", "流式", "全双工", "HTTP", "MCP", "Streamable HTTP", "AI Agent", "通信协议", "面试"]
    },
    {
      "id": "manual_skills_progressive_disclosure",
      "type": "manual_note",
      "title": "Claude Code Skills 渐进式披露机制",
      "description": "SKILL.md 不是一次性全塞进 context 的——Anthropic 用三级 Progressive Disclosure（渐进式披露）：metadata 启动时常驻（约100 token/Skill）、正文按需触发加载、资源文件由 Claude 主动用工具读取。含 description 触发公式（做什么+何时使用+触发短语）、token 预算对比、资源「读」与「注入」的本质区别、面试四步回答框架。",
      "source_url": "https://mp.weixin.qq.com/s/nKEhdlLAo8AvtHFon--j9w",
      "md_path": "wiki_html/ClaudeCode-Skills渐进式披露机制.html",
      "keywords": ["Claude Code", "Skills", "SKILL.md", "Progressive Disclosure", "渐进式披露", "metadata", "description", "context", "token", "面试", "anthropic"]
    },
    {
      "id": "manual_feature_flag_agent",
      "type": "manual_note",
      "title": "Agent 系统的 Feature Flag 管控",
      "description": "Agent 的行为不应全部写死在代码里。模型选择、工具开放、Prompt 版本、MCP Server 灰度、安全策略、kill switch 都应做成运行时 GrowthBook 开关。8 个实战例子（数据库工具灰度、Prompt A/B、模型路由、MCP 灰度、用户分层、安全动态收紧、自动执行分级、记忆功能开关）+ 运行时 vs 构建时 Flag 判断标准 + 企业知识库 Agent 完整代码示例。核心洞察：Feature Flag 在 Agent 中的价值不是普通 UI 开关，而是控制 Agent 的不确定性。",
      "source_url": "",
      "md_path": "wiki_manual/Agent系统的Feature Flag管控.md",
      "keywords": ["Agent", "Feature Flag", "GrowthBook", "灰度", "kill switch", "A/B测试", "运行时配置", "MCP", "模型路由", "安全策略"]
    },
    {
      "id": "manual_qwen_arch_pretrain_evolution",
      "type": "manual_note",
      "title": "Qwen 架构与预训练演进（2.5→3.7）",
      "description": "五版本架构对比：2.5（GQA+MoE+YARN/DCA）→ 3（QK-Norm+128专家去共享专家）→ 3.5（Transformer+线性注意力混合，计算成本降50%）→ 3.6（100万上下文）→ 3.7（解耦Harness-Verifier训练基础设施）。预训练数据从18T→36T/119语言，词表15万→25万，原生多模态早期融合。核心趋势：从规模驱动到设计驱动，小模型靠架构和训练策略追平大模型。",
      "source_url": "https://mp.weixin.qq.com/s/vKptJ55Lgr_c6Eppv9BHKA",
      "md_path": "wiki_manual/Qwen模型演进技术总结.md",
      "keywords": ["Qwen", "Transformer", "MoE", "GQA", "QK-Norm", "线性注意力", "混合注意力", "预训练", "YARN", "DCA", "原生多模态", "词表扩展", "RoPE", "ABF"]
    },
    {
      "id": "manual_qwen_posttrain_evolution",
      "type": "manual_note",
      "title": "Qwen 后训练技术演进（2.5→3.7）",
      "description": "四个版本的后训练创新：2.5（DPO离线RL+GRPO在线RL两阶段）→ 3（Thinking Budget思维控制+强到弱知识蒸馏，蒸馏仅需1/10 GPU时间超越RL；但思考模式融合后出现退化——通用RL削弱了复杂任务专业能力）→ 3.5（异步RL并行系统效率提升3-5倍+FP8混合精度显存减半）→ 3.7（跨框架跨验证器RL逼迫泛化+自进化反作弊体系：80+小时SWE训练中模型自归纳13条规则拦截1618个作弊案例+长程时序复杂度强化对抗记忆腐化）。",
      "source_url": "https://mp.weixin.qq.com/s/vKptJ55Lgr_c6Eppv9BHKA",
      "md_path": "wiki_manual/Qwen模型演进技术总结.md",
      "keywords": ["Qwen", "DPO", "GRPO", "RL", "SFT", "Thinking Budget", "知识蒸馏", "强到弱蒸馏", "异步RL", "FP8", "BF16", "退化现象", "跨框架RL", "反作弊", "Reward Hacking", "记忆腐化", "指令漂移"]
    },
    {
      "id": "manual_qwen_agent_infra_evolution",
      "type": "manual_note",
      "title": "Qwen Agent 能力与 RL 基础设施演进",
      "description": "从通用RL到Agent专项RL的跨越：3.5引入真实环境RL使模型在不同任务上表现均衡、异步并行系统将数据生成与模型训练分离；3.6 Agent能力飞跃（前端开发+代码仓库级求解+终端自动化+长程规划最优）；3.7解耦设计（Task/Harness/Verifier三组件正交，同一任务低成本与不同框架验证器自由重组）迫使模型学习泛化解题策略而非依赖特定捷径。核心洞察：Qwen3.7的重点不再是模型参数，而是RL基础设施的解耦设计和训练效率——模型能力从拼'谁更大'到拼'谁更聪明地用参数'。",
      "source_url": "https://mp.weixin.qq.com/s/vKptJ55Lgr_c6Eppv9BHKA",
      "md_path": "wiki_manual/Qwen模型演进技术总结.md",
      "keywords": ["Qwen", "Agent", "RL", "基础设施", "解耦", "Harness", "Verifier", "Task", "异步并行", "泛化", "跨框架", "长程规划", "SWE", "自进化"]
    }
  ],
  "edges": [
    {
      "source": "manual_opencli_browser_agent",
      "target": "topic_agent_architecture",
      "relation": "references_source",
      "relation_label": "OpenCLI GitHub"
    },
    {
      "source": "manual_sft_rl_dip_recover",
      "target": "topic_finetuning_trajectories",
      "relation": "references_source",
      "relation_label": "SFT+RL 机制解析原文"
    },
    {
      "source": "manual_llm_no_dropout",
      "target": "topic_finetuning_trajectories",
      "relation": "references_source",
      "relation_label": "Dropout 在 LLM 预训练中的演变"
    },
    {
      "source": "manual_sft_grpo_subjective_pitfalls",
      "target": "topic_finetuning_trajectories",
      "relation": "references_source",
      "relation_label": "GRPO vs DPO 场景选择实战"
    },
    {
      "source": "topic_prompt_engineering",
      "target": "manual_llm_inference",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：LLM 推理机制"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_pd_kv_transfer",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：PD 分离 KV Cache 传输"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_pd_load_schedule",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：PD 分离负载与调度"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_pd_memory_sensitivity",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：PD 分离显存与性能"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_json_channel",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：JSON 通道机制"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_json_validation",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：空壳工具校验"
    },
    {
      "source": "topic_rag_and_retrieval",
      "target": "manual_rag_code_failure",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：代码场景 RAG 失效"
    },
    {
      "source": "topic_rag_and_retrieval",
      "target": "manual_agentic_search_philosophy",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agentic Search 取舍"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_agent_deadloop_causes",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agent 死循环成因"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_agent_four_layer_defense",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agent 四层兜底"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_context_engineering",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：上下文工程方法论"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_todolist_tree_action",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：TodoList + Tree Action"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_agent_four_stage_framework",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：四阶段 Agent 框架"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_subagent_role_definition",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：SubAgent 角色定义"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_deepagent_three_tiers",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：三层基础设施"
    },
    {
      "source": "topic_rag_and_retrieval",
      "target": "manual_rag_soft_constraint_flywheel",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：RAG 软约束与飞轮"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_three_lang_stack",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：AI 工程三语言栈分析"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_tmic_methodology_html",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：TMIC Agent 设计方法论（HTML 长文）"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_agent_tool_failure",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agent 工具调用失败处理机制"
    },
    {
      "source": "topic_fault_tolerance_permission",
      "target": "manual_agent_tool_failure",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agent 工具调用失败处理（容错）"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_ws_vs_sse",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：WebSocket vs SSE 协议对比"
    },
    {
      "source": "manual_three_lang_stack",
      "target": "manual_ws_vs_sse",
      "relation": "references_source",
      "relation_label": "三语言栈中流式异步的协议层深入解析"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_skills_progressive_disclosure",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Skills 渐进式披露三级加载机制"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_feature_flag_agent",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Agent 系统的 Feature Flag 运行时管控"
    },
    {
      "source": "topic_finetuning_trajectories",
      "target": "manual_qwen_arch_pretrain_evolution",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Qwen 架构与预训练五版本演进"
    },
    {
      "source": "topic_finetuning_trajectories",
      "target": "manual_qwen_posttrain_evolution",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Qwen 后训练技术四版本演进"
    },
    {
      "source": "topic_agent_architecture",
      "target": "manual_qwen_agent_infra_evolution",
      "relation": "manual_enrichment",
      "relation_label": "人工补充：Qwen Agent 与 RL 基础设施演进"
    }
  ]
};
