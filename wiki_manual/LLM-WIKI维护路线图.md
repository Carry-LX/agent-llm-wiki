# LLM-WIKI 维护路线图

这份路线图用于把当前 OneNote 导出的 Agent 知识库，逐步升级成可持续维护的 LLM-WIKI。

## 当前定位

当前项目已经完成第一层结构：

- `raw/` 保存 OneNote 原始导出和图片。
- `data/` 保存图谱、检索语料和首版 claim。
- `wiki_generated/` 保存自动主题页。
- `wiki_manual/` 保存长期人工理解。
- `app/` 提供本地可视化入口。

现在最重要的问题不是继续堆材料，而是提高从证据到结论的可靠性。

## 优先级 1：把高价值图片改成视觉模型理解

健康检查显示大部分 `best_text_source` 仍是 Tesseract。下一步应优先处理这些材料：

- 命中 OCR 噪声的证据。
- 缺 source_url 但内容重要的证据。
- 出现在多个主题中的重复图片。
- RAG、Agent Memory、Tool Use、Text2SQL 等高频主题的中心证据。

目标是把它们补成：

```json
{
  "best_text_source": "codex_vision_model",
  "label_title": "...",
  "label_summary": "...",
  "label_keywords": ["..."]
}
```

## 优先级 2：把 claim 从规则抽取升级为审校结论

当前 `data/claims.jsonl` 是规则抽取的首版，适合作为索引，不适合作为最终结论。后续应把低置信 claim 改成：

- 一句话结论。
- 支撑 evidence_id。
- source_url 或图片路径。
- 置信度。
- 是否存在反例或适用边界。

好的 claim 应该像这样：

```text
Agent 记忆不应只放入同一个向量库，应按用户稳定偏好、反馈规则、项目状态、外部引用分层管理，因为这些记忆的时效、优先级和注入时机不同。
```

## 优先级 3：重写自动主题页的摘要区

自动主题页当前证据表有价值，但摘要区仍容易受 OCR 噪声影响。后续生成页应改成：

1. 核心判断。
2. 工程取舍表。
3. 常见误区。
4. 面试表达。
5. 支撑 claims。
6. 原始 evidence 表。

每条核心判断后都应该带 evidence_id。

## 优先级 4：补完整 OneNote 同步脚本

README 里曾提到 OneNote 同步脚本，但当前项目没有 `tools/sync_onenote_agent.ps1` 和 `tools/build_agent_wiki.py`。后续如果要恢复完整生成链路，应先找回原脚本或重建：

- 同步 OneNote 页面和图片。
- 增量识别新增/变更对象。
- 调用视觉模型富化图片。
- 重建 graph、search corpus、wiki、app 数据。
- 只在全部成功后更新 `raw/last_sync_manifest.json`。

## 每次维护后的固定动作

```powershell
& .\tools\rebuild_derived_layers.ps1
```

然后查看：

- `data/claims.jsonl`
- `reports/wiki_health_report.md`
- `log.md`
