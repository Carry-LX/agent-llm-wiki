"""为 assets_enriched.jsonl 补全 label_title/label_summary，并交叉回填 source_url。

生成规则:
- label_title: 直接使用 search_corpus 中对应 asset_id 的 evidence_label
- label_summary: 从 clean_text 或 best_text 提取前 120 个有效字符，在句号处截断
- source_url 双向回填: asset <-> search_corpus <-> claims
- OCR 噪声标记: 为命中 OCR 噪声模式的 asset 追加 ocr_noise flag

用法: python tools/enrich_asset_labels.py
"""
import json, re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = ROOT / 'raw' / 'assets_enriched.jsonl'
CORPUS_PATH = ROOT / 'data' / 'search_corpus.jsonl'
CLAIMS_PATH = ROOT / 'data' / 'claims.jsonl'

OCR_NOISE_PATTERNS = [
    '暴万', '余弱', 'AINE',
    '氵', '扌',
    '履盖', 'Witte Ata',
    '宀',
    '上玉文',
    '注意万不集中',
]

def generate_summary(text, max_chars=120):
    if not text:
        return ""
    text = text.strip()
    truncated = text[:max_chars]
    for sep in ['。', '；', '\n', '，']:
        idx = truncated.rfind(sep)
        if idx > max_chars * 0.4:
            truncated = truncated[:idx] + sep if sep in '。；' else truncated[:idx]
            break
    return truncated.strip()

def has_ocr_noise(text):
    if not text:
        return False
    return any(pat in text for pat in OCR_NOISE_PATTERNS)

def main():
    with open(CORPUS_PATH, 'r', encoding='utf-8', errors='replace') as f:
        corpus = [json.loads(l) for l in f if l.strip()]
    corpus_by_aid = {c['asset_id']: c for c in corpus}

    with open(ASSETS_PATH, 'r', encoding='utf-8', errors='replace') as f:
        assets = [json.loads(l) for l in f if l.strip()]
    asset_by_aid = {a['asset_id']: a for a in assets}

    if CLAIMS_PATH.exists():
        with open(CLAIMS_PATH, 'r', encoding='utf-8') as f:
            claims = [json.loads(l) for l in f if l.strip()]
    else:
        claims = []

    filled_title = 0
    filled_summary = 0
    flagged_noise = 0
    corpus_url_filled = 0
    claim_url_filled = 0

    # 1. 补 asset label_title / label_summary / ocr_noise
    for a in assets:
        aid = a['asset_id']
        c = corpus_by_aid.get(aid, {})

        if not a.get('label_title') and c.get('evidence_label'):
            a['label_title'] = c['evidence_label']
            filled_title += 1

        if not a.get('label_summary'):
            text = a.get('clean_text', '') or a.get('best_text', '')
            if text:
                a['label_summary'] = generate_summary(text)
                filled_summary += 1

        if has_ocr_noise(a.get('best_text', '')):
            a['ocr_noise'] = True
            flagged_noise += 1

    # 2. 双向回填 source_url: asset -> corpus
    for c in corpus:
        if not c.get('source_url'):
            a = asset_by_aid.get(c['asset_id'], {})
            if a.get('source_url'):
                c['source_url'] = a['source_url']
                corpus_url_filled += 1

    # 3. 回填 claim source_urls: 从 corpus 聚合
    for claim in claims:
        if not claim.get('source_urls'):
            urls = []
            for eid in claim.get('evidence_ids', []):
                cr = corpus_by_aid.get(eid, {})
                url = cr.get('source_url', '')
                if url:
                    urls.append(url)
            if urls:
                claim['source_urls'] = list(set(urls))
                claim_url_filled += 1

    # 写回
    with open(ASSETS_PATH, 'w', encoding='utf-8') as f:
        for a in assets:
            f.write(json.dumps(a, ensure_ascii=False) + '\n')

    with open(CORPUS_PATH, 'w', encoding='utf-8') as f:
        for c in corpus:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    if claims:
        with open(CLAIMS_PATH, 'w', encoding='utf-8') as f:
            for c in claims:
                f.write(json.dumps(c, ensure_ascii=False) + '\n')

    print(f'已处理 {len(assets)} 条 asset / {len(corpus)} 条 corpus / {len(claims)} 条 claim:')
    print(f'  补 asset label_title: {filled_title}')
    print(f'  补 asset label_summary: {filled_summary}')
    print(f'  标记 asset ocr_noise: {flagged_noise}')
    print(f'  回填 corpus source_url: {corpus_url_filled}')
    print(f'  回填 claim source_urls: {claim_url_filled}')
    if corpus_url_filled == 0 and claim_url_filled == 0:
        print('  (source_url 无来源可回填，待 P3 恢复同步链路后自动生效)')

if __name__ == '__main__':
    main()
