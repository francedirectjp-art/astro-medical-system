#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swiss Ephemeris API for Anti-Gravity Prompt Builder
超高精度天体計算APIエンドポイント
"""
from flask import Blueprint, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

# Blueprintの作成
swisseph_api = Blueprint('swisseph_api', __name__)

# エフェメリスファイルのパスを設定
EPHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swisseph_data')
if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)

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

@swisseph_api.route('/api/calculate-chart', methods=['POST'])
def calculate_chart():
    """
    ネイタルチャート計算APIエンドポイント
    
    Request Body (JSON):
    {
        "year": 1990,
        "month": 3,
        "day": 21,
        "hour": 15,
        "minute": 30,
        "latitude": 35.6762,
        "longitude": 139.6503,
        "house_system": "P"  # オプション、デフォルトはPlacidus
    }
    """
    try:
        data = request.get_json()
        
        # 必須パラメータの検証
        required_fields = ['year', 'month', 'day', 'hour', 'minute', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 日本標準時（JST）をUTCに変換
        # JST = UTC+9なので、9時間引く
        jst_hour = data['hour'] + data['minute'] / 60.0
        utc_hour = jst_hour - 9.0
        
        # 日付をまたぐ場合の処理
        from datetime import datetime, timedelta
        jst_datetime = datetime(data['year'], data['month'], data['day'], data['hour'], data['minute'])
        utc_datetime = jst_datetime - timedelta(hours=9)
        
        # ユリウス日の計算（UTC時刻）
        jd = swe.julday(
            utc_datetime.year,
            utc_datetime.month,
            utc_datetime.day,
            utc_datetime.hour + utc_datetime.minute / 60.0
        )
        
        # 全天体の計算
        planets = {}
        for planet_name, planet_id in PLANETS.items():
            planets[planet_name] = calculate_planet_position(jd, planet_id)
        
        # ハウスとアングルの計算
        house_system = data.get('house_system', 'P')
        houses = calculate_houses(jd, data['latitude'], data['longitude'], house_system)
        
        # 各天体のハウスを判定
        for planet_name, planet_data in planets.items():
            if 'longitude' in planet_data:
                planet_data['house'] = get_planet_house(
                    planet_data['longitude'],
                    houses['cusps']
                )
        
        return jsonify({
            'success': True,
            'julian_day': round(jd, 6),
            'planets': planets,
            'houses': houses,
            'calculation_engine': 'Swiss Ephemeris (pyswisseph 2.10.3.2)',
            'precision': '±0.001 degrees'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@swisseph_api.route('/api/calculate-progressions', methods=['POST'])
def calculate_progressions():
    """
    プログレス計算APIエンドポイント
    
    Request Body (JSON):
    {
        "birth_year": 1990,
        "birth_month": 3,
        "birth_day": 21,
        "birth_hour": 15,  # JST時刻
        "birth_minute": 30,  # JST時刻
        "current_date": "2024-12-18"  # ISO format
    }
    """
    try:
        data = request.get_json()
        
        # 現在日
        current_date = datetime.fromisoformat(data['current_date'])
        birth_date = datetime(data['birth_year'], data['birth_month'], data['birth_day'])
        
        # プログレス日の計算（1日=1年のセカンダリープログレス）
        days_since_birth = (current_date - birth_date).days
        years_elapsed = days_since_birth / 365.25  # 閏年を考慮
        progressed_days = int(years_elapsed)  # 経過年数 = プログレス日数
        
        # プログレス日 = 出生日 + プログレス日数
        progress_date = birth_date + timedelta(days=progressed_days)
        
        # 出生時刻（JST）をプログレス計算に使用
        birth_hour = data.get('birth_hour', 12)
        birth_minute = data.get('birth_minute', 0)
        
        # 一部ソフトウェアの方式：出生時刻（JST）をそのままUTC時刻として使用
        # （UTC変換せず、JST時刻をUTCとして扱う）
        progress_jd = swe.julday(
            progress_date.year,
            progress_date.month,
            progress_date.day,
            birth_hour + birth_minute / 60.0
        )
        
        # P-Sun と P-Moon の計算
        p_sun = calculate_planet_position(progress_jd, swe.SUN)
        p_moon = calculate_planet_position(progress_jd, swe.MOON)
        
        # 月相の計算
        lunation = (p_moon['longitude'] - p_sun['longitude']) % 360
        
        # 月相フェーズの判定
        if lunation < 45:
            phase = 'ニュームーン期（新月）'
        elif lunation < 90:
            phase = 'クレセント期（三日月）'
        elif lunation < 135:
            phase = 'ファーストクォーター期（上弦）'
        elif lunation < 180:
            phase = 'ギバウス期（満ちゆく月）'
        elif lunation < 225:
            phase = 'フルムーン期（満月）'
        elif lunation < 270:
            phase = 'ディセミネイティング期（欠けゆく月）'
        elif lunation < 315:
            phase = 'ラストクォーター期（下弦）'
        else:
            phase = 'バルサミック期（暗い月）'
        
        return jsonify({
            'success': True,
            'progress_date': progress_date.isoformat(),
            'p_sun': p_sun,
            'p_moon': p_moon,
            'lunar_phase': phase,
            'lunation_angle': round(lunation, 2)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@swisseph_api.route('/api/calculate-transits', methods=['POST'])
def calculate_transits():
    """
    トランジット計算APIエンドポイント（3年間の木星・土星サイン移動）
    
    Request Body (JSON):
    {
        "start_date": "2024-12-18",  # ISO format
        "years": 3
    }
    """
    try:
        data = request.get_json()
        
        start_date = datetime.fromisoformat(data['start_date'])
        years = data.get('years', 3)
        
        # 現在の外惑星位置
        current_jd = swe.julday(start_date.year, start_date.month, start_date.day, 12.0)
        
        outer_planets = {}
        for planet_name in ['Uranus', 'Neptune', 'Pluto']:
            outer_planets[planet_name] = calculate_planet_position(
                current_jd,
                PLANETS[planet_name]
            )
        
        # 木星と土星のサイン移動を計算（日単位で正確に）
        jupiter_transits = []
        saturn_transits = []
        
        # 日単位でチェック（より正確）
        for planet_name, planet_id, transits_list in [
            ('Jupiter', PLANETS['Jupiter'], jupiter_transits),
            ('Saturn', PLANETS['Saturn'], saturn_transits)
        ]:
            current_sign = None
            end_date = start_date + relativedelta(years=years)
            
            # 日単位でチェック
            check_date = start_date
            while check_date <= end_date:
                check_jd = swe.julday(check_date.year, check_date.month, check_date.day, 12.0)
                
                position = calculate_planet_position(check_jd, planet_id)
                sign_index = int(position['longitude'] // 30)
                
                if current_sign is None:
                    # 初回は現在のサインを記録
                    current_sign = sign_index
                elif current_sign != sign_index:
                    # サインが変わった = イングレス発生
                    transits_list.append({
                        'date': check_date.isoformat().split('T')[0],
                        'sign': SIGNS[sign_index],
                        'signJP': SIGNS_JP[sign_index]
                    })
                    current_sign = sign_index
                
                # 次の日へ
                check_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'outer_planets': outer_planets,
            'jupiter_transits': jupiter_transits,
            'saturn_transits': saturn_transits
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@swisseph_api.route('/api/calculate-solar-return', methods=['POST'])
def calculate_solar_return():
    """
    ソーラーリターン（太陽回帰図）計算APIエンドポイント
    今日以降で直近の回帰を、出生地で作図する。

    Request Body (JSON):
    {
        "birth_year": 1990,
        "birth_month": 3,
        "birth_day": 21,
        "birth_hour": 15,     # 出生地ローカル時刻
        "birth_minute": 30,
        "latitude": 35.6762,  # 出生地
        "longitude": 139.6503,
        "tz_name": "Asia/Tokyo",       # オプション、デフォルト Asia/Tokyo
        "current_date": "2026-08-26",  # ISO format（この日以降で直近の回帰）
        "house_system": "P"
    }
    """
    try:
        data = request.get_json()

        required_fields = ['birth_year', 'birth_month', 'birth_day',
                           'birth_hour', 'birth_minute', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        tz_name = data.get('tz_name') or 'Asia/Tokyo'
        try:
            from zoneinfo import ZoneInfo
            tzinfo = ZoneInfo(tz_name)
        except Exception:
            from zoneinfo import ZoneInfo
            tz_name = 'Asia/Tokyo'
            tzinfo = ZoneInfo(tz_name)

        # 出生ローカル時刻 → UTC（タイムゾーンの歴史的変更も zoneinfo が吸収）
        from datetime import timezone
        birth_local = datetime(data['birth_year'], data['birth_month'], data['birth_day'],
                               data['birth_hour'], data['birth_minute'], tzinfo=tzinfo)
        birth_utc = birth_local.astimezone(timezone.utc)
        natal_jd = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day,
                              birth_utc.hour + birth_utc.minute / 60.0 + birth_utc.second / 3600.0)

        # ネイタル太陽黄経
        natal_sun = calculate_planet_position(natal_jd, swe.SUN)
        if 'error' in natal_sun:
            return jsonify({'success': False, 'error': natal_sun['error']}), 500
        natal_sun_lon = natal_sun['longitude']

        # 基準日（この日時以降で直近の回帰を探す）
        current_date = datetime.fromisoformat(data.get('current_date', datetime.utcnow().date().isoformat()))
        now_jd = swe.julday(current_date.year, current_date.month, current_date.day, 0.0)

        TROPICAL_YEAR = 365.2421897

        def solve_return(jd_guess):
            """ニュートン法で太陽黄経がネイタルに一致する瞬間のJDを求める"""
            jd = jd_guess
            for _ in range(30):
                swe.set_ephe_path(EPHE_PATH)
                pos = swe.calc_ut(jd, swe.SUN)[0]
                diff = ((pos[0] - natal_sun_lon) + 180.0) % 360.0 - 180.0
                if abs(diff) < 1e-8:
                    break
                speed = pos[3] if pos[3] > 0.5 else 0.9856  # deg/day
                jd -= diff / speed
            return jd

        # 経過年数から初期値を作り、基準日以降になるまで1年ずつ進める
        years_elapsed = int((now_jd - natal_jd) / TROPICAL_YEAR)
        return_jd = solve_return(natal_jd + years_elapsed * TROPICAL_YEAR)
        while return_jd < now_jd:
            years_elapsed += 1
            return_jd = solve_return(natal_jd + years_elapsed * TROPICAL_YEAR)

        # JD → UTC → ローカル時刻
        y, m, d, ut = swe.revjul(return_jd)
        total_seconds = round(ut * 3600)
        return_utc = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(seconds=total_seconds)
        return_local = return_utc.astimezone(tzinfo)
        utc_offset = return_local.utcoffset()
        offset_hours = utc_offset.total_seconds() / 3600
        offset_str = f"UTC{'+' if offset_hours >= 0 else '-'}{abs(int(offset_hours)):d}" \
            + (f":{abs(int(utc_offset.total_seconds() % 3600 // 60)):02d}" if utc_offset.total_seconds() % 3600 else '')

        # リターン瞬間・出生地でチャート作成
        planets = {}
        for planet_name, planet_id in PLANETS.items():
            planets[planet_name] = calculate_planet_position(return_jd, planet_id)

        house_system = data.get('house_system', 'P')
        houses = calculate_houses(return_jd, data['latitude'], data['longitude'], house_system)

        if 'cusps' in houses:
            for planet_name, planet_data in planets.items():
                if 'longitude' in planet_data:
                    planet_data['house'] = get_planet_house(planet_data['longitude'], houses['cusps'])

        return jsonify({
            'success': True,
            'age': years_elapsed,
            'return_jd': round(return_jd, 6),
            'return_datetime_utc': return_utc.strftime('%Y-%m-%d %H:%M'),
            'return_datetime_local': return_local.strftime('%Y-%m-%d %H:%M'),
            'tz_name': tz_name,
            'utc_offset': offset_str,
            'natal_sun_longitude': round(natal_sun_lon, 6),
            'planets': planets,
            'houses': houses
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@swisseph_api.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'swiss_ephemeris': 'pyswisseph 2.10.3.2',
        'ephemeris_path': EPHE_PATH,
        'available_bodies': list(PLANETS.keys())
    })
