# -*- coding: utf-8 -*-
"""ホロスコープ図(SVG)とデータ表(HTML)のPython版レンダラー
reading/chart.js と同一のロジック・デザイン（自動鑑定書PDF用）。
"""
import math

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']
SIGN_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
SIGN_COLORS = ['#c0392b', '#7d6608', '#2471a3', '#1e8449'] * 3
GLYPHS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
    'TrueNode': '☊', 'Chiron': '⚷'}
ORDER = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
         'Uranus', 'Neptune', 'Pluto', 'TrueNode', 'Chiron']
NAMES_JP = {'Sun': '太陽', 'Moon': '月', 'Mercury': '水星', 'Venus': '金星',
            'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星', 'Uranus': '天王星',
            'Neptune': '海王星', 'Pluto': '冥王星', 'TrueNode': 'ドラゴンヘッド',
            'Chiron': 'キローン'}
RULERS_JP = ['火星', '金星', '水星', '月', '太陽', '水星',
             '金星', '火星', '木星', '土星', '土星', '木星']

CX = CY = 540
R_OUT, R_IN, R_PLANET, R_HOUSE, R_ASPECT = 400, 340, 265, 165, 195
R_TRANS, R_TRANS_OUT = 428, 466
INK, ACCENT, LINE = '#2b2a26', '#7a5c2e', '#cbc2ae'
C_TRANS, C_PROG = '#2471a3', '#1e8449'
FONT = "NSSym, Noto Serif JP, serif"


def fmt_deg(d):
    deg = math.floor(d)
    mi = round((d - deg) * 60)
    if mi == 60:
        deg += 1
        mi = 0
    return f'{deg}°{mi:02d}′'


def house_of(lon, cusps):
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        if (lon - a) % 360 < (b - a) % 360:
            return i + 1
    return 12


def profection(age, cusps):
    house = (age % 12) + 1
    si = int(cusps[house - 1] // 30)
    return {'age': age, 'house': house, 'signJP': SIGNS_JP[si],
            'lordJP': RULERS_JP[si], 'prevAge': age - 12}


def wheel_svg(natal, extras=None):
    asc = natal['houses']['ascendant']['longitude']
    mc = natal['houses']['midheaven']['longitude']
    cusps = natal['houses']['cusps']
    has_outer = bool(extras and (extras.get('transit') or extras.get('progressed')))
    view_h = 1148 if has_outer else 1080

    def pt(deg, r):
        th = math.radians(180.0 + (deg - asc))
        return CX + r * math.cos(th), CY - r * math.sin(th)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 {view_h}" '
         f'font-family="{FONT}">']
    for r in (R_OUT, R_IN, R_ASPECT):
        s.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
    s.append(f'<circle cx="{CX}" cy="{CY}" r="{R_OUT}" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>')
    if has_outer:
        s.append(f'<circle cx="{CX}" cy="{CY}" r="{R_TRANS_OUT}" fill="none" stroke="{LINE}" stroke-width="1.2"/>')

    for i in range(12):
        x1, y1 = pt(i * 30, R_IN)
        x2, y2 = pt(i * 30, R_OUT)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{ACCENT}" stroke-width="1.2"/>')
        gx, gy = pt(i * 30 + 15, (R_OUT + R_IN) / 2)
        s.append(f'<text x="{gx:.1f}" y="{gy + 12:.1f}" text-anchor="middle" font-size="34" '
                 f'fill="{SIGN_COLORS[i]}">{SIGN_GLYPHS[i]}</text>')
        for d in range(0, 30, 5):
            ax, ay = pt(i * 30 + d, R_IN)
            bx, by = pt(i * 30 + d, R_IN + (14 if d % 10 == 0 else 8))
            s.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                     f'stroke="{LINE}" stroke-width="1"/>')

    for i, c in enumerate(cusps):
        bold = i in (0, 3, 6, 9)
        x1, y1 = pt(c, R_ASPECT)
        x2, y2 = pt(c, R_IN)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{ACCENT if bold else LINE}" stroke-width="{2.5 if bold else 1}"/>')
        span = (cusps[(i + 1) % 12] - c) % 360
        hx, hy = pt(c + span / 2, R_HOUSE)
        s.append(f'<text x="{hx:.1f}" y="{hy + 6:.1f}" text-anchor="middle" font-size="17" '
                 f'fill="#9b9483">{i + 1}</text>')

    for ang, name in ((asc, 'ASC'), (mc, 'MC')):
        lx, ly = pt(ang, (R_TRANS_OUT if has_outer else R_OUT) + 24)
        s.append(f'<text x="{lx:.1f}" y="{ly + 6:.1f}" text-anchor="middle" font-size="19" '
                 f'font-weight="bold" fill="{ACCENT}">{name}</text>')

    entries = sorted(
        (natal['planets'][k]['longitude'], k, natal['planets'][k])
        for k in ORDER if 'longitude' in natal['planets'].get(k, {}))
    placed = []
    for deg, name, pd in entries:
        r = R_PLANET
        moved = True
        while moved:
            moved = False
            for pdeg, pr in placed:
                if abs((deg - pdeg + 180) % 360 - 180) < 8 and abs(r - pr) < 36:
                    r -= 42
                    moved = True
        placed.append((deg, r))
        tx, ty = pt(deg, R_IN)
        ix, iy = pt(deg, R_IN - 10)
        s.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{ix:.1f}" y2="{iy:.1f}" '
                 f'stroke="{INK}" stroke-width="2"/>')
        gx, gy = pt(deg, r)
        s.append(f'<text x="{gx:.1f}" y="{gy + 11:.1f}" text-anchor="middle" font-size="30" '
                 f'fill="{INK}">{GLYPHS[name]}</text>')
        rx, ry = pt(deg, r - 34)
        retro = 'R' if pd.get('retrograde') else ''
        di = math.floor(pd['degree'])
        mi = round((pd['degree'] - di) * 60)
        s.append(f'<text x="{rx:.1f}" y="{ry + 5:.1f}" text-anchor="middle" font-size="13" '
                 f'fill="#6b675e">{di}°{mi:02d}{retro}</text>')

    aspects = [(60, 5, '#1e8449', 1.4), (90, 6, '#c0392b', 1.6),
               (120, 6, '#2471a3', 1.6), (180, 7, '#c0392b', 2)]
    majors = [e for e in entries if e[1] not in ('TrueNode', 'Chiron')]
    for i in range(len(majors)):
        for j in range(i + 1, len(majors)):
            diff = abs((majors[i][0] - majors[j][0] + 180) % 360 - 180)
            for ang, orb, color, w in aspects:
                if abs(diff - ang) <= orb:
                    x1, y1 = pt(majors[i][0], R_ASPECT)
                    x2, y2 = pt(majors[j][0], R_ASPECT)
                    s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                             f'stroke="{color}" stroke-width="{w}" opacity="0.55"/>')
                    break

    if has_outer:
        outer = []
        transit = (extras or {}).get('transit') or {}
        for k in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                  'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'):
            p = transit.get(k)
            if p and 'longitude' in p:
                outer.append({'deg': p['longitude'], 'glyph': GLYPHS[k], 'pd': p,
                              'color': C_TRANS, 'small': False})
        for e in (extras or {}).get('progressed') or []:
            if e.get('pd') and 'longitude' in e['pd']:
                outer.append({'deg': e['pd']['longitude'], 'glyph': e['label'],
                              'pd': e['pd'], 'color': C_PROG, 'small': True})
        outer.sort(key=lambda o: o['deg'])
        placed_outer = []
        for o in outer:
            r = R_TRANS
            moved = True
            while moved:
                moved = False
                for pdeg, pr in placed_outer:
                    if abs((o['deg'] - pdeg + 180) % 360 - 180) < 6 and abs(r - pr) < 30:
                        r += 32
                        moved = True
            placed_outer.append((o['deg'], r))
            tx, ty = pt(o['deg'], R_OUT)
            ix, iy = pt(o['deg'], R_OUT + 9)
            s.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{ix:.1f}" y2="{iy:.1f}" '
                     f'stroke="{o["color"]}" stroke-width="2"/>')
            gx, gy = pt(o['deg'], r)
            fs = 17 if o['small'] else 22
            s.append(f'<text x="{gx:.1f}" y="{gy + 8:.1f}" text-anchor="middle" '
                     f'font-size="{fs}" fill="{o["color"]}">{o["glyph"]}</text>')
            rx, ry = pt(o['deg'], r + 22)
            retro = 'R' if o['pd'].get('retrograde') else ''
            s.append(f'<text x="{rx:.1f}" y="{ry + 4:.1f}" text-anchor="middle" font-size="11" '
                     f'fill="{o["color"]}" opacity="0.8">{math.floor(o["pd"]["degree"])}°{retro}</text>')
        s.append(f'<text x="{CX}" y="1112" text-anchor="middle" font-size="19" fill="#6b675e">'
                 f'<tspan fill="{INK}">● 内円=ネイタル</tspan>'
                 f'<tspan dx="26" fill="{C_TRANS}">● 外周=トランジット(現在)</tspan>'
                 f'<tspan dx="26" fill="{C_PROG}">● P=プログレス</tspan></text>')

    s.append('</svg>')
    return ''.join(s)


def tables_html(natal, prog, trans, sr, prof, current_date):
    h = ['<div class="data-grid">']
    h.append('<div class="data-card"><h4>ネイタル天体</h4><table>')
    for k in ORDER:
        p = natal['planets'].get(k)
        if not p or 'longitude' not in p:
            continue
        rx = ' ℞' if p.get('retrograde') else ''
        h.append(f'<tr><td>{GLYPHS[k]} {NAMES_JP[k]}</td>'
                 f'<td>{p["signJP"]} {fmt_deg(p["degree"])}{rx}</td>'
                 f'<td>第{p["house"]}ハウス</td></tr>')
    hs = natal['houses']
    h.append(f'<tr><td>ASC</td><td>{hs["ascendant"]["signJP"]} {fmt_deg(hs["ascendant"]["degree"])}</td><td>—</td></tr>')
    h.append(f'<tr><td>MC</td><td>{hs["midheaven"]["signJP"]} {fmt_deg(hs["midheaven"]["degree"])}</td><td>—</td></tr>')
    h.append('</table></div>')

    h.append('<div class="data-card"><h4>プロフェクション（今年の部屋）</h4><table>')
    h.append(f'<tr><td>現在の年齢</td><td>{prof["age"]}歳</td></tr>')
    h.append(f'<tr><td>起動ハウス</td><td>第{prof["house"]}ハウス（{prof["signJP"]}）</td></tr>')
    h.append(f'<tr><td>年主星（鍵を預かる星）</td><td><strong>{prof["lordJP"]}</strong></td></tr>')
    if prof['prevAge'] >= 0:
        h.append(f'<tr><td>同じ部屋が前回起動した年齢</td><td>{prof["prevAge"]}歳</td></tr>')
    h.append('</table></div>')

    if prog and prog.get('p_sun'):
        cusps = natal['houses']['cusps']
        ps_h = house_of(prog['p_sun']['longitude'], cusps)
        pm_h = house_of(prog['p_moon']['longitude'], cusps)
        h.append('<div class="data-card"><h4>プログレス（進行図）</h4><table>')
        h.append(f'<tr><td>進行の太陽</td><td>{prog["p_sun"]["signJP"]} {fmt_deg(prog["p_sun"]["degree"])}（ネイタル第{ps_h}ハウス）</td></tr>')
        h.append(f'<tr><td>進行の月</td><td>{prog["p_moon"]["signJP"]} {fmt_deg(prog["p_moon"]["degree"])}（ネイタル第{pm_h}ハウス）</td></tr>')
        h.append(f'<tr><td>基準日</td><td>{current_date}</td></tr>')
        h.append('</table></div>')

    if trans:
        h.append('<div class="data-card"><h4>トランジット</h4><table>')
        for k in ('Uranus', 'Neptune', 'Pluto'):
            p = (trans.get('outer_planets') or {}).get(k)
            if p:
                h.append(f'<tr><td>{GLYPHS[k]} {NAMES_JP[k]}（現在）</td>'
                         f'<td>{p["signJP"]} {fmt_deg(p["degree"])}{" ℞" if p.get("retrograde") else ""}</td></tr>')
        for t in trans.get('jupiter_transits') or []:
            h.append(f'<tr><td>♃︎ 木星イングレス</td><td>{t["date"]} {t["signJP"]}入り</td></tr>')
        for t in trans.get('saturn_transits') or []:
            h.append(f'<tr><td>♄︎ 土星イングレス</td><td>{t["date"]} {t["signJP"]}入り</td></tr>')
        h.append('</table></div>')

    if sr and sr.get('houses'):
        h.append('<div class="data-card"><h4>ソーラーリターン（今年の図）</h4><table>')
        h.append(f'<tr><td>有効期間</td><td>{sr["valid_from"]} 〜 {sr["valid_until"]}</td></tr>')
        h.append(f'<tr><td>SR-ASC</td><td>{sr["houses"]["ascendant"]["signJP"]} {fmt_deg(sr["houses"]["ascendant"]["degree"])}</td></tr>')
        h.append(f'<tr><td>SR-MC</td><td>{sr["houses"]["midheaven"]["signJP"]} {fmt_deg(sr["houses"]["midheaven"]["degree"])}</td></tr>')
        su = (sr.get('planets') or {}).get('Sun')
        if su and su.get('house'):
            h.append(f'<tr><td>SR太陽の部屋</td><td>第{su["house"]}ハウス</td></tr>')
        mo = (sr.get('planets') or {}).get('Moon')
        if mo:
            hh = f'（第{mo["house"]}ハウス）' if mo.get('house') else ''
            h.append(f'<tr><td>SR月</td><td>{mo["signJP"]} {fmt_deg(mo["degree"])}{hh}</td></tr>')
        h.append('</table></div>')

    h.append('</div>')
    return ''.join(h)
