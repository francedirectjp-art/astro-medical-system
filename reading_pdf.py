# -*- coding: utf-8 -*-
"""鑑定書PDF生成（WeasyPrint版・自動発行用）

md_to_pdf.py(Chrome版)と同じ紙面設計:
表紙 → あなたの星の地図(ネイタル単円) → 本文 → 巻末資料(三重円+データ表)
"""
import base64
import html as html_mod
import os
import re

import horoscope_render as hr

_BASE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(_BASE, 'fonts')

CHAPTER = re.compile(r'^(序章|第[0-9１-９十]+章|終章|あなたの問いへ)([｜|].*)?$')

CSS = """
@font-face { font-family: 'Noto Serif JP'; src: url('__FD__/NotoSerifJP-Regular.otf'); }
@font-face { font-family: 'Noto Serif JP'; font-weight: bold; src: url('__FD__/NotoSerifJP-Bold.otf'); }
@font-face { font-family: 'NSSym'; src: url('__FD__/NotoSansSymbols-Regular.ttf'); }
body { font-family: 'Noto Serif JP', serif;
       font-size: 10.5pt; line-height: 2.0; color: #2b2a26; margin: 0; }
.cover { text-align: center; margin-top: 70mm; page-break-after: always; }
.cover .label { font-size: 9pt; letter-spacing: 0.35em; color: #b49a6c; margin-bottom: 22px; }
.cover h1 { font-size: 22pt; font-weight: bold; letter-spacing: 0.12em; margin: 0 0 14px; }
.cover .meta { font-size: 9.5pt; color: #6b675e; margin-bottom: 30px; }
.cover .author { font-size: 11pt; letter-spacing: 0.15em; color: #7a5c2e; }
h2 { font-size: 13.5pt; font-weight: bold; letter-spacing: 0.08em; color: #7a5c2e;
     margin: 3em 0 1.4em; padding-bottom: 0.5em; border-bottom: 1pt solid #e4ddd0;
     page-break-after: avoid; }
p { margin: 0 0 1.5em; text-align: justify; orphans: 3; widows: 3; }
p.recipe { margin-bottom: 0.4em; padding-left: 1em; }
img.wheel { width: 100%; }
.data-grid { }
.data-card { border: 1pt solid #e4ddd0; border-radius: 4pt; padding: 6pt 8pt;
             margin-bottom: 8pt; page-break-inside: avoid; }
.data-card h4 { font-size: 9.5pt; color: #7a5c2e; margin: 0 0 4pt; letter-spacing: 0.08em; }
.data-card table { width: 100%; border-collapse: collapse; font-size: 8.5pt; line-height: 1.6; }
.data-card td { padding: 1pt 3pt; border-bottom: 0.5pt solid #eee7d9; }
@page { margin: 22mm 18mm; }
""".replace('__FD__', FONT_DIR.replace('\\', '/'))


def _svg_img(svg, cls='wheel', max_width_mm=None):
    b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    style = f'style="max-width:{max_width_mm}mm;"' if max_width_mm else ''
    return (f'<img class="{cls}" {style} '
            f'src="data:image/svg+xml;base64,{b64}"/>')


def _body_html(reading_md):
    body = []
    para = []

    def fmt(s):
        s = html_mod.escape(s)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

    def flush():
        if para:
            body.append('<p>' + fmt(''.join(para)) + '</p>')
            para.clear()

    for raw in reading_md.split('\n'):
        line = raw.strip()
        if not line or line == '---':
            flush()
            continue
        heading = re.sub(r'^#+\s*', '', line)
        if CHAPTER.match(heading) or (re.match(r'^#+\s', line) and len(heading) <= 24):
            flush()
            body.append(f'<h2>{fmt(heading)}</h2>')
            continue
        if re.match(r'^[-*・]\s?', line):
            flush()
            body.append('<p class="recipe">・' + fmt(re.sub(r'^[-*・]\s?', '', line)) + '</p>')
            continue
        para.append(line)
    flush()
    return ''.join(body)


def build_pdf(person, reading_md, data, out_path):
    natal = data['natal']
    prog = data['prog']
    trans = data['trans']
    sr = data['sr']
    current_date = data['current_date']

    prof = hr.profection(sr['age'], natal['houses']['cusps'])
    natal_svg = hr.wheel_svg(natal)
    extras = {'transit': data['transit_chart']['planets'],
              'progressed': [{'label': 'P☉︎', 'pd': prog['p_sun']},
                             {'label': 'P☽︎', 'pd': prog['p_moon']}]}
    tri_svg = hr.wheel_svg(natal, extras)
    tables = hr.tables_html(natal, prog, trans, sr, prof, current_date)

    sun = natal['planets']['Sun']
    moon = natal['planets']['Moon']
    asc = natal['houses']['ascendant']
    meta = (f"{person['y']}年{person['mo']}月{person['d']}日 "
            f"{person['h']}時{person['mi']:02d}分{'頃' if person.get('time_estimated') else ''} "
            f"{person['place']}生まれ ／ 鑑定日 {current_date}")

    doc = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<title>{html_mod.escape(person['name'])} 様 鑑定書</title><style>{CSS}</style></head><body>
<div class="cover"><div class="label">NARRATIVE ASTROLOGY READING</div>
<h1>{html_mod.escape(person['name'])} 様</h1><div class="meta">{html_mod.escape(meta)}</div>
<div class="author">星とハーブの研究家　織田 剛</div></div>
<div style="page-break-after:always;text-align:center;">
<h2 style="border-bottom:none;margin:0 0 4mm;">あなたの星の地図</h2>
{_svg_img(natal_svg, max_width_mm=135)}
<p style="font-size:9.5pt;color:#6b675e;text-align:center;margin-top:2mm;line-height:1.9;">
太陽（☉）は{sun['signJP']}{hr.fmt_deg(sun['degree'])}・第{sun['house']}ハウスに、
月（☽）は{moon['signJP']}{hr.fmt_deg(moon['degree'])}・第{moon['house']}ハウスに。<br/>
あなたの入口（ASC）は{asc['signJP']}{hr.fmt_deg(asc['degree'])}。この一枚が、本書で読み解く設計図です。</p></div>
{_body_html(reading_md)}
<div style="page-break-before:always;">
<h2 style="border-bottom:none;text-align:center;">巻末資料｜三重円と鑑定データ</h2>
<p style="font-size:9pt;color:#6b675e;text-align:center;">※星を読まれる方のための技術資料です。本文の鑑定はこのデータに基づいています。</p>
<div style="text-align:center;">{_svg_img(tri_svg, max_width_mm=128)}</div>
{tables}</div>
</body></html>"""

    from weasyprint import HTML
    HTML(string=doc, base_url=_BASE).write_pdf(out_path)
    return out_path
