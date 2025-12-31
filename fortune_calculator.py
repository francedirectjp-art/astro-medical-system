#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開運言霊占星術師 - 天体計算エンジン
Swiss Ephemerisによる高精度占星術計算
"""

import swisseph as swe
from datetime import datetime, timedelta
import math

# 星座の定義
ZODIAC_SIGNS = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
                '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']

ZODIAC_SIGNS_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                   'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# 天体ID
SUN = swe.SUN
MOON = swe.MOON
MERCURY = swe.MERCURY
VENUS = swe.VENUS
MARS = swe.MARS
JUPITER = swe.JUPITER
SATURN = swe.SATURN
URANUS = swe.URANUS
NEPTUNE = swe.NEPTUNE
PLUTO = swe.PLUTO
TRUE_NODE = swe.TRUE_NODE  # ドラゴンヘッド

# 都道府県データ（県庁所在地の座標）
PREFECTURES = {
    '北海道': (43.0642, 141.3469),
    '青森県': (40.8244, 140.7400),
    '岩手県': (39.7036, 141.1527),
    '宮城県': (38.2682, 140.8721),
    '秋田県': (39.7186, 140.1022),
    '山形県': (38.2404, 140.3633),
    '福島県': (37.7503, 140.4677),
    '茨城県': (36.3418, 140.4468),
    '栃木県': (36.5658, 139.8836),
    '群馬県': (36.3906, 139.0608),
    '埼玉県': (35.8617, 139.6455),
    '千葉県': (35.6074, 140.1065),
    '東京都': (35.6762, 139.6503),
    '神奈川県': (35.4478, 139.6425),
    '新潟県': (37.9026, 139.0232),
    '富山県': (36.6959, 137.2137),
    '石川県': (36.5946, 136.6256),
    '福井県': (36.0652, 136.2216),
    '山梨県': (35.6642, 138.5681),
    '長野県': (36.6513, 138.1809),
    '岐阜県': (35.3912, 136.7223),
    '静岡県': (34.9756, 138.3827),
    '愛知県': (35.1802, 136.9066),
    '三重県': (34.7302, 136.5086),
    '滋賀県': (35.0045, 135.8686),
    '京都府': (35.0211, 135.7556),
    '大阪府': (34.6937, 135.5023),
    '兵庫県': (34.6913, 135.1830),
    '奈良県': (34.6851, 135.8048),
    '和歌山県': (34.2261, 135.1675),
    '鳥取県': (35.5038, 134.2378),
    '島根県': (35.4723, 133.0505),
    '岡山県': (34.6618, 133.9346),
    '広島県': (34.3963, 132.4596),
    '山口県': (34.1861, 131.4707),
    '徳島県': (34.0658, 134.5593),
    '香川県': (34.3401, 134.0430),
    '愛媛県': (33.8416, 132.7658),
    '高知県': (33.5597, 133.5311),
    '福岡県': (33.6064, 130.4181),
    '佐賀県': (33.2494, 130.2989),
    '長崎県': (32.7503, 129.8779),
    '熊本県': (32.7898, 130.7417),
    '大分県': (33.2382, 131.6126),
    '宮崎県': (31.9077, 131.4202),
    '鹿児島県': (31.5602, 130.5581),
    '沖縄県': (26.2124, 127.6792)
}


def get_zodiac_sign(longitude):
    """黄経から星座を取得"""
    sign_index = int((longitude % 360) // 30) % 12
    return ZODIAC_SIGNS[sign_index], ZODIAC_SIGNS_EN[sign_index]


def get_degree_in_sign(longitude):
    """星座内の度数を取得"""
    return longitude % 30


def format_position(longitude):
    """位置を読みやすい形式にフォーマット"""
    sign_jp, sign_en = get_zodiac_sign(longitude)
    degree = get_degree_in_sign(longitude)
    return f"{sign_jp} {degree:.2f}度"


def jst_to_utc(year, month, day, hour, minute):
    """JST時刻をUTCに変換"""
    jst_datetime = datetime(year, month, day, hour, minute)
    utc_datetime = jst_datetime - timedelta(hours=9)
    return utc_datetime


def calculate_julian_day(year, month, day, hour, minute):
    """ユリウス日を計算（UTC変換込み）"""
    utc_datetime = jst_to_utc(year, month, day, hour, minute)
    jd = swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        utc_datetime.hour + utc_datetime.minute / 60.0
    )
    return jd


def calculate_planet_position(jd, planet_id):
    """天体の位置を計算"""
    try:
        result = swe.calc_ut(jd, planet_id)
        longitude = result[0][0]
        speed = result[0][3]
        
        sign_jp, sign_en = get_zodiac_sign(longitude)
        degree = get_degree_in_sign(longitude)
        
        return {
            'longitude': longitude,
            'sign_jp': sign_jp,
            'sign_en': sign_en,
            'degree': degree,
            'formatted': format_position(longitude),
            'speed': speed,
            'retrograde': speed < 0
        }
    except Exception as e:
        print(f"Error calculating planet position: {e}")
        return None


def calculate_houses(jd, latitude, longitude):
    """ハウスとアングルを計算（Placidusハウスシステム）"""
    try:
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
        
        asc = ascmc[0]  # アセンダント
        mc = ascmc[1]   # MC（天頂）
        
        asc_sign_jp, asc_sign_en = get_zodiac_sign(asc)
        mc_sign_jp, mc_sign_en = get_zodiac_sign(mc)
        
        return {
            'ascendant': {
                'longitude': asc,
                'sign_jp': asc_sign_jp,
                'sign_en': asc_sign_en,
                'degree': get_degree_in_sign(asc),
                'formatted': format_position(asc)
            },
            'midheaven': {
                'longitude': mc,
                'sign_jp': mc_sign_jp,
                'sign_en': mc_sign_en,
                'degree': get_degree_in_sign(mc),
                'formatted': format_position(mc)
            },
            'cusps': list(cusps)[:12]
        }
    except Exception as e:
        print(f"Error calculating houses: {e}")
        return None


def get_planet_house(planet_longitude, house_cusps):
    """天体がどのハウスに位置するかを判定"""
    normalized_long = planet_longitude % 360
    
    for i in range(12):
        current_cusp = house_cusps[i] % 360
        next_cusp = house_cusps[(i + 1) % 12] % 360
        
        if next_cusp > current_cusp:
            # 通常のケース
            if current_cusp <= normalized_long < next_cusp:
                return i + 1
        else:
            # 360度をまたぐケース
            if normalized_long >= current_cusp or normalized_long < next_cusp:
                return i + 1
    
    return 1


def calculate_natal_chart(year, month, day, hour, minute, latitude, longitude):
    """ネイタルチャートを計算"""
    jd = calculate_julian_day(year, month, day, hour, minute)
    
    # 主要天体の計算
    sun = calculate_planet_position(jd, SUN)
    moon = calculate_planet_position(jd, MOON)
    mercury = calculate_planet_position(jd, MERCURY)
    venus = calculate_planet_position(jd, VENUS)
    mars = calculate_planet_position(jd, MARS)
    jupiter = calculate_planet_position(jd, JUPITER)
    saturn = calculate_planet_position(jd, SATURN)
    uranus = calculate_planet_position(jd, URANUS)
    neptune = calculate_planet_position(jd, NEPTUNE)
    pluto = calculate_planet_position(jd, PLUTO)
    true_node = calculate_planet_position(jd, TRUE_NODE)
    
    # ハウスとアングルの計算
    houses = calculate_houses(jd, latitude, longitude)
    
    # 天体のハウス位置を計算
    if houses:
        cusps = houses['cusps']
        sun['house'] = get_planet_house(sun['longitude'], cusps)
        moon['house'] = get_planet_house(moon['longitude'], cusps)
        jupiter['house'] = get_planet_house(jupiter['longitude'], cusps)
        saturn['house'] = get_planet_house(saturn['longitude'], cusps)
        true_node['house'] = get_planet_house(true_node['longitude'], cusps)
    
    return {
        'sun': sun,
        'moon': moon,
        'mercury': mercury,
        'venus': venus,
        'mars': mars,
        'jupiter': jupiter,
        'saturn': saturn,
        'uranus': uranus,
        'neptune': neptune,
        'pluto': pluto,
        'true_node': true_node,
        'houses': houses,
        'julian_day': jd
    }


def calculate_progressed_chart(birth_jd, current_year, current_month, current_day):
    """セカンダリープログレッション（進行図）を計算
    1日=1年の進行法
    """
    # 出生日からの経過年数を計算
    birth_date = swe.revjul(birth_jd)
    birth_year = int(birth_date[0])
    
    years_passed = current_year - birth_year
    
    # 進行日数を計算（1年=1日）
    progressed_jd = birth_jd + years_passed + (current_month / 12.0)
    
    # プログレスの太陽と月を計算
    prog_sun = calculate_planet_position(progressed_jd, SUN)
    prog_moon = calculate_planet_position(progressed_jd, MOON)
    
    # 月のフェーズを計算
    sun_long = prog_sun['longitude']
    moon_long = prog_moon['longitude']
    phase_angle = (moon_long - sun_long) % 360
    
    # フェーズの判定
    if phase_angle < 45:
        moon_phase = "新月"
        moon_phase_desc = "新しい始まり、種まきの時期"
    elif phase_angle < 90:
        moon_phase = "三日月"
        moon_phase_desc = "成長と発展の時期"
    elif phase_angle < 135:
        moon_phase = "上弦の月"
        moon_phase_desc = "決断と行動の時期"
    elif phase_angle < 180:
        moon_phase = "満ちゆく凸月"
        moon_phase_desc = "完成に向かう時期"
    elif phase_angle < 225:
        moon_phase = "満月"
        moon_phase_desc = "達成と完成の時期"
    elif phase_angle < 270:
        moon_phase = "欠けゆく凸月"
        moon_phase_desc = "見直しと調整の時期"
    elif phase_angle < 315:
        moon_phase = "下弦の月"
        moon_phase_desc = "手放しと浄化の時期"
    else:
        moon_phase = "残月"
        moon_phase_desc = "終わりと準備の時期"
    
    return {
        'progressed_sun': prog_sun,
        'progressed_moon': prog_moon,
        'moon_phase': moon_phase,
        'moon_phase_desc': moon_phase_desc,
        'phase_angle': phase_angle
    }


def calculate_transits(current_year, current_month, current_day):
    """トランジット（経過図）を計算
    主に木星と土星の現在位置と今後3年間の移動を予測
    """
    # 現在のユリウス日
    current_jd = swe.julday(current_year, current_month, current_day, 12.0)
    
    # 現在の木星と土星の位置
    jupiter_now = calculate_planet_position(current_jd, JUPITER)
    saturn_now = calculate_planet_position(current_jd, SATURN)
    
    # 今後3年間のサイン移動を予測
    jupiter_movements = []
    saturn_movements = []
    
    current_jupiter_sign = jupiter_now['sign_en']
    current_saturn_sign = saturn_now['sign_en']
    
    for year_offset in range(0, 37, 12):  # 3年間を12ヶ月刻みで
        future_jd = current_jd + year_offset * 30.4375  # 1ヶ月≈30.4375日
        
        jupiter_future = calculate_planet_position(future_jd, JUPITER)
        saturn_future = calculate_planet_position(future_jd, SATURN)
        
        # サインが変わった場合に記録
        if jupiter_future['sign_en'] != current_jupiter_sign:
            future_date = swe.revjul(future_jd)
            jupiter_movements.append({
                'date': f"{int(future_date[0])}年{int(future_date[1])}月",
                'sign_jp': jupiter_future['sign_jp'],
                'sign_en': jupiter_future['sign_en']
            })
            current_jupiter_sign = jupiter_future['sign_en']
        
        if saturn_future['sign_en'] != current_saturn_sign:
            future_date = swe.revjul(future_jd)
            saturn_movements.append({
                'date': f"{int(future_date[0])}年{int(future_date[1])}月",
                'sign_jp': saturn_future['sign_jp'],
                'sign_en': saturn_future['sign_en']
            })
            current_saturn_sign = saturn_future['sign_en']
    
    return {
        'jupiter_now': jupiter_now,
        'saturn_now': saturn_now,
        'jupiter_movements': jupiter_movements[:3],  # 最大3つまで
        'saturn_movements': saturn_movements[:3]
    }


def calculate_solar_return(birth_jd, current_year, birth_latitude, birth_longitude):
    """ソーラーリターン（太陽回帰図）のASCを計算
    太陽が出生時と同じ位置に戻る瞬間のアセンダント
    """
    # 出生時の太陽の黄経を取得
    birth_sun = calculate_planet_position(birth_jd, SUN)
    birth_sun_long = birth_sun['longitude']
    
    # 今年の1月1日から開始して、太陽が同じ位置に来る日を探す
    start_jd = swe.julday(current_year, 1, 1, 12.0)
    
    # 約365日の範囲で太陽の位置をチェック
    for day_offset in range(365):
        test_jd = start_jd + day_offset
        test_sun = calculate_planet_position(test_jd, SUN)
        test_sun_long = test_sun['longitude']
        
        # 太陽の黄経が出生時と1度以内の場合
        diff = abs(test_sun_long - birth_sun_long)
        if diff < 1.0 or diff > 359.0:
            # この瞬間のASCを計算
            sr_houses = calculate_houses(test_jd, birth_latitude, birth_longitude)
            if sr_houses:
                return {
                    'solar_return_date': swe.revjul(test_jd),
                    'ascendant': sr_houses['ascendant']
                }
    
    # 見つからない場合は現在の位置を返す
    current_houses = calculate_houses(start_jd, birth_latitude, birth_longitude)
    return {
        'solar_return_date': swe.revjul(start_jd),
        'ascendant': current_houses['ascendant'] if current_houses else None
    }


def calculate_full_fortune_data(year, month, day, hour, minute, prefecture):
    """開運アドバイスに必要な全データを計算"""
    # 都道府県から緯度経度を取得
    if prefecture not in PREFECTURES:
        prefecture = '東京都'
    
    latitude, longitude = PREFECTURES[prefecture]
    
    # 1. ネイタルチャートの計算
    natal = calculate_natal_chart(year, month, day, hour, minute, latitude, longitude)
    
    # 2. プログレッションの計算（現在時点）
    current_date = datetime.now()
    progression = calculate_progressed_chart(
        natal['julian_day'],
        current_date.year,
        current_date.month,
        current_date.day
    )
    
    # 3. トランジットの計算
    transits = calculate_transits(current_date.year, current_date.month, current_date.day)
    
    # 4. ソーラーリターンASCの計算
    solar_return = calculate_solar_return(
        natal['julian_day'],
        current_date.year,
        latitude,
        longitude
    )
    
    return {
        'natal': natal,
        'progression': progression,
        'transits': transits,
        'solar_return': solar_return,
        'birth_info': {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'prefecture': prefecture,
            'latitude': latitude,
            'longitude': longitude
        }
    }


if __name__ == "__main__":
    # テスト実行
    print("=== 開運言霊占星術師 - 計算エンジンテスト ===\n")
    
    # サンプルデータ
    result = calculate_full_fortune_data(1990, 5, 15, 10, 30, '東京都')
    
    print("【ネイタル太陽】")
    sun = result['natal']['sun']
    print(f"  {sun['formatted']} (第{sun.get('house', '?')}ハウス)")
    
    print("\n【プログレス太陽・月】")
    print(f"  P太陽: {result['progression']['progressed_sun']['formatted']}")
    print(f"  P月: {result['progression']['progressed_moon']['formatted']}")
    print(f"  月相: {result['progression']['moon_phase']} - {result['progression']['moon_phase_desc']}")
    
    print("\n【トランジット木星】")
    jupiter = result['transits']['jupiter_now']
    natal_jupiter_house = result['natal']['jupiter'].get('house', '?')
    print(f"  現在位置: {jupiter['formatted']} (ネイタル第{natal_jupiter_house}ハウス)")
    
    print("\n【トランジット土星】")
    saturn = result['transits']['saturn_now']
    natal_saturn_house = result['natal']['saturn'].get('house', '?')
    print(f"  現在位置: {saturn['formatted']} (ネイタル第{natal_saturn_house}ハウス)")
    
    print("\n【ドラゴンヘッド】")
    node = result['natal']['true_node']
    print(f"  {node['formatted']} (第{node.get('house', '?')}ハウス)")
    
    print("\n【ソーラーリターンASC】")
    sr_asc = result['solar_return']['ascendant']
    if sr_asc:
        print(f"  {sr_asc['formatted']}")
    
    print("\n計算完了！")
