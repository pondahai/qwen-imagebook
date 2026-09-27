# -*- coding: utf-8 -*-
"""壓圖：把 generated/ 裡各頁最新版本的 PNG 壓成 compressed/page{N}.jpg（ODT 素材）。

版本優先順序：page{N}_v3.png > page{N}_v2.png > page{N}_*.png（初版）
用法:
  python compress_images.py          # 42 頁全壓
  python compress_images.py 1 18 42  # 只壓指定頁
"""
import glob
import os
import sys

from PIL import Image

root = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(root, 'generated')
DST = os.path.join(root, 'compressed')


def find_src(n):
    cands = [os.path.join(SRC, 'page%d_v3.png' % n),
             os.path.join(SRC, 'page%d_v2.png' % n)]
    cands += sorted(glob.glob(os.path.join(SRC, 'page%d_*.png' % n)), reverse=True)
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def main():
    pages = [int(x) for x in sys.argv[1:]] or list(range(1, 43))
    os.makedirs(DST, exist_ok=True)
    for n in pages:
        src = find_src(n)
        if not src:
            print('page%d: NO SOURCE FOUND' % n)
            continue
        dst = os.path.join(DST, 'page%d.jpg' % n)
        img = Image.open(src).convert('RGB')
        img.thumbnail((1400, 1400), Image.LANCZOS)
        img.save(dst, 'JPEG', quality=85)
        print('page%d <- %s (%d KB)' % (n, os.path.basename(src), os.path.getsize(dst) // 1024))
    print('DONE')


if __name__ == '__main__':
    main()