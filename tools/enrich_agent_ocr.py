"""对 raw/assets.jsonl 中的图片运行 tesseract OCR，生成 raw/assets_enriched.jsonl。

输入: raw/assets.jsonl (sync_onenote_agent.ps1 的输出)
输出:
  - raw/ocr_cache/*.txt (每张图片的 OCR 原文)
  - raw/assets_enriched.jsonl (在 assets.jsonl 基础上追加 OCR 字段)

依赖: 本机需安装 tesseract (默认路径 E:\tesseract\tesseract.exe)
      中文语言包 chi_sim

用法: python tools/enrich_agent_ocr.py
"""
import json, re, subprocess, sys, io
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ====== 配置变量 ======
ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = ROOT / 'raw' / 'assets.jsonl'
OUTPUT_PATH = ROOT / 'raw' / 'assets_enriched.jsonl'
OCR_CACHE_DIR = ROOT / 'raw' / 'ocr_cache'
TESSERACT_EXE = r'E:\tesseract\tesseract.exe'
TESSERACT_LANG = 'chi_sim+eng'

def clean_ocr_text(text):
    """清理 OCR 输出：合并空白、去掉明显噪声行。"""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 去掉纯标点/符号行
        if len(line) < 2:
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)

def run_tesseract(image_path, cache_path):
    """对单张图片运行 tesseract，结果写入 cache_path。返回 OCR 文本。"""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # tesseract 输出: image.png output_base (不加 .txt 后缀)
    output_base = str(cache_path.with_suffix(''))
    try:
        subprocess.run(
            [TESSERACT_EXE, str(image_path), output_base, '-l', TESSERACT_LANG],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        print(f'  [TIMEOUT] {image_path.name}')
        return ""
    except FileNotFoundError:
        print(f'  [SKIP] tesseract 未安装在 {TESSERACT_EXE}')
        return ""

    txt_path = cache_path.with_suffix('.txt')
    if txt_path.exists():
        text = txt_path.read_text(encoding='utf-8', errors='replace')
        return clean_ocr_text(text)
    return ""

def generate_clean_text(ocr_text):
    """从 OCR 原文生成紧凑版纯文本（去行连接）。"""
    if not ocr_text:
        return ""
    # 用空格替换换行，合并多余空白
    text = ocr_text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    if not ASSETS_PATH.exists():
        print(f'错误: {ASSETS_PATH} 不存在，请先运行 sync_onenote_agent.ps1')
        return

    with open(ASSETS_PATH, 'r', encoding='utf-8', errors='replace') as f:
        assets = [json.loads(l) for l in f if l.strip()]

    print(f'处理 {len(assets)} 条 asset...')

    ocr_count = 0
    skip_count = 0

    for a in assets:
        aid = a['asset_id']
        image_path = a.get('image_path', '')

        if a.get('asset_type') != 'onenote_image' or not image_path:
            skip_count += 1
            continue

        full_image = ROOT / image_path
        cache_path = OCR_CACHE_DIR / f'{aid}.txt'

        # 如果已有缓存且图片未变，跳过
        if cache_path.exists():
            existing = cache_path.read_text(encoding='utf-8', errors='replace')
            if existing.strip():
                a['tesseract_text'] = existing
                a['ocr_text'] = existing
                a['clean_text'] = generate_clean_text(existing)
                a['best_text'] = a['clean_text']
                a['best_text_source'] = 'tesseract_chi_sim_eng'
                skip_count += 1
                continue

        if not full_image.exists():
            print(f'  [MISSING] {image_path}')
            skip_count += 1
            continue

        print(f'  OCR [{aid}] {image_path}')
        text = run_tesseract(full_image, cache_path)
        if text:
            a['tesseract_text'] = text
            a['ocr_text'] = text
            a['clean_text'] = generate_clean_text(text)
            a['best_text'] = a['clean_text']
            a['best_text_source'] = 'tesseract_chi_sim_eng'
            ocr_count += 1

    # 写回
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for a in assets:
            f.write(json.dumps(a, ensure_ascii=False) + '\n')

    print(f'\n完成: OCR {ocr_count} 张, 跳过 {skip_count} 条')
    print(f'输出: {OUTPUT_PATH}')

if __name__ == '__main__':
    main()
