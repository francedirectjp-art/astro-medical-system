# -*- coding: utf-8 -*-
"""自動鑑定書エンジン（第7版）

Flask の test_client で自前の計算APIを叩き、チャートテキストを組み立て、
Claude (Sonnet 5) の2分割生成で約20,000字の鑑定書を返す。
scratchpad/gen_v3.py で検証済みのロジックの本番移植。
"""
import json
import math
import os
import re
import time
from datetime import date

_BASE = os.path.dirname(os.path.abspath(__file__))
GEM_PATH = os.path.join(_BASE, 'gem_narrative_astrologer_v7.md')
SABIAN_PATH = os.path.join(_BASE, 'reading', 'sabian360.json')

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']
SIGN_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
           'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
RULERS_JP = ['火星', '金星', '水星', '月', '太陽', '水星',
             '金星', '火星', '木星', '土星', '土星', '木星']
PJP = {'Sun': '太陽', 'Moon': '月', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星',
       'Jupiter': '木星', 'Saturn': '土星', 'Uranus': '天王星', 'Neptune': '海王星',
       'Pluto': '冥王星', 'TrueNode': 'ドラゴンヘッド', 'Chiron': 'キローン'}
SEASON = {'火': '春', '土': '夏', '風': '秋', '水': '冬'}
ELEM_JP = ['火', '土', '風', '水']
MODE_JP = ['活動', '不動', '柔軟']

MODEL = os.environ.get('AUTO_READING_MODEL', 'claude-sonnet-5')
MARKER = re.compile(r'（[『「]はい[』」]または[『「]続けて[』」]と入力すると、次へ進みます。?）')

P1_TAIL = ('以上のデータで鑑定書を執筆してください。今回は対話ではなく2回に分けた一括生成です。'
           '第2節のブロック停止ルールは適用しません。'
           'まず前半として、序章・第1章・第2章・第3章・第4章・第5章・第6章・第7章を途中で止まらずに書いてください。'
           '前半の合計は12,500字前後。第5節の各章の文字数目安を一章ずつ守り、'
           '実感の場面描写と代償の記述を省略しないでください。章は必ず番号順に書き、'
           '順序の言い直しや（※〜）のような断り書きを本文に一切残さないでください。第7章まで書いたら止まってください。')
P2 = ('続けて後半です。第8章・第9章・第10章・（ご相談があれば「あなたの問いへ」）・第11章・終章を'
      '途中で止まらずに書き切ってください。後半の合計は8,000字前後。'
      '第5節の各章の文字数目安を一章ずつ守ってください。')
CONT = '続けて。残りの章を終章まで書き切ってください。'


def _load_sabian():
    with open(SABIAN_PATH, encoding='utf-8') as f:
        return json.load(f)


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


def season_of_sign(lon):
    return SEASON[ELEM_JP[int(lon // 30) % 4]]


def season_of_house(h):
    return SEASON[ELEM_JP[(h - 1) % 4]]


class ReadingEngine:
    def __init__(self, flask_app, anthropic_client):
        self.app = flask_app
        self.client = anthropic_client
        self.sabian = _load_sabian()
        with open(GEM_PATH, encoding='utf-8') as f:
            self.gem = f.read()

    # ── 計算API(自プロセス内呼び出し) ──────────────────────────
    def _api(self, path, body):
        with self.app.test_client() as tc:
            r = tc.post(path, json=body)
            data = r.get_json()
        if not data or not data.get('success'):
            raise RuntimeError(f'{path}: {data and data.get("error")}')
        return data

    def sabian_of(self, sign_jp, degree):
        si = SIGNS_JP.index(sign_jp)
        d = min(int(degree) + 1, 30)
        return d, self.sabian.get(f'{SIGN_EN[si]}_{d}', '')

    # ── データ収集 ────────────────────────────────────────────
    def collect(self, person):
        p = person
        current_date = time.strftime('%Y-%m-%d')
        natal = self._api('/api/calculate-chart',
                          {'year': p['y'], 'month': p['mo'], 'day': p['d'],
                           'hour': p['h'], 'minute': p['mi'],
                           'latitude': p['lat'], 'longitude': p['lon']})
        prog = self._api('/api/calculate-progressions',
                         {'birth_year': p['y'], 'birth_month': p['mo'], 'birth_day': p['d'],
                          'birth_hour': p['h'], 'birth_minute': p['mi'],
                          'current_date': current_date})
        trans = self._api('/api/calculate-transits', {'start_date': current_date, 'years': 3})
        sr = self._api('/api/calculate-solar-return',
                       {'birth_year': p['y'], 'birth_month': p['mo'], 'birth_day': p['d'],
                        'birth_hour': p['h'], 'birth_minute': p['mi'],
                        'latitude': p['lat'], 'longitude': p['lon'], 'tz_name': 'Asia/Tokyo',
                        'current_date': current_date,
                        'sr_latitude': p['lat'], 'sr_longitude': p['lon'],
                        'sr_tz_name': 'Asia/Tokyo'})
        ty, tm, td = map(int, current_date.split('-'))
        transit_chart = self._api('/api/calculate-chart',
                                  {'year': ty, 'month': tm, 'day': td, 'hour': 12, 'minute': 0,
                                   'latitude': p['lat'], 'longitude': p['lon']})
        return {'natal': natal, 'prog': prog, 'trans': trans, 'sr': sr,
                'transit_chart': transit_chart, 'current_date': current_date}

    # ── 内部計算 ─────────────────────────────────────────────
    def element_balance(self, natal):
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

    def part_of_fortune(self, natal, sect_day):
        asc = natal['houses']['ascendant']['longitude']
        sun = natal['planets']['Sun']['longitude']
        moon = natal['planets']['Moon']['longitude']
        lon = (asc + moon - sun) % 360 if sect_day else (asc + sun - moon) % 360
        return lon, SIGNS_JP[int(lon // 30)], lon % 30, house_of(lon, natal['houses']['cusps'])

    def natal_aspects(self, natal):
        pts = [(PJP[k], v['longitude'], k in ('Sun', 'Moon'))
               for k, v in natal['planets'].items() if 'longitude' in v and k in PJP]
        pts.append(('ASC', natal['houses']['ascendant']['longitude'], False))
        pts.append(('MC', natal['houses']['midheaven']['longitude'], False))
        defs = [(0, '合'), (60, 'セクスタイル'), (90, 'スクエア'),
                (120, 'トライン'), (180, 'オポジション')]
        rows = []
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                n1, l1, lum1 = pts[i]
                n2, l2, lum2 = pts[j]
                d = angdiff(l1, l2)
                for ang, label in defs:
                    orb_max = 4 if ang == 60 else (7 if (lum1 or lum2) else 6)
                    orb = abs(d - ang)
                    if orb <= orb_max:
                        rows.append(f"{n1} と {n2}: {label}（オーブ{orb:.1f}度）")
                        break
        return rows

    def solar_arc_contacts(self, natal, prog):
        arc = (prog['p_sun']['longitude'] - natal['planets']['Sun']['longitude']) % 360
        points = {PJP[k]: v['longitude'] for k, v in natal['planets'].items()
                  if 'longitude' in v and k in PJP}
        points['ASC'] = natal['houses']['ascendant']['longitude']
        points['MC'] = natal['houses']['midheaven']['longitude']
        contacts = []
        for name, lon in points.items():
            directed = (lon + arc) % 360
            for tname, tlon in points.items():
                if tname == name:
                    continue
                for asp, label in ((0, '合'), (90, 'スクエア'), (180, 'オポジション')):
                    orb = abs(angdiff(directed, tlon) - asp)
                    if orb <= 1.5:
                        contacts.append(f'SA{name} → ネイタル{tname} {label}（オーブ{orb:.1f}度）')
        return arc, contacts

    def prog_moon_contacts(self, natal, prog):
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

    def profection_timeline(self, p, natal, current_age):
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
            rows.append(f"{age}歳({y1}年{p['mo']}月〜{y1+1}年{p['mo']}月): "
                        f"第{ph}ハウス・年主星{RULERS_JP[si]} {mark}".rstrip())
        return rows

    def pmoon_history(self, p, natal, current_age, years=9):
        rows = []
        prev = None
        for k in range(years, -1, -1):
            y = p['y'] + current_age - k
            prog_k = self._api('/api/calculate-progressions',
                               {'birth_year': p['y'], 'birth_month': p['mo'],
                                'birth_day': p['d'], 'birth_hour': p['h'],
                                'birth_minute': p['mi'],
                                'current_date': f"{y}-{p['mo']:02d}-{p['d']:02d}"})
            pm = prog_k['p_moon']
            h = house_of(pm['longitude'], natal['houses']['cusps'])
            elem = ELEM_JP[int(pm['longitude'] // 30) % 4]
            cur = (pm['signJP'], h)
            note = '' if cur == prev else (' ★移動' if prev else '')
            rows.append(f"{y}年{p['mo']}月時点: {pm['signJP']}({elem}={SEASON[elem]}) "
                        f"第{h}ハウス(現実={season_of_house(h)}){note}")
            prev = cur
        return rows

    # ── チャートテキスト ──────────────────────────────────────
    def build_chart_text(self, p, data):
        natal, prog, trans, sr = data['natal'], data['prog'], data['trans'], data['sr']
        current_date = data['current_date']
        sa_arc, sa_contacts = self.solar_arc_contacts(natal, prog)
        t = f"# {p['name']}さんの占星術データ（鑑定用）\n\n## 基本情報\n"
        t += f"- 生年月日: {p['y']}年{p['mo']}月{p['d']}日 {p['h']}時{p['mi']}分\n"
        t += f"- 出生地: {p['place']}\n- 鑑定日: {current_date}\n"
        if p.get('time_estimated'):
            t += "- ※出生時間は推定（時刻依存の断言は控えめに）\n"
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

        cusps = houses['cusps']
        ps_h = house_of(prog['p_sun']['longitude'], cusps)
        pm_h = house_of(prog['p_moon']['longitude'], cusps)
        t += "\n## プログレス（セカンダリー進行図・ハウスは出生図に重ねた在室）\n"
        t += f"- 基準日: {current_date}\n"
        t += f"- プログレス太陽: {prog['p_sun']['signJP']} {fdeg(prog['p_sun']['degree'])} [ネイタル第{ps_h}ハウス]\n"
        t += f"- プログレス月: {prog['p_moon']['signJP']} {fdeg(prog['p_moon']['degree'])} [ネイタル第{pm_h}ハウス]\n"
        t += (f"- 進行の月の季節: 心の季節（サイン）={season_of_sign(prog['p_moon']['longitude'])}、"
              f"現実の季節（ハウス）={season_of_house(pm_h)}\n")
        pmc = self.prog_moon_contacts(natal, prog)
        t += ("- 進行の月が接触中: " + "、".join(pmc) + "\n") if pmc else \
             "- 進行の月が接触中のネイタル天体（オーブ2度以内）: なし\n"

        if isinstance(sr.get('age'), int):
            t += "\n## 進行の月の履歴（計算済み・過去を当てる材料）\n"
            for r in self.pmoon_history(p, natal, sr['age']):
                t += f"- {r}\n"
            t += "\n## プロフェクション年表（計算済み・過去を当てる材料）\n"
            for r in self.profection_timeline(p, natal, sr['age']):
                t += f"- {r}\n"

        elem, mode, erows, eorder = self.element_balance(natal)
        t += "\n## 四大元素バランス（計算済み・体質と気質の章で使うこと）\n"
        t += "- 各点の元素: " + "、".join(erows) + "\n"
        t += ("- 重み付き合計（太陽・月・ASC=3、個人天体=2、社会・外惑星=1）: "
              + "、".join(f"{e}={elem[e]}" for e in ELEM_JP) + "\n")
        t += f"- 優勢な元素: {eorder[0]}（次点: {eorder[1]}） ／ 最も弱い元素: {eorder[-1]}\n"
        t += "- 3区分（同じ重み付け）: " + "、".join(f"{m}={mode[m]}" for m in MODE_JP) + "\n"

        t += "\n## サビアンシンボル（計算済み・検証済み原文）\n"
        t += "※占星術の慣例により、度数表記◯°◯′は「切り上げた度数」のシンボルに正式に対応する（例: 獅子座8°32′→獅子座9度）。\n"
        t += "※以下が各天体の正式なサビアン度数である。本文では「近い度数」「およそ」等と言わず、その天体のサビアンシンボルそのものとして断言し、情景は原文に忠実な日本語で描写すること。\n"
        for key in PJP:
            pl = natal['planets'].get(key)
            if not pl or 'degree' not in pl:
                continue
            d, sym = self.sabian_of(pl['signJP'], pl['degree'])
            t += f"- {PJP[key]}: {pl['signJP']}{d}度 \"{sym}\"\n"
        for label, obj in (('ASC', houses['ascendant']), ('MC', houses['midheaven'])):
            d, sym = self.sabian_of(obj['signJP'], obj['degree'])
            t += f"- {label}: {obj['signJP']}{d}度 \"{sym}\"\n"
        for label, obj in (('進行の太陽', prog['p_sun']), ('進行の月', prog['p_moon'])):
            d, sym = self.sabian_of(obj['signJP'], obj['degree'])
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
            t += f"\n### 外惑星の現在位置（{current_date}時点）\n"
            for key in ('Uranus', 'Neptune', 'Pluto'):
                pl = trans['outer_planets'].get(key)
                if pl:
                    t += f"- {PJP[key]}: {pl['signJP']} {fdeg(pl['degree'])}{' ℞' if pl.get('retrograde') else ''}\n"
        for label, arr in (('木星', trans.get('jupiter_transits')),
                           ('土星', trans.get('saturn_transits'))):
            if arr:
                t += f"\n### {label}のサイン移動（今後3年）\n"
                for tr in arr:
                    t += f"- {tr['date']}: {tr['signJP']}入り\n"
        t += "\n### 日食・月食\n- データ提供なし（言及しないでください）\n"

        sun_house = natal['planets'].get('Sun', {}).get('house')
        sect = None
        if sun_house:
            sect = '昼生まれ' if 7 <= sun_house <= 12 else '夜生まれ'
            t += f"\n## セクト（計算済み・この値をそのまま使うこと）\n- 太陽が第{sun_house}ハウス → {sect}\n"
            pof_lon, pof_sign, pof_deg, pof_h = self.part_of_fortune(natal, sect == '昼生まれ')
            pd_, psym = self.sabian_of(pof_sign, pof_deg)
            t += f"\n## パート・オブ・フォーチュン（計算済み・{sect}式）\n"
            t += f"- {pof_sign} {fdeg(pof_deg)} [第{pof_h}ハウス] サビアン: {pof_sign}{pd_}度 \"{psym}\"\n"
        t += "\n## 主要アスペクト表（計算済み・この表を使い自分で計算しない）\n"
        for r in self.natal_aspects(natal):
            t += f"- {r}\n"

        if isinstance(sr.get('age'), int):
            age = sr['age']
            ph = (age % 12) + 1
            si = int(cusps[ph - 1] // 30)
            t += "\n## プロフェクション（計算済み・この値をそのまま使うこと）\n"
            t += f"- 現在の年齢: {age}歳\n- 起動ハウス: 第{ph}ハウス\n"
            t += f"- 起動サイン: {SIGNS_JP[si]}\n- 年主星（今年、鍵を預かる星）: {RULERS_JP[si]}\n"
            t += f"- 同じ部屋が前回起動した年齢: {age - 12}歳\n"
        if sr.get('planets'):
            t += "\n## ソーラーリターン図（裏取り専用・本文で言及しない）\n"
            t += f"- SR-ASC: {sr['houses']['ascendant']['signJP']} {fdeg(sr['houses']['ascendant']['degree'])}\n"
            t += f"- SR-MC: {sr['houses']['midheaven']['signJP']} {fdeg(sr['houses']['midheaven']['degree'])}\n"
            for key in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'):
                pl = sr['planets'].get(key)
                if not pl or pl.get('error'):
                    continue
                hh = f" [第{pl['house']}ハウス]" if pl.get('house') else ''
                t += f"- {PJP[key]}: {pl['signJP']} {fdeg(pl['degree'])}{hh}\n"

        q = p.get('questions') or {}
        if q.get('future') or q.get('challenge') or q.get('today'):
            t += "\n## ご本人の三つの答え\n"
            if q.get('future'):
                t += f"- ①行きたい未来: {q['future']}\n"
            if q.get('challenge'):
                t += f"- ②いま感じている課題: {q['challenge']}\n"
            if q.get('today'):
                t += f"- ③今日あえて聞いてみたいこと: {q['today']}\n"
        else:
            t += "\n## ご相談\n- 記載なし（「あなたの問いへ」の章は省略し、その分を第5章と第9章に配分）\n"
        t += f"\n---\n{P1_TAIL}\n"
        return t

    # ── 生成 ─────────────────────────────────────────────────
    def _gen_one(self, messages):
        for attempt in range(3):
            try:
                text = ''
                with self.client.messages.stream(
                        model=MODEL, max_tokens=28000,
                        thinking={'type': 'disabled'},
                        system=[{'type': 'text', 'text': self.gem,
                                 'cache_control': {'type': 'ephemeral'}}],
                        messages=messages) as stream:
                    for tk in stream.text_stream:
                        text += tk
                if len(text) >= 4000:
                    return text
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(20)
        raise RuntimeError('generation failed')

    def qa_clean(self, text):
        """偽見出し断片・停止マーカー・メタ発言の除去"""
        text = MARKER.sub('', text)
        # 章順の書き損じ: 見出し直後に(※...)が来る断片を除去
        text = re.sub(r'#+ [^\n]+\n+（※[^）]*）\n+(---\n+)?(続けて[^\n]*執筆いたします。?\n+)?',
                      '', text)
        text = re.sub(r'\n（※[^）]*先に記載[^）]*）\n', '\n', text)
        return text

    def generate(self, person):
        data = self.collect(person)
        chart = self.build_chart_text(person, data)
        messages = [{'role': 'user', 'content': chart}]
        blocks = []
        prompts = [P2, CONT, CONT]
        for i in range(4):
            text = self._gen_one(messages)
            blocks.append(text)
            messages.append({'role': 'assistant', 'content': text})
            if re.search(r'終章[｜|]', text):
                break
            if i < 3:
                messages.append({'role': 'user', 'content': prompts[i]})
        full = '\n\n'.join(b.strip() for b in blocks)
        full = self.qa_clean(full)
        if '終章' not in full:
            raise RuntimeError('終章まで到達しなかった')
        return full, data
