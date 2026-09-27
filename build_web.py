# -*- coding: utf-8 -*-
"""
靜態網頁版打包腳本
- 解析 storyboard/完整故事.md（42 頁正文＋5 段落）
- 複製 compressed/page{N}.jpg → images/page{N}.jpg
- 產生 index.html（專案根目錄，GitHub Pages 可直接發布）

版面：翻頁電子書（封面、前言 2 頁、42 頁、開發過程、生成環境，共 47 頁）
     可切換回「直式捲動」完整版面
翻頁方式：左右箭頭鍵、點畫面、左右滑動、左右按鈕
用法：python build_web.py
"""
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STORY = ROOT / 'storyboard' / '完整故事.md'
SRC = ROOT / 'compressed'
DST = ROOT / 'images'
OUT = ROOT / 'index.html'

TITLE = '記憶方舟'
SUBTITLE = '42 頁 AI 繪本 · 為測試「Qwen-Image 2.1 模型 × GB10 機器」而構思的圖文故事'

ORIGIN = [
    '這本畫本，是為了測試一套軟硬體組合而構思的：<b>Qwen-Image 2.1</b>（生圖模型）與 <b>NVIDIA GB10</b>（機器）。',
    '我們沒有只測幾張單圖，而是讓它從頭到尾生成一本完整的 42 頁繪本。因為只有「完成品」才測得出模型的極限：',
]
ORIGIN_LIST = [
    '<b>批次耐力</b> — 42 張連續生成、每張 30-60 秒、一批跑完超過半小時，測機器能否全程穩定不掉鏈子。',
    '<b>長篇一致性</b> — 同一批角色（小滿、小芽、老燈、蝕）與同一座塔反覆出現，測模型「記不記得住」同一個人、同一座塔。',
    '<b>色彩控制</b> — 42 頁分成 5 段，每段不同色調（藍紫 → 紅橙 → 綠金），測提示詞能不能主導畫面配色。',
]
ORIGIN_END = '測試也真的測出了問題，最明顯的是「塔的造型沒有統一」——翻到最後「開發過程」可以看到怎麼修好它。'

SYNOPSIS = [
    '某個傍晚，草原中央升起一座比城市最高樓還高的塔。沒有人知道那是什麼，大家先叫它「那座塔」。',
    '十歲的林小滿決定去看個清楚。塔的最深處，他遇到一個忘了自己名字、用光做成的存在——「老燈」，也知道了塔的真實身分：<b>記憶方舟</b>，保存人類的記憶。而因為專門吞噬記憶與光的舊敵<b>蝕</b>正在逼近，方舟需要一顆「人心」才能完全啟動。',
    '小滿自願走進核心，成為方舟的心。決戰時，他把手心的妹妹笑聲與家的溫度丟進蝕的身體裡——蝕什麼光都吃得下，唯一消化不了的，是「想記住的意志」。',
    '蝕碎了，塔轉成柔和的綠金色，老燈終於睡著。每天傍晚，小芽的窗邊會亮一盞小小的光：「我在。」「我記得你。」',
]

DEVLOG = [
    ('2026-09-26 · 故事定稿', '決定故事地基（塔＝記憶方舟、守護者老燈、敵人蝕、主角小滿）、角色表與角色視覺基準，定稿 42 頁正文。'),
    ('2026-09-26 · 首批批量生成', '42 頁提示詞分 4 批送進 ComfyUI（每批 10-12 張、間隔 3 秒、輪詢結果），42 張全部成功。'),
    ('2026-09-26 · 繪本檔（ODT）產出', '先試直接寫 ODT 檔案格式，圖片被 LibreOffice 全數丟棄；改採「先做 DOCX 再轉 ODT」的中繼路線，搞定。'),
    ('2026-09-27 · 全書重生成（v2）', '統一提示詞格式後全書重生。驗收時發現問題：「塔的造型沒有統一」——每張圖獨立生成，AI 每頁畫了不同的塔。'),
    ('2026-09-27 · 塔視覺塊（v3）', '把固定塔描述（細高、圓頂、由內發光的巨大燈籠）寫進所有提示詞，以 P35 為基準頁，重生有塔的 15 頁。'),
    ('2026-09-27 · 驗收通過', '確認塔造型；最終檔改名為「繪本_42頁完整版.odt」；目錄整理、腳本收進專案、git 版本控制。'),
    ('2026-09-27 · 靜態網頁版', '把繪本做成翻頁電子書網頁（單一 HTML＋42 張圖，方向鍵、滑動或點畫面翻頁），不需要伺服器，GitHub Pages 即可發布。'),
]

CREDITS = [
    '故事文字：qwen3.8-27b（大語言模型）',
    '圖片生成：Qwen-Image 2.1（int8）· 文字理解 Qwen3-VL 8B（int8）· VAE（bf16）',
    '硬體：NVIDIA GB10 · 128GB 統一記憶體',
    '軟體：ComfyUI 0.37.0 / PyTorch 2.10 / Python 3.12',
    '生成參數：1024×1024 · steps 30 · CFG 1.0 · euler / simple · denoise 1.0',
]

CSS = """
:root { --ink:#3a3226; --paper:#f6f1e6; --accent:#8a6d3b; --muted:#a09478; --card:#fffdf7; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
  font-family:"Noto Serif TC","PMingLiU","Microsoft JhengHei",serif; }
.wrap { max-width:760px; margin:0 auto; padding:28px 16px 56px; }
.site { text-align:center; margin-bottom:20px; }
.site h1 { font-size:1.9rem; margin:0 0 6px; letter-spacing:.08em; }
.site .subtitle { color:var(--muted); font-size:.92rem; line-height:1.7; margin:0; }
#modeBtn { margin-top:12px; background:none; border:1px solid #cbbd97; color:var(--muted);
  border-radius:20px; padding:6px 18px; font-size:.85rem; cursor:pointer; font-family:inherit; }
#modeBtn:hover { color:var(--ink); border-color:var(--accent); }

/* ---- 翻頁電子書 ---- */
.readerbox { position:relative; }
.stage { position:relative; height:min(80vh,800px); background:var(--card);
  border-radius:14px; box-shadow:0 8px 30px rgba(90,70,40,.16); overflow:hidden;
  perspective:1800px; cursor:pointer; }
.sheet { position:absolute; inset:0; padding:30px 44px; opacity:0; pointer-events:none;
  transform:rotateY(10deg) translateX(8%); transform-origin:left center;
  transition:transform .5s ease, opacity .5s ease; }
.sheet.active { opacity:1; pointer-events:auto; transform:none; }
.sheet.before { opacity:0; transform:rotateY(-10deg) translateX(-8%); transform-origin:right center; }
.inner { height:100%; overflow-y:auto; display:flex; flex-direction:column;
  align-items:center; text-align:center; }
.inner::-webkit-scrollbar { width:6px; }
.inner::-webkit-scrollbar-thumb { background:#d8cdb4; border-radius:3px; }
.covtitle { font-size:2.6rem; font-weight:700; margin-top:16vh; letter-spacing:.12em; }
.covsub { color:var(--muted); line-height:2.1; margin-top:20px; }
.covhint { margin-top:20vh; color:#c4b795; font-size:.85rem; }
.sheet h2 { border:none; margin:0 0 18px; font-size:1.4rem; }
.sheet p { font-size:1.02rem; line-height:2; text-align:justify; margin:0 0 14px; max-width:620px; }
.sheet ul { padding-left:1.3em; margin:0 0 14px; }
.sheet li { font-size:1rem; line-height:1.9; margin:6px 0; }
.sheet ol.dev { padding-left:1.3em; margin:0; width:100%; max-width:620px; text-align:left; }
.sheet ol.dev li { margin:10px 0; }
.sheet ol.dev b { color:var(--accent); }
.sheet .pnum { font-size:.78rem; color:var(--muted); letter-spacing:.25em; }
.sheet .ptitle { font-size:1.3rem; font-weight:700; margin:6px 0 12px; }
.sheet img { width:100%; max-width:460px; max-height:44vh; object-fit:contain;
  border-radius:8px; margin:0 auto; }
.sheet .ptext { font-size:1.03rem; line-height:2; margin:16px 0 0; }
.sheet .credits { margin-top:20px; padding:18px 22px; background:#efe8d8; border-radius:12px;
  font-size:.95rem; line-height:2; text-align:left; }
.sheet .credits b { display:block; margin-bottom:6px; font-size:1.05rem; }
.nav { position:absolute; top:50%; transform:translateY(-50%); width:44px; height:44px;
  border-radius:50%; border:1px solid #d8cdb4; background:var(--card); color:var(--ink);
  font-size:1.5rem; line-height:1; cursor:pointer; padding:0 0 4px; z-index:5;
  box-shadow:0 2px 8px rgba(90,70,40,.15); }
.nav:hover { background:#f3ecdb; }
.nav-prev { left:10px; } .nav-next { right:10px; }
.barwrap { height:4px; background:#e8dfc9; border-radius:2px; margin-top:14px; overflow:hidden; }
.bar { height:100%; width:2%; background:var(--accent); transition:width .4s ease; }
.cnt { text-align:center; color:var(--muted); font-size:.8rem; margin-top:8px; letter-spacing:.1em; }

/* ---- 直式捲動版面 ---- */
#listview { display:none; }
body.listmode #reader { display:none; }
body.listmode #listview { display:block; }
#listview h2 { font-size:1.5rem; border-left:4px solid var(--accent); padding-left:10px; margin:48px 0 16px; }
#listview .intro p { font-size:1.02rem; line-height:1.95; margin:0 0 14px; }
#listview .intro ul { margin:0 0 14px; padding-left:1.4em; }
#listview .intro li { font-size:1rem; line-height:1.85; margin:6px 0; }
.part { display:flex; flex-wrap:wrap; align-items:baseline; gap:12px; margin:56px 0 4px;
  padding:10px 16px; border-radius:10px; }
.part .pname { font-size:1.3rem; font-weight:700; }
.part .pmeta { font-size:.85rem; opacity:.75; }
.page { margin:26px 0 42px; text-align:center; }
.pnum { font-size:.78rem; color:var(--muted); letter-spacing:.25em; }
.ptitle { font-size:1.3rem; font-weight:700; margin:6px 0 14px; }
.page img { width:100%; max-width:560px; border-radius:10px;
  box-shadow:0 3px 14px rgba(90,70,40,.18); }
.ptext { font-size:1.05rem; line-height:2; margin:20px auto 0; max-width:560px; text-align:justify; }
ol.dev { padding-left:1.3em; }
ol.dev li { margin:12px 0; line-height:1.85; }
ol.dev b { color:var(--accent); }
.credits { margin-top:20px; padding:18px 20px; background:#efe8d8; border-radius:10px;
  font-size:.9rem; line-height:1.9; }
.credits b { display:block; margin-bottom:6px; }
footer { text-align:center; margin-top:44px; color:var(--muted); font-size:.8rem; line-height:1.8; }
@media (max-width:560px) {
  .sheet { padding:24px 34px; }
  .covtitle { font-size:2rem; }
  .nav { width:38px; height:38px; font-size:1.2rem; }
}
"""

JS = """
(function(){
  var sheets = Array.prototype.slice.call(document.querySelectorAll('.sheet'));
  var cur = 0, busy = false;
  var cnt = document.getElementById('cnt'), bar = document.getElementById('bar');
  function show(n){
    n = Math.max(0, Math.min(sheets.length - 1, n));
    if(n === cur) return;
    for(var i = 0; i < sheets.length; i++){
      sheets[i].classList.toggle('active', i === n);
      sheets[i].classList.toggle('before', i < n);
    }
    cur = n;
    cnt.textContent = (n + 1) + ' / ' + sheets.length;
    bar.style.width = ((n + 1) / sheets.length * 100) + '%';
  }
  function guard(fn){
    if(busy) return;
    busy = true; fn();
    setTimeout(function(){ busy = false; }, 520);
  }
  window.next = function(){ guard(function(){ show(cur + 1); }); };
  window.prev = function(){ guard(function(){ show(cur - 1); }); };
  document.addEventListener('keydown', function(e){
    if(e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown'){ e.preventDefault(); window.next(); }
    else if(e.key === 'ArrowLeft' || e.key === 'PageUp'){ e.preventDefault(); window.prev(); }
  });
  var stage = document.getElementById('stage'), tx = 0, ty = 0;
  stage.addEventListener('click', function(e){
    var r = stage.getBoundingClientRect();
    if(e.clientX - r.left < r.width * 0.3) window.prev(); else window.next();
  });
  stage.addEventListener('touchstart', function(e){
    tx = e.touches[0].clientX; ty = e.touches[0].clientY;
  }, {passive:true});
  stage.addEventListener('touchend', function(e){
    var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if(Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy)){
      if(dx < 0) window.next(); else window.prev();
    }
  }, {passive:true});
  var btn = document.getElementById('modeBtn');
  btn.addEventListener('click', function(){
    var list = document.body.classList.toggle('listmode');
    btn.textContent = list ? '▤ 回到翻頁模式' : '⊞ 看完整直式版面';
  });
})();
"""


def parse_story(text):
    body = text.split('## 42 頁故事', 1)[1].split('## 圖片處置總表', 1)[0]
    sections, pages, cur = [], [], None
    for line in body.splitlines():
        m = re.match(r'^### 段落 (\d+)：(.+?)（(.+?)）\s*$', line)
        if m:
            parts = m.group(3).split('，')
            sections.append({
                'no': int(m.group(1)),
                'name': m.group(2).strip(),
                'range': parts[0].strip(),
                'tone': parts[-1].strip(),
            })
            continue
        pm = re.match(r'^\*\*P(\d+) (.+?)\*\*\s*$', line)
        if pm:
            cur = {'num': int(pm.group(1)), 'title': pm.group(2).strip(), 'text': '', 'sec': len(sections)}
            pages.append(cur)
            continue
        if cur is not None and line.startswith('> '):
            cur['text'] += line[2:].strip()
    return sections, pages


def tone_style(tone):
    if '藍紫' in tone:
        return '#5b4b8a', '#ede8f7'
    if '紅' in tone or '红' in tone:
        return '#b03a26', '#fbe9e3'
    if '綠' in tone or '绿' in tone:
        return '#3d7a38', '#e8f2e4'
    return '#6b6250', '#f0ece1'


def copy_images():
    DST.mkdir(exist_ok=True)
    n = 0
    for f in sorted(SRC.glob('page*.jpg')):
        if re.match(r'^page(\d+)\.jpg$', f.name):
            shutil.copy2(f, DST / f.name)
            n += 1
    return n


def text_sheet(head, body_html):
    return f'<div class="sheet"><div class="inner"><h2>{head}</h2>{body_html}</div></div>'


def story_sheet(p, e):
    t = e(p['title'])
    return ('<div class="sheet"><div class="inner">'
            f'<div class="pnum">P{p["num"]}</div>'
            f'<div class="ptitle">{t}</div>'
            f'<img src="images/page{p["num"]}.jpg" alt="P{p["num"]} {t}" loading="lazy">'
            f'<p class="ptext">{e(p["text"])}</p>'
            '</div></div>')


def build_html(sections, pages):
    e = html.escape
    h = ['<!DOCTYPE html>', '<html lang="zh-Hant">', '<head>',
         '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f'<title>{TITLE}｜42 頁 AI 繪本</title>',
         f'<style>{CSS}</style>', '</head>', '<body>', '<div class="wrap">']

    h.append('<header class="site">')
    h.append(f'<h1>{e(TITLE)}</h1>')
    h.append(f'<p class="subtitle">{e(SUBTITLE)}</p>')
    h.append('<button id="modeBtn" type="button">⊞ 看完整直式版面</button>')
    h.append('</header>')

    # ---- 翻頁視圖 ----
    origin_body = ''.join(f'<p>{p}</p>' for p in ORIGIN)
    origin_body += '<ul>' + ''.join(f'<li>{li}</li>' for li in ORIGIN_LIST) + '</ul>'
    origin_body += f'<p>{ORIGIN_END}</p>'
    syn_body = ''.join(f'<p>{p}</p>' for p in SYNOPSIS)
    dev_body = '<ol class="dev">' + ''.join(
        f'<li><b>{e(t)}</b> — {e(d)}</li>' for t, d in DEVLOG) + '</ol>'
    cred_body = '<div class="credits"><b>生成環境</b><br>' + '<br>'.join(e(c) for c in CREDITS) + '</div>'

    sheets = [
        '<div class="sheet active"><div class="inner">'
        f'<div class="covtitle">{e(TITLE)}</div>'
        f'<div class="covsub">42 頁 AI 繪本<br>為測試「Qwen-Image 2.1 × GB10」而構思</div>'
        '<div class="covhint">← → 鍵、左右滑動，或點畫面翻頁</div>'
        '</div></div>',
        text_sheet('前言：測試的源起', origin_body),
        text_sheet('故事大綱', syn_body),
    ]
    sheets += [story_sheet(p, e) for p in pages]
    sheets.append(text_sheet('開發過程', dev_body))
    sheets.append(text_sheet('生成環境', cred_body))
    total = len(sheets)

    h.append('<section id="reader">')
    h.append('<div class="readerbox">')
    h.append('<div class="stage" id="stage">')
    h.extend(sheets)
    h.append('</div>')
    h.append('<button class="nav nav-prev" type="button" onclick="prev()" aria-label="上一頁">‹</button>')
    h.append('<button class="nav nav-next" type="button" onclick="next()" aria-label="下一頁">›</button>')
    h.append('</div>')
    h.append('<div class="barwrap"><div class="bar" id="bar"></div></div>')
    h.append(f'<div class="cnt" id="cnt">1 / {total}</div>')
    h.append('</section>')

    # ---- 直式捲動視圖 ----
    h.append('<section id="listview">')
    h.append('<div class="intro">')
    h.append('<h2>前言：測試的源起</h2>')
    h.extend(f'<p>{p}</p>' for p in ORIGIN)
    h.append('<ul>')
    h.extend(f'<li>{li}</li>' for li in ORIGIN_LIST)
    h.append('</ul>')
    h.append(f'<p>{ORIGIN_END}</p>')
    h.append('<h2>故事大綱</h2>')
    h.extend(f'<p>{p}</p>' for p in SYNOPSIS)
    h.append('</div>')

    last_sec = 0
    for p in pages:
        if p['sec'] > last_sec:
            s = sections[p['sec'] - 1]
            fg, bg = tone_style(s['tone'])
            h.append(f'<div class="part" style="background:{bg};color:{fg}">'
                     f'<span class="pname">段落 {s["no"]}｜{e(s["name"])}</span>'
                     f'<span class="pmeta">{e(s["range"])} · {e(s["tone"])}</span></div>')
            last_sec = p['sec']
        t = e(p['title'])
        h.append('<div class="page">')
        h.append(f'<div class="pnum">P{p["num"]}</div>')
        h.append(f'<div class="ptitle">{t}</div>')
        h.append(f'<img src="images/page{p["num"]}.jpg" alt="P{p["num"]} {t}" loading="lazy">')
        h.append(f'<p class="ptext">{e(p["text"])}</p>')
        h.append('</div>')

    h.append('<h2>開發過程</h2>')
    h.append('<ol class="dev">')
    h.extend(f'<li><b>{e(t)}</b> — {e(d)}</li>' for t, d in DEVLOG)
    h.append('</ol>')

    h.append('<div class="credits"><b>生成環境</b>')
    h.extend(e(c) for c in CREDITS)
    h.append('</div>')

    h.append('<footer>')
    h.append(f'《{e(TITLE)}》42 頁 AI 繪本 · 全書 42 圖由 Qwen-Image 2.1 生成 · 2026')
    h.append('</footer>')
    h.append('</section>')

    h.append('</div>')
    h.append(f'<script>{JS}</script>')
    h.append('</body></html>')
    return '\n'.join(h) + '\n'


def main():
    text = STORY.read_text(encoding='utf-8')
    sections, pages = parse_story(text)
    if len(pages) != 42:
        raise SystemExit(f'頁數異常：解析到 {len(pages)} 頁（應為 42）')
    n_img = copy_images()
    OUT.write_text(build_html(sections, pages), encoding='utf-8')
    print(f'index.html 已產生（47 頁翻頁視圖＋直式捲動視圖）')
    print(f'images/ 已複製 {n_img} 張圖')


if __name__ == '__main__':
    main()