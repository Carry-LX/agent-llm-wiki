# LLM-WIKI 交接说明

更新时间：2026-05-24

本项目是个人 LLM-WIKI 知识库，主题覆盖 Agent / RAG / Claude Code / Text2SQL / Prompt / Memory。当前工作重点不是继续堆 raw 资料，而是把已有 OneNote 导出的证据层，持续整理成可维护、可重建、可审校的知识库。

## 项目位置

```text
E:\projects\llm-wiki
```

## Git 状态

本地 Git 仓库，仅用于本地备份和回退，不主动 push。接手前先运行：

```powershell
git status --short --branch
```

## 关键入口

- `README.md`：项目入口、分层约定、Schema、常用命令
- `log.md`：历史操作流水
- `HANDOFF.md`：本文件
- `app/index.html`：本地可视化入口

## 已完成的工作

### 维护骨架（P0-P3 全部完成）

- `AGENTS.md` 和 `SCHEMA.md` 已融合进 `README.md`
- 工具链：9 个脚本（build_claims、lint、search、enrich_labels、enrich_ocr、build_wiki、rebuild_derived_layers、rebuild_agent_wiki、sync_onenote）
- P0：低置信 claim 清零（全部 8 个主题除 1 条 needs_review 外已清零 low）
- P1：3 个自动主题页摘要区已基于 claim 重写，不再含 OCR 噪声
- P2：label_title/label_summary 全部补全，warning 从 7→5
- P3：4 个缺失脚本已补回，完整重建链路恢复
- 8 个人工审校页已写入 `wiki_manual/`

常用重建命令：

```powershell
& .\tools\rebuild_derived_layers.ps1
```

全量重建（需 OneNote 桌面版）：

```powershell
& .\tools\rebuild_agent_wiki.ps1
```

### 当前总体状态

```text
claims=139（high=22, medium=116, low=1）
health check=0 error / 5 warning
```

剩余 5 个 warning 均为硬约束（source_url 缺失、OCR 噪声、图片哈希重复），需后续视觉模型重读或重新同步解决。

## 下一步建议

1. 运行 `& .\tools\rebuild_derived_layers.ps1` 确认一切正常。
2. 打开 `reports/wiki_health_report.md` 了解当前 warning 细节。
3. 高价值方向：
   - 用视觉模型重读关键图片（RAG/Prompt 主题目前没有 high claim）。
   - 对关键 source_url 做网页正文抓取，写入 best_text。
   - 在 OneNote 桌面版可用时测试 `sync_onenote_agent.ps1`。

## 注意事项

- `data/claims.jsonl` 是派生文件，会被脚本重建。人工审校写入 `data/claim_overrides.json`。
- `wiki_generated/` 不应手工长期修改。长期理解写入 `wiki_manual/`。
- `build_agent_wiki.py` 内置 guard：含 `## 核心判断` 标记的页面不会被覆盖。
- 文件保持 UTF-8 和 LF。
- Git 只作本地备份，不主动 push。
- ⚠️ **新增知识需同时更新两套展示系统**：
  1. **图谱节点**：在 `wiki_manual/manifest.js` 中添加 node 和 edge
  2. **文档版本**：运行 `python tools/build_wiki_content.py` 将 Markdown 编译到 `app/wiki_content.js`
  缺一不可，否则节点视图或文档视图中会丢失新增内容。
