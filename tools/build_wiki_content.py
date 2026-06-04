"""从 wiki_generated/ + wiki_manual/ 构建 app/wiki_content.js。

输入:
  - wiki_generated/*.md       (自动生成的 wiki 页面)
  - wiki_manual/*.md          (人工笔记)
  - wiki_manual/manifest.js   (人工笔记 → 主题 映射)
  - data/topics.json          (主题定义)

输出:
  - app/wiki_content.js       (浏览器端 wiki 内容)

用法: python tools/build_wiki_content.py
"""
import json, re, sys, io
from pathlib import Path
from collections import defaultdict

if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

# 生成页面文件名 → topic_id 映射
PAGE_TOPIC_MAP = {
    "Agent_系统架构.md": "agent_architecture",
    "RAG_与检索增强.md": "rag_and_retrieval",
    "Prompt_约束与上下文设计.md": "prompt_engineering",
    "规划、执行与反思.md": "planning_execution",
    "微调、轨迹与训练数据.md": "finetuning_trajectories",
    "评测集与数据构造.md": "evaluation_dataset",
    "Text2SQL_与查询校验.md": "text2sql",
    "容错、权限与安全边界.md": "fault_tolerance_permission",
}


def md_to_html(text: str) -> str:
    """简版 Markdown → HTML 转换，覆盖用户内容中的常见格式。"""
    lines = text.split('\n')
    out = []
    in_code_block = False
    in_table = False
    in_ul = False
    in_ol = False
    in_blockquote = False
    code_lang = ''
    code_lines = []
    table_rows = []
    buf: list[str] = []  # paragraph buffer

    def flush_buf():
        nonlocal buf
        if not buf:
            return
        content = ' '.join(buf).strip()
        buf = []
        if content:
            content = _inline(content)
            out.append(f'<p>{content}</p>')

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            return
        html_rows = []
        for i, row in enumerate(table_rows):
            tag = 'th' if i == 0 else 'td'
            cells = ''.join(f'<{tag}>{_inline(c.strip())}</{tag}>' for c in row)
            html_rows.append(f'<tr>{cells}</tr>')
        out.append(f'<table>{"".join(html_rows)}</table>')
        table_rows = []
        in_table = False

    for line in lines:
        # 围栏代码块
        if line.startswith('```'):
            if in_code_block:
                out.append(f'<pre><code class="language-{code_lang}">{_escape("\n".join(code_lines))}</code></pre>')
                code_lines = []
                in_code_block = False
            else:
                flush_buf()
                flush_table()
                in_code_block = True
                code_lang = line[3:].strip()
            continue
        if in_code_block:
            code_lines.append(line)
            continue

        # 表格
        if line.startswith('|') and line.rstrip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(c.replace('-', '').replace(':', '').replace(' ', '') == '' for c in cells):
                continue  # 跳过分隔行
            if not in_table:
                flush_buf()
                in_table = True
            table_rows.append(cells)
            continue
        elif in_table:
            flush_table()

        # 水平线
        if re.match(r'^[-*_]{3,}\s*$', line):
            flush_buf()
            out.append('<hr>')
            continue

        # 标题
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            flush_buf()
            level = len(m.group(1))
            text = _inline(m.group(2))
            out.append(f'<h{level}>{text}</h{level}>')
            continue

        # 引用块
        m = re.match(r'^>\s?(.*)$', line)
        if m:
            if not in_blockquote:
                flush_buf()
                in_blockquote = True
            content = _inline(m.group(1))
            out.append(f'<blockquote><p>{content}</p></blockquote>')
            continue
        elif in_blockquote:
            in_blockquote = False

        # 无序列表
        m = re.match(r'^[-*]\s+(.+)$', line)
        if m:
            if not in_ul:
                flush_buf()
                in_ul = True
                out.append('<ul>')
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue
        elif in_ul:
            out.append('</ul>')
            in_ul = False

        # 有序列表
        m = re.match(r'^\d+\.\s+(.+)$', line)
        if m:
            if not in_ol:
                flush_buf()
                in_ol = True
                out.append('<ol>')
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue
        elif in_ol:
            out.append('</ol>')
            in_ol = False

        # HTML 注释 (skip)
        if line.strip().startswith('<!--') and line.strip().endswith('-->'):
            continue

        # 空行 → 刷新缓冲
        if not line.strip():
            flush_buf()
            continue

        # 普通段落文本
        buf.append(line)

    # 清理未闭合块
    flush_buf()
    flush_table()
    if in_ul:
        out.append('</ul>')
    if in_ol:
        out.append('</ol>')

    return '\n'.join(out)


def _escape(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _inline(text: str) -> str:
    """内联格式：粗体、斜体、行内代码、链接、图片。"""
    # 图片 ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # 行内代码 `code`
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    # 粗体 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体 *text*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


def infer_importance(text: str, source: str, md_path: str = '') -> str:
    """推断页面重要性。"""
    if '## 核心判断' in text:
        return 'high'
    if source == 'manual':
        # >100 行的笔记通常属于深入分析
        if text.count('\n') > 100:
            return 'high'
        if text.count('\n') > 40:
            return 'medium'
        return 'low'
    # 生成的页面：按证据数估算
    evidence_count = len(re.findall(r'\[agent_\w+\]', text))
    if evidence_count >= 10:
        return 'high'
    if evidence_count >= 5:
        return 'medium'
    return 'low'


def parse_manifest():
    """从 manifest.js 提取 manual_note_id → topic_id 映射。"""
    manifest_path = ROOT / 'wiki_manual' / 'manifest.js'
    if not manifest_path.exists():
        return {}
    text = manifest_path.read_text(encoding='utf-8')
    # 解析 nodes: id → md_path
    node_to_path = {}
    for m in re.finditer(r'"id":\s*"([^"]+)"[^}]*?"md_path":\s*"([^"]+)"', text, re.DOTALL):
        node_to_path[m.group(1)] = m.group(2)
    # 解析 edges: source → target (仅保留 manual_enrichment 和 references_source)
    path_to_topic = {}
    for m in re.finditer(r'"source":\s*"([^"]+)"\s*,\s*"target":\s*"([^"]+)"\s*,\s*"relation":\s*"(manual_enrichment|references_source)"', text):
        src_id, tgt_id = m.group(1), m.group(2)
        # 确定哪个是 topic，哪个是 manual note
        src_path = node_to_path.get(src_id, '')
        tgt_path = node_to_path.get(tgt_id, '')
        if 'wiki_manual/' in src_path and tgt_id.startswith('topic_'):
            path_to_topic[src_path] = tgt_id.replace('topic_', '')
        elif 'wiki_manual/' in tgt_path and src_id.startswith('topic_'):
            path_to_topic[tgt_path] = src_id.replace('topic_', '')
    return path_to_topic


def resolve_asset_refs(text: str) -> str:
    """将 `agent_img_XXX_YYY_HASH` 代码引用转换为内嵌图片。"""
    return re.sub(
        r'`(agent_img_\d{3}_\d{3}_[a-f0-9]{12})`',
        r'![evidence](../raw/images/\1.png)',
        text
    )


def main():
    topics_path = ROOT / 'data' / 'topics.json'
    topics = []
    if topics_path.exists():
        topics = json.loads(topics_path.read_text(encoding='utf-8'))

    topic_map = {t['id']: t for t in topics}
    page_topic = dict(PAGE_TOPIC_MAP)
    path_to_topic = parse_manifest()

    pages = {}
    tree_topics: dict[str, list[dict]] = defaultdict(list)
    standalone_pages: list[dict] = []
    seen_ids = set()

    def add_page(page_id: str, title: str, html: str, raw: str,
                 importance: str, source: str, topic_id: str = ''):
        if page_id in seen_ids:
            return
        seen_ids.add(page_id)
        page_entry = {
            'id': page_id, 'title': title, 'html': html, 'raw': raw,
            'importance': importance, 'source': source, 'topic': topic_id
        }
        pages[page_id] = page_entry
        tree_entry = {'id': page_id, 'title': title, 'importance': importance, 'source': source}
        if topic_id:
            tree_topics[topic_id].append(tree_entry)
        else:
            standalone_pages.append(tree_entry)

    # --- 处理生成的 wiki 页面 ---
    gen_dir = ROOT / 'wiki_generated'
    for md_file in sorted(gen_dir.glob('*.md')):
        if md_file.name == 'index.md':
            continue
        raw = md_file.read_text(encoding='utf-8')
        raw = resolve_asset_refs(raw)
        title = md_file.stem
        # 从第一行 H1 提取标题
        m = re.match(r'^#\s+(.+)', raw)
        if m:
            title = m.group(1).strip()
        html = md_to_html(raw)
        topic_id = page_topic.get(md_file.name, '')
        importance = infer_importance(raw, 'generated')
        add_page(md_file.stem, title, html, raw, importance, 'generated', topic_id)

    # --- 处理人工笔记 ---
    man_dir = ROOT / 'wiki_manual'
    for md_file in sorted(man_dir.glob('*.md')):
        if md_file.name in ('README.md',):
            continue
        raw = md_file.read_text(encoding='utf-8')
        raw = resolve_asset_refs(raw)
        title = md_file.stem
        m = re.match(r'^#\s+(.+)', raw)
        if m:
            title = m.group(1).strip()
        html = md_to_html(raw)
        # 从 manifest 查找 topic 映射
        rel_path = f'wiki_manual/{md_file.name}'
        topic_id = path_to_topic.get(rel_path, '')
        importance = infer_importance(raw, 'manual', str(md_file))
        add_page(md_file.stem, title, html, raw, importance, 'manual', topic_id)

    # --- 构建目录树 ---
    tree = []
    for t in topics:
        topic_pages = tree_topics.get(t['id'], [])
        if not topic_pages:
            continue
        # 排序：generated first, then manual; high importance first
        topic_pages.sort(key=lambda p: (0 if p['source'] == 'generated' else 1,
                                         0 if p['importance'] == 'high' else 1 if p['importance'] == 'medium' else 2,
                                         p['title']))
        tree.append({
            'id': t['id'],
            'title': t['title'],
            'summary': t.get('summary', ''),
            'pages': topic_pages
        })

    # 收集未被映射到任何主题的人工笔记
    mapped_manual = {p['id'] for t in tree for p in t['pages'] if p['source'] == 'manual'}
    for p in standalone_pages:
        if p['id'] not in mapped_manual:
            # 尝试推测主题
            pass

    if standalone_pages:
        standalone_pages.sort(key=lambda p: (0 if p['importance'] == 'high' else 1, p['title']))
        tree.append({
            'id': '_standalone',
            'title': '独立页面',
            'summary': '未归入特定主题的页面',
            'pages': standalone_pages
        })

    # --- 输出 wiki_content.js ---
    output = []
    output.append('// 由 build_wiki_content.py 自动生成。请勿手动编辑。')
    output.append('// 重新生成: python tools/build_wiki_content.py')
    output.append('window.__WIKI_CONTENT__ = {')

    # pages
    output.append('  pages: {')
    for pid, p in sorted(pages.items()):
        entry = {
            'id': p['id'], 'title': p['title'], 'html': p['html'],
            'importance': p['importance'], 'source': p['source'], 'topic': p['topic']
        }
        raw_str = p['raw']
        entry['raw'] = raw_str
        js = json.dumps(entry, ensure_ascii=False, indent=None)
        output.append(f'    {json.dumps(pid, ensure_ascii=False)}: {js},')
    output.append('  },')

    # tree
    output.append('  tree: ')
    output.append(json.dumps(tree, ensure_ascii=False, indent=2))
    output.append('};')

    out_path = ROOT / 'app' / 'wiki_content.js'
    out_path.write_text('\n'.join(output), encoding='utf-8')
    print(f'写入 {out_path} ({len(pages)} 页, {len(tree)} 个主题分组)')


if __name__ == '__main__':
    main()
