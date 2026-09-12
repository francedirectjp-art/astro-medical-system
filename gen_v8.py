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
GEM = open('/Users/oda/CCAGI/astro-medical-system/gem_narrative_astrologer_v8.md', encoding='utf-8').read()
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

PERSON = {'slug': 'tozawa', 'name': '戸澤麻理',
          'y': 1972, 'mo': 7, 'd': 13, 'h': 7, 'mi': 40,
          'lat': 36.0785, 'lon': 140.2044,
          'pref': '茨城県', 'place': '茨城県土浦市', 'gender': '',
          'consult': '',
          'questions': {
              'future': ('たくさんの人が「自分の人生って楽しくてしょうがない」「この人生を生きるために生まれてきた」と'
                         '思いながら生きている世界をつくりたい。そのきっかけをつくる人でありたい。'
                         '自分を知り、誰かの正解ではなく自分で自分の人生を選んでいく人を増やしたい。'
                         'つくりたい「Marin Harbor」は、迷ったときに一度戻ってきて、自分を取り戻し、'
                         '必要な人や知識や仕事と出会い、また人生という海へ出ていくための港。'
                         '人と人、才能と才能をつなぎ、その輪を日本だけでなく世界へ広げたい。'
                         '手段として今は鑑定・講座・相談・発信をしており、これからは人前で話すスピーカーとしても、'
                         '文章を書く人としても活動したい。私自身も、私を愛してくれて私も心から愛せる人と一緒に生き、'
                         '仲間と互いの力を活かし合えるコミュニティをつくりたい。'),
              'challenge': ('一番大きな課題はお金。やりたいことと目指す未来は明確になってきたが、'
                            '現在は生活や返済のために働く時間が必要で、やりたいことに使える時間とお金が限られている。'
                            '得意なことと人とのつながりを、きちんと収入につながる仕事として確立し、'
                            '生活のために働く状態から、自分のやりたい仕事で十分な収入を得られる状態へ移行したい。'),
              'today': '私が目指す未来のために、私自身がまだ気づいていない才能や役割は何でしょうか？',
          }}

PARTS = int(__import__('os').environ.get('PARTS', '5'))

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']
RULERS_JP = ['火星', '金星', '水星', '月', '太陽', '水星',
             '金星', '火星', '木星', '土星', '土星', '木星']
PJP = {'Sun': '太陽', 'Moon': '月', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星',
       'Jupiter': '木星', 'Saturn': '土星', 'Uranus': '天王星', 'Neptune': '海王星',
       'Pluto': '冥王星', 'TrueNode': 'ドラゴンヘッド', 'Chiron': 'キローン'}

P1_TAIL = ('以上のデータで鑑定書を執筆してください。今回は対話ではなく4回に分けた一括生成です。'
           '第2節のブロック停止ルールは適用しません。'
           'まず第1便として、第5節5-1の「はじめに」（九段の型を順序どおり厳守）、序章、第1章、'
           '「一葉｜心当たり」、第2章、そして「一葉｜太陽と月を、一緒に読む」までを、途中で止まらずに書いてください。'
           '合計7,700字前後。記入欄は全角カッコの空欄として実際に紙面に出してください。'
           '「はじめに」では質問も記入欄も出さず、他の占いへの言及もしないでください。'
           '十本の指は「はじめに」の八段目で一段落だけ触れ、序章では繰り返さないでください。'
           + '章は必ず番号順に書き、順序の言い直しや（※〜）のような断り書き、メタ発言を本文に一切残さないでください。各章末には第5節5-0の三点セット（読みの手順／ここで私が決めなかったこと／指の回収）を必ず付けてください。弱い推量（〜ではないでしょうか等）は一章一回まで。' +
           '「一葉｜太陽と月を、一緒に読む」まで書いたら止まってください。')

P2 = ('続けて第2便です。第3章・第4章・第5章を、途中で止まらずに書いてください。合計5,500字前後。'
      '第5章末で十本の指が揃う回収を必ず書いてください。'
      + '章は必ず番号順に書き、順序の言い直しや（※〜）のような断り書き、メタ発言を本文に一切残さないでください。各章末には第5節5-0の三点セット（読みの手順／ここで私が決めなかったこと／指の回収）を必ず付けてください。弱い推量（〜ではないでしょうか等）は一章一回まで。' +
      '第5章まで書いたら止まってください。')

P3 = ('続けて第3便です。第6章・第7章・第8章・第9章を、途中で止まらずに書いてください。合計6,600字前後。'
      '第7章は「だから、この条件では消耗し、この条件では力を使いやすくなる」まで書き切ること。'
      '第9章には周期の年数（十二年に一度／二十九年に一度）を必ず入れること。'
      + '章は必ず番号順に書き、順序の言い直しや（※〜）のような断り書き、メタ発言を本文に一切残さないでください。各章末には第5節5-0の三点セット（読みの手順／ここで私が決めなかったこと／指の回収）を必ず付けてください。弱い推量（〜ではないでしょうか等）は一章一回まで。' +
      '第9章まで書いたら止まってください。')

P4 = ('続けて最終便です。第10章・（ご相談があれば「あなたの問いへ」）・第11章・終章・'
      '第5節5-2の「第一葉｜次の扉」「第二葉｜王国の宮廷」を、途中で止まらずに書き切ってください。合計5,900字前後。'
      '第11章は冒頭で配合の根拠を一度開示し、三つの処方が同一配合になっていないか必ず突き合わせること。'
      '終章に完了宣言（「もう繰り返される必要のない物語になりました」等）を書かないこと。'
      '「次の扉」は第5節5-2の型に厳密に従い、日付・URL・講座名・価格・期限を一切書かないこと。'
      + '章は必ず番号順に書き、順序の言い直しや（※〜）のような断り書き、メタ発言を本文に一切残さないでください。各章末には第5節5-0の三点セット（読みの手順／ここで私が決めなかったこと／指の回収）を必ず付けてください。弱い推量（〜ではないでしょうか等）は一章一回まで。')

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


def build_chart_text(p, natal, prog, trans, sr, sa_arc, sa_contacts):
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
    t += f"- 優勢な元素: {eorder[0]}（次点: {eorder[1]}） ／ 最も弱い元素: {eorder[-1]}\n"
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
        for key in ('Uranus', 'Neptune', 'Pluto'):
            pl = trans['outer_planets'].get(key)
            if pl:
                t += f"- {PJP[key]}: {pl['signJP']} {fdeg(pl['degree'])}{' ℞' if pl.get('retrograde') else ''}\n"
    for label, arr in (('木星', trans.get('jupiter_transits')), ('土星', trans.get('saturn_transits'))):
        if arr:
            t += f"\n### {label}のサイン移動（今後3年）\n"
            for tr in arr:
                t += f"- {tr['date']}: {tr['signJP']}入り\n"
    t += "\n### 日食・月食\n- データ提供なし（言及しないでください）\n"
    sun_house = natal['planets'].get('Sun', {}).get('house')
    if sun_house:
        sect = '昼生まれ' if 7 <= sun_house <= 12 else '夜生まれ'
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
        t += f"- 起動ハウス: 第{ph}ハウス\n"
        t += f"- 起動サイン: {SIGNS_JP[si]}\n"
        t += f"- 年主星（今年、鍵を預かる星）: {RULERS_JP[si]}\n"
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
blocks = []
usd = 0.0
prompts = [P2, P3, P4, CONT]
for i in range(PARTS):
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
            if len(text) < 2500:
                print(f'part {i+1} attempt {attempt+1}: too short ({len(text)}) — retry', flush=True)
                continue
            cw = getattr(u, 'cache_creation_input_tokens', 0) or 0
            cr = getattr(u, 'cache_read_input_tokens', 0) or 0
            usd += u.input_tokens / 1e6 * 2.0 + u.output_tokens / 1e6 * 10.0 + cw / 1e6 * 2.5 + cr / 1e6 * 0.20
            break
        except Exception as e:
            print(f'part {i+1} attempt {attempt+1} error: {str(e)[:150]}', flush=True)
            time.sleep(20)
    if not text or len(text) < 2500:
        raise RuntimeError(f'part {i+1} failed')
    text = re.sub(r'\n*[（(]『?(?:はい|続けて)[^）)]{0,40}[）)]\s*$', '', text.rstrip())
    text = re.sub(r'^\*\*\s*([【\[][^】\]]*[】\]])\s*\*\*', r'\1', text, flags=re.M)
    text = re.sub(r'^\*\*(第[0-9１-９]+章末|序章末|終章末)\*\*[\s　]*', '', text, flags=re.M)
    print(f'part {i+1}: {len(text)} chars', flush=True)
    blocks.append(text)
    messages.append({'role': 'assistant', 'content': text})
    full = '\n\n'.join(b.strip() for b in blocks)
    open(f'{DIR}/reading8_{p["slug"]}.md', 'w', encoding='utf-8').write(full)
    if re.search(r'王国の宮廷', text):
        break
    messages.append({'role': 'user', 'content': prompts[i]})

print(f'DONE: {len(full)} chars, ${usd:.3f} (≒{usd*150:.0f}円)', flush=True)
