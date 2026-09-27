# -*- coding: utf-8 -*-
"""円形ホロスコープ図SVG生成: 既存Swiss Ephemeris計算部を直接利用
usage: gen_horoscope_svg.py <year> <month> <day> <hour> <minute> <lat> <lon> <label> <out.svg>"""
import math
import sys

sys.path.insert(0, '/Users/oda/CCAGI/astro-medical-system')
for p in ('lib/python3.9/site-packages', 'lib/python3.13/site-packages'):
    sys.path.insert(0, f'/Users/oda/CCAGI/astro-medical-system/.venv/{p}')

from datetime import datetime, timedelta

import swisseph as swe

from swisseph_api import PLANETS, calculate_planet_position, calculate_houses, get_planet_house

year, month, day, hour, minute = map(int, sys.argv[1:6])
lat, lon = float(sys.argv[6]), float(sys.argv[7])
label, out_path = sys.argv[8], sys.argv[9]

# JST→UTC(本体APIと同じ処理)
utc = datetime(year, month, day, hour, minute) - timedelta(hours=9)
jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0)

planets = {name: calculate_planet_position(jd, pid) for name, pid in PLANETS.items()}
houses = calculate_houses(jd, lat, lon, 'P')
for name, pd in planets.items():
    if 'longitude' in pd:
        pd['house'] = get_planet_house(pd['longitude'], houses['cusps'])

asc = houses['ascendant']['longitude']
mc = houses['midheaven']['longitude']
cusps = houses['cusps']

SIGN_GLYPHS = [g + '\ufe0e' for g in ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']]
SIGN_COLORS = ['#c0392b', '#7d6608', '#2471a3', '#1e8449'] * 3  # 火土風水
PLANET_GLYPHS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
    'TrueNode': '☊', 'Chiron': '⚷',
}
PLANET_GLYPHS = {k: v + '\ufe0e' for k, v in PLANET_GLYPHS.items()}
PLANET_ORDER = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                'Uranus', 'Neptune', 'Pluto', 'TrueNode', 'Chiron']

CX = 460
CY = 420
R_SIGN_OUT, R_SIGN_IN = 400, 340
R_HOUSE_NUM = 165
R_PLANET = 265
R_TICK = 340
R_ASPECT = 195
INK, ACCENT, LINE = '#2b2a26', '#7a5c2e', '#cbc2ae'


def pt(deg_ecl, r):
    """黄経→SVG座標(ASCを左端9時方向に、反時計回り)"""
    th = math.radians(180.0 + (deg_ecl - asc))
    return CX + r * math.cos(th), CY - r * math.sin(th)


svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 920" '
           f'font-family="Hiragino Mincho ProN, Yu Mincho, serif">')
svg.append(f'<rect width="920" height="920" fill="#f7f4ee"/>')
svg.append(f'<text x="460" y="52" text-anchor="middle" font-size="26" fill="{ACCENT}" '
           f'letter-spacing="4">{label}</text>')
g = f'<g transform="translate(0,60)">'
svg.append(g)

# リング
for r in (R_SIGN_OUT, R_SIGN_IN, R_ASPECT):
    svg.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_SIGN_OUT}" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>')

# サイン境界と glyph
for i in range(12):
    x1, y1 = pt(i * 30, R_SIGN_IN)
    x2, y2 = pt(i * 30, R_SIGN_OUT)
    svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
               f'stroke="{ACCENT}" stroke-width="1.2"/>')
    gx, gy = pt(i * 30 + 15, (R_SIGN_OUT + R_SIGN_IN) / 2)
    svg.append(f'<text x="{gx:.1f}" y="{gy + 12:.1f}" text-anchor="middle" font-size="34" '
               f'fill="{SIGN_COLORS[i]}">{SIGN_GLYPHS[i]}</text>')
    # 5度刻みチック
    for d in range(0, 30, 5):
        t1, t2 = (R_SIGN_IN, R_SIGN_IN + (14 if d % 10 == 0 else 8))
        ax, ay = pt(i * 30 + d, t1)
        bx, by = pt(i * 30 + d, t2)
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                   f'stroke="{LINE}" stroke-width="1"/>')

# ハウスカスプ
for i, c in enumerate(cusps):
    bold = i in (0, 3, 6, 9)
    x1, y1 = pt(c, R_ASPECT)
    x2, y2 = pt(c, R_SIGN_IN)
    svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
               f'stroke="{ACCENT if bold else LINE}" stroke-width="{2.5 if bold else 1}"/>')
    nxt = cusps[(i + 1) % 12]
    span = (nxt - c) % 360
    hx, hy = pt(c + span / 2, R_HOUSE_NUM)
    svg.append(f'<text x="{hx:.1f}" y="{hy + 6:.1f}" text-anchor="middle" font-size="17" '
               f'fill="#9b9483">{i + 1}</text>')

# ASC/MC 矢印ラベル
for ang, name in ((asc, 'ASC'), (mc, 'MC')):
    lx, ly = pt(ang, R_SIGN_OUT + 22)
    svg.append(f'<text x="{lx:.1f}" y="{ly + 6:.1f}" text-anchor="middle" font-size="19" '
               f'font-weight="bold" fill="{ACCENT}">{name}</text>')

# 天体(近接時は半径をずらす)
placed = []  # (deg, r)
entries = []
for name in PLANET_ORDER:
    pd = planets[name]
    if 'longitude' not in pd:
        continue
    entries.append((pd['longitude'], name, pd))
entries.sort()
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
    gx, gy = pt(deg, r)
    tickx, ticky = pt(deg, R_SIGN_IN)
    inx, iny = pt(deg, R_SIGN_IN - 10)
    svg.append(f'<line x1="{tickx:.1f}" y1="{ticky:.1f}" x2="{inx:.1f}" y2="{iny:.1f}" '
               f'stroke="{INK}" stroke-width="2"/>')
    svg.append(f'<text x="{gx:.1f}" y="{gy + 11:.1f}" text-anchor="middle" font-size="30" '
               f'fill="{INK}">{PLANET_GLYPHS[name]}</text>')
    d_in_sign = int(pd['degree'])
    minutes = int(round((pd['degree'] - d_in_sign) * 60))
    rx, ry = pt(deg, r - 34)
    retro = 'R' if pd.get('retrograde') else ''
    svg.append(f'<text x="{rx:.1f}" y="{ry + 5:.1f}" text-anchor="middle" font-size="13" '
               f'fill="#6b675e">{d_in_sign}°{minutes:02d}{retro}</text>')

# アスペクト
ASPECTS = [(0, 7, '#b49a6c', '2'), (60, 5, '#1e8449', '1.4'), (90, 6, '#c0392b', '1.6'),
           (120, 6, '#2471a3', '1.6'), (180, 7, '#c0392b', '2')]
MAJOR = [e for e in entries if e[1] not in ('TrueNode', 'Chiron')]
for i in range(len(MAJOR)):
    for j in range(i + 1, len(MAJOR)):
        d1, d2 = MAJOR[i][0], MAJOR[j][0]
        diff = abs((d1 - d2 + 180) % 360 - 180)
        for ang, orb, color, w in ASPECTS:
            if ang == 0:
                continue  # 合は線を引かない
            if abs(diff - ang) <= orb:
                x1, y1 = pt(d1, R_ASPECT)
                x2, y2 = pt(d2, R_ASPECT)
                svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                           f'stroke="{color}" stroke-width="{w}" opacity="0.55"/>')
                break

svg.append('</g>')
svg.append('</svg>')
open(out_path, 'w', encoding='utf-8').write('\n'.join(svg))

# 検証出力
print(f"ASC {houses['ascendant']['signJP']} {houses['ascendant']['degree']:.2f} / "
      f"MC {houses['midheaven']['signJP']} {houses['midheaven']['degree']:.2f}")
for name in PLANET_ORDER:
    pd = planets[name]
    if 'longitude' in pd:
        print(f"{name}: {pd['signJP']} {pd['degree']:.2f} H{pd['house']}"
              f"{' R' if pd.get('retrograde') else ''}")
print('saved:', out_path)
