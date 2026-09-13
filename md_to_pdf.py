# -*- coding: utf-8 -*-
"""鑑定書md → 印刷用HTML → Chrome headless でPDF化"""
import html
import os
import re
import subprocess
import sys

try:
    import figures as FIG
except ImportError:
    FIG = None

# 章扉に差し込む図(コード側で確定配置する。モデルにマーカーを書かせない)
FIG_BEFORE = {
    '第2章': ('elements', 'あなたの炉の火加減。器の満ち方が、生まれつきの体質です。'),
    '一葉｜太陽と月': ('sunmoon', '王と王妃。育てていきたい方向と、心が安心する条件。'),
    '第3章': ('castle',   'あなたの王国の間取り。どの官が、どの部屋に住んでいるか。'),
    '第8章': ('timeline', '心の季節と、現実の季節。そして今年の部屋と、時代の波。'),
}
# 章末に置く指の回収図(その章まででいくつ灯ったか)
HANDS_AFTER = {'第1章': 2, '第3章': 5, '第4章': 8, '第5章': 10}

CHAPTER = re.compile(r'^(はじめに|序章|第[0-9１-９十]+章|終章|第[一二]葉|一葉|次の扉|王国の宮廷)([｜|]|$)')
METHOD = re.compile(r'^[【\[]\s*(星を読まれる方へ|読みの手順)\s*[】\]]')
HOLD = re.compile(r'^[【\[]\s*(いかがでしょうか|ここで私が決めなかったこと|判断を止めた場所)\s*[】\]]')
FINGERS = re.compile(r'^.{0,60}(戻りました|揃いました|入りました|弾き方です)。$')
BLANK = re.compile(r'[（(][\s　]{4,}[）)]')

CSS = """
body { font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
       font-size: 10.5pt; line-height: 2.0; color: #2b2a26; margin: 0; }
.cover { text-align: center; margin-top: 70mm; page-break-after: always; }
.cover .label { font-size: 9pt; letter-spacing: 0.35em; color: #b49a6c; margin-bottom: 22px; }
.cover h1 { font-size: 22pt; font-weight: 600; letter-spacing: 0.12em; margin: 0 0 14px; }
.cover .meta { font-size: 9.5pt; color: #6b675e; margin-bottom: 30px; }
.cover .author { font-size: 11pt; letter-spacing: 0.15em; color: #7a5c2e; }
h2 { font-size: 13.5pt; font-weight: 600; letter-spacing: 0.08em; color: #7a5c2e;
     margin: 3em 0 1.4em; padding-bottom: 0.5em; border-bottom: 1px solid #e4ddd0;
     page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 2em 0 1em; }
p { margin: 0 0 1.5em; text-align: justify; orphans: 3; widows: 3; }
p.recipe { margin-bottom: 0.4em; padding-left: 1em; }
p.recipe { margin-bottom: 0.4em; padding-left: 1em; }
/* 技術層: 本文の詩情と切り離して罫線囲みで隔離する */
.tech { margin: 1.8em 0 1.2em; padding: 3.5mm 5mm; background: #faf8f4;
        border-left: 2px solid #c9bb9a; page-break-inside: avoid; }
.tech .cap { font-size: 8.5pt; letter-spacing: 0.12em; color: #9a7b42;
             margin: 0 0 0.5em; font-weight: 600; }
.tech p { font-size: 9pt; line-height: 1.75; margin: 0 0 0.35em; color: #4a463e; }
/* 読者への問いかけ: 技術欄とは別の見た目にする(温度を上げる) */
.ask { margin: 1.8em 0 1.2em; padding: 3.5mm 6mm; border-top: 1px solid #ded5c4;
       border-bottom: 1px solid #ded5c4; page-break-inside: avoid; }
.ask .cap { font-size: 9pt; letter-spacing: 0.14em; color: #7a5c2e;
            margin: 0 0 0.6em; font-weight: 600; text-align: center; }
.ask p { font-size: 10pt; line-height: 1.95; margin: 0 0 0.35em; color: #2b2a26; }
.fingers { margin: 1.2em 0 2.4em; padding-top: 0.7em; border-top: 1px solid #e4ddd0;
           font-size: 9.5pt; letter-spacing: 0.05em; color: #7a5c2e; text-align: right; }
/* 記入欄: 読者が実際に書き込む罫線 */
.blank { border-bottom: 1px solid #b9b2a4; height: 9mm; margin: 0.6em 0 1.8em 6mm;
          width: calc(100% - 12mm); }
.blank + .blank { margin-top: -1.2em; }
.dateline { font-size: 9pt; color: #6b675e; margin: 2em 0 1em; }
.gate { margin: 2.5em 0; padding: 6mm 7mm; border: 1px solid #ded5c4;
        page-break-inside: avoid; }
.gate p { margin: 0 0 0.9em; }
.gatefold { page-break-before: always; page-break-after: always; text-align: center;
            padding-top: 26mm; }
.gatefold .no { font-size: 30pt; color: #d8cdb6; letter-spacing: 0.1em; line-height: 1; }
.gatefold .ti { font-size: 15pt; color: #7a5c2e; letter-spacing: 0.14em;
                margin: 5mm 0 2mm; font-weight: 600; }
.gatefold .sub { font-size: 9.5pt; color: #8a8478; letter-spacing: 0.1em; }
.gatefold .fig { max-width: 150mm; margin: 12mm auto 6mm; }
.gatefold.tall { padding-top: 12mm; }
.gatefold.tall .fig { max-width: 132mm; margin: 8mm auto 5mm; }
.gatefold.leaf .no { font-size: 13pt; letter-spacing: 0.3em; color: #b49a6c; }
.gatefold .cap { font-size: 9pt; color: #8a8478; }
.handfig { margin: 0.8em auto 2.6em; max-width: 96mm; }
.handfig.big { max-width: 150mm; margin: 6mm auto; }
@page { margin: 22mm 18mm; }
"""


def md_to_html(md_path, title, meta, out_html, cover=True):
    body = []
    para = []
    tech_open = [False, 0]   # [開いているか, 箱に入れた本文の数]
    chart = os.environ.get('CHART_TXT')
    D = FIG.parse_chart(chart) if (FIG and chart and os.path.exists(chart)) else None
    prev_ch = [None]

    def svg(kind):
        if kind == 'elements':
            return FIG.fig_elements(D['elem'], D['modes'])
        if kind == 'castle':
            return FIG.fig_castle(D['houses'], D.get('asc', ''), D.get('mc', ''))
        if kind == 'sunmoon':
            return FIG.fig_sun_moon(D)
        if kind == 'timeline':
            return FIG.fig_timeline(D)
        return ''

    def close_chapter():
        n = HANDS_AFTER.get(prev_ch[0])
        if n and D is not None:
            body.append('<div class="handfig">' + FIG.fig_hands(n) + '</div>')
        prev_ch[0] = None

    def fmt(s):
        s = html.escape(s)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

    def flush():
        if para:
            body.append('<p>' + fmt(''.join(para)) + '</p>')
            para.clear()

    for raw in open(md_path, encoding='utf-8'):
        line = raw.strip()
        # モデルが太字で包む / 欄外ラベルを本文化する揺れを吸収する
        line = re.sub(r'^\*\*\s*([【\[][^】\]]*[】\]])\s*\*\*', r'\1', line)
        line = re.sub(r'^\*\*?[^*\n]{0,24}(章末|葉末)\*\*?[\s　]+', '', line)
        # モデルが三点セットの見出しを # 形式で書く揺れを【】形式へ正規化する
        line = re.sub(r'^#+\s*(星を読まれる方へ|読みの手順|いかがでしょうか|ここで私が決めなかったこと)\s*$',
                      r'【\1】', line)
        line = line.replace('**', '')   # 本文に太字は置かない
        if re.match(r'^[（(]『?(はい|続けて)', line):
            continue
        if not line or line == '---':
            flush()
            # 見出し直後の空行では閉じない。本文が1つ以上入ってから閉じる
            if tech_open[0] and tech_open[1] > 0:
                body.append('</div>')
                tech_open[0] = False
            continue
        heading = re.sub(r'^#+\s*', '', line)
        # 完全版の章題(序章/第N章/終章)と、簡易版の「本質｜」「あなたの問いへ」等の#見出し
        if re.match(r'^#+\s', line) and (CHAPTER.match(heading) or len(heading) <= 24):
            flush()
            close_chapter()
            if D is not None and heading.startswith('王国の宮廷'):
                body.append(f'<h2>{fmt(heading)}</h2>')
                body.append('<div class="handfig big">' + FIG.fig_hands(10, labels=True) + '</div>')
                prev_ch[0] = None
                continue
            key = next((k for k in FIG_BEFORE if heading.startswith(k)), None) if D is not None else None
            if key:
                kind, cap = FIG_BEFORE[key]
                parts = heading.split('｜')
                no = parts[0]
                ti = parts[1] if len(parts) > 1 else ''
                sub = ''
                if '――' in ti:
                    ti, sub = ti.split('――', 1)
                cls = 'gatefold tall' if kind == 'castle' else (
                    'gatefold leaf' if not no.startswith('第') or '葉' in no else 'gatefold')
                body.append('<div class="' + cls + '"><div class="no">' + fmt(no) + '</div>'
                            '<div class="ti">' + fmt(ti) + '</div><div class="sub">' + fmt(sub) + '</div>'
                            '<div class="fig">' + svg(kind) + '</div>'
                            '<div class="cap">' + fmt(cap) + '</div></div>')
            body.append(f'<h2>{fmt(heading)}</h2>')
            prev_ch[0] = heading.split('｜')[0]
            continue
        if re.match(r'^#+\s', line):
            flush()
            body.append(f'<h3>{fmt(heading)}</h3>')
            continue
        if METHOD.match(line) or HOLD.match(line):
            flush()
            is_tech = bool(METHOD.match(line))
            cap = '星を読まれる方へ' if is_tech else 'いかがでしょうか'
            rest = re.sub(r'^[【\[][^】\]]*[】\]]\s*', '', line)
            body.append(f'<div class="{"tech" if is_tech else "ask"}"><p class="cap">{cap}</p>')
            tech_open[0] = True
            tech_open[1] = 0
            if rest:
                body.append(f'<p>{fmt(rest)}</p>')
                tech_open[1] += 1
            continue
        if tech_open[0]:
            # 箱の中身。長い段落も取りこぼさない（2本まで）
            if tech_open[1] < 2:
                body.append(f'<p>{fmt(line)}</p>')
                tech_open[1] += 1
                continue
            body.append('</div>')
            tech_open[0] = False
        if FINGERS.match(line):
            flush()
            body.append(f'<p class="fingers">{fmt(line)}</p>')
            continue
        if re.match(r'^記入日', line):
            flush()
            body.append(f'<p class="dateline">{fmt(line)}</p>')
            continue
        if BLANK.fullmatch(line.strip()):
            flush()
            body.append('<div class="blank"></div>')
            continue
        if re.match(r'^[-*・]\s?', line):
            flush()
            body.append('<p class="recipe">・' + fmt(re.sub(r'^[-*・]\s?', '', line)) + '</p>')
            continue
        para.append(line)
    flush()
    if tech_open[0]:
        body.append('</div>')
        tech_open[0] = False
    close_chapter()

    wheel_html = ''
    wheel_path = os.environ.get('WHEEL_SVG')
    if wheel_path and os.path.exists(wheel_path):
        svg = open(wheel_path, encoding='utf-8').read()
        wheel_html = (f'<div style="page-break-after:always;text-align:center;">'
                      f'<h2 style="border-bottom:none;margin:0 0 4mm;">鑑定データ｜三重円</h2>'
                      f'<div style="max-width:150mm;margin:0 auto;">{svg}</div></div>')
    front_path = os.environ.get('FRONT_HTML')
    if front_path and os.path.exists(front_path):
        wheel_html = open(front_path, encoding='utf-8').read()
    appendix_html = ''
    appendix_path = os.environ.get('APPENDIX_HTML')
    if appendix_path and os.path.exists(appendix_path):
        appendix_html = open(appendix_path, encoding='utf-8').read()

    cover_html = f"""<div class="cover"><div class="label">NARRATIVE ASTROLOGY READING</div>
<h1>{html.escape(title)}</h1><div class="meta">{html.escape(meta)}</div>
<div class="author">星とハーブの研究家　織田 剛</div></div>""" if cover else \
        f"""<div style="text-align:center;margin:8mm 0 12mm;">
<div class="label" style="font-size:8pt;letter-spacing:0.3em;color:#b49a6c;">NARRATIVE ASTROLOGY READING</div>
<h1 style="font-size:16pt;letter-spacing:0.1em;margin:8px 0 6px;">{html.escape(title)}</h1>
<div class="meta" style="font-size:9pt;color:#6b675e;">{html.escape(meta)}</div></div>"""

    doc = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<title>{html.escape(title)}</title><style>{CSS}
svg {{ width: 100%; height: auto; }}</style></head><body>
{cover_html}
{wheel_html}
{''.join(body)}
{appendix_html}
</body></html>"""
    open(out_html, 'w', encoding='utf-8').write(doc)


if __name__ == '__main__':
    md, title, meta, out_pdf = sys.argv[1:5]
    cover = '--no-cover' not in sys.argv
    md = os.path.abspath(md)
    out_pdf = os.path.abspath(out_pdf)
    out_html = md.replace('.md', '_print.html')
    md_to_html(md, title, meta, out_html, cover=cover)
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={out_pdf}', f'file://{out_html}'],
                   check=True, capture_output=True, timeout=120)
    print('PDF:', out_pdf)
