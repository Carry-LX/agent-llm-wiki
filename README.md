<p align="center">
  <img src="https://img.shields.io/badge/status-active-2ea44f?style=flat-square" alt="status">
  <img src="https://img.shields.io/badge/claims-139-157a7d?style=flat-square" alt="claims">
  <img src="https://img.shields.io/badge/health-0_errors_/_5_warnings-6f42c1?style=flat-square" alt="health">
  <img src="https://img.shields.io/badge/topics-8-db6e32?style=flat-square" alt="topics">
</p>

<h3 align="center">个人大模型知识库</h3>
<p align="center">从 OneNote 导出 → 分层结构化 → 图谱可视化 → 持续审校</p>

---

## 入口

| 入口 | 说明 |
|---|---|
| `app/index.html` | 本地网页 — 节点网络视图，搜索、图谱浏览、图片放大 |
| `wiki_generated/` | 自动生成的 8 个主题页 |
| `wiki_manual/` | 人工笔记与审校结论 |
| `wiki_html/` | 精品文章深度感悟（HTML 长文） |
| `reports/wiki_health_report.md` | 最近一次健康检查报告 |
| `log.md` | 历史操作流水 |

## 分层

```text
raw/    原始层        OneNote 导出 + 图片 + 大模型读图结果
  ↓
data/   结构化中间层   图谱、检索语料、claim 观点层
  ↓
wiki_generated/  +  wiki_manual/  +  wiki_html/
自动 wiki        人工长期理解      精品感悟
  ↓
app/    展示层        本地网页 + wiki_data
  ↓
reports/  检查层      健康报告
```

| 层 | 目录 | 手工改？ | 用途 |
|---|---|---|---|
| 原始 | `raw/images/` | 可追加 | 图片原件 |
| 原始 | `raw/assets_enriched.jsonl` | 不推荐 | 大模型读图后的证据文本与标签 |
| 中间 | `data/graph.json` | 临时可改 | 图谱总数据 |
| 中间 | `data/search_corpus.jsonl` | 临时可改 | 搜索语料 |
| 中间 | `data/claims.jsonl` | 派生文件 | 观点层（会被重建） |
| 中间 | `data/claim_overrides.json` | **推荐** | 人工审校覆盖（不会被覆盖） |
| Wiki | `wiki_generated/` | 不推荐 | 自动生成主题页 |
| Wiki | `wiki_manual/` | **推荐** | 人工长期整理 |
| Wiki | `wiki_html/` | **推荐** | 精品感悟 HTML |
| 展示 | `app/` | 可改 | 网页界面与数据 |

## 常用命令

```powershell
# 日常维护（推荐）
& .\tools\rebuild_derived_layers.ps1

# 全量重建（需 OneNote 桌面版）
& .\tools\rebuild_agent_wiki.ps1

# 启动本地服务（⚠️ 必须从项目根目录启动，否则节点图片无法加载）
python -m http.server 8082
# 然后打开 http://localhost:8082/app/index.html

# 检索
python .\tools\search_agent_wiki.py

# 健康检查
python .\tools\lint_agent_wiki.py
```

## 核心概念

### Claim → 可引用的观点

```json
{
  "claim_id": "claim_agent_img_002_021_001",
  "claim_type": "engineering_judgment",
  "claim_text": "高维向量相似度搜索不适合依赖 B-tree，应使用专门向量索引。",
  "topic_id": "rag_and_retrieval",
  "evidence_ids": ["agent_img_002_021_9b3378ea7e27"],
  "confidence": "medium"
}
```

类型：`definition` · `engineering_judgment` · `risk` · `workflow` · `metric` · `comparison` · `example`

### 图谱关系 → 四类，避免"页面目录图"

1. **来源关系** `contains_evidence` — 证据来自哪个页面
2. **主题关系** `supported_by` — 证据属于哪个知识主题
3. **概念关系** `explained_by` — 证据解释了哪个概念
4. **跨页语义** `semantic_evidence` — 证据虽在别的页面，内容属于当前主题

## 当前状态

| 指标 | 数值 |
|---|---|
| Claims | 139（high=22, medium=116, low=1） |
| 健康检查 | 0 errors / 5 warnings |
| 主题 | 8 个，全部低置信清零 |
| 工具链 | 9 个脚本 |
| 人工笔记 | 13 篇 |

## 约定

- UTF-8 + LF · 脚本顶部显式变量 · Git 仅本地备份不主动 push
- 不直接改 `raw/` · 不长期改 `wiki_generated/` · 人工结论写 `claim_overrides.json`
- 新增 `wiki_manual/*.md` → 同步更新 `manifest.js` + 运行 `build_wiki_content.py`

## 质量红线

- 结论必须能追溯到 evidence_id 或 source_url
- 新增图片由视觉模型直接读图，不以 OCR 作为主要内容来源
- 同一图片以 `image_sha256` 去重
- 失败时不推进同步水位
