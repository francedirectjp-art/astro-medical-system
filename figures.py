# -*- coding: utf-8 -*-
"""鑑定書の図版テンプレート (第8版)
チャートテキストを読み、章扉に差し込むSVGを返す。データ差し込みのみで、
図の構造そのものは全冊共通のテンプレート。
"""
import re

INK, GOLD, LINE, PALE, BG = '#2b2a26', '#b49a6c', '#c9bb9a', '#efe9dd', '#faf8f4'
BROWN = '#7a5c2e'
V = '︎'  # 異体字セレクタ(グリフの絵文字化を防ぐ)
GLYPH = {'太陽': '☉', '月': '☽', '水星': '☿', '金星': '♀', '火星': '♂', '木星': '♃',
         '土星': '♄', '天王星': '♅', '海王星': '♆', '冥王星': '♇',
         'ドラゴンヘッド': '☊', 'キローン': '⚷'}
# 指の割り当て(全冊固定のテンプレート)
LEFT = [('月', '王妃'), ('金星', '担当官'), ('木星', '大臣'), ('海王星', '来訪者'), ('冥王星', '恵みの主')]
RIGHT = [('太陽', '王'), ('水星', '使者'), ('火星', '将軍'), ('土星', '長老'), ('天王星', '革命家')]
LIT = {2: {'太陽', '月'},
       5: {'太陽', '月', '水星', '火星', '土星'},
       8: {'太陽', '月', '水星', '火星', '土星', '金星', '木星', '海王星'},
       10: {p for p, _ in LEFT + RIGHT}}
ROOMS = {1: '城門', 2: '蔵', 3: '使いの道', 4: '魂の根', 5: '喜びの庭', 6: '作業場',
         7: '対面の広間', 8: '継承の地下', 9: '遠見の塔', 10: '天職の塔',
         11: '仲間の広間', 12: '奥の静室'}
CELL = {1: (0, 2), 2: (0, 3), 3: (1, 3), 4: (2, 3), 5: (3, 3), 6: (3, 2),
        7: (3, 1), 8: (3, 0), 9: (2, 0), 10: (1, 0), 11: (0, 0), 12: (0, 1)}


def parse_chart(path):
    t = open(path, encoding='utf-8').read()
    d = {'planets': {}, 'houses': {}, 'pmoon': [], 'ingress': []}
    # 天体配置はネイタル節に限定する(SR図・プログレスに同形式の行があり上書きされるため)
    natal = t.split('### 天体の配置')[-1].split('### アングル')[0]
    for m in re.finditer(r'^- (\S+?): (\S+?座) (\d+)°(\d+)′.*?\[第(\d+)ハウス\]', natal, re.M):
        d['planets'][m.group(1)] = {'sign': m.group(2), 'deg': int(m.group(3)),
                                    'min': int(m.group(4)), 'house': int(m.group(5))}
    for name, p in d['planets'].items():
        d['houses'].setdefault(p['house'], []).append(name)
    ang = t.split('### アングル')[-1].split('###')[0]
    for key, pat in [('asc', r'ASC（アセンダント）: (\S+座) (\d+)°'), ('mc', r'MC（天頂）: (\S+座) (\d+)°')]:
        m = re.search(pat, ang)
        if m:
            d[key] = f'{m.group(1)}{m.group(2)}度'
    m = re.search(r'重み付き合計[^:：]*[:：]\s*火=(\d+)、土=(\d+)、風=(\d+)、水=(\d+)', t)
    d['elem'] = dict(zip('火土風水', map(int, m.groups()))) if m else {}
    m = re.search(r'3区分[^:：]*[:：]\s*活動=(\d+)、不動=(\d+)、柔軟=(\d+)', t)
    d['modes'] = dict(zip(['活動', '不動', '柔軟'], map(int, m.groups()))) if m else {}
    for m in re.finditer(r'^- (\d{4})年7月時点: (\S+?座)\((.)=(.)\) 第(\d+)ハウス\(現実=(.)\)', t, re.M):
        d['pmoon'].append({'y': int(m.group(1)), 'sign': m.group(2), 'heart': m.group(4),
                           'house': int(m.group(5)), 'real': m.group(6)})
    for m in re.finditer(r'^- (\d{4})-(\d{2})-\d{2}: (\S+?座)入り', t, re.M):
        d['ingress'].append({'y': int(m.group(1)), 'mo': int(m.group(2)), 'sign': m.group(3)})
    # プロフェクションの確定値は専用セクションからのみ拾う(年表行と取り違えない)
    pf = t.split('## プロフェクション（計算済み')[-1]
    for key, pat in [('pf_house', r'起動ハウス: 第(\d+)ハウス'),
                     ('pf_ruler', r'年主星[^:：]*[:：]\s*(\S+?)\s*$'),
                     ('pf_sign', r'起動サイン: (\S+座)'), ('age', r'現在の年齢: (\d+)歳')]:
        m = re.search(pat, pf, re.M)
        if m:
            d[key] = m.group(1)
    sab = t.split('## サビアンシンボル')[-1].split('\n## ')[0]
    d['sabian_deg'] = {m.group(1): f'{m.group(2)}{m.group(3)}度'
                       for m in re.finditer(r'^- (\S+?): (\S+?座)(\d+)度 "', sab, re.M)}
    return d


def _cap(s):
    return f'<text x="0" y="0" font-size="8.5" fill="{BROWN}" letter-spacing="1.5">{s}</text>'


def fig_hands(lit_n, labels=False, w=520):
    """十本の指。lit_n 本が金で灯る。labels=True で役職名を添える(巻末用)"""
    lit = LIT[lit_n]
    h = 250 if labels else 190
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">']
    for hi, (hand, label) in enumerate([(LEFT, '左手　王妃と愛の手'), (RIGHT, '右手　王と仕事の手')]):
        bx = 60 + hi * 260
        # 手のひら(弧)
        o.append(f'<path d="M{bx-6} 150 Q {bx+90} 182 {bx+186} 150" fill="none" '
                 f'stroke="{LINE}" stroke-width="1.4"/>')
        for i, (planet, role) in enumerate(hand):
            x = bx + i * 45
            # 親指は短く、中指が最長になるよう指の高さを変える
            top = [86, 60, 48, 58, 82][i]
            on = planet in lit
            o.append(f'<line x1="{x}" y1="150" x2="{x}" y2="{top+13}" stroke="{LINE}" stroke-width="1.2"/>')
            o.append(f'<circle cx="{x}" cy="{top}" r="13" fill="{GOLD if on else "#fff"}" '
                     f'stroke="{GOLD if on else LINE}" stroke-width="1.4"/>')
            o.append(f'<text x="{x}" y="{top+5}" text-anchor="middle" font-size="14" '
                     f'fill="{"#fff" if on else LINE}">{GLYPH[planet]}{V}</text>')
            if labels:
                o.append(f'<text x="{x}" y="{top+34}" text-anchor="middle" font-size="8" fill="{INK}">{role}</text>')
                o.append(f'<text x="{x}" y="{top+46}" text-anchor="middle" font-size="7.5" fill="{BROWN}">{planet}</text>')
        o.append(f'<text x="{bx+90}" y="176" text-anchor="middle" font-size="8" '
                 f'fill="{BROWN}" letter-spacing="1.2">{label}</text>')
    o.append(f'<text x="{w/2}" y="26" text-anchor="middle" font-size="11" fill="{BROWN}" '
             f'letter-spacing="3">{lit_n} / 10</text></svg>')
    return ''.join(o)


def fig_elements(elem, modes):
    """四大元素の炉。器の満ち方で体質の偏りを見せる"""
    order = [('火', '着火する力'), ('土', '形にする力'), ('風', 'つなぐ力'), ('水', '感じる力')]
    mx = max(elem.values()) or 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 250">']
    for i, (e, sub) in enumerate(order):
        x, v = 55 + i * 115, elem.get(e, 0)
        fh = int(120 * v / mx)
        o.append(f'<path d="M{x} 40 L{x} 160 Q{x} 172 {x+14} 172 L{x+56} 172 Q{x+70} 172 {x+70} 160 L{x+70} 40" '
                 f'fill="none" stroke="{LINE}" stroke-width="1.4"/>')
        o.append(f'<rect x="{x+2}" y="{160-fh}" width="66" height="{fh+10}" fill="{GOLD}" opacity="0.5"/>')
        o.append(f'<text x="{x+35}" y="{152-fh}" text-anchor="middle" font-size="15" fill="{BROWN}">{v}</text>')
        o.append(f'<text x="{x+35}" y="192" text-anchor="middle" font-size="14" fill="{INK}">{e}</text>')
        o.append(f'<text x="{x+35}" y="207" text-anchor="middle" font-size="8" fill="{BROWN}">{sub}</text>')
    tot = sum(modes.values()) or 1
    cx = 55
    o.append(f'<text x="55" y="232" font-size="8" fill="{BROWN}">三区分</text>')
    for k, v in modes.items():
        wv = int(390 * v / tot)
        o.append(f'<rect x="{cx+45}" y="224" width="{wv}" height="9" fill="{BROWN}" opacity="0.{3+list(modes).index(k)*2}"/>')
        o.append(f'<text x="{cx+45+wv/2}" y="232" text-anchor="middle" font-size="7.5" fill="#fff">{k}{v}</text>')
        cx += wv
    o.append('</svg>')
    return ''.join(o)


def fig_castle(houses, asc='', mc=''):
    """王国の間取り図。円が読めない人でも自分の配置が分かる平面図"""
    S, P = 118, 8
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S*4+P*2} {S*4+P*2}">']
    o.append(f'<rect x="{P}" y="{P}" width="{S*4}" height="{S*4}" fill="{BG}" stroke="{LINE}"/>')
    for hno, (c, r) in CELL.items():
        x, y = P + c * S, P + r * S
        o.append(f'<rect x="{x}" y="{y}" width="{S}" height="{S}" fill="#fff" stroke="{LINE}" stroke-width="0.9"/>')
        o.append(f'<text x="{x+7}" y="{y+15}" font-size="9" fill="{LINE}">{hno}</text>')
        o.append(f'<text x="{x+S/2}" y="{y+30}" text-anchor="middle" font-size="10.5" fill="{BROWN}">{ROOMS[hno]}</text>')
        ps = houses.get(hno, [])
        for j, p in enumerate(ps[:4]):
            gy = y + 56 + j * 17
            o.append(f'<text x="{x+S/2}" y="{gy}" text-anchor="middle" font-size="13" fill="{INK}">'
                     f'{GLYPH.get(p, "")}{V} <tspan font-size="8" fill="{BROWN}">{p}</tspan></text>')
    cx, cy = P + S, P + S
    o.append(f'<rect x="{cx}" y="{cy}" width="{S*2}" height="{S*2}" fill="{PALE}" stroke="{LINE}"/>')
    o.append(f'<text x="{cx+S}" y="{cy+S-16}" text-anchor="middle" font-size="11" fill="{BROWN}" letter-spacing="3">あなたの王国</text>')
    o.append(f'<text x="{cx+S}" y="{cy+S+8}" text-anchor="middle" font-size="9" fill="{INK}">城門　{asc}</text>')
    o.append(f'<text x="{cx+S}" y="{cy+S+24}" text-anchor="middle" font-size="9" fill="{INK}">天職の塔　{mc}</text>')
    o.append('</svg>')
    return ''.join(o)


def fig_sun_moon(d):
    """太陽と月の二極図。記入欄を図の中に持つ"""
    s, m = d['planets']['太陽'], d['planets']['月']
    sb = d.get('sabian_deg', {})
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 300">']
    for i, (name, p, cap) in enumerate([('太陽', s, '育てていきたい方向'), ('月', m, '心が安心する条件')]):
        cx = 140 + i * 240
        o.append(f'<circle cx="{cx}" cy="62" r="40" fill="{"#fff" if i else GOLD}" fill-opacity="{0.25 if not i else 1}" stroke="{GOLD if not i else LINE}" stroke-width="1.5"/>')
        o.append(f'<text x="{cx}" y="70" text-anchor="middle" font-size="30" fill="{BROWN}">{GLYPH[name]}{V}</text>')
        o.append(f'<text x="{cx}" y="122" text-anchor="middle" font-size="11" fill="{INK}">{name}　{p["sign"]}{p["deg"]}度　第{p["house"]}ハウス</text>')
        o.append(f'<text x="{cx}" y="138" text-anchor="middle" font-size="8.5" fill="{BROWN}">{cap}</text>')
        t = sb.get(name, '')
        if t:
            o.append(f'<text x="{cx}" y="154" text-anchor="middle" font-size="8.5" fill="{LINE}">天の情景　{t}</text>')
        lab = '実現したかったこと' if not i else '失いたくなかったもの'
        o.append(f'<text x="{cx-95}" y="196" font-size="8.5" fill="{BROWN}">{lab}</text>')
        for r in range(2):
            o.append(f'<line x1="{cx-95}" y1="{218+r*30}" x2="{cx+95}" y2="{218+r*30}" stroke="{LINE}" stroke-width="0.9"/>')
    o.append(f'<text x="260" y="62" text-anchor="middle" font-size="20" fill="{LINE}">⇄</text>')
    o.append(f'<text x="260" y="288" text-anchor="middle" font-size="8.5" fill="{BROWN}">'
             f'この二つは、同じ方向を向いていますか。別々を向いていますか。</text></svg>')
    return ''.join(o)


def fig_timeline(d):
    """時間の三層。心の季節・現実の季節・今年の部屋・時代の波を一枚に"""
    hist = d['pmoon']
    if not hist:
        return ''
    y0, y1 = hist[0]['y'], max(hist[-1]['y'] + 3, max([g['y'] for g in d['ingress']] or [0]) + 1)
    W, L, R = 560, 78, 506
    def X(y): return L + (R - L) * (y - y0) / (y1 - y0)
    col = {'春': '#d9c28a', '夏': '#c99a5c', '秋': '#a8a07e', '冬': '#9fb0bd'}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 228">']
    for row, key, lab in [(0, 'heart', '心の季節'), (1, 'real', '現実の季節')]:
        yy = 30 + row * 40
        o.append(f'<text x="0" y="{yy+16}" font-size="8.5" fill="{BROWN}">{lab}</text>')
        for i, g in enumerate(hist):
            x2 = X(hist[i+1]['y']) if i + 1 < len(hist) else X(hist[-1]['y'] + 1)
            o.append(f'<rect x="{X(g["y"]):.1f}" y="{yy}" width="{x2-X(g["y"]):.1f}" height="24" '
                     f'fill="{col[g[key]]}" opacity="0.75"/>')
            if i == 0 or g[key] != hist[i-1][key]:
                o.append(f'<text x="{X(g["y"])+4:.1f}" y="{yy+16}" font-size="9" fill="#fff">{g[key]}</text>')
    yy = 110
    o.append(f'<text x="0" y="{yy+14}" font-size="8.5" fill="{BROWN}">今年の部屋</text>')
    now = hist[-1]['y']
    o.append(f'<rect x="{X(now):.1f}" y="{yy}" width="{X(now+1)-X(now):.1f}" height="22" fill="{BROWN}" opacity="0.85"/>')
    o.append(f'<text x="{X(now)+2:.1f}" y="{yy-5}" font-size="8.5" fill="{BROWN}">'
             f'第{d.get("pf_house","")}ハウス（{d.get("pf_sign","")}）・{d.get("pf_ruler","")}が鍵を預かる年</text>')
    yy = 150
    o.append(f'<text x="0" y="{yy+4}" font-size="8.5" fill="{BROWN}">時代の波</text>')
    o.append(f'<line x1="{L}" y1="{yy}" x2="{R}" y2="{yy}" stroke="{LINE}"/>')
    for i, g in enumerate(sorted(d['ingress'], key=lambda g: (g['y'], g['mo']))):
        x = X(g['y'] + (g['mo'] - 1) / 12)
        dy = 15 + (i % 3) * 12                  # 三段にずらして重なりを防ぐ
        o.append(f'<circle cx="{x:.1f}" cy="{yy}" r="4" fill="{GOLD}"/>')
        o.append(f'<line x1="{x:.1f}" y1="{yy+3}" x2="{x:.1f}" y2="{yy+dy-7:.1f}" stroke="{GOLD}" stroke-width="0.7"/>')
        o.append(f'<text x="{x:.1f}" y="{yy+dy}" text-anchor="middle" font-size="7.5" fill="{BROWN}">'
                 f'{g["y"]}.{g["mo"]}　{g["sign"]}</text>')
    for y in range(y0, y1 + 1, 2):
        o.append(f'<text x="{X(y):.1f}" y="212" text-anchor="middle" font-size="8" fill="{LINE}">{y}</text>')
    o.append(f'<line x1="{X(now):.1f}" y1="24" x2="{X(now):.1f}" y2="200" stroke="{BROWN}" stroke-width="1" stroke-dasharray="3 3"/>')
    o.append(f'<text x="{X(now):.1f}" y="20" text-anchor="middle" font-size="8" fill="{BROWN}">いま</text></svg>')
    return ''.join(o)
