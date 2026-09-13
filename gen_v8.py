# -*- coding: utf-8 -*-
"""第3版構成の完全版鑑定(約18,000字): ソーラーアーク計算+SR裏取り+2分割生成
usage: gen_v3.py  (対象はスクリプト内 PERSON)"""
import os
import re
import sys
import time
import json
import math
import urllib.request

with open('/Users/oda/.nexus/.env', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('ANTHROPIC_API_KEY='):
            os.environ['ANTHROPIC_API_KEY'] = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

for p in os.listdir('/Users/oda/CCAGI/astro-medical-system/.venv/lib'):
    sp = f'/Users/oda/CCAGI/astro-medical-system/.venv/lib/{p}/site-packages'
    if os.path.isdir(sp) and sp not in sys.path:
        sys.path.insert(0, sp)

from anthropic import Anthropic

BASE = 'http://localhost:5000'
DIR = '/private/tmp/claude-501/-Users-oda/cc5c59e7-fce2-43a3-a323-8dc218c6a19c/scratchpad'
GEM_PATH = os.environ.get('GEM_PATH', '/Users/oda/CCAGI/astro-medical-system/gem_narrative_astrologer_v8.md')
GEM = open(GEM_PATH, encoding='utf-8').read()
SABIAN = json.load(open('/Users/oda/CCAGI/astro-medical-system/reading/sabian360.json', encoding='utf-8'))
SIGN_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
           'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']


def sabian_of(sign_jp, degree):
    """サイン内度数→サビアン度数(0°00-0°59=1度)→原文"""
    si = SIGNS_JP.index(sign_jp)
    d = int(degree) + 1
    if d > 30:
        d = 30
    return d, SABIAN.get(f'{SIGN_EN[si]}_{d}', '')
MODEL = 'claude-sonnet-5'
CURRENT_DATE = time.strftime('%Y-%m-%d')

import json as _json
_pj = os.environ.get('PERSON_JSON')
if _pj:
    PERSON = _json.load(open(_pj, encoding='utf-8'))
else:
    PERSON = {'slug': 'tozawa', 'name': '戸澤麻理',
              'y': 1972, 'mo': 7, 'd': 13, 'h': 7, 'mi': 40,
              'lat': 36.0785, 'lon': 140.2044,
              'pref': '茨城県', 'place': '茨城県土浦市', 'gender': '',
              'consult': '', 'questions': {'future': '', 'challenge': '', 'today': ''}}

PARTS = int(__import__('os').environ.get('PARTS', '5'))

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']
RULERS_JP = ['火星', '金星', '水星', '月', '太陽', '水星',
             '金星', '火星', '木星', '土星', '土星', '木星']
PJP = {'Sun': '太陽', 'Moon': '月', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星',
       'Jupiter': '木星', 'Saturn': '土星', 'Uranus': '天王星', 'Neptune': '海王星',
       'Pluto': '冥王星', 'TrueNode': 'ドラゴンヘッド', 'Chiron': 'キローン'}

GUARD = ('章は必ず番号順に書き、順序の言い直しや（※〜）のような断り書き、メタ発言を本文に一切残さないでください。'
         '各章末には第5節5-0の三点セット（【星を読まれる方へ】／【思い当たることはありませんか？】／指の回収）を必ず付けてください。'
         '【星を読まれる方へ】は占星術の補足で、度数と技術的判断を書きます。第1章の初出のみ「ご存じない方は読み飛ばしてくださって構いません」と添えます。'
         '【星を読まれる方へ】も本文の一部です。術語は使わず翻訳語で書き、ソーラーアーク・ソーラーリターンには一切触れないでください。'
         '「ディスポジター連鎖を辿らないようにしました」のような制作上の都合や内規の説明も書かないでください。'
         '【思い当たることはありませんか？】は読者への問いかけで、日常の一場面を挙げて「思い当たることはありませんか」と尋ねます。'
         '三点セットは字数調整の対象外です。字数を詰めるときも必ず残してください。'
         '弱い推量（〜ではないでしょうか等）は一章一回まで。'
         '停止案内（「（『はい』または『続けて』…）」等）を本文に書かないでください。'
         '三点セットの見出しは、必ず【星を読まれる方へ】【思い当たることはありませんか？】と角括弧で書いてください。'
         '# や ## を付けた見出し行にしないでください（章題と誤認されます）。太字記号でも包まないでください。'
         'アスペクトの五語（合・オポジション・スクエア・トライン・セクスタイル）と'
         'ソーラーアーク・プロフェクション・トランジット・ディスポジター等の術語を本文に出さず、翻訳語だけで書いてください。'
         '★サビアンの情景は、天体・サイン・ハウスで「なぜそうなるか」を説明したあとに置いてください。'
         '説明より先に情景を出すと、占星術を知らない読者には固有名詞が唐突に現れたように見えます。'
         '厚く描く情景は一章にひとつだけ。第1章の初出時のみ、サビアンとは何かを一文で説明してください。'
         '★各章・各葉の冒頭には、必ず # を付けた章題行を独立した一行として置いてください。'
         '章題は第5節の章構成に書かれているとおりに一字一句写してください。'
         '第3節の呼び名だけを使ってください。旧版の語彙（王・王妃・城主・部屋・区画・大臣・将軍・長老）を記憶から書かないこと。'
         '旧版の章題を記憶から書かないこと。'
         '例: 「# はじめに」「# 序章｜私信のはじまり」「# 中庭｜心当たり」「# 終章｜扉」「# 次の扉」。'
         '章題は第5節の表記どおりに書き、本文と地続きにしないでください。章題行がないとPDFの章扉が作れません。'
         '指の回収の行頭に「第1章末」のような欄外ラベルを書かず、回収の一文だけを書いてください。')

# 便ごとの目標字数。実測とのズレは次便へ繰り越して自動補正する（5章前後・約5,000字ずつ）
BLOCKS = [
    {'name': '第1便 はじめに〜第2章', 'target': 5300,
     'body': 'まず第1便として、第5節5-1の「はじめに」（十段の型を順序どおり厳守）、序章、第1章、'
             '第2章までを、途中で止まらずに書いてください。「中庭｜心当たり」はここではまだ書きません。'
             '記入欄は全角カッコの空欄として実際に紙面に出してください。'
             '「はじめに」では質問も記入欄も出さず、他の占いへの言及もしないでください。'
             '十本の指は「はじめに」では触れず、序章で一段落だけ置いてください。'
             '第2章まで書いたら止まってください。'},
    {'name': '第2便 中庭〜第5章', 'target': 4400,
     'body': '続けて第2便です。「中庭｜太陽と月を、一緒に読む」、第3章、第4章、第5章を書いてください。'
             '第5章末で十本の指が揃う回収を必ず書いてください。第5章まで書いたら止まってください。'},
    {'name': '第3便 第6章〜第9章', 'target': 5200,
     'body': '続けて第3便です。第6章・第7章・「中庭｜心当たり」・第8章・第9章を、この順で書いてください。'
             '「中庭｜心当たり」は第7章と第8章のあいだに置きます。冒頭で「ここから先は未来の話に入る。'
             'これから読む未来は、いままで読んできた過去とまったく同じ方法で読むので、'
             '先に過去のほうが当たっているか確かめてほしい」と、なぜこれをするのかを必ず述べてください。'
             '検証できる素材を五つだけ出し、各項目に記入欄（全角カッコの空欄）を付けてください。'
             '第8章の冒頭では、この中庭を一度だけ振り返ってください。'
             '第7章は「だから、この条件では消耗し、この条件では力を使いやすくなる」まで書き切ること。'
             '第9章には周期の年数（十二年に一度／二十九年に一度）を必ず入れること。'
             '第9章まで書いたら止まってください。'},
    {'name': '第4便 第10章〜巻末', 'target': 4550, 'no_carry': True,
     'body': '続けて最終便です。第10章・（ご相談があれば「あなたの問いへ」）・第11章・終章・'
             '第5節5-2の「次の扉」「王国の宮廷」を書き切ってください。'
             '第11章は冒頭で配合の根拠を一度開示し、三つの処方が同一配合になっていないか必ず突き合わせること。'
             '終章に完了宣言（「もう繰り返される必要のない物語になりました」等）を書かないこと。'
             '「次の扉」は第5節5-2の型に厳密に従い、日付・URL・講座名・価格・期限を一切書かないこと。'},
]
TOTAL_CAP = 18000

P1_TAIL = ('以上のデータで鑑定書を執筆してください。今回は対話ではなく4回に分けた一括生成です。'
           '第2節のブロック停止ルールは適用しません。全体は18,000字を上限とし、各章の字数目安を厳守してください。')

CONT = '続けて。残りの章を終章まで書き切ってください。'


def api(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    if not data.get('success'):
        raise RuntimeError(f'{path}: {data.get("error")}')
    return data


def fdeg(d):
    deg = math.floor(d)
    mi = round((d - deg) * 60)
    if mi == 60:
        deg += 1
        mi = 0
    return f'{deg}°{mi:02d}′'


def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def house_of(lon, cusps):
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        if (lon - a) % 360 < (b - a) % 360:
            return i + 1
    return 12


def prog_moon_contacts(natal, prog):
    """進行の月が接触中のネイタル天体(合/オポ、オーブ2度)"""
    pm = prog['p_moon']['longitude']
    out = []
    for k, v in natal['planets'].items():
        if 'longitude' not in v or k not in PJP:
            continue
        d = angdiff(pm, v['longitude'])
        if d <= 2.0:
            out.append(f"ネイタル{PJP[k]}と合（オーブ{d:.1f}度）")
        elif abs(d - 180) <= 2.0:
            out.append(f"ネイタル{PJP[k]}とオポジション（オーブ{abs(d-180):.1f}度）")
    return out


ELEM_JP = ['火', '土', '風', '水']
MODE_JP = ['活動', '不動', '柔軟']


def element_balance(natal):
    """四大元素と3区分の分布(太陽・月・ASCは重み3、個人天体2、社会天体1、外惑星1)"""
    weights = {'Sun': 3, 'Moon': 3, 'Mercury': 2, 'Venus': 2, 'Mars': 2,
               'Jupiter': 1, 'Saturn': 1, 'Uranus': 1, 'Neptune': 1, 'Pluto': 1}
    elem = {e: 0 for e in ELEM_JP}
    mode = {m: 0 for m in MODE_JP}
    rows = []
    for k, w in weights.items():
        pl = natal['planets'].get(k)
        if not pl or 'longitude' not in pl:
            continue
        si = int(pl['longitude'] // 30)
        elem[ELEM_JP[si % 4]] += w
        mode[MODE_JP[si % 3]] += w
        rows.append(f"{PJP[k]}={ELEM_JP[si % 4]}")
    asc_si = int(natal['houses']['ascendant']['longitude'] // 30)
    elem[ELEM_JP[asc_si % 4]] += 3
    mode[MODE_JP[asc_si % 3]] += 3
    rows.append(f"ASC={ELEM_JP[asc_si % 4]}")
    order = sorted(elem, key=elem.get, reverse=True)
    return elem, mode, rows, order


def element_verdict(elem):
    """同点を同点として扱い、「乏しい」と呼べる閾値を機械的に決める。
       総量に対する比率で判定する（均等配分は25%）。
       18%未満=際立って乏しい / 18〜22%=やや少ない / それ以外=偏りとは呼ばない"""
    total = sum(elem.values()) or 1
    hi = max(elem.values())
    lo = min(elem.values())
    tops = [e for e, v in elem.items() if v == hi]
    lows = [e for e, v in elem.items() if v == lo]
    pct = lo / total * 100
    if pct < 18:
        grade = '際立って乏しい'
    elif pct < 22:
        grade = 'やや少ない'
    else:
        grade = '目立った不足とは言えない'
    lines = []
    if len(tops) > 1:
        lines.append(f"優勢な元素: {'と'.join(tops)}が同点（各{hi}）。"
                     f"どちらか一方を『優勢』と書かず、二つが拮抗していると書くこと")
    else:
        lines.append(f"優勢な元素: {tops[0]}（{hi}）")
    if len(lows) > 1:
        lines.append(f"最も少ない元素: {'と'.join(lows)}が同点（各{lo}・全体の{pct:.0f}%）。"
                     f"一方だけを『最も弱い』と書かないこと")
    else:
        lines.append(f"最も少ない元素: {lows[0]}（{lo}・全体の{pct:.0f}%）")
    lines.append(f"不足の程度: {grade}。"
                 f"『驚くほど乏しい』『ほとんど無い』といった強い言い方は、際立って乏しい（18%未満）のときだけ許される")
    return lines


def transit_to_natal(natal, trans_pos):
    """トランジット外惑星→ネイタル天体・アングルの接触（オーブ3度以内）。
       計算して渡さないとモデルが見落とす。第7版でオーブ56分の合を落とした"""
    pts = [(PJP[k], v['longitude']) for k, v in natal['planets'].items()
           if 'longitude' in v and k in PJP]
    pts.append(('ASC', natal['houses']['ascendant']['longitude']))
    pts.append(('MC', natal['houses']['midheaven']['longitude']))
    rows = []
    for tname, tlon in trans_pos:
        for nname, nlon in pts:
            d = angdiff(tlon, nlon)
            for ang, label in ASPECTS_DEF:
                orb = abs(d - ang)
                if orb <= 3.0:
                    tight = '★接触中（1度以内・最重要）' if orb <= 1.0 else ''
                    rows.append(f"T{tname} → N{nname}: {label}（オーブ{orb:.1f}度）{tight}")
                    break
    return sorted(rows, key=lambda r: float(r.split('オーブ')[1].split('度')[0]))


SEASON = {'火': '春', '土': '夏', '風': '秋', '水': '冬'}


def season_of_sign(lon):
    return SEASON[['火', '土', '風', '水'][int(lon // 30) % 4]]


def season_of_house(h):
    return SEASON[['火', '土', '風', '水'][(h - 1) % 4]]


def part_of_fortune(natal, sect_day):
    """PoF: 昼=ASC+月-太陽 / 夜=ASC+太陽-月"""
    asc = natal['houses']['ascendant']['longitude']
    sun = natal['planets']['Sun']['longitude']
    moon = natal['planets']['Moon']['longitude']
    lon = (asc + moon - sun) % 360 if sect_day else (asc + sun - moon) % 360
    si = int(lon // 30)
    deg = lon % 30
    h = house_of(lon, natal['houses']['cusps'])
    return lon, SIGNS_JP[si], deg, h


ASPECTS_DEF = [(0, '合'), (60, 'セクスタイル'), (90, 'スクエア'), (120, 'トライン'), (180, 'オポジション')]


def natal_aspects(natal):
    """主要アスペクト表(ルミナリー7度/他6度、セクスタイルは4度)"""
    pts = [(PJP[k], v['longitude'], k in ('Sun', 'Moon'))
           for k, v in natal['planets'].items() if 'longitude' in v and k in PJP]
    pts.append(('ASC', natal['houses']['ascendant']['longitude'], False))
    pts.append(('MC', natal['houses']['midheaven']['longitude'], False))
    rows = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            n1, l1, lum1 = pts[i]
            n2, l2, lum2 = pts[j]
            d = angdiff(l1, l2)
            for ang, label in ASPECTS_DEF:
                orb_max = 4 if ang == 60 else (7 if (lum1 or lum2) else 6)
                orb = abs(d - ang)
                if orb <= orb_max:
                    rows.append(f"{n1} と {n2}: {label}（オーブ{orb:.1f}度）")
                    break
    return rows


def profection_timeline(p, natal, current_age):
    """過去24年のプロフェクション年表(年齢・西暦・起動ハウス・年主星)"""
    rows = []
    for age in range(max(0, current_age - 24), current_age + 1):
        ph = (age % 12) + 1
        si = int(natal['houses']['cusps'][ph - 1] // 30)
        y1 = p['y'] + age
        mark = ''
        if ph == 12:
            mark = '←静かな切り替わり・仕込みの年'
        elif ph == 1:
            mark = '←再起動の年'
        elif ph == 7:
            mark = '←契約と対人の年'
        elif ph == 10:
            mark = '←表舞台の年'
        if age in (29, 30):
            mark += '（土星回帰の時期）'
        rows.append(f"{age}歳({y1}年{p['mo']}月〜{y1+1}年{p['mo']}月): 第{ph}ハウス・年主星{RULERS_JP[si]} {mark}".rstrip())
    return rows


def pmoon_history(p, natal, current_age, years=9):
    """過去N年の各誕生日時点の進行の月(サイン・エレメント・在室ハウス)"""
    rows = []
    prev = None
    for k in range(years, -1, -1):
        y = p['y'] + current_age - k
        prog_k = api('/api/calculate-progressions',
                     {'birth_year': p['y'], 'birth_month': p['mo'], 'birth_day': p['d'],
                      'birth_hour': p['h'], 'birth_minute': p['mi'],
                      'current_date': f"{y}-{p['mo']:02d}-{p['d']:02d}"})
        pm = prog_k['p_moon']
        h = house_of(pm['longitude'], natal['houses']['cusps'])
        si = int(pm['longitude'] // 30)
        elem = ['火', '土', '風', '水'][si % 4]
        cur = (pm['signJP'], h)
        note = '' if cur == prev else ' ★移動'
        rows.append(f"{y}年{p['mo']}月時点: {pm['signJP']}({elem}={SEASON[elem]}) 第{h}ハウス(現実={season_of_house(h)}){note if prev else ''}")
        prev = cur
    return rows


def solar_arc_contacts(natal, prog):
    """SA主要接触(合/スクエア/オポジション、オーブ1.5度以内)"""
    arc = (prog['p_sun']['longitude'] - natal['planets']['Sun']['longitude']) % 360
    points = {PJP[k]: v['longitude'] for k, v in natal['planets'].items()
              if 'longitude' in v and k in PJP}
    points['ASC'] = natal['houses']['ascendant']['longitude']
    points['MC'] = natal['houses']['midheaven']['longitude']
    targets = dict(points)
    contacts = []
    for name, lon in points.items():
        directed = (lon + arc) % 360
        for tname, tlon in targets.items():
            if tname == name:
                continue
            for asp, label in ((0, '合'), (90, 'スクエア'), (180, 'オポジション')):
                orb = angdiff(angdiff(directed, tlon), asp) if asp == 0 else abs(angdiff(directed, tlon) - asp)
                orb = abs(angdiff(directed, tlon) - asp)
                if orb <= 1.5:
                    contacts.append(f'SA{name} → ネイタル{tname} {label}（オーブ{orb:.1f}度）')
    return arc, contacts



# ---- エッセンシャルディグニティ（城主＝ディグニティコードをコードで確定する） ----
DOMICILE = {'太陽': ['獅子座'], '月': ['蟹座'], '水星': ['双子座', '乙女座'],
            '金星': ['牡牛座', '天秤座'], '火星': ['牡羊座', '蠍座'],
            '木星': ['射手座', '魚座'], '土星': ['山羊座', '水瓶座']}
EXALT = {'太陽': '牡羊座', '月': '牡牛座', '水星': '乙女座', '金星': '魚座',
         '火星': '山羊座', '木星': '蟹座', '土星': '天秤座'}
DETRIMENT = {'太陽': ['水瓶座'], '月': ['山羊座'], '水星': ['射手座', '魚座'],
             '金星': ['蠍座', '牡羊座'], '火星': ['天秤座', '牡牛座'],
             '木星': ['双子座', '乙女座'], '土星': ['蟹座', '獅子座']}
FALL = {'太陽': '天秤座', '月': '蠍座', '水星': '魚座', '金星': '乙女座',
        '火星': '蟹座', '木星': '山羊座', '土星': '牡羊座'}
ELEM_OF = {'牡羊座': '火', '獅子座': '火', '射手座': '火', '牡牛座': '土', '乙女座': '土',
           '山羊座': '土', '双子座': '風', '天秤座': '風', '水瓶座': '風',
           '蟹座': '水', '蠍座': '水', '魚座': '水'}
TRIPL = {'火': ('太陽', '木星'), '土': ('金星', '月'), '風': ('土星', '水星'), '水': ('火星', '火星')}
TRAD7 = ['太陽', '月', '水星', '金星', '火星', '木星', '土星']
ANGULAR = (1, 4, 7, 10)


def dignity_score(planet, sign, is_day):
    """リリー式。ドミサイル+5 / エグザルテーション+4 / トリプリシティ+3 /
       デトリメント-5 / フォール-4 / いずれも無ければペレグリン-5"""
    marks, sc = [], 0
    if sign in DOMICILE.get(planet, []):
        sc += 5; marks.append('自分の城')
    if EXALT.get(planet) == sign:
        sc += 4; marks.append('賓客の上座')
    tri = TRIPL[ELEM_OF[sign]][0 if is_day else 1]
    if tri == planet:
        sc += 3; marks.append('親戚の家')
    if not marks:
        if sign in DETRIMENT.get(planet, []):
            sc = -5; marks.append('敵地')
        elif FALL.get(planet) == sign:
            sc = -4; marks.append('崖から落とされた')
        else:
            sc = -5; marks.append('旅先')
    return sc, '＋'.join(marks)


def decide_lord(natal_jp, is_day, year_ruler):
    """ディグニティコード(城主)を機械的に決める。
       ①点数最高 ②同点ならアングル ③ASC/MC/太陽/月と合(3度以内) ④年主星 ⑤伝統順"""
    rows = []
    for pl in TRAD7:
        v = natal_jp.get(pl)
        if not v:
            continue
        sc, mark = dignity_score(pl, v['sign'], is_day)
        rows.append({'p': pl, 'score': sc, 'mark': mark, 'sign': v['sign'],
                     'house': v['house'], 'lon': v['lon']})
    rows.sort(key=lambda r: -r['score'])
    top = [r for r in rows if r['score'] == rows[0]['score']]
    reason = '点数最高'
    if len(top) > 1:
        cand = [r for r in top if r['house'] in ANGULAR]
        if len(cand) == 1:
            top, reason = cand, '同点→アングル配置'
        elif cand:
            top = cand
    if len(top) > 1 and year_ruler:
        cand = [r for r in top if r['p'] == year_ruler]
        if len(cand) == 1:
            top, reason = cand, '同点→今年の年主星'
    if len(top) > 1:
        top = sorted(top, key=lambda r: TRAD7.index(r['p']))[:1]
        reason = '同点→伝統的な天体順'
    return rows, top[0], reason


def build_chart_text(p, natal, prog, trans, sr, sa_arc, sa_contacts):
    _ctx = {'is_day': None, 'year_ruler': None}
    t = f"# {p['name']}さんの占星術データ（鑑定用）\n\n"
    t += "## 基本情報\n"
    t += f"- 生年月日: {p['y']}年{p['mo']}月{p['d']}日 {p['h']}時{p['mi']}分\n"
    t += f"- 出生地: {p['place']}\n"
    t += f"- 鑑定日: {CURRENT_DATE}\n"
    if isinstance(sr.get('age'), int):
        t += f"- 現在の年齢: {sr['age']}歳\n"
    t += "\n## ネイタルチャート（出生図）\n\n### 天体の配置\n"
    for key, pl in natal['planets'].items():
        if pl.get('error'):
            continue
        rx = ' ℞（逆行）' if pl.get('retrograde') else ''
        t += f"- {PJP.get(key, key)}: {pl['signJP']} {fdeg(pl['degree'])}{rx} [第{pl['house']}ハウス]\n"
    houses = natal['houses']
    t += "\n### アングル\n"
    t += f"- ASC（アセンダント）: {houses['ascendant']['signJP']} {fdeg(houses['ascendant']['degree'])}\n"
    t += f"- MC（天頂）: {houses['midheaven']['signJP']} {fdeg(houses['midheaven']['degree'])}\n"
    t += "\n### ハウスカスプ（Placidus式）\n"
    for i, cusp in enumerate(houses['cusps']):
        t += f"- 第{i+1}ハウス: {SIGNS_JP[int(cusp // 30)]} {fdeg(cusp % 30)}\n"
    cusps = natal['houses']['cusps']
    ps_h = house_of(prog['p_sun']['longitude'], cusps)
    pm_h = house_of(prog['p_moon']['longitude'], cusps)
    t += "\n## プログレス（セカンダリー進行図・ハウスは出生図に重ねた在室）\n"
    t += f"- 基準日: {CURRENT_DATE}\n"
    t += f"- プログレス太陽: {prog['p_sun']['signJP']} {fdeg(prog['p_sun']['degree'])} [ネイタル第{ps_h}ハウス]\n"
    t += f"- プログレス月: {prog['p_moon']['signJP']} {fdeg(prog['p_moon']['degree'])} [ネイタル第{pm_h}ハウス]\n"
    t += f"- 進行の月の季節: 心の季節（サイン）={season_of_sign(prog['p_moon']['longitude'])}、現実の季節（ハウス）={season_of_house(pm_h)}\n"
    pmc = prog_moon_contacts(natal, prog)
    if pmc:
        t += "- 進行の月が接触中: " + "、".join(pmc) + "\n"
    else:
        t += "- 進行の月が接触中のネイタル天体（オーブ2度以内）: なし\n"
    if isinstance(sr.get('age'), int):
        t += "\n## 進行の月の履歴（計算済み・過去を当てる材料）\n"
        for r in pmoon_history(p, natal, sr['age']):
            t += f"- {r}\n"
        t += "\n## プロフェクション年表（計算済み・過去を当てる材料）\n"
        for r in profection_timeline(p, natal, sr['age']):
            t += f"- {r}\n"
    elem, mode, erows, eorder = element_balance(natal)
    t += "\n## 四大元素バランス（計算済み・体質と気質の章で使うこと）\n"
    t += "- 各点の元素: " + "、".join(erows) + "\n"
    t += f"- 重み付き合計（太陽・月・ASC=3、個人天体=2、社会・外惑星=1）: "
    t += "、".join(f"{e}={elem[e]}" for e in ELEM_JP) + "\n"
    for _l in element_verdict(elem):
        t += f"- {_l}\n"
    t += "- 3区分（同じ重み付け）: " + "、".join(f"{m}={mode[m]}" for m in MODE_JP) + "\n"
    t += "\n## サビアンシンボル（計算済み・検証済み原文）\n"
    t += "※占星術の慣例により、度数表記◯°◯′は「切り上げた度数」のシンボルに正式に対応する（例: 獅子座8°32′→獅子座9度）。\n"
    t += "※以下が各天体の正式なサビアン度数である。本文では「近い度数」「およそ」等と言わず、その天体のサビアンシンボルそのものとして断言し、情景は原文に忠実な日本語で描写すること。\n"
    for key in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                'Uranus', 'Neptune', 'Pluto', 'TrueNode', 'Chiron'):
        pl = natal['planets'].get(key)
        if not pl or 'degree' not in pl:
            continue
        d, sym = sabian_of(pl['signJP'], pl['degree'])
        t += f"- {PJP[key]}: {pl['signJP']}{d}度 \"{sym}\"\n"
    for label, obj in (('ASC', natal['houses']['ascendant']), ('MC', natal['houses']['midheaven'])):
        d, sym = sabian_of(obj['signJP'], obj['degree'])
        t += f"- {label}: {obj['signJP']}{d}度 \"{sym}\"\n"
    for label, obj in (('進行の太陽', prog['p_sun']), ('進行の月', prog['p_moon'])):
        d, sym = sabian_of(obj['signJP'], obj['degree'])
        t += f"- {label}: {obj['signJP']}{d}度 \"{sym}\"\n"
    t += "\n## ソーラーアーク（計算済み・裏取り専用）\n"
    t += f"- 太陽弧: {sa_arc:.1f}度\n"
    if sa_contacts:
        t += "- 主要接触（オーブ1.5度以内）:\n"
        for c in sa_contacts:
            t += f"  - {c}\n"
    else:
        t += "- オーブ1.5度以内の主要接触なし\n"
    t += "\n## トランジット\n"
    if trans.get('outer_planets'):
        t += f"\n### 外惑星の現在位置（{CURRENT_DATE}時点）\n"
        _tpos = []
        for key in ('Uranus', 'Neptune', 'Pluto', 'Saturn', 'Jupiter'):
            pl = trans['outer_planets'].get(key)
            if pl:
                if key in ('Uranus', 'Neptune', 'Pluto'):
                    t += f"- {PJP[key]}: {pl['signJP']} {fdeg(pl['degree'])}{' ℞' if pl.get('retrograde') else ''}\n"
                if 'longitude' in pl:
                    _tpos.append((PJP[key], pl['longitude']))
        _tc = transit_to_natal(natal, _tpos) if _tpos else []
        if _tc:
            t += ("\n### 今の空からネイタルへの接触（計算済み・オーブ3度以内・この表を使い自分で探さない）\n"
                  "※★印は1度以内。いま最も効いている接触なので、未来形（やがて・数年のうちに）で書かず、"
                  "すでに起きていることとして扱うこと\n")
            for r in _tc:
                t += f"- {r}\n"
    for label, arr in (('木星', trans.get('jupiter_transits')), ('土星', trans.get('saturn_transits'))):
        if arr:
            t += f"\n### {label}のサイン移動（今後3年）\n"
            for tr in arr:
                t += f"- {tr['date']}: {tr['signJP']}入り\n"
    t += "\n### 日食・月食\n- データ提供なし（言及しないでください）\n"
    sun_house = natal['planets'].get('Sun', {}).get('house')
    if sun_house:
        sect = '昼生まれ' if 7 <= sun_house <= 12 else '夜生まれ'
        _ctx['is_day'] = (sect == '昼生まれ')
        t += f"\n## セクト（計算済み・この値をそのまま使うこと）\n- 太陽が第{sun_house}ハウス → {sect}\n"
        pof_lon, pof_sign, pof_deg, pof_h = part_of_fortune(natal, sect == '昼生まれ')
        pd_, psym = sabian_of(pof_sign, pof_deg)
        t += f"\n## パート・オブ・フォーチュン（計算済み・{sect}式）\n"
        t += f"- {pof_sign} {fdeg(pof_deg)} [第{pof_h}ハウス] サビアン: {pof_sign}{pd_}度 \"{psym}\"\n"
        t += "\n## 主要アスペクト表（計算済み・この表を使い自分で計算しない）\n"
        for r in natal_aspects(natal):
            t += f"- {r}\n"
    if isinstance(sr.get('age'), int):
        age = sr['age']
        ph = (age % 12) + 1
        si = int(natal['houses']['cusps'][ph - 1] // 30)
        t += "\n## プロフェクション（計算済み・この値をそのまま使うこと）\n"
        t += f"- 現在の年齢: {age}歳\n"
        _bd = f"{p['mo']}月{p['d']}日"
        _y0 = p['y'] + age
        t += f"- 今年の期間: {_y0}年{_bd} 〜 {_y0 + 1}年{_bd}（この期間が「今年」。鑑定日はこの中にある）\n"
        _pph = ((age - 1) % 12) + 1
        _psi = int(natal['houses']['cusps'][_pph - 1] // 30)
        t += (f"- ひとつ前の期間: {_y0 - 1}年{_bd} 〜 {_y0}年{_bd}（{age - 1}歳・第{_pph}ハウス・"
              f"年主星{RULERS_JP[_psi]}）。これは既に終わっている。「今この瞬間まで」と書かないこと\n"
              f"- 起動ハウス: 第{ph}ハウス\n")
        t += f"- 起動サイン: {SIGNS_JP[si]}\n"
        t += f"- 年主星（今年、鍵を預かる星）: {RULERS_JP[si]}\n"
        _ctx['year_ruler'] = RULERS_JP[si]
        t += f"- 同じ部屋が前回起動した年齢: {age - 12}歳\n"
    if sr.get('planets'):
        t += "\n## ソーラーリターン図（裏取り専用・本文で言及しない）\n"
        t += f"- SR-ASC: {sr['houses']['ascendant']['signJP']} {fdeg(sr['houses']['ascendant']['degree'])}\n"
        t += f"- SR-MC: {sr['houses']['midheaven']['signJP']} {fdeg(sr['houses']['midheaven']['degree'])}\n"
        for key in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                    'Jupiter', 'Saturn'):
            pl = sr['planets'].get(key)
            if not pl or pl.get('error'):
                continue
            house = f" [第{pl['house']}ハウス]" if pl.get('house') else ''
            t += f"- {PJP[key]}: {pl['signJP']} {fdeg(pl['degree'])}{house}\n"
    q = p.get('questions') or {}
    if q.get('future') or q.get('challenge') or q.get('today'):
        t += "\n## ご本人の三つの答え\n"
        if q.get('future'):
            t += f"- ①行きたい未来: {q['future']}\n"
        if q.get('challenge'):
            t += f"- ②いま感じている課題: {q['challenge']}\n"
        if q.get('today'):
            t += f"- ③今日あえて聞いてみたいこと: {q['today']}\n"
    elif p.get('consult'):
        t += f"\n## ご本人からの近況とご相談（参考）\n{p['consult']}\n"
    else:
        t += "\n## ご相談\n- 記載なし（「あなたの問いへ」の章は省略し、その分を第5章と第9章に配分）\n"
    # ---- エッセンシャルディグニティ（城主をここで確定し、AIに選ばせない） ----
    natal_jp = {}
    for key, pl in natal['planets'].items():
        jp = PJP.get(key, key)
        if jp in TRAD7 and not pl.get('error'):
            natal_jp[jp] = {'sign': pl['signJP'], 'house': pl['house'],
                            'lon': pl['longitude']}
    if natal_jp and _ctx['is_day'] is not None:
        rows, lord, reason = decide_lord(natal_jp, _ctx['is_day'], _ctx['year_ruler'])
        t += "\n## エッセンシャルディグニティ（計算済み・城主はこの値で確定。選び直さないこと）\n"
        t += "※リリー式。自分の城+5／賓客の上座+4／親戚の家+3／敵地-5／崖から落とされた-4／旅先-5\n"
        for r in rows:
            t += f"- {r['p']}: {r['sign']} 第{r['house']}ハウス　{r['mark']}　{r['score']:+d}\n"
        t += f"- ★城主（ディグニティコード）: {lord['p']}（{lord['sign']}・第{lord['house']}ハウス・{lord['score']:+d}・{reason}）\n"
        t += "- この城主を第7章の中心に据え、王の香りもこの星で処方する。\n"
    t += f"\n---\n{P1_TAIL}\n"
    return t


p = PERSON
natal = api('/api/calculate-chart',
            {'year': p['y'], 'month': p['mo'], 'day': p['d'],
             'hour': p['h'], 'minute': p['mi'], 'latitude': p['lat'], 'longitude': p['lon']})
prog = api('/api/calculate-progressions',
           {'birth_year': p['y'], 'birth_month': p['mo'], 'birth_day': p['d'],
            'birth_hour': p['h'], 'birth_minute': p['mi'], 'current_date': CURRENT_DATE})
trans = api('/api/calculate-transits', {'start_date': CURRENT_DATE, 'years': 3})
sr = api('/api/calculate-solar-return',
         {'birth_year': p['y'], 'birth_month': p['mo'], 'birth_day': p['d'],
          'birth_hour': p['h'], 'birth_minute': p['mi'],
          'latitude': p['lat'], 'longitude': p['lon'], 'tz_name': 'Asia/Tokyo',
          'current_date': CURRENT_DATE,
          'sr_latitude': p['lat'], 'sr_longitude': p['lon'], 'sr_tz_name': 'Asia/Tokyo'})
sa_arc, sa_contacts = solar_arc_contacts(natal, prog)
chart = build_chart_text(p, natal, prog, trans, sr, sa_arc, sa_contacts)
open(f'{DIR}/chart8_{p["slug"]}.txt', 'w', encoding='utf-8').write(chart)
print(f'chart ready ({len(chart)} chars, SA contacts: {len(sa_contacts)})', flush=True)

client = Anthropic()
system_blocks = [{'type': 'text', 'text': GEM, 'cache_control': {'type': 'ephemeral'}}]
messages = [{'role': 'user', 'content': chart}]
blocks, usd, carry = [], 0.0, 0

for bi, blk in enumerate(BLOCKS):
    # 前便までのズレを繰り越して目標を補正（下振れ・上振れの両方を吸収する）
    if blk.get('no_carry'):
        # 締めの便は前便のズレを持ち込まない（終章・次の扉・宮廷が痩せるのを防ぐ）
        adj = blk['target']
    else:
        adj = max(int(blk['target'] * 0.8), min(int(blk['target'] * 1.6), blk['target'] + carry))
    note = ''
    if blk.get('no_carry'):
        note = '（この便には終章と締めの二葉が入ります。字数を必ず使い切ってください）'
    elif carry > 200:
        note = f'（前便が目安より{carry}字少なかったため、この便は厚めに書いてください）'
    elif carry < -200:
        note = f'（前便が目安より{-carry}字多かったため、この便は引き締めて書いてください）'
    prompt = f"{blk['body']}この便の合計は{adj:,}字前後にしてください。{note}{GUARD}"
    if bi > 0:
        messages.append({'role': 'user', 'content': prompt})
    else:
        messages[0]['content'] = chart.replace(P1_TAIL, P1_TAIL + '\n' + prompt)

    text = ''
    for attempt in range(3):
        try:
            text = ''
            with client.messages.stream(model=MODEL, max_tokens=28000,
                                        thinking={'type': 'disabled'},
                                        system=system_blocks, messages=messages) as stream:
                for tk in stream.text_stream:
                    text += tk
                u = stream.get_final_message().usage
            if len(text) < adj * (0.8 if blk.get('no_carry') else 0.7):
                print(f"  [{blk['name']}] 試行{attempt+1}: 短すぎ {len(text):,}字 / 目標 {adj:,}字 — 書き直し", flush=True)
                messages.append({'role': 'assistant', 'content': text})
                messages.append({'role': 'user', 'content':
                                 f'短すぎます。同じ範囲を{adj:,}字前後まで厚みを足して書き直してください。'
                                 f'章を増やさず、実感の場面描写と代償の記述を補ってください。' + GUARD})
                continue
            cw = getattr(u, 'cache_creation_input_tokens', 0) or 0
            cr = getattr(u, 'cache_read_input_tokens', 0) or 0
            usd += u.input_tokens / 1e6 * 2.0 + u.output_tokens / 1e6 * 10.0 + cw / 1e6 * 2.5 + cr / 1e6 * 0.20
            break
        except Exception as e:
            print(f"  [{blk['name']}] 試行{attempt+1} エラー: {str(e)[:140]}", flush=True)
            time.sleep(20)
    if not text:
        raise RuntimeError(f"{blk['name']} 失敗")

    text = re.sub(r'\n*[（(]『?(?:はい|続けて)[^）)]{0,40}[）)]\s*$', '', text.rstrip())
    text = re.sub(r'^\*\*\s*([【\[][^】\]]*[】\]])\s*\*\*', r'\1', text, flags=re.M)
    text = re.sub(r'^\*\*(第[0-9１-９]+章末|序章末|終章末)\*\*[\s　]*', '', text, flags=re.M)

    blocks.append(text)
    messages.append({'role': 'assistant', 'content': text})
    carry += adj - len(text)
    total = sum(len(x) for x in blocks)
    mark = 'OK' if abs(len(text) - adj) <= adj * 0.15 else '要確認'
    print(f"  [{blk['name']}] {len(text):,}字 / 目標 {adj:,}字  ({mark})  累計 {total:,}字  繰越 {carry:+,}字", flush=True)
    if total > TOTAL_CAP * 1.15:
        print(f"  ! 累計が上限{TOTAL_CAP:,}字を大きく超えています。以降の便を引き締めます。", flush=True)
    full = '\n\n'.join(b.strip() for b in blocks)
    open(f'{DIR}/reading8_{p["slug"]}.md', 'w', encoding='utf-8').write(full)

print(f'DONE: {len(full)} chars, ${usd:.3f} (≒{usd*150:.0f}円)', flush=True)
