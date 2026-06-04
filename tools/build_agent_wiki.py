"""从 raw/assets_enriched.jsonl 构建 wiki 派生层。

输入:
  - raw/assets_enriched.jsonl (OCR 富化后的资产)
  - data/evidence_label_cache.json (可选的标签缓存)
  - data/manual_evidence_labels.json (人工标注)

输出:
  - data/search_corpus.jsonl   (检索语料，含主题分配和标签)
  - data/graph_nodes.jsonl     (图谱节点)
  - data/graph_edges.jsonl     (图谱边)
  - data/topics.json           (主题定义)
  - wiki_generated/*.md        (自动主题页)

重建时保留已有 labels 和 topic 分配，仅新增/更新资产条目。

用法: python tools/build_agent_wiki.py
"""
import json, re, hashlib, sys, io
from pathlib import Path
from collections import defaultdict, OrderedDict
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

# ====== 配置 ======
ASSETS_PATH = ROOT / 'raw' / 'assets_enriched.jsonl'
LABEL_CACHE_PATH = ROOT / 'data' / 'evidence_label_cache.json'
MANUAL_LABELS_PATH = ROOT / 'data' / 'manual_evidence_labels.json'
CORPUS_PATH = ROOT / 'data' / 'search_corpus.jsonl'
NODES_PATH = ROOT / 'data' / 'graph_nodes.jsonl'
EDGES_PATH = ROOT / 'data' / 'graph_edges.jsonl'
TOPICS_PATH = ROOT / 'data' / 'topics.json'
WIKI_DIR = ROOT / 'wiki_generated'

# 主题定义
TOPICS = [
    {"id": "agent_architecture", "title": "Agent 系统架构",
     "summary": "围绕工具调用、执行链路、状态管理、观测反馈和 Agent 项目工程化的材料集合。"},
    {"id": "rag_and_retrieval", "title": "RAG 与检索增强",
     "summary": "围绕 RAG、GraphRAG、LightRAG、知识库构建、检索策略、chunk 和评测的材料集合。"},
    {"id": "prompt_engineering", "title": "Prompt 约束与上下文设计",
     "summary": "围绕 System Prompt、上下文约束、工具调用边界、参数 schema 和决策规则的材料集合。"},
    {"id": "planning_execution", "title": "规划、执行与反思",
     "summary": "围绕 CoT、Plan-Execute、Observe、Reflection、自我修正和多步骤任务拆解的材料集合。"},
    {"id": "finetuning_trajectories", "title": "微调、轨迹与训练数据",
     "summary": "围绕 SFT、RL、训练数据构造、轨迹评估和模型能力内化的材料集合。"},
    {"id": "evaluation_dataset", "title": "评测集与数据构造",
     "summary": "围绕评测指标、测试集构造、RAGAS 评测和评估方法的数据集合。"},
    {"id": "text2sql", "title": "Text2SQL 与查询校验",
     "summary": "围绕 NL2SQL、SQL 生成、执行前校验、执行后校验和业务实体一致性的材料集合。"},
    {"id": "fault_tolerance_permission", "title": "容错、权限与安全边界",
     "summary": "围绕 Agent 安全边界、权限控制、容错机制和数据安全的材料集合。"},
]

# 页面→主题 映射（基于 page_title 推断默认主题）
PAGE_TOPIC_MAP = {
    "Agent": "agent_architecture",
    "RAG": "rag_and_retrieval",
    "Text2SQL": "text2sql",
    "提示词": "prompt_engineering",
    "微调": "finetuning_trajectories",
    "Planning": "planning_execution",
    "容错 / 权限": "fault_tolerance_permission",
    "Claude code": "agent_architecture",
    "杂项": "agent_architecture",
    "记忆": "agent_architecture",
    "新增": "agent_architecture",
    "评测": "evaluation_dataset",
}

def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows

def read_json(path):
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')

def get_label(asset_id):
    """获取 evidence_label，优先人工标注，其次缓存。"""
    if asset_id in MANUAL_LABELS:
        return MANUAL_LABELS[asset_id]
    if asset_id in LABEL_CACHE:
        return LABEL_CACHE[asset_id]
    return ""

def get_topic(asset, existing_corpus_by_aid=None):
    """推断资产所属主题。优先使用已有分配。"""
    aid = asset['asset_id']
    if existing_corpus_by_aid and aid in existing_corpus_by_aid:
        c = existing_corpus_by_aid[aid]
        tid = c.get('topic_id', '')
        ttitle = c.get('topic_title', '')
        if tid and ttitle:
            return tid, ttitle
    page = asset.get('page_title', '')
    tid = PAGE_TOPIC_MAP.get(page, 'agent_architecture')
    for t in TOPICS:
        if t['id'] == tid:
            return tid, t['title']
    return 'agent_architecture', 'Agent 系统架构'

def build_corpus(assets, existing_corpus_by_aid):
    """从资产生成 search_corpus。"""
    rows = []
    generated_at = datetime.now(timezone.utc).isoformat()

    for a in assets:
        aid = a['asset_id']
        label = get_label(aid)
        if not label:
            # 从已有 corpus 继承
            existing = existing_corpus_by_aid.get(aid, {})
            label = existing.get('evidence_label', '')

        topic_id, topic_title = get_topic(a, existing_corpus_by_aid)
        text = a.get('best_text') or a.get('clean_text') or ''
        source_url = a.get('source_url', '')

        row = {
            'topic_id': topic_id,
            'topic_title': topic_title,
            'asset_id': aid,
            'evidence_label': label,
            'content_modified_at': a.get('object_modified_time') or a.get('page_modified_time', ''),
            'label_generated_at': generated_at,
            'label_model': 'codex-manual-labels-v1',
            'asset_type': a.get('asset_type', ''),
            'page_title': a.get('page_title', ''),
            'source_url': source_url,
            'image_path': a.get('image_path', ''),
            'text': text,
        }
        rows.append(row)

    return rows

def build_graph(assets, corpus_by_aid):
    """从资产和语料生成图谱节点和边。"""
    nodes = []
    edges = []
    node_ids = set()

    def add_node(nid, ntype, name, **extra):
        if nid in node_ids:
            return
        node_ids.add(nid)
        node = {'id': nid, 'type': ntype, 'name': name}
        node.update(extra)
        nodes.append(node)

    # Root
    add_node('root_agent_wiki', 'root', 'LLM-WIKI Root')

    # 主题节点
    topic_by_id = {}
    for t in TOPICS:
        nid = f'topic_{t["id"]}'
        add_node(nid, 'topic', t['title'])
        topic_by_id[t['id']] = nid
        edges.append({'source': 'root_agent_wiki', 'target': nid, 'relation': 'has_topic'})

    # 页面节点
    pages_seen = {}
    for a in assets:
        ptitle = a.get('page_title', '')
        if not ptitle or ptitle in pages_seen:
            continue
        pidx = a.get('page_index', len(pages_seen) + 1)
        nid = f'page_{pidx:03d}'
        pages_seen[ptitle] = nid
        add_node(nid, 'page', ptitle)
        tid = PAGE_TOPIC_MAP.get(ptitle, 'agent_architecture')
        if tid in topic_by_id:
            edges.append({'source': topic_by_id[tid], 'target': nid, 'relation': 'contains_page'})

    # 证据节点 + 概念节点
    concept_nodes = set()

    for a in assets:
        aid = a['asset_id']
        img_hash = ''
        ipath = a.get('image_path', '')
        if ipath:
            m = re.search(r'_([0-9a-f]{12})$', Path(ipath).stem)
            if m:
                img_hash = m.group(1)

        enid = f'asset_{aid}'
        add_node(enid, 'evidence', aid,
                 asset_type=a.get('asset_type', ''),
                 page_title=a.get('page_title', ''),
                 image_hash=img_hash)

        c = corpus_by_aid.get(aid, {})
        tid = c.get('topic_id', '')
        if tid in topic_by_id:
            edges.append({'source': topic_by_id[tid], 'target': enid, 'relation': 'contains_evidence'})

        ptitle = a.get('page_title', '')
        if ptitle in pages_seen:
            edges.append({'source': pages_seen[ptitle], 'target': enid, 'relation': 'contains_evidence'})

        # 图片哈希节点（去重）
        if img_hash:
            hnid = f'asset_imgsha_{img_hash}'
            add_node(hnid, 'evidence', f'image_{img_hash}')
            edges.append({'source': enid, 'target': hnid, 'relation': 'semantic_evidence'})

        # source_url 节点已废弃：域名级 source 节点无实际辨识度，文本乱码，且 evidence
        # 节点自身已携带 source_url。人工整理的 source 节点见 wiki_manual/manifest.js。

    return nodes, edges

def build_wiki_pages(assets, corpus_by_aid):
    """为每个主题生成 wiki_generated/*.md。

    注意：如果目标文件已包含「## 核心判断」段（即已被人为 P1 审校重写），
    则跳过覆盖，避免自动生成内容覆盖人工整理。
    """
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    # 按主题分组
    topic_assets = defaultdict(list)
    for a in assets:
        aid = a['asset_id']
        c = corpus_by_aid.get(aid, {})
        tid = c.get('topic_id', 'agent_architecture')
        topic_assets[tid].append(a)

    index_lines = ['# LLM-WIKI 主题索引', '', '<!-- generated: auto-built topic index -->', '']

    for t in TOPICS:
        tid = t['id']
        t_assets = topic_assets.get(tid, [])
        corpus_entries = [corpus_by_aid.get(a['asset_id'], {}) for a in t_assets]

        images = sum(1 for a in t_assets if a.get('asset_type') == 'onenote_image')
        links = sum(1 for a in t_assets if a.get('asset_type') == 'onenote_text_link')

        safe_title = t['title'].replace(' ', '_').replace('/', '_')
        md_path = WIKI_DIR / f'{safe_title}.md'

        # 如果页面已被人工审校（包含「## 核心判断」），跳过自动生成
        CURATED_MARKER = '## 核心判断'
        if md_path.exists():
            existing = md_path.read_text(encoding='utf-8', errors='replace')
            if CURATED_MARKER in existing:
                index_lines.append(f'- [{t["title"]}]({safe_title}.md) — {t["summary"]} *(保留人工审校版)*')
                continue

        index_lines.append(f'- [{t["title"]}]({safe_title}.md) — {t["summary"]}')

        # 收集页面名
        pages_set = set(a.get('page_title', '') for a in t_assets if a.get('page_title'))

        lines = [
            f'# {t["title"]}',
            '',
            '<!-- generated: do not hand-edit this file; put durable notes in ../wiki_manual/ -->',
            '',
            '## 自动摘要',
            '',
            t['summary'],
            '',
            f'- 证据数量：{len(t_assets)} 条，其中图片 {images} 条、文本链接 {links} 条。',
            f'- 涉及 OneNote 页面：{", ".join(sorted(pages_set)) if pages_set else "无"}。',
            '',
            '## 关键要点',
            '',
        ]

        for a in t_assets:
            aid = a['asset_id']
            c = corpus_by_aid.get(aid, {})
            label = c.get('evidence_label', '')
            text = c.get('text', '')
            ipath = a.get('image_path', '')
            if label and text:
                lines.append(f'- {label}：{text}')
            elif label:
                lines.append(f'- {label}')
            elif text:
                lines.append(f'- {text}')
            if ipath:
                lines.append(f'  ![evidence](../{ipath})')

        lines.append('')
        lines.append('## 证据表')
        lines.append('')
        lines.append('| evidence_id | 类型 | OneNote 页面 | 原链接 | 图片 | 摘要片段 |')
        lines.append('|---|---|---|---|---|---|')

        for a in t_assets:
            aid = a['asset_id']
            atype = a.get('asset_type', '')
            page = a.get('page_title', '')
            surl = a.get('source_url', '')
            ipath = a.get('image_path', '')
            label = corpus_by_aid.get(aid, {}).get('evidence_label', '')
            text = a.get('best_text', '') or a.get('clean_text', '')

            url_cell = f'[source]({surl})' if surl and surl.startswith('http') else (surl if surl else '')
            img_cell = f'![evidence](../{ipath})' if ipath else ''

            lines.append(f'| {aid} | {atype} | {page} | {url_cell} | {img_cell} | {label}: {text} |')

        lines.append('')
        lines.append('## 后续人工补充建议')
        lines.append('')
        lines.append('- 将稳定理解写入 `wiki_manual/`，不要直接修改本文件。')
        lines.append(f'- 已有关联审校页：查看 `wiki_manual/` 下对应主题。')
        lines.append('')

        md_path.write_text('\n'.join(lines), encoding='utf-8', newline='\n')

    # 索引页
    index_lines.append('')
    index_path = WIKI_DIR / 'index.md'
    index_path.write_text('\n'.join(index_lines), encoding='utf-8', newline='\n')


def main():
    assets = read_jsonl(ASSETS_PATH)
    if not assets:
        print(f'错误: {ASSETS_PATH} 为空或不存在')
        return

    print(f'读取 {len(assets)} 条资产')

    # 加载已有 corpus（保留已分配的 topic 和 label）
    existing_corpus = read_jsonl(CORPUS_PATH)
    existing_corpus_by_aid = {c['asset_id']: c for c in existing_corpus if c.get('asset_id')}
    print(f'已有 {len(existing_corpus_by_aid)} 条语料记录')

    # 加载标签
    global MANUAL_LABELS, LABEL_CACHE
    manual_data = read_json(MANUAL_LABELS_PATH)
    MANUAL_LABELS = manual_data.get('labels', {}) if isinstance(manual_data, dict) else {}
    cache_data = read_json(LABEL_CACHE_PATH)
    LABEL_CACHE = cache_data.get('labels', {}) if isinstance(cache_data, dict) else {}
    print(f'标签: {len(MANUAL_LABELS)} 人工 + {len(LABEL_CACHE)} 缓存')

    # 1. 生成 search_corpus
    print('\n[1/4] 生成 search_corpus...')
    corpus = build_corpus(assets, existing_corpus_by_aid)
    write_jsonl(CORPUS_PATH, corpus)
    print(f'  -> {CORPUS_PATH} ({len(corpus)} 条)')

    corpus_by_aid = {c['asset_id']: c for c in corpus}

    # 2. 生成图谱
    print('[2/4] 生成图谱...')
    nodes, edges = build_graph(assets, corpus_by_aid)
    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    print(f'  -> {NODES_PATH} ({len(nodes)} 节点)')
    print(f'  -> {EDGES_PATH} ({len(edges)} 边)')

    # 3. 生成 topics.json
    print('[3/4] 生成 topics...')
    topic_asset_counts = defaultdict(int)
    for c in corpus:
        topic_asset_counts[c.get('topic_id', '')] += 1
    topics_out = []
    for t in TOPICS:
        safe_title = t['title'].replace(' ', '_').replace('/', '_')
        topics_out.append({
            'id': t['id'],
            'title': t['title'],
            'summary': t['summary'],
            'asset_count': topic_asset_counts.get(t['id'], 0),
            'markdown_path': f'wiki_generated/{safe_title}.md',
        })
    with open(TOPICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(topics_out, f, ensure_ascii=False, indent=2)
    print(f'  -> {TOPICS_PATH} ({len(topics_out)} 个主题)')

    # 4. 生成 wiki 页面
    print('[4/4] 生成 wiki 页面...')
    build_wiki_pages(assets, corpus_by_aid)
    print(f'  -> {WIKI_DIR}/*.md')

    # 5. 构建 wiki 浏览器内容
    print('[5/5] 构建 wiki 浏览器内容...')
    import build_wiki_content
    build_wiki_content.main()

    print('\n构建完成。')


if __name__ == '__main__':
    main()
