# -*- coding: utf-8 -*-
"""批次生成：從 storyboard/42頁提示詞.md 讀 prompt，送 ComfyUI 下載成品。

用法:
  python api/batch_generate.py                 # 全部 42 頁
  python api/batch_generate.py 1 18 42         # 指定頁
  python api/batch_generate.py --suffix v3     # 輸出綴字尾（預設 v3）
輸出: generated/page{N}_{suffix}.png（已存在的會跳過）
"""
import json
import os
import re
import sys
import time
import urllib.request

COMFY = 'http://100.89.149.50:8188'
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(root, 'api', 'template.json')
OUTDIR = os.path.join(root, 'generated')
MD = os.path.join(root, 'storyboard', '42頁提示詞.md')


def load_prompts():
    with open(MD, encoding='utf-8') as f:
        text = f.read()
    m = re.findall(r'### P(\d+)\s*\n```\s*\n(.*?)\s*\n```', text, re.DOTALL)
    return {int(n): p.strip() for n, p in m}


def http_get_json(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def send(num, prompt, suffix):
    with open(TEMPLATE, encoding='utf-8') as f:
        t = json.load(f)
    t['prompt']['4']['inputs']['prompt'] = prompt
    t['prompt']['8']['inputs']['filename_prefix'] = 'page%d' % num
    data = json.dumps(t).encode('utf-8')
    req = urllib.request.Request(COMFY + '/prompt', data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))['prompt_id']


def wait_and_download(num, pid, suffix):
    fn = os.path.join(OUTDIR, 'page%d_%s.png' % (num, suffix))
    for _ in range(84):
        time.sleep(5)
        try:
            h = http_get_json(COMFY + '/history/' + pid)
        except Exception as e:
            print('  P%d poll error: %s' % (num, e), flush=True)
            continue
        entry = h.get(pid)
        if not entry:
            continue
        status = (entry.get('status') or {}).get('status_str', '')
        if status == 'error':
            print('P%d ERROR %s' % (num, entry.get('status')), flush=True)
            return False
        for node_id in sorted(entry.get('outputs') or {}):
            for img in (entry['outputs'][node_id].get('images') or []):
                url = '%s/view?filename=%s&subfolder=%s&type=%s' % (
                    COMFY, img['filename'], img.get('subfolder', ''),
                    img.get('type', 'output'))
                urllib.request.urlretrieve(url, fn)
                print('P%d ok -> %s' % (num, fn), flush=True)
                return True
    print('P%d TIMEOUT' % num, flush=True)
    return False


def main():
    args = [a for a in sys.argv[1:]]
    suffix = 'v3'
    if '--suffix' in args:
        i = args.index('--suffix')
        suffix = args[i + 1]
        del args[i:i + 2]
    pages = [int(x) for x in args] if args else list(range(1, 43))

    prompts = load_prompts()
    print('prompts parsed: %d' % len(prompts), flush=True)
    ok, failed = [], []
    for idx, num in enumerate(pages):
        fn = os.path.join(OUTDIR, 'page%d_%s.png' % (num, suffix))
        if os.path.exists(fn):
            print('P%d skip (already exists)' % num, flush=True)
            ok.append(num)
            continue
        if idx > 0:
            time.sleep(3)
        prompt = prompts.get(num)
        if not prompt:
            print('P%d NO PROMPT FOUND IN MD' % num, flush=True)
            failed.append(num)
            continue
        pid = None
        for attempt in range(2):
            try:
                pid = send(num, prompt, suffix)
                break
            except Exception as e:
                print('P%d send attempt %d failed: %s' % (num, attempt + 1, e), flush=True)
                time.sleep(10)
        if not pid:
            failed.append(num)
            continue
        (ok if wait_and_download(num, pid, suffix) else failed).append(num)
    print('BATCH DONE ok=%d failed=%s' % (len(ok), failed), flush=True)


if __name__ == '__main__':
    main()