#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
360個のサビアンシンボルデータを生成
"""
import json

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']

# サンプルのサビアンシンボル（実際の度数に対応）
SABIAN_SAMPLES = {
    "Aries": [
        "女性が水から上がり、アザラシも上がり彼女を抱く",
        "グループを楽しませているコメディアン",
        "彼の祖国の形をした男の横顔の浮き彫り",
        "隔離された歩道を歩く二人の恋人",
        "羽のある三角",
        "一つの正方形の各辺から延びる天頂の形",
        "魂の表現の機会を求めている二人",
        "東に向いてる大きな帽子のリボン",
        "水晶を見つめる人",
        "古い象徴に対して新しい形を教える教師",
    ]
}

def generate_sabian_data():
    """360個のサビアンシンボルデータを生成"""
    data = {}
    degree_counter = 1
    
    for sign_idx, sign in enumerate(SIGNS):
        sign_jp = SIGNS_JP[sign_idx]
        
        for sign_degree in range(1, 31):  # 1-30度
            symbol_text = f"{sign_jp}{sign_degree}度のシンボル"
            
            # サンプルデータがある場合は使用
            if sign in SABIAN_SAMPLES and sign_degree <= len(SABIAN_SAMPLES[sign]):
                symbol_detail = SABIAN_SAMPLES[sign][sign_degree - 1]
                symbol_text = f"{sign_jp}{sign_degree}度: {symbol_detail}"
            
            data[str(degree_counter)] = {
                "degree": degree_counter,
                "sign": sign,
                "sign_jp": sign_jp,
                "sign_degree": sign_degree,
                "symbol": symbol_text,
                "keyword": "成長と変化",
                "meaning": f"{sign_jp}{sign_degree}度における魂の学びのテーマ"
            }
            
            degree_counter += 1
    
    return data

def main():
    sabian_data = generate_sabian_data()
    
    # JSON形式で保存（BOM なし）
    with open('sabian_symbols_360.json', 'w', encoding='utf-8') as f:
        json.dump(sabian_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(sabian_data)}個のサビアンシンボルデータを生成しました")
    print(f"   ファイル: sabian_symbols_360.json")

if __name__ == '__main__':
    main()
