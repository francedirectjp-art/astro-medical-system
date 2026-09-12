# -*- coding: utf-8 -*-
"""鑑定書md → 印刷用HTML → Chrome headless でPDF化"""
import html
import os
import re
import subprocess
import sys

CHAPTER = re.compile(r'^(序章|第[0-9１-９十]+章|終章)[｜|]')

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
@page { margin: 22mm 18mm; }
"""


def md_to_html(md_path, title, meta, out_html, cover=True):
    body = []
    para = []

    def fmt(s):
        s = html.escape(s)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

    def flush():
        if para:
            body.append('<p>' + fmt(''.join(para)) + '</p>')
            para.clear()

    for raw in open(md_path, encoding='utf-8'):
        line = raw.strip()
        if not line or line == '---':
            flush()
            continue
        heading = re.sub(r'^#+\s*', '', line)
        # 完全版の章題(序章/第N章/終章)と、簡易版の「本質｜」「あなたの問いへ」等の#見出し
        if CHAPTER.match(heading) or (re.match(r'^#+\s', line) and len(heading) <= 24):
            flush()
            body.append(f'<h2>{fmt(heading)}</h2>')
            continue
        if re.match(r'^#+\s', line):
            flush()
            body.append(f'<h3>{fmt(heading)}</h3>')
            continue
        if re.match(r'^[-*・]\s?', line):
            flush()
            body.append('<p class="recipe">・' + fmt(re.sub(r'^[-*・]\s?', '', line)) + '</p>')
            continue
        para.append(line)
    flush()

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
