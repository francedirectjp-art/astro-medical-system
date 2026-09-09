# -*- coding: utf-8 -*-
"""自動鑑定書ワーカー

MyASPシナリオ(星の鑑定書)の新規登録者をポーリングし、
第7版の鑑定書を生成→PDF化→トークンURLで公開→MyASPの自由項目(free10)に書き戻す。
ステップメール(登録30分後)が %free10% を差し込んで配信する。

有効化: 環境変数 AUTO_READING=1, MYASP_API_KEY, ANTHROPIC_API_KEY
"""
import json
import os
import re
import secrets
import threading
import time
import traceback
from datetime import datetime

SCENARIO_ID = os.environ.get('AUTO_READING_SCENARIO', 'N2hq9AJ5')
POLL_SEC = int(os.environ.get('AUTO_READING_POLL_SEC', '180'))
STORE = os.environ.get('READING_STORE',
                       os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'generated_readings'))
PUBLIC_BASE = os.environ.get('PUBLIC_BASE_URL',
                             'https://grand-vision-production-48ec.up.railway.app')

PREFECTURES = {
    '北海道': (43.0642, 141.3469), '青森県': (40.8244, 140.7400), '岩手県': (39.7036, 141.1527),
    '宮城県': (38.2682, 140.8721), '秋田県': (39.7186, 140.1022), '山形県': (38.2404, 140.3633),
    '福島県': (37.7503, 140.4677), '茨城県': (36.3418, 140.4468), '栃木県': (36.5658, 139.8836),
    '群馬県': (36.3906, 139.0608), '埼玉県': (35.8617, 139.6455), '千葉県': (35.6074, 140.1065),
    '東京都': (35.6762, 139.6503), '神奈川県': (35.4478, 139.6425), '新潟県': (37.9026, 139.0232),
    '富山県': (36.6959, 137.2137), '石川県': (36.5946, 136.6256), '福井県': (36.0652, 136.2216),
    '山梨県': (35.6642, 138.5681), '長野県': (36.6513, 138.1809), '岐阜県': (35.3912, 136.7223),
    '静岡県': (34.9756, 138.3827), '愛知県': (35.1802, 136.9066), '三重県': (34.7302, 136.5086),
    '滋賀県': (35.0045, 135.8686), '京都府': (35.0211, 135.7556), '大阪府': (34.6937, 135.5023),
    '兵庫県': (34.6913, 135.1830), '奈良県': (34.6851, 135.8048), '和歌山県': (34.2261, 135.1675),
    '鳥取県': (35.5038, 134.2378), '島根県': (35.4723, 133.0505), '岡山県': (34.6618, 133.9346),
    '広島県': (34.3963, 132.4596), '山口県': (34.1861, 131.4707), '徳島県': (34.0658, 134.5593),
    '香川県': (34.3401, 134.0430), '愛媛県': (33.8416, 132.7658), '高知県': (33.5597, 133.5311),
    '福岡県': (33.6064, 130.4181), '佐賀県': (33.2494, 130.2989), '長崎県': (32.7503, 129.8779),
    '熊本県': (32.7898, 130.7417), '大分県': (33.2382, 131.6126), '宮崎県': (31.9077, 131.4202),
    '鹿児島県': (31.5602, 130.5581), '沖縄県': (26.2124, 127.6792),
}


# 主要市区町村→都道府県(フォームに県名が無い場合の解決用)
CITY2PREF = {
    '札幌': '北海道', '旭川': '北海道', '函館': '北海道',
    '仙台': '宮城県', '青森': '青森県', '盛岡': '岩手県', '秋田': '秋田県',
    '山形': '山形県', '福島': '福島県', '郡山': '福島県',
    'さいたま': '埼玉県', '川口': '埼玉県', '八潮': '埼玉県', '川越': '埼玉県', '所沢': '埼玉県',
    '千葉': '千葉県', '船橋': '千葉県', '柏': '千葉県', '松戸': '千葉県',
    '横浜': '神奈川県', '川崎': '神奈川県', '相模原': '神奈川県', '藤沢': '神奈川県',
    '新潟': '新潟県', '富山': '富山県', '金沢': '石川県', '穴水': '石川県', '鳳珠': '石川県',
    '輪島': '石川県', '七尾': '石川県', '福井': '福井県', '甲府': '山梨県', '長野': '長野県',
    '松本': '長野県', '岐阜': '岐阜県', '静岡': '静岡県', '浜松': '静岡県',
    '名古屋': '愛知県', '豊田': '愛知県', '岡崎': '愛知県', '津': '三重県', '四日市': '三重県',
    '大津': '滋賀県', '京都': '京都府', '大阪': '大阪府', '堺': '大阪府', '大東': '大阪府',
    '東大阪': '大阪府', '豊中': '大阪府', '吹田': '大阪府', '枚方': '大阪府',
    '神戸': '兵庫県', '姫路': '兵庫県', '西宮': '兵庫県', '尼崎': '兵庫県',
    '奈良': '奈良県', '和歌山': '和歌山県', '鳥取': '鳥取県', '松江': '島根県', '出雲': '島根県',
    '岡山': '岡山県', '倉敷': '岡山県', '広島': '広島県', '福山': '広島県',
    '下関': '山口県', '徳島': '徳島県', '高松': '香川県', '土庄': '香川県', '小豆': '香川県',
    '松山': '愛媛県', '高知': '高知県',
    '福岡': '福岡県', '北九州': '福岡県', '久留米': '福岡県',
    '佐賀': '佐賀県', '長崎': '長崎県', '佐世保': '長崎県', '熊本': '熊本県',
    '大分': '大分県', '宮崎': '宮崎県', '鹿児島': '鹿児島県', '鹿屋': '鹿児島県',
    '那覇': '沖縄県', '宮古島': '沖縄県', '石垣': '沖縄県',
    '世田谷': '東京都', '杉並': '東京都', '中野': '東京都', '江戸川': '東京都', '八王子': '東京都',
}


def resolve_pref(city_text):
    """自由記述の出生地から都道府県を推定"""
    t = (city_text or '').strip()
    for p in PREFECTURES:
        if p in t or p.rstrip('都道府県') in t[:4]:
            if p in t:
                return p
    for p in PREFECTURES:
        if p in t:
            return p
    # 「大阪」「兵庫」のような県名の省略形
    for p in PREFECTURES:
        short = p.rstrip('都道府県')
        if t.startswith(short):
            return p
    for city, p in CITY2PREF.items():
        if city in t:
            return p
    return None


def log(msg):
    print(f"[auto-reading {datetime.now():%H:%M:%S}] {msg}", flush=True)


def parse_birth(raw):
    """'1979.8.1' '1979-08-01' '19790801' '1979年8月1日' → (y, m, d)"""
    s = str(raw).strip()
    m = re.search(r'(19|20)(\d{2})[年./\-]\s*(\d{1,2})[月./\-]\s*(\d{1,2})', s)
    if m:
        return int(m.group(1) + m.group(2)), int(m.group(3)), int(m.group(4))
    m = re.fullmatch(r'((?:19|20)\d{2})(\d{2})(\d{2})', re.sub(r'\D', '', s))
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    raise ValueError(f'生年月日を解釈できない: {raw!r}')


def parse_time(raw):
    """'18:04' '1804' '18時4分' '朝' '不明' → (h, m, estimated)"""
    s = str(raw or '').strip()
    m = re.search(r'(\d{1,2})[:：時]\s*(\d{1,2})?', s)
    if m:
        h = int(m.group(1))
        mi = int(m.group(2) or 0)
        approx = ('頃' in s) or ('ごろ' in s) or ('約' in s)
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h, mi, approx
    digits = re.sub(r'\D', '', s)
    if len(digits) in (3, 4):
        h, mi = int(digits[:-2]), int(digits[-2:])
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h, mi, False
    for word, hh in (('朝', 7), ('午前', 9), ('昼', 12), ('午後', 15),
                     ('夕', 17), ('夜', 21), ('深夜', 0)):
        if word in s:
            return hh, 0, True
    return 12, 0, True  # 不明


class Worker:
    def __init__(self, flask_app):
        from anthropic import Anthropic
        from myasp_mcp import MyASP
        from reading_engine import ReadingEngine
        self.app = flask_app
        self.engine = ReadingEngine(flask_app, Anthropic())
        self.MyASP = MyASP
        os.makedirs(STORE, exist_ok=True)
        self.state_path = os.path.join(STORE, '_state.json')
        self.state = {}
        if os.path.exists(self.state_path):
            try:
                self.state = json.load(open(self.state_path, encoding='utf-8'))
            except Exception:  # noqa: BLE001
                self.state = {}
        # 再デプロイ時は失敗マークを掃除して再挑戦させる
        for k in list(self.state):
            v = self.state[k]
            if k.startswith('fail_') or (isinstance(v, dict) and v.get('token') in ('failed', 'external')):
                del self.state[k]

    def _save_state(self):
        json.dump(self.state, open(self.state_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=0)

    def _person_from_subscriber(self, sub):
        free = sub.get('free_fields') or []
        if isinstance(free, dict):
            fmap = {k: (v.get('value') if isinstance(v, dict) else v) for k, v in free.items()}
        else:
            fmap = {it.get('field_key'): it.get('value') for it in free if isinstance(it, dict)}
        def fv(k):
            v = fmap.get(k)
            return v.strip() if isinstance(v, str) else (v or '')
        name = f"{sub.get('name1') or ''}{sub.get('name2') or ''}".strip() or 'お客'
        y, mo, d = parse_birth(fv('free1'))
        h, mi, approx = parse_time(fv('free2'))
        pref = (sub.get('pref') or '').lstrip('*')
        city = fv('free3')
        if pref not in PREFECTURES:
            pref = resolve_pref(city) or '東京都'
        lat, lon = PREFECTURES[pref]
        place = f"{pref}{city}" if city and not city.startswith(pref) else (city or pref)
        return {
            'name': name, 'y': y, 'mo': mo, 'd': d, 'h': h, 'mi': mi,
            'lat': lat, 'lon': lon, 'pref': pref, 'place': place,
            'time_estimated': approx or '不明' in str(fv('free2')),
            'questions': {'future': fv('free4'), 'challenge': fv('free5'),
                          'today': fv('free6')},
        }

    def process_one(self, sub, token=None):
        sid = str(sub.get('subscriber_id') or sub.get('id'))
        person = self._person_from_subscriber(sub)
        log(f"生成開始: {sid} {person['name']} ({person['y']}-{person['mo']}-{person['d']}) pref={person['pref']}")
        reading_md, data = self.engine.generate(person)
        token = token or secrets.token_urlsafe(16)
        pdf_path = os.path.join(STORE, f'{token}.pdf')
        from reading_pdf import build_pdf
        build_pdf(person, reading_md, data, pdf_path)
        with open(os.path.join(STORE, f'{token}.md'), 'w', encoding='utf-8') as f:
            f.write(reading_md)
        url = f'{PUBLIC_BASE}/r/{token}.pdf'
        my = self.MyASP().connect()
        my.call('update_subscriber',
                {'subscriber_id': sid,
                 'free_fields': [{'field_key': 'free10', 'value': url}]})
        self.state[sid] = {'token': token, 'done': time.time(), 'name': person['name']}
        self._save_state()
        log(f"完了: {sid} → {url} ({len(reading_md)}字)")

    def cycle(self):
        log('cycle: connect')
        my = self.MyASP().connect()
        log('cycle: search')
        res = my.call('search_subscribers',
                      {'scenario_id': SCENARIO_ID, 'limit': 50})
        subs = res.get('subscribers') if isinstance(res, dict) else res
        subs = subs or []
        log(f'cycle: {len(subs)}件 / state={list(self.state)[:5]}')
        for sub in subs:
            sid = str(sub.get('subscriber_id') or sub.get('id'))
            ent = self.state.get(sid)
            prev_token = ent.get('token') if isinstance(ent, dict) else None
            if prev_token in ('external', 'failed'):
                prev_token = None
            # 一覧のfree_fieldsで判定(空なら再処理=同トークン上書き)
            free = sub.get('free_fields') or []
            fmap = {it.get('field_key'): it.get('value') for it in free if isinstance(it, dict)}
            if fmap.get('free10'):
                if not isinstance(ent, dict):
                    self.state[sid] = {'token': 'external', 'done': time.time()}
                    self._save_state()
                continue
            detail = my.call('get_subscriber_details', {'subscriber_id': sid})
            try:
                self.process_one(detail, token=prev_token)
            except Exception as e:  # noqa: BLE001
                log(f"ERROR {sid}: {e}\n{traceback.format_exc()[:500]}")
                fails = self.state.get(f'fail_{sid}', 0)
                if isinstance(fails, dict):
                    fails = fails.get('n', 0)
                self.state[f'fail_{sid}'] = fails + 1 if isinstance(fails, int) else 1
                if isinstance(fails, int) and fails + 1 >= 3:
                    self.state[sid] = {'token': 'failed', 'done': time.time()}
                self._save_state()

    def run_forever(self):
        log(f"worker start: scenario={SCENARIO_ID} poll={POLL_SEC}s store={STORE}")
        while True:
            try:
                self.cycle()
            except Exception as e:  # noqa: BLE001
                log(f"cycle error: {e}")
            time.sleep(POLL_SEC)


def start_worker(flask_app):
    if os.environ.get('AUTO_READING') != '1':
        return None
    if not os.environ.get('MYASP_API_KEY') or not os.environ.get('ANTHROPIC_API_KEY'):
        log('AUTO_READING=1 だが MYASP_API_KEY / ANTHROPIC_API_KEY が無いため起動しない')
        return None
    w = Worker(flask_app)
    t = threading.Thread(target=w.run_forever, daemon=True, name='auto-reading')
    t.start()
    return t
