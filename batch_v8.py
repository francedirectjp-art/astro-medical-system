#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MyASP登録者を指定して、第8版の鑑定書を一括生成しPDFまで作る。
  使い方: python3 batch_v8.py "戸澤 麻理" "島村 拓史" ...
"""
import json, os, re, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from myasp_mcp import MyASP
import auto_reading_worker as W

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT_DIR', '/tmp/reading_v8')
SCENARIO = 'N2hq9AJ5'
os.makedirs(OUT, exist_ok=True)


def norm(s):
    return unicodedata.normalize('NFKC', (s or '')).replace(' ', '').replace('　', '')


PREFS = ['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県',
         '埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県',
         '岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県',
         '鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県',
         '佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']


def ai_pref(place):
    """表に無い地名はHaikuで都道府県を判定する(黙って東京都にしない)"""
    if not place:
        print('  ! 出生地が空 → 東京都で計算')
        return '東京都'
    try:
        from anthropic import Anthropic
        r = Anthropic().messages.create(
            model='claude-haiku-4-5-20251001', max_tokens=20,
            messages=[{'role': 'user',
                       'content': f'「{place}」は日本のどの都道府県ですか。都道府県名だけを答えてください。'}])
        a = r.content[0].text.strip()
        for p in PREFS:
            if p in a:
                print(f'  ! 表に無い地名「{place}」→ AI判定で {p}')
                return p
    except Exception as e:
        print('  ! AI判定失敗:', str(e)[:80])
    print(f'  !! 「{place}」の都道府県を特定できず → 東京都で計算(要確認)')
    return '東京都'


def person_from(sub):
    ff = {f['field_key']: (f.get('value') or '').strip()
          for f in sub.get('free_fields', []) if isinstance(f, dict)}
    y, mo, d = W.parse_birth(ff.get('free1', ''))
    h, mi, _approx = W.parse_time(ff.get("free2", ""))
    place = ff.get('free3', '')
    pref = W.resolve_pref(place) or ai_pref(place)
    lat, lon = W.PREFECTURES.get(pref, (35.6895, 139.6917))
    name = norm(sub.get('name', ''))
    return {'slug': re.sub(r'\W', '', sub['subscriber_id']), 'name': name,
            'y': y, 'mo': mo, 'd': d, 'h': h, 'mi': mi,
            'lat': lat, 'lon': lon, 'pref': pref,
            'place': place or pref, 'gender': '', 'consult': '',
            'questions': {'future': ff.get('free4', ''),
                          'challenge': ff.get('free5', ''),
                          'today': ff.get('free6', '')}}


def main(targets):
    m = MyASP().connect()
    subs = m.call('search_subscribers', {'scenario_id': SCENARIO})
    subs = subs if isinstance(subs, list) else (subs.get('subscribers') or [])
    want = [norm(t) for t in targets]
    picked = []
    for w in want:
        hit = [s for s in subs if norm(s.get('name', '')) == w]
        if not hit:
            hit = [s for s in subs if w in norm(s.get('name', ''))]
        if not hit:
            print(f'!! 該当なし: {w}')
            continue
        if len(hit) > 1:
            print(f'!! 複数一致({len(hit)}件): {w} → ' +
                  ', '.join(f"{s['subscriber_id']}/{s.get('email')}" for s in hit))
            continue
        full = m.call('get_subscriber_details',
                      {'scenario_id': SCENARIO, 'subscriber_id': hit[0]['subscriber_id']})
        picked.append(full)
    if len(picked) != len(targets):
        print(f'\n確定 {len(picked)}/{len(targets)} 名。中止します。')
        return 1
    print('\n=== 対象 ===')
    for s in picked:
        p = person_from(s)
        print(f"{p['name']:10} {p['y']}-{p['mo']:02d}-{p['d']:02d} {p['h']:02d}:{p['mi']:02d} "
              f"{p['place']} → {p['pref']}  ({s.get('email')})")
    print()
    for s in picked:
        p = person_from(s)
        pj = f"{OUT}/{p['slug']}.person.json"
        json.dump(p, open(pj, 'w', encoding='utf-8'), ensure_ascii=False)
        env = dict(os.environ, PERSON_JSON=pj, DIR_OVERRIDE=OUT)
        print(f"--- 生成開始: {p['name']}", flush=True)
        r = subprocess.run([f'{BASE}/.venv/bin/python3', f'{BASE}/gen_v8.py'],
                           env=env, cwd=BASE, capture_output=True, text=True)
        print(r.stdout[-400:] or r.stderr[-400:], flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
