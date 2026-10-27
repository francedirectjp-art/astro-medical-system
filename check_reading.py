#!/usr/bin/env python3
"""鑑定書 納品前検品 (第8版)
使い方: python3 check_reading.py <reading.md | reading.pdf>
PDFは pdftotext があれば自動変換して検品する。
"""
import re, sys, subprocess, os, collections

FORBIDDEN_TERMS = ['ドミサイル','エグザルテーション','トリプリシティ','ペレグリン','デトリメント',
 'フォール','ディスポジター','セクト','コンバスト','アンギュラー','レセプション','オポジション',
 'スクエア','トライン','セクスタイル','プロフェクション','ソーラーリターン','ソーラーアーク',
 'プログレス','トランジット']
COMPLETION = ['繰り返される必要のない','もう変わりました','この循環はここで終わり',
 '変わり終わ','必要のない物語になりました']
HEDGE = ['ではないでしょうか','でしょうか','かもしれません','だと思います','のではないか']
RULERS = {'牡羊座':'火星','牡牛座':'金星','双子座':'水星','蟹座':'月','獅子座':'太陽','乙女座':'水星',
 '天秤座':'金星','蠍座':'火星','射手座':'木星','山羊座':'土星','水瓶座':'土星','魚座':'木星'}
PLANETS = ['太陽','月','水星','金星','火星','木星','土星','天王星','海王星','冥王星']

def load(path):
    if path.lower().endswith('.pdf'):
        out = path + '.txt'
        subprocess.run(['pdftotext','-nopgbrk',path,out], check=True)
        t = open(out, encoding='utf-8').read(); os.remove(out); return t
    return open(path, encoding='utf-8').read()

def main(path):
    raw = load(path)
    flat = raw.replace('\n','')
    fail, warn, ok = [], [], []

    # 1 字数
    n = len(re.sub(r'\s','',raw))
    (ok if n >= 20000 else warn).append(f'総字数 {n:,}字' + ('' if n>=20000 else ' (目安21,000字に不足)'))

    # 2 完了宣言
    hits = [w for w in COMPLETION if w in flat]
    (fail if hits else ok).append('完了宣言: ' + (', '.join(hits) if hits else 'なし'))

    # 3 支配語の誤り「◯◯の支配する△△座」
    bad = []
    for m in re.finditer(r'(' + '|'.join(PLANETS) + r')の支配する(' + '|'.join(RULERS) + r')', flat):
        p, s = m.group(1), m.group(2)
        bad.append(f'「{p}の支配する{s}」' + (f' ← {s}の城主は{RULERS[s]}' if RULERS[s]!=p else ' ← 語順が誤読を招く'))
    (fail if bad else ok).append('支配語: ' + ('; '.join(bad) if bad else '誤りなし'))

    # 4 括弧内否定
    par = re.findall(r'[（(][^）)]{0,30}ではなく[^）)]{0,30}[）)]', flat)
    (fail if par else ok).append('括弧内否定: ' + ('; '.join(par) if par else 'なし'))

    # 5 弱い推量 (章ごと)
    chaps = re.split(r'(はじめに|序章[｜|]|第\d+章[｜|]|中庭[｜|]|終章[｜|]|'
                     r'あなたの問いへ|次の扉|王国の宮廷)', raw)
    counts = {}
    for i in range(1, len(chaps), 2):
        title = chaps[i].strip('｜|')
        body = chaps[i+1] if i+1 < len(chaps) else ''
        # 十本の指について「これまで何本使ってきたか」を断定しないための配慮形は数えない
        #（プロンプト5-0の規定。自信のなさではなく読者の領分を侵さないための節度）
        body_x = re.sub(r'[^。]{0,80}(指|ピアノ)[^。]{0,80}かもしれません。', '', body)
        c = sum(body_x.count(h) for h in ['ではないでしょうか','かもしれません','だと思います'])
        counts[title] = c
    over = {k:v for k,v in counts.items() if v > 1}
    total = sum(flat.count(h) for h in ['ではないでしょうか','かもしれません','だと思います'])
    (fail if over else ok).append(f'弱い推量 合計{total}箇所 / 上限超過の章: ' + (', '.join(f'{k}={v}' for k,v in over.items()) if over else 'なし'))

    # 6 三点セット (存在する章数に連動させる)
    nch = len(set(re.findall(r'第(\d+)章[｜|]', raw)))
    need = min(nch, 10)
    for label, pat in [('星を読まれる方へ','星を読まれる方へ'),('思い当たることはありませんか','思い当たることはありませんか')]:
        cc = flat.count(pat)
        (ok if cc >= need else fail).append(f'{label}: {cc}箇所 / 本文の章数{nch}に対し{need}必要')

    # 7 香り三処方の重複(中心植物の重複を主判定にする)
    flatn = flat.translate(str.maketrans('一二三四五六七八九', '123456789'))
    centers = re.findall(r'([ァ-ヶー・]+)\s*(?:を)?\s*3滴', flatn)
    # 城主と年主星が同一天体なら中心は同じになりうる。全4種が完全一致した場合だけ誤りとする
    recipes = re.findall(r'精油[：:]\s*((?:[ァ-ヶー・]+\d滴[、,]?\s*)+)', flatn)
    norm = [tuple(sorted(re.findall(r'([ァ-ヶー・]+)(\d)滴', r))) for r in recipes]
    dupc = [r for r,k in collections.Counter(norm).items() if k > 1 and r]
    (fail if dupc else ok).append(f'香り: 中心={centers} / 処方{len(recipes)}件 ' +
        (f'← 完全同一の配合が{len(dupc)}組' if dupc else '(完全同一なし)'))

    # 8 禁止術語 (巻末資料は技術資料なので対象外)
    body = flat.split('巻末資料')[0]
    t = [w for w in FORBIDDEN_TERMS if w in body]
    (fail if t else ok).append('禁止術語: ' + (', '.join(t) if t else 'なし'))

    # 9 メタ発言・偽見出しの断片
    meta = re.findall(r'[（(]※[^）)]{0,40}[）)]|申し訳(?:ありません|ございません)|先ほどの章|'
                      r'章を書き直|訂正します|以下に書き直|失礼しました', flat)
    (fail if meta else ok).append('メタ発言: ' + ('; '.join(meta[:3]) if meta else 'なし'))

    # 9b 停止案内・便の継ぎ目の漏れ
    seam = re.findall(r'[（(]『?(?:はい|続けて)[^）)]{0,40}[）)]|\*\*【', flat)
    (fail if seam else ok).append('停止案内/書式の漏れ: ' + (f'{len(seam)}箇所 {seam[:2]}' if seam else 'なし'))

    # 9c 本文の太字
    bold = re.findall(r'\*\*[^*\n]{1,40}\*\*', raw)
    (fail if bold else ok).append('本文の太字: ' + (f'{len(bold)}箇所 {bold[:2]}' if bold else 'なし'))

    # 10 次の扉に売り込みが混入していないか
    m = re.search(r'次の扉(.{0,1200})', flat, re.S)
    if m:
        seg = m.group(1)
        sell = re.findall(r'https?://|\d{1,2}月\d{1,2}日|\d+[,，]?\d*円|お申し込み|募集|定員|期限', seg)
        (fail if sell else ok).append('次の扉の売り込み混入: ' + ('; '.join(sell) if sell else 'なし'))
    else:
        warn.append('次の扉: 見つからない')

    # 11 記入欄
    blanks = len(re.findall(r'[（(]\s{4,}[）)]|（　+）', raw))
    if path.lower().endswith('.pdf'):
        warn.append(f'記入欄: PDFでは罫線に変換されるため判定不可（原稿mdで確認すること）')
    else:
        (ok if blanks >= 5 else fail).append(f'記入欄: {blanks}箇所 (最低5必要)')

    # 12 本文とチャートデータの整合（第8版で最も効く検品。形式ではなく中身を見る）
    chart_path = os.environ.get('CHART_TXT')
    if chart_path and os.path.exists(chart_path):
        ct = open(chart_path, encoding='utf-8').read()
        issues = []

        # 天体の在室ハウスが本文と食い違っていないか
        natal = ct.split('### 天体の配置')[-1].split('### アングル')[0]
        houses = {m.group(1): int(m.group(2))
                  for m in re.finditer(r'^- (\S+?): \S+?座 \d+°\d+′.*?\[第(\d+)ハウス\]', natal, re.M)}
        PLN = '太陽|月|水星|金星|火星|木星|土星|天王星|海王星|冥王星|ドラゴンヘッド|キローン'
        # 「第Nハウス」ごとに、直前で最も近い天体名を主語とみなして照合する
        seen = set()
        for m in re.finditer(r'第(\d+)ハウス', flat):
            head = flat[max(0, m.start() - 30):m.start()]
            cands = list(re.finditer(PLN, head))
            if not cands:
                continue
            last = cands[-1]
            pl = last.group(0)
            # 進行・トランジット・SRの天体はネイタルと比較しない
            # 指示語で受ける文（「この月が」等）は、さらに前方まで遡って主語を判定する
            # プロフェクション文脈(今年/年/月から月にかけて)はネイタルの在室ではない
            near = flat[max(0, m.start() - 60):m.start()]
            if re.search(r'今年|年\d+月|にかけて|灯りがついて|起動', near):
                continue
            wide = flat[max(0, m.start() - 220):m.start()]
            if re.search(r'(進行|プログレス|ソーラー|SR|今の空|トランジット)', wide[-120:]) \
               and re.search(r'(この|その)' + re.escape(pl), head):
                continue
            ctx = head[max(0, last.start() - 8):]
            if re.search(r'進行|プログレス|ソーラー|SR|今の空|移動し|入り', ctx):
                continue
            if pl in seen or pl not in houses:
                continue
            if int(m.group(1)) != houses[pl]:
                issues.append(f'{pl}は第{houses[pl]}ハウス。本文に第{m.group(1)}ハウスの記述')
                seen.add(pl)

        # 進行の月・太陽の在室ハウス
        for label, pat in [('進行の月', r'プログレス月: \S+? \d+°\d+′\s*［?\[?ネイタル第(\d+)ハウス'),
                           ('進行の太陽', r'プログレス太陽: \S+? \d+°\d+′\s*［?\[?ネイタル第(\d+)ハウス')]:
            mm = re.search(pat, ct)
            if mm:
                h = int(mm.group(1))
                other = '進行の太陽' if label == '進行の月' else '進行の月'
                for m in re.finditer(re.escape(label) + r'((?:(?!' + re.escape(other) + r').){0,30}?)第(\d+)ハウス', flat):
                    if int(m.group(2)) != h:
                        issues.append(f'{label}はネイタル第{h}ハウス。本文に第{m.group(2)}ハウスの記述')
                        break

        # 今年のプロフェクション（年齢と部屋）
        pf = ct.split('## プロフェクション（計算済み')[-1]
        ma = re.search(r'現在の年齢: (\d+)歳', pf)
        mh = re.search(r'起動ハウス: 第(\d+)ハウス', pf)
        if ma and mh:
            age, ph = int(ma.group(1)), int(mh.group(1))
            for m in re.finditer(r'(\d+)歳[^。]{0,30}?(?:から)?[^。]{0,20}?今[^。]{0,20}?まで', flat):
                if int(m.group(1)) != age:
                    issues.append(f'今年は{age}歳。本文に「{m.group(1)}歳から今まで」型の記述')
                    break
            mm = re.search(r'今年[^。]{0,24}?第(\d+)ハウス', flat)
            if mm and int(mm.group(1)) != ph:
                issues.append(f'今年の部屋は第{ph}ハウス。本文に第{mm.group(1)}ハウスの記述')

        # 1度以内のトランジット接触が本文で未来形にされていないか
        # 神話版・庭版では天体を別名で呼ぶ。別名も言及とみなす
        ALIAS = {'太陽': ['アポロン', '主木'], '月': ['アルテミス'], '水星': ['ヘルメス', '風と蜂'],
                 '金星': ['アフロディーテ'], '火星': ['アレス', '鍬'], '木星': ['ゼウス', '実り'],
                 '土星': ['クロノス', '支柱'], '天王星': ['ウラノス'], '海王星': ['ポセイドン', '朝霧'],
                 '冥王星': ['ハデス']}
        def _named(p):
            return p in flat or any(a in flat for a in ALIAS.get(p, []))
        for m in re.finditer(r'T(\S+?) → N(\S+?): (\S+?)（オーブ([\d.]+)度）★', ct):
            t1, t2 = m.group(1), m.group(2)
            if _named(t1) and _named(t2):
                seg = re.search(r'[^。]{0,60}' + re.escape(t1) + r'[^。]{0,60}' + re.escape(t2) + r'[^。]{0,60}。', flat)
                if seg and re.search(r'やがて|いずれ(?!も|に[せし])|数年のうちに|これから訪れ|近いうちに', seg.group(0)):
                    issues.append(f'T{t1}→N{t2}はオーブ{m.group(4)}度（すでに接触中）。本文が未来形')
            elif not _named(t1):
                issues.append(f'T{t1}→N{t2}がオーブ{m.group(4)}度で接触中だが、本文に{t1}の言及なし')

        (fail if issues else ok).append('本文とデータの整合: ' +
            (f'{len(issues)}件の食い違い ／ ' + ' ／ '.join(issues[:4]) if issues else '食い違いなし'))
    else:
        warn.append('本文とデータの整合: CHART_TXT 未指定のため検査せず')

    # 13 サビアンの転換文（型と個別性の区切り）
    nsab = len(set(re.findall(r'第(\d+)章[｜|]', raw)))
    trans = len(re.findall(r'どなたにも当てはま|同じ配置|あなたの度数だけ|ここからが、あなただけのもの', flat))
    (fail if trans < 4 else ok).append(f'サビアンの転換文: {trans}箇所（絵を出す章ごとに必要。最低4）')

    # 14 天体名の破損（後処理の置換事故を検出する）
    broken = re.findall(r'[天海冥][ァ-ヶ]{2,6}星|[ァ-ヶ]{2,6}王星(?!)', flat)
    broken = [b for b in set(broken) if b not in ('天王星', '海王星', '冥王星')]
    (fail if broken else ok).append('天体名の破損: ' + (', '.join(broken) if broken else 'なし'))

    # 出力
    print(f'\n=== 検品: {os.path.basename(path)} ===\n')
    for label, items, mark in [('NG', fail, '✗'), ('要確認', warn, '!'), ('OK', ok, '✓')]:
        for it in items:
            print(f'  {mark} {it}')
    print(f'\n判定: ' + ('不合格 (NG %d件)' % len(fail) if fail else '合格'))
    return 1 if fail else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
