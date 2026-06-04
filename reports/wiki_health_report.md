# LLM-WIKI 健康检查报告

- 节点：275；边：509；搜索语料：139；资产：139；claims：139。
- 报告生成时间：2026-05-24T03:42:29.736764+00:00。

## 结论
- ERROR：0 项。
- WARN：5 项，建议纳入后续清理。

## Errors
- 无

## Warnings
- `data/search_corpus.jsonl` 中 45 条记录缺少 source_url。
- `data/search_corpus.jsonl` 中 2 条记录只有 OneNote 内部来源。
- 存在 11 组图片哈希被多个 asset_id 引用，需要确认去重语义。
- 搜索语料中 5 条记录命中疑似 OCR 噪声模式。
- `data/claims.jsonl` 中 45 条 claim 缺少 source_urls。

## 节点类型
| 项 | 数量 |
|---|---:|
| evidence | 249 |
| page | 10 |
| topic | 8 |
| source | 7 |
| root | 1 |

## 边关系
| 项 | 数量 |
|---|---:|
| contains_evidence | 278 |
| semantic_evidence | 121 |
| from_source | 92 |
| contains_page | 10 |
| has_topic | 8 |

## best_text_source 分布
| 项 | 数量 |
|---|---:|
| tesseract_chi_sim_eng | 114 |
| anchor_text | 18 |
| codex_vision_model | 5 |
| onenote_ocr_cleaned | 2 |

## claim 类型
| 项 | 数量 |
|---|---:|
| engineering_judgment | 46 |
| workflow | 28 |
| risk | 19 |
| metric | 18 |
| definition | 16 |
| comparison | 7 |
| example | 5 |

## claim 置信度
| 项 | 数量 |
|---|---:|
| medium | 116 |
| high | 22 |
| low | 1 |

## OCR 噪声样例
| asset_id | topic | 命中模式 |
|---|---|---|
| agent_img_001_002_cd654a4171e8 | 评测集与数据构造 | 履盖,Witte Ata |
| agent_img_002_003_cd654a4171e8 | 评测集与数据构造 | 履盖,Witte Ata |
| agent_img_002_017_644feb67b2da | RAG 与检索增强 | 履盖 |
| agent_img_002_021_9b3378ea7e27 | RAG 与检索增强 | 暴万,余弱,AINE |
| agent_img_010_011_2fe9a3cb897f | RAG 与检索增强 | 暴万 |

## 重复图片哈希样例
| image_hash | asset_ids |
|---|---|
| e11ee8244f22 | agent_img_001_001_e11ee8244f22, agent_img_002_002_e11ee8244f22 |
| cd654a4171e8 | agent_img_001_002_cd654a4171e8, agent_img_002_003_cd654a4171e8 |
| 30bfe2dad039 | agent_img_001_003_30bfe2dad039, agent_img_002_004_30bfe2dad039 |
| 90500f357b93 | agent_img_001_004_90500f357b93, agent_img_002_005_90500f357b93 |
| ce1638579d53 | agent_img_001_005_ce1638579d53, agent_img_002_006_ce1638579d53 |
| ccc7f5e4f8ea | agent_img_001_006_ccc7f5e4f8ea, agent_img_002_007_ccc7f5e4f8ea |
| d75dc63bc8b4 | agent_img_001_007_d75dc63bc8b4, agent_img_002_008_d75dc63bc8b4 |
| cd3df81953ab | agent_img_001_008_cd3df81953ab, agent_img_002_009_cd3df81953ab |
| 94911bd17c4e | agent_img_001_009_94911bd17c4e, agent_img_002_010_94911bd17c4e |
| 06e3063fd73c | agent_img_001_010_06e3063fd73c, agent_img_002_011_06e3063fd73c |
| 6947aa966103 | agent_img_001_011_6947aa966103, agent_img_002_012_6947aa966103 |
