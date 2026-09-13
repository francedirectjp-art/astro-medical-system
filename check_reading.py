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
    chaps = re.split(r'(序章[｜|]|第\d+章[｜|]|終章[｜|]|あなたの問いへ)', raw)
    counts = {}
    for i in range(1, len(chaps), 2):
        title = chaps[i].strip('｜|')
        body = chaps[i+1] if i+1 < len(chaps) else ''
        c = sum(body.count(h) for h in ['ではないでしょうか','かもしれません','だと思います'])
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
    meta = re.findall(r'[（(]※[^）)]{0,40}[）)]|申し訳|先ほどの章|書き直し|訂正します', flat)
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

    # 出力
    print(f'\n=== 検品: {os.path.basename(path)} ===\n')
    for label, items, mark in [('NG', fail, '✗'), ('要確認', warn, '!'), ('OK', ok, '✓')]:
        for it in items:
            print(f'  {mark} {it}')
    print(f'\n判定: ' + ('不合格 (NG %d件)' % len(fail) if fail else '合格'))
    return 1 if fail else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
