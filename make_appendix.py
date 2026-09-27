#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巻末資料(三重円+鑑定データ表)のHTMLを作る。
  usage: make_appendix.py <person.json> <chart.txt> <out.html>
内円=ネイタル / 中円(緑)=プログレス / 外円(青)=鑑定日のトランジット
"""
import json, math, os, re, sys, time, urllib.request

BASE = 'http://localhost:5000'
SIGNS = ['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座','天秤座','蠍座','射手座','山羊座','水瓶座','魚座']
SG = [g + '︎' for g in ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']]
PG = {'太陽':'☉','月':'☽','水星':'☿','金星':'♀','火星':'♂','木星':'♃','土星':'♄',
      '天王星':'♅','海王星':'♆','冥王星':'♇','ドラゴンヘッド':'☊','キローン':'⚷'}
PG = {k: v + '︎' for k, v in PG.items()}
EN2JP = {'Sun':'太陽','Moon':'月','Mercury':'水星','Venus':'金星','Mars':'火星','Jupiter':'木星',
         'Saturn':'土星','Uranus':'天王星','Neptune':'海王星','Pluto':'冥王星',
         'TrueNode':'ドラゴンヘッド','Chiron':'キローン'}
INK, ACC, LINE, GREEN, BLUE = '#2b2a26', '#7a5c2e', '#cbc2ae', '#2e7d4f', '#2f6fa8'
CX, CY = 430, 410
R_SO, R_SI = 396, 352          # サイン帯(いちばん外)
R_TRN = 320                    # 外円=トランジット
R_PRG = 262                    # 中円=プログレス
R_NAT = 202                    # 内円=ネイタル
R_RING = (352, 292, 232, 172)  # 帯を仕切る円
R_HNUM = 150


def api(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def lon_of(sign, deg, mi):
    return SIGNS.index(sign) * 30 + deg + mi / 60.0


def parse(path):
    t = open(path, encoding='utf-8').read()
    d = {'natal': {}, 'cusps': [], 'prog': {}, 'sr': {}}
    natal = t.split('### 天体の配置')[-1].split('### アングル')[0]
    for m in re.finditer(r'^- (\S+?): (\S+?座) (\d+)°(\d+)′(.*?)\[第(\d+)ハウス\]', natal, re.M):
        d['natal'][m.group(1)] = {'lon': lon_of(m.group(2), int(m.group(3)), int(m.group(4))),
                                  'sign': m.group(2), 'deg': int(m.group(3)), 'min': int(m.group(4)),
                                  'r': '℞' in m.group(5), 'house': int(m.group(6))}
    ang = t.split('### アングル')[-1].split('###')[0]
    for k, pat in [('asc', r'ASC（アセンダント）: (\S+座) (\d+)°(\d+)′'), ('mc', r'MC（天頂）: (\S+座) (\d+)°(\d+)′')]:
        m = re.search(pat, ang)
        if m:
            d[k] = lon_of(m.group(1), int(m.group(2)), int(m.group(3)))
            d[k + '_txt'] = f'{m.group(1)} {m.group(2)}°{m.group(3)}′'
    cus = t.split('### ハウスカスプ')[-1].split('\n##')[0]
    for m in re.finditer(r'^- 第(\d+)ハウス: (\S+?座) (\d+)°(\d+)′', cus, re.M):
        d['cusps'].append((int(m.group(1)), lon_of(m.group(2), int(m.group(3)), int(m.group(4)))))
    d['cusps'].sort()
    pr = t.split('## プログレス')[-1].split('\n##')[0]
    for m in re.finditer(r'^- プログレス(太陽|月): (\S+?座) (\d+)°(\d+)′.*?\[ネイタル第(\d+)ハウス\]', pr, re.M):
        d['prog'][m.group(1)] = {'lon': lon_of(m.group(2), int(m.group(3)), int(m.group(4))),
                                 'txt': f'{m.group(2)} {m.group(3)}°{m.group(4)}′', 'house': m.group(5)}
    srb = t.split('## ソーラーリターン図')[-1].split('\n##')[0]
    for k, pat in [('period', r'有効期間: (\S+)'), ('asc', r'SR-ASC: (\S+座 \d+°\d+′)'),
                   ('mc', r'SR-MC: (\S+座 \d+°\d+′)'), ('sun_h', r'SR太陽の部屋: (\S+)'),
                   ('moon', r'SR月: (\S+座 \d+°\d+′.*?)$')]:
        m = re.search(pat, srb, re.M)
        if m:
            d['sr'][k] = m.group(1)
    for k, pat in [('pf_house', r'起動ハウス: 第(\d+)ハウス'), ('pf_sign', r'起動サイン: (\S+座)'),
                   ('pf_ruler', r'年主星[^:：]*[:：]\s*(\S+?)\s*$'), ('pf_prev', r'前回起動した年齢: (\d+)歳')]:
        m = re.search(pat, t.split('## プロフェクション（計算済み')[-1], re.M)
        if m:
            d[k] = m.group(1)
    m = re.search(r'現在の年齢: (\d+)歳', t)
    d['age'] = m.group(1) if m else ''
    dg = t.split('## エッセンシャルディグニティ')[-1].split('\n## ')[0]
    d['dignity'] = [(m.group(1), f'{m.group(2)} 第{m.group(3)}ハウス', m.group(4), m.group(5))
                    for m in re.finditer(r'^- (\S+?): (\S+?座) 第(\d+)ハウス\s+(\S+?)\s+([+-]\d+)$', dg, re.M)]
    m = re.search(r'★城主（ディグニティコード）: (\S+?)（(.+?)）', dg)
    d['lord'] = (m.group(1), m.group(2)) if m else None
    return d


def deg_txt(lon):
    s = int(lon // 30) % 12
    v = lon - s * 30
    return f'{SIGNS[s]} {int(v)}°{int(round((v - int(v)) * 60)):02d}′'


def wheel(d, trans):
    asc = d['asc']
    def pt(lon, r):
        th = math.radians(180.0 + (lon - asc))
        return CX + r * math.cos(th), CY - r * math.sin(th)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CX*2} {CY*2+30}">']
    for r in (R_SO,) + R_RING:
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    for i in range(12):
        a = i * 30
        for r0, r1 in ((R_SI, R_SO),):
            x0, y0 = pt(a, r0); x1, y1 = pt(a, r1)
            o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{LINE}"/>')
        gx, gy = pt(a + 15, (R_SI + R_SO) / 2)
        o.append(f'<text x="{gx:.1f}" y="{gy+6:.1f}" text-anchor="middle" font-size="19" fill="{ACC}">{SG[i]}</text>')
    for hno, c in d['cusps']:
        x0, y0 = pt(c, R_HNUM - 18); x1, y1 = pt(c, R_SI)
        w = 1.7 if hno in (1, 4, 7, 10) else 0.7
        o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{ACC if w>1 else LINE}" stroke-width="{w}"/>')
        nxt = d['cusps'][hno % 12][1]
        mid = c + ((nxt - c) % 360) / 2
        hx, hy = pt(mid, R_HNUM)
        o.append(f'<text x="{hx:.1f}" y="{hy+4:.1f}" text-anchor="middle" font-size="11" fill="{LINE}">{hno}</text>')
    for lab, lon, col in (('ASC', d['asc'], ACC), ('MC', d['mc'], ACC)):
        x, y = pt(lon, R_SO + 14)
        o.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="11" fill="{col}" font-weight="600">{lab}</text>')

    def place(items, r, col, size):
        used = []
        for name, lon in sorted(items, key=lambda x: x[1]):
            a = lon
            while any(abs(((a - u) + 180) % 360 - 180) < 7 for u in used):
                a += 7
            used.append(a)
            x, y = pt(a, r)
            o.append(f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle" font-size="{size}" fill="{col}">{PG.get(name,"")}</text>')
            tx, ty = pt(a, r - 16)
            o.append(f'<text x="{tx:.1f}" y="{ty+3:.1f}" text-anchor="middle" font-size="6.5" fill="{col}" opacity="0.75">{int(lon%30)}</text>')

    place([(n, v['lon']) for n, v in d['natal'].items()], R_NAT, INK, 16)
    place([('太陽', d['prog']['太陽']['lon']), ('月', d['prog']['月']['lon'])], R_PRG, GREEN, 16)
    place(trans, R_TRN, BLUE, 14)
    o.append(f'<text x="{CX}" y="{CY*2+16}" text-anchor="middle" font-size="9.5" fill="{INK}">'
             f'<tspan fill="{INK}">● 内円＝ネイタル</tspan>　'
             f'<tspan fill="{GREEN}">● 中円＝プログレス（進行の太陽と月）</tspan>　'
             f'<tspan fill="{BLUE}">● 外円＝トランジット（鑑定日の空）</tspan></text></svg>')
    return ''.join(o)


def tables(d, trans):
    def tb(title, rows):
        r = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
        return f'<div class="apbox"><div class="aptitle">{title}</div><table>{r}</table></div>'
    nat = [(f'{PG.get(n,"")} {n}', f'{v["sign"]} {v["deg"]}°{v["min"]:02d}′' + ('&#8478;' if v['r'] else ''),
            f'第{v["house"]}ハウス') for n, v in sorted(d['natal'].items(), key=lambda x: x[1]['lon'])]
    nat += [('ASC（アセンダント）', d.get('asc_txt', ''), '—'), ('MC（天頂）', d.get('mc_txt', ''), '—')]
    pf = [('現在の年齢', f'{d.get("age","")}歳', ''),
          ('起動ハウス', f'第{d.get("pf_house","")}ハウス（{d.get("pf_sign","")}）', ''),
          ('年主星（鍵を預かる星）', d.get('pf_ruler', ''), ''),
          ('同じ部屋の前回起動', f'{d.get("pf_prev","")}歳', '')]
    pr = [('進行の太陽', d['prog']['太陽']['txt'], f'ネイタル第{d["prog"]["太陽"]["house"]}ハウス'),
          ('進行の月', d['prog']['月']['txt'], f'ネイタル第{d["prog"]["月"]["house"]}ハウス')]
    tr = [(f'{PG.get(n,"")} {n}', deg_txt(l), '') for n, l in trans]
    sr = [(k, v, '') for k, v in [('有効期間', d['sr'].get('period', '')), ('SR-ASC', d['sr'].get('asc', '')),
                                  ('SR-MC', d['sr'].get('mc', '')), ('SR太陽の部屋', d['sr'].get('sun_h', '')),
                                  ('SR月', d['sr'].get('moon', ''))] if v]
    dg = [(f'{PG.get(n,"")} {n}', pos, f'{mark}　{sc}') for n, pos, mark, sc in d.get('dignity', [])]
    if d.get('lord'):
        dg.append(('★城主（ディグニティコード）', d['lord'][0], d['lord'][1]))
    return (tb('ネイタル天体', nat)
            + (tb('エッセンシャルディグニティ（城主の判定根拠）', dg) if dg else '')
            + tb('プロフェクション（今年の部屋）', pf)
            + tb('プログレス（進行図）', pr) + tb('トランジット（鑑定日の空）', tr)
            + (tb('ソーラーリターン（今年の図）', sr) if sr else ''))


CSS = """<style>
.apwrap{page-break-before:always;}
.aphead{text-align:center;font-size:13.5pt;color:#7a5c2e;letter-spacing:.08em;margin:0 0 2mm;font-weight:600;}
.apnote{text-align:center;font-size:9pt;color:#8a8478;margin:0 0 6mm;}
.apsvg{max-width:150mm;margin:0 auto 6mm;}
.apbox{border:1px solid #ded5c4;border-radius:2mm;padding:3mm 4mm;margin:0 0 4mm;page-break-inside:avoid;}
.aptitle{font-size:10pt;color:#7a5c2e;letter-spacing:.06em;margin-bottom:1.5mm;font-weight:600;}
.apbox table{width:100%;border-collapse:collapse;font-size:9pt;}
.apbox td{padding:1.1mm 0;border-bottom:1px solid #f0ebe0;}
.apbox td:nth-child(2){text-align:right;padding-right:6mm;}
.apbox td:nth-child(3){width:26%;color:#6b675e;}
</style>"""


def main(pj, chart, out):
    p = json.load(open(pj, encoding='utf-8'))
    d = parse(chart)
    n = time.localtime()
    t = api('/api/calculate-chart', {'year': n.tm_year, 'month': n.tm_mon, 'day': n.tm_mday,
                                     'hour': 12, 'minute': 0,
                                     'latitude': p['lat'], 'longitude': p['lon']})
    pl = t.get('planets') or t.get('data', {}).get('planets') or {}
    trans = []
    for en, v in pl.items():
        jp = EN2JP.get(en)
        lon = v.get('longitude') if isinstance(v, dict) else None
        if jp and lon is not None:
            trans.append((jp, float(lon)))
    html = (CSS + '<div class="apwrap"><div class="aphead">巻末資料｜三重円と鑑定データ</div>'
            '<div class="apnote">※星を読まれる方のための技術資料です。本文の鑑定はこのデータに基づいています。</div>'
            f'<div class="apsvg">{wheel(d, trans)}</div>' + tables(d, trans) + '</div>')
    open(out, 'w', encoding='utf-8').write(html)
    print(f'appendix: {out}  (ネイタル{len(d["natal"])} / トランジット{len(trans)} / カスプ{len(d["cusps"])})')


if __name__ == '__main__':
    main(*sys.argv[1:4])
