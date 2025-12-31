#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開運言霊占星術師 - プロンプト生成エンジン
鑑定証用のプロンプトを生成
"""


def generate_fortune_prompt(fortune_data):
    """開運アドバイス用の完全なプロンプトを生成（3000文字程度）"""
    
    natal = fortune_data['natal']
    progression = fortune_data['progression']
    transits = fortune_data['transits']
    solar_return = fortune_data['solar_return']
    
    # 各データを取得
    sun = natal['sun']
    sun_house = sun.get('house', 1)
    
    prog_sun = progression['progressed_sun']
    prog_moon = progression['progressed_moon']
    moon_phase = progression['moon_phase']
    moon_phase_desc = progression['moon_phase_desc']
    
    jupiter = transits['jupiter_now']
    jupiter_house = natal['jupiter'].get('house', 1)
    jupiter_movements = transits['jupiter_movements']
    
    saturn = transits['saturn_now']
    saturn_house = natal['saturn'].get('house', 1)
    
    true_node = natal['true_node']
    node_house = true_node.get('house', 1)
    
    sr_asc = solar_return['ascendant']
    
    # 木星の移動予測テキスト生成
    jupiter_future_text = ""
    if jupiter_movements:
        jupiter_future_text = f"さらに、{jupiter_movements[0]['date']}頃には{jupiter_movements[0]['sign_jp']}へ移動し、"
    
    # プロンプトを生成
    prompt = f"""# 役割
あなたは、クライアントの魂の輝きを見抜き、言葉の力（言霊）によって人生を好転させる「開運言霊占星術師」です。
西洋占星術のロジックに基づきながらも、単なる吉凶判断にとどまらず、読むだけで運気が上がり、行動したくなるような「鑑定証（3000文字程度）」を作成してください。

# ターゲット読者
自分の人生をより良くしたい、運気の波に乗りたいと願っている前向きな個人。

# 入力データ（占星術パラメーター）
以下の占星術パラメーターを元に鑑定します：

1. **ネイタル太陽（本質）**: {sun['sign_jp']} {sun['degree']:.1f}度・第{sun_house}ハウス
2. **プログレスの太陽・月（現在のバイオリズム）**: 
   - P太陽: {prog_sun['sign_jp']} {prog_sun['degree']:.1f}度
   - P月: {prog_moon['sign_jp']} {prog_moon['degree']:.1f}度
   - 月のフェーズ: {moon_phase}（{moon_phase_desc}）
3. **トランジット木星（拡大・発展）**: {jupiter['sign_jp']} {jupiter['degree']:.1f}度・第{jupiter_house}ハウス
   {jupiter_future_text}新たなステージへと進みます。
4. **トランジット土星（課題・調整）**: {saturn['sign_jp']} {saturn['degree']:.1f}度・第{saturn_house}ハウス
5. **ドラゴンヘッド（魂の使命・ご縁）**: {true_node['sign_jp']} {true_node['degree']:.1f}度・第{node_house}ハウス
6. **ソーラーリターンASC（今年のテーマ）**: {sr_asc['sign_jp']} {sr_asc['degree']:.1f}度

# 記事の構成と執筆ルール
以下の6つのセクションで構成し、合計3000文字程度で執筆してください。各セクションにはキャッチーな見出しをつけてください。

## 1. 魂の季節：現在のバイオリズム（約500文字）
* **参照:** プログレスの太陽・月（P太陽: {prog_sun['sign_jp']}、P月: {prog_moon['sign_jp']}、月相: {moon_phase}）
* **内容:** 今が人生のどのような季節（種まき、開花、収穫、土作りなど）にあるかを解説し、焦らずその時期を楽しむための心構えを説いてください。
* **トーン:** 寄り添うような優しさ。

## 2. あなたという光：本質の再確認（約500文字）
* **参照:** ネイタル太陽（{sun['sign_jp']} 第{sun_house}ハウス）
* **内容:** クライアントが生まれ持った「輝き」や「強み」を肯定的に描写してください。
* **言霊:** 「あなたは本来、〇〇な光を持った人です」と断定し、自信を持たせてください。

## 3. 幸運の追い風：木星からのギフト（約600文字）
* **参照:** トランジット木星（{jupiter['sign_jp']} 第{jupiter_house}ハウス）
* **内容:** 今年の最大のチャンスがどこにあるか、具体的にどのような行動（自己表現、リーダーシップなど）が運を開くかを情熱的に語ってください。
* **言霊:** 背中を強く押すような力強い言葉。

## 4. 魂の磨き方：土星の試練と成長（約500文字）
* **参照:** トランジット土星（{saturn['sign_jp']} 第{saturn_house}ハウス）
* **内容:** 今感じている重圧や課題は「不運」ではなく「土台固め」であることを伝えてください。具体的に何をメンテナンスすべきかアドバイスします。
* **トーン:** 冷静かつ誠実なアドバイス。

## 5. 運命の鍵：ご縁と今年のテーマ（約500文字）
* **参照:** ドラゴンヘッド（{true_node['sign_jp']} 第{node_house}ハウス）、ソーラーリターンASC（{sr_asc['sign_jp']}）
* **内容:** どのような人や環境との関わりが魂の成長を促すか、そして今年1年をどのような「スタンス（衣装）」で過ごすべきかを示します。

## 6. 開運の言霊（まとめ）（約400文字）
* **内容:** 全体を総括し、この鑑定証を読み終えた瞬間から人生が変わるような、短く強力なアファメーション（肯定的な宣言）を贈ってください。

# 表現のトーン＆マナー（重要）
* **「言霊」を意識する:** 否定的な言葉は使わず、すべての星の配置を「成長のためのギフト」として解釈してください。
* **リズム感:** 読み手が心地よく読めるよう、体言止めや問いかけを交え、情緒的な文章にしてください。
* **専門用語:** 星座や惑星の名前は出して構いませんが、専門知識がない人にもイメージが伝わる比喩を使って解説してください（例：「土星先生が宿題を出しています」など）。
* **一人称:** 「私（占星術師）」
* **二人称:** 「あなた」

# 出力形式
Markdown形式で見出しをつけて出力してください。

---

上記の情報を元に、魂を揺さぶる3000文字の開運鑑定証を作成してください。
"""
    
    return prompt


def generate_simple_summary(fortune_data):
    """シンプルな要約テキストを生成"""
    
    natal = fortune_data['natal']
    progression = fortune_data['progression']
    transits = fortune_data['transits']
    solar_return = fortune_data['solar_return']
    birth_info = fortune_data['birth_info']
    
    sun = natal['sun']
    prog_sun = progression['progressed_sun']
    prog_moon = progression['progressed_moon']
    jupiter = transits['jupiter_now']
    saturn = transits['saturn_now']
    true_node = natal['true_node']
    sr_asc = solar_return['ascendant']
    
    summary = f"""
【開運言霊占星術 - 鑑定データ】

◆ 基本情報
生年月日: {birth_info['year']}年{birth_info['month']}月{birth_info['day']}日
出生時刻: {birth_info['hour']}時{birth_info['minute']}分
出生地: {birth_info['prefecture']}

◆ あなたの本質（ネイタル太陽）
{sun['formatted']} - 第{sun.get('house', '?')}ハウス
→ 生まれ持った魂の輝き、人生の目的

◆ 現在のバイオリズム（プログレッション）
P太陽: {prog_sun['formatted']}
P月: {prog_moon['formatted']}
月相: {progression['moon_phase']} - {progression['moon_phase_desc']}
→ 今、人生のどの季節にいるか

◆ 幸運の追い風（木星）
{jupiter['formatted']} - 第{natal['jupiter'].get('house', '?')}ハウス
→ 最大のチャンスがある分野

◆ 魂の磨き方（土星）
{saturn['formatted']} - 第{natal['saturn'].get('house', '?')}ハウス
→ 課題と成長のテーマ

◆ 運命の鍵（ドラゴンヘッド）
{true_node['formatted']} - 第{true_node.get('house', '?')}ハウス
→ 魂の使命と引き寄せるご縁

◆ 今年のテーマ（ソーラーリターンASC）
{sr_asc['formatted']}
→ この1年をどう過ごすべきか

---

このデータを元に、開運言霊占星術師としての鑑定証（3000文字）を生成してください。
"""
    
    return summary


if __name__ == "__main__":
    # テスト実行
    from fortune_calculator import calculate_full_fortune_data
    
    print("=== プロンプト生成テスト ===\n")
    
    result = calculate_full_fortune_data(1990, 5, 15, 10, 30, '東京都')
    prompt = generate_fortune_prompt(result)
    
    print(prompt)
    print("\n" + "="*50)
    print("\n【要約版】\n")
    print(generate_simple_summary(result))
