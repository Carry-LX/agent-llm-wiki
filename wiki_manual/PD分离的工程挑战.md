# PD 分离的工程挑战

## 背景

LLM 推理分两个阶段：**Prefill**（计算密集型，并行处理整个 prompt，生成 KV Cache）和 **Decode**（内存密集型，逐 token 串行生成，频繁读写 KV Cache）。两个阶段的资源需求完全相反，混在一起跑会互相干扰。

**PD 分离**就是把这两个阶段拆到不同 GPU 上执行：Prefill 用高算力卡，Decode 用高带宽卡。听起来很美好，但工业界真正落地时，有五个大坑。

---

## 问题一：KV Cache 传输开销

这是最核心的问题。Prefill 算完之后，得把整个 KV Cache 传给 Decode，这个传输量有多大？

以 **Llama-3.1-70B** 为例，单个请求的 KV Cache 约 **1.34GB**。如果 TTFT 要求 500ms 以内，Prefill 本身可能吃掉 200ms，留给传输的只有 300ms。

这时候网络就是瓶颈：

| 网络 | 传输 1.34GB 耗时 | 是否可用 |
|---|---|---|
| 10GbE | ~1.1s | 不够 |
| 25GbE | ~430ms | 勉强 |
| InfiniBand HDR | ~60ms | 可用 |
| NVLink | ~几 ms | 理想 |

> **关键判断：如果传输开销超过分离带来的性能收益，整个架构就白搭。PD 分离必须有高速互联网络支撑，不是随便拿几台机器就能做的。**

Meta、Kimi 等生产环境用的都是专门的高速网络，成本不低。

---

## 问题二：生产者-消费者负载不均衡

Prefill 和 Decode 之间的负载不均衡，取决于 workload 特征：

- **短 prompt、长输出**（如聊天）：Decode 压力大 → 需要 **1P3D**（1 Prefill : 3 Decode）
- **长上下文**（如文档总结、代码分析）：Prefill 是瓶颈 → 需要 **3P1D**

真实业务的流量是动态变化的。上午短问答，下午长文档处理。如果 P:D 比例是静态配置的，就会出现一边闲置、一边排队的情况。

有论文实验表明，**当 Prompt/Output 比例变化时，不同 P:D 配置的性能曲线会交叉**。没有万能配置，必须根据实际 workload 调整。

---

## 问题三：调度复杂度飙升

传统架构调度器只管一个队列。PD 分离后，调度器要实时决策：

- 这个请求分配给哪个 Prefill 实例？
- Prefill 完成后，KV Cache 传给哪个 Decode 实例？

考虑的因素包括：各节点负载、显存剩余、KV Cache 复用率、网络拓扑。Prefill 和 Decode 之间还存在生产者-消费者同步问题——Prefill 做完了 Decode 还在忙，或者 Decode 空闲了 Prefill 还没准备好，都会产生资源利用率的"气泡"。

DistServe 和 Mooncake 为了解决这个问题设计了复杂调度算法。Mooncake 甚至做了三层架构：Prefill 集群 + Decode 集群 + Caching 集群（管理 KV Cache）。

---

## 问题四：显存压力和碎片化

- **Prefill 阶段**：可能同时处理多个请求，每个都生成 KV Cache，显存占用瞬间飙升。
- **Decode 阶段**：要保留所有生成中请求的完整 KV Cache，且随生成长度增加而不断增长。

虽然 PagedAttention 等技术能缓解碎片化，但 PD 分离后 KV Cache 生命周期跨越两个节点，管理更复杂——要确保 Prefill 生成的 Cache 能高效映射到 Decode 显存，还要处理好释放和复用时机。管理不好就会出现一边频繁 OOM、另一边大量闲置。

---

## 问题五：P:D 比例的性能敏感性

实验测试了 1P3D、2P2D、3P1D 三种配置，发现性能曲线随 Prompt/Output 比例变化而交叉——某个 workload 下最优的配置，换一个 workload 可能变成最差的。

本质是 Prefill 和 Decode 的瓶颈切换不是平滑的，而是突变的。当 workload 从 Decode 密集型切换到 Prefill 密集型时，性能可能断崖式下跌。

另外，从 TP2 变成 1P1D 时，prefilling 的卡减少，大 batch size 或长输入会导致 TTFT 变长。因为 prefill 计算量大、decoder 传输量大，所以 PD 分离允许对两个阶段使用不同类型的显卡，最大化性价比。

---

## 面试回答框架

如果面试官问"PD 分离背后可能出现什么问题"，从这几个维度答：

1. **KV Cache 传输开销**（核心）：算一下传输时间，说明为什么需要 InfiniBand/NVLink。
2. **负载不均衡**：不同 workload 下 P:D 比例需求不同，静态配置导致浪费。
3. **调度复杂度**：生产者-消费者同步、资源分配、气泡问题。
4. **显存管理**：跨节点 KV Cache 生命周期、碎片化、OOM 风险。
5. **性能敏感性**：没有万能配置，workload 变化时性能可能断崖下跌。

如果追问"怎么解决"：高速网络、智能调度（DistServe/Mooncake）、动态伸缩、KV Cache 压缩和复用。
