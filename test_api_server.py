#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone test server for Swiss Ephemeris API
"""
from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
import os
import traceback

app = Flask(__name__)

# エフェメリスファイルのパスを設定
EPHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swisseph_data')
if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)
    print(f"✅ Ephemeris path set to: {EPHE_PATH}")
else:
    print(f"⚠️  Warning: Ephemeris path does not exist: {EPHE_PATH}")

# 天体ID定義
PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
    'TrueNode': swe.TRUE_NODE,
    'Chiron': swe.CHIRON
}

# 星座名
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']

def calculate_planet_position(jd, planet_id):
    """天体の位置を計算"""
    try:
        # エフェメリスパスを毎回設定（グローバル設定が効かない場合のため）
        swe.set_ephe_path(EPHE_PATH)
        result = swe.calc_ut(jd, planet_id)
        position = result[0]
        
        longitude = position[0]  # 黄経
        latitude = position[1]   # 黄緯
        distance = position[2]   # 距離
        speed = position[3]      # 速度
        
        # 経度を0-360の範囲に正規化
        normalized_longitude = longitude % 360
        
        sign_index = int(normalized_longitude // 30) % 12
        degree_in_sign = normalized_longitude % 30
        
        return {
            'longitude': round(normalized_longitude, 6),
            'latitude': round(latitude, 6),
            'distance': round(distance, 6),
            'speed': round(speed, 6),
            'sign': SIGNS[sign_index],
            'signJP': SIGNS_JP[sign_index],
            'degree': round(degree_in_sign, 6),
            'retrograde': speed < 0
        }
    except Exception as e:
        print(f"❌ Error calculating planet {planet_id}: {str(e)}")
        traceback.print_exc()
        return {'error': str(e)}

def calculate_houses(jd, latitude, longitude, house_system='P'):
    """ハウスカスプとアングルを計算"""
    try:
        cusps, ascmc = swe.houses(jd, latitude, longitude, house_system.encode())
        
        # cuspsはタプルなのでリストに変換（12要素）
        cusps_list = list(cusps)[:12] if cusps else []
        
        asc = ascmc[0]  # アセンダント
        mc = ascmc[1]   # MC（天頂）
        
        # 経度を0-360の範囲に正規化してサイン計算
        asc_sign_index = int((asc % 360) // 30) % 12
        mc_sign_index = int((mc % 360) // 30) % 12
        
        return {
            'cusps': [round(cusp, 6) for cusp in cusps_list],
            'ascendant': {
                'longitude': round(asc, 6),
                'sign': SIGNS[asc_sign_index],
                'signJP': SIGNS_JP[asc_sign_index],
                'degree': round(asc % 30, 6)
            },
            'midheaven': {
                'longitude': round(mc, 6),
                'sign': SIGNS[mc_sign_index],
                'signJP': SIGNS_JP[mc_sign_index],
                'degree': round(mc % 30, 6)
            },
            'armc': round(ascmc[2], 6)  # Sidereal time
        }
    except Exception as e:
        print(f"❌ Error calculating houses: {str(e)}")
        traceback.print_exc()
        return {'error': str(e)}

def get_planet_house(planet_longitude, house_cusps):
    """天体が入るハウスを判定"""
    if not house_cusps or len(house_cusps) < 12:
        return 1  # デフォルトは第1ハウス
    
    # 経度を0-360の範囲に正規化
    normalized_long = planet_longitude % 360
    
    for i in range(12):
        current_cusp = house_cusps[i] % 360
        next_cusp = house_cusps[(i + 1) % 12] % 360
        
        if next_cusp > current_cusp:
            if current_cusp <= normalized_long < next_cusp:
                return i + 1
        else:  # ハウスカスプが360度をまたぐ場合（12ハウス→1ハウス）
            if normalized_long >= current_cusp or normalized_long < next_cusp:
                return i + 1
    
    return 1  # デフォルトは第1ハウス

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'service': 'Swiss Ephemeris API',
        'version': '1.0.0',
        'ephe_path': EPHE_PATH
    })

@app.route('/api/calculate-chart', methods=['POST'])
def calculate_chart():
    """ネイタルチャート計算APIエンドポイント"""
    try:
        data = request.get_json()
        print(f"📥 Received request: {data}")
        
        # 必須パラメータの検証
        required_fields = ['year', 'month', 'day', 'hour', 'minute', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}', 'success': False}), 400
        
        # ユリウス日の計算
        jd = swe.julday(
            data['year'],
            data['month'],
            data['day'],
            data['hour'] + data['minute'] / 60.0
        )
        print(f"✅ Julian Day: {jd}")
        
        # 全天体の計算
        planets = {}
        for planet_name, planet_id in PLANETS.items():
            planets[planet_name] = calculate_planet_position(jd, planet_id)
            if 'error' not in planets[planet_name]:
                print(f"✅ {planet_name}: {planets[planet_name]['signJP']} {planets[planet_name]['degree']:.2f}°")
        
        # ハウスとアングルの計算
        house_system = data.get('house_system', 'P')
        houses = calculate_houses(jd, data['latitude'], data['longitude'], house_system)
        
        if 'error' not in houses:
            print(f"✅ ASC: {houses['ascendant']['signJP']} {houses['ascendant']['degree']:.2f}°")
            print(f"✅ MC: {houses['midheaven']['signJP']} {houses['midheaven']['degree']:.2f}°")
            
            # 各天体のハウスを判定
            for planet_name, planet_data in planets.items():
                if 'longitude' in planet_data:
                    planet_data['house'] = get_planet_house(
                        planet_data['longitude'],
                        houses['cusps']
                    )
                    print(f"✅ {planet_name} is in House {planet_data['house']}")
        
        response = {
            'success': True,
            'julian_day': round(jd, 6),
            'planets': planets,
            'houses': houses,
            'calculation_engine': 'Swiss Ephemeris (pyswisseph 2.10.3.2)',
            'precision': '±0.001 degrees'
        }
        
        print(f"✅ Response generated successfully")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in calculate_chart: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("✅ Swiss Ephemeris API Server Starting...")
    print(f"📂 Ephemeris Data Path: {EPHE_PATH}")
    print(f"📍 Endpoint: http://0.0.0.0:5000/api/calculate-chart")
    print(f"❤️  Health Check: http://0.0.0.0:5000/api/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
