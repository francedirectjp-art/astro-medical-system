from flask import Flask, request, render_template, jsonify, redirect, url_for
import math
import ephem
from datetime import datetime
import json
import os

app = Flask(__name__)

# 現在のスクリプトのディレクトリを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json_safe(filename, default_data=None):
    """JSONファイルを安全に読み込む（絶対パス対応）"""
    try:
        filepath = os.path.join(BASE_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using default data.")
        return default_data or {}
    except json.JSONDecodeError:
        print(f"Warning: {filename} is not valid JSON. Using default data.")
        return default_data or {}

# JSONファイルを安全に読み込み
SABIAN_SYMBOLS = load_json_safe('sabian_symbols_360.json', {})
SIXTEEN_ARCHETYPES = load_json_safe('sixteen_archetypes_complete.json', {})

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

def calculate_planetary_positions(birth_datetime, latitude, longitude):
    """惑星位置を計算"""
    try:
        observer = ephem.Observer()
        observer.date = birth_datetime.strftime('%Y/%m/%d %H:%M:%S')
        observer.lat = str(math.radians(latitude))
        observer.lon = str(math.radians(longitude))

        sun = ephem.Sun()
        moon = ephem.Moon()

        sun.compute(observer)
        moon.compute(observer)

        # 黄道座標を度数で取得
        sun_longitude = math.degrees(sun.hlon)
        moon_longitude = math.degrees(moon.hlon)

        return {
            'sun_longitude': sun_longitude,
            'moon_longitude': moon_longitude,
            'sun_sign': get_zodiac_sign(sun_longitude),
            'moon_sign': get_zodiac_sign(moon_longitude),
            'sun_element': get_element(get_zodiac_sign(sun_longitude)),
            'moon_element': get_element(get_zodiac_sign(moon_longitude)),
            'sun_degree': sun_longitude % 30,
            'moon_degree': moon_longitude % 30
        }
    except Exception as e:
        print(f"Error calculating planetary positions: {e}")
        # フォールバック値を返す
        return {
            'sun_longitude': 0,
            'moon_longitude': 0,
            'sun_sign': 'Aries',
            'moon_sign': 'Aries',
            'sun_element': 'Fire',
            'moon_element': 'Fire',
            'sun_degree': 0,
            'moon_degree': 0
        }

def get_zodiac_sign(longitude):
    """黄経から星座を取得"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs[int(longitude // 30) % 12]

def get_element(sign):
    """星座から元素を取得"""
    elements = {
        'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
        'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
        'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
        'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
    }
    return elements.get(sign, 'Fire')

def get_sixteen_archetype(sun_element, moon_element):
    """太陽×月の元素組み合わせから16元型を判定"""
    combinations = {
        ('Fire', 'Fire'): 'Warrior',
        ('Fire', 'Earth'): 'Builder',
        ('Fire', 'Air'): 'Catalyst',
        ('Fire', 'Water'): 'Intuitive',
        ('Earth', 'Fire'): 'Pioneer',
        ('Earth', 'Earth'): 'Guardian',
        ('Earth', 'Air'): 'Analyst',
        ('Earth', 'Water'): 'Nurturer',
        ('Air', 'Fire'): 'Innovator',
        ('Air', 'Earth'): 'Organizer',
        ('Air', 'Air'): 'Communicator',
        ('Air', 'Water'): 'Harmonizer',
        ('Water', 'Fire'): 'Transformer',
        ('Water', 'Earth'): 'Stabilizer',
        ('Water', 'Air'): 'Mediator',
        ('Water', 'Water'): 'Mystic'
    }
    return combinations.get((sun_element, moon_element), 'Unknown')

def generate_comprehensive_health_data(astro_data, archetype):
    """包括的な健康データを生成"""

    # アーキタイプから詳細情報を取得
    archetype_info = SIXTEEN_ARCHETYPES.get(archetype, {})

    # 基本的な体質データを生成
    base_data = {
        'birth_date': '生成されたデータ',
        'birth_time': '生成されたデータ',
        'birth_place': '生成されたデータ',
        'diagnosis_timestamp': datetime.now().strftime('%Y年%m月%d日 %H:%M'),

        # 基本診断用データ
        'primary_archetype': archetype,
        'archetype_description': archetype_info.get('description', f'{archetype}タイプの体質的特徴'),
        'energy_type': archetype_info.get('energy_type', f'{astro_data["sun_element"]}系エネルギー'),
        'metabolism_type': archetype_info.get('metabolism', f'{astro_data["moon_element"]}系代謝'),
        'circulation_type': f'{astro_data["sun_element"]}-{astro_data["moon_element"]}循環型',
        'nervous_system_type': f'{astro_data["moon_element"]}系神経',
        'health_warnings': f'{archetype}タイプは{astro_data["sun_element"]}エネルギーの過剰に注意が必要です。',
        'wellness_tips': [
            f'{astro_data["sun_element"]}元素のバランスを保つ',
            f'{astro_data["moon_element"]}元素の調和を図る',
            '規則正しい生活リズムの維持',
            '適度な運動と休息のバランス'
        ],
        'lunar_influence': f'{astro_data["moon_sign"]}月座の影響により、感情的なバランスが重要です。',

        # 詳細診断用データ
        'archetype_detailed_description': archetype_info.get('detailed_description', f'{archetype}アーキタイプの詳細な体質分析結果'),
        'secondary_archetypes': [
            {
                'name': f'補助型A-{astro_data["sun_element"]}',
                'description': f'{astro_data["sun_element"]}要素による補助的影響',
                'influence_level': '中程度'
            },
            {
                'name': f'補助型B-{astro_data["moon_element"]}',
                'description': f'{astro_data["moon_element"]}要素による補助的影響',
                'influence_level': '中程度'
            }
        ],

        # 惑星分析データ
        'planetary_analysis': [
            {
                'name': '太陽',
                'symbol': '☉',
                'position': f'{astro_data["sun_sign"]} {astro_data["sun_degree"]:.1f}°',
                'health_influence': f'{astro_data["sun_sign"]}による生命力への影響',
                'constitutional_trait': f'{astro_data["sun_element"]}系基本体質'
            },
            {
                'name': '月',
                'symbol': '☽',
                'position': f'{astro_data["moon_sign"]} {astro_data["moon_degree"]:.1f}°',
                'health_influence': f'{astro_data["moon_sign"]}による感情・リズムへの影響',
                'constitutional_trait': f'{astro_data["moon_element"]}系感情体質'
            }
        ],

        # 詳細体質分析
        'detailed_constitution': {
            'energy_type': f'{astro_data["sun_element"]}系主導型',
            'activity_pattern': f'{astro_data["sun_element"]}-{astro_data["moon_element"]}リズム',
            'fatigue_pattern': f'{astro_data["moon_element"]}系疲労パターン',
            'recovery_method': f'{astro_data["sun_element"]}系回復法',
            'metabolism_type': f'{astro_data["moon_element"]}系代謝',
            'digestion_trait': f'{astro_data["moon_sign"]}消化特性',
            'nutrient_absorption': f'{astro_data["moon_element"]}系吸収',
            'suitable_foods': f'{astro_data["sun_element"]}-{astro_data["moon_element"]}適合食材',
            'circulation_type': f'{astro_data["sun_element"]}系循環',
            'blood_pressure_tendency': f'{astro_data["sun_element"]}血圧傾向',
            'heart_rate_trait': f'{astro_data["sun_element"]}心拍特性',
            'exercise_suitability': f'{astro_data["sun_element"]}-{astro_data["moon_element"]}運動適性',
            'nervous_system_type': f'{astro_data["moon_element"]}系神経',
            'stress_response': f'{astro_data["moon_element"]}ストレス反応',
            'sleep_pattern': f'{astro_data["moon_sign"]}睡眠パターン',
            'mental_tendency': f'{astro_data["moon_element"]}精神傾向',
            'immune_type': f'{astro_data["sun_element"]}-{astro_data["moon_element"]}免疫型',
            'infection_resistance': f'{astro_data["sun_element"]}抵抗性',
            'allergy_tendency': f'{astro_data["moon_element"]}アレルギー傾向',
            'healing_capacity': f'{astro_data["sun_element"]}回復力',
            'hormone_balance': f'{astro_data["moon_element"]}ホルモンバランス',
            'temperature_regulation': f'{astro_data["sun_element"]}体温調節',
            'fluid_metabolism': f'{astro_data["moon_element"]}水分代謝',
            'age_related_changes': f'{archetype}加齢変化'
        },

        # 健康警告
        'detailed_health_warnings': {
            'primary_concerns': f'{archetype}タイプは{astro_data["sun_element"]}エネルギーの過剰と{astro_data["moon_element"]}の不足に注意が必要です。',
            'critical_periods': [
                f'{astro_data["sun_element"]}が強まる時期',
                f'{astro_data["moon_element"]}が不安定な時期',
                '季節の変わり目',
                'ストレス過多時期'
            ],
            'preventive_measures': [
                f'{astro_data["sun_element"]}エネルギーのコントロール',
                f'{astro_data["moon_element"]}の補強',
                '定期的な健康チェック',
                'ライフスタイルの調整'
            ]
        },

        # 包括的ウェルネス
        'comprehensive_wellness': {
            'nutrition': [
                f'{astro_data["sun_element"]}系食材の摂取',
                f'{astro_data["moon_element"]}バランス食品',
                '季節に応じた食材選択',
                '適切な水分摂取'
            ],
            'exercise': [
                f'{astro_data["sun_element"]}系運動（活動的）',
                f'{astro_data["moon_element"]}系運動（調和的）',
                '有酸素運動とバランス運動',
                '自然との接触'
            ],
            'rest': [
                f'{astro_data["moon_sign"]}に適した睡眠時間',
                'リラクゼーション技法',
                '瞑想・マインドフルネス',
                '自然のリズムとの調和'
            ],
            'mental_care': [
                f'{astro_data["moon_element"]}系感情ケア',
                'ストレス管理技法',
                'ポジティブ思考の実践',
                '創造的活動への参加'
            ],
            'alternative_therapy': [
                f'{astro_data["sun_element"]}系アロマテラピー',
                f'{astro_data["moon_element"]}系ハーブ療法',
                'クリスタルヒーリング',
                'エネルギーワーク'
            ],
            'lifestyle': [
                '規則正しい生活リズム',
                '環境の整理整頓',
                'ソーシャル活動への参加',
                '継続的な学習と成長'
            ]
        },

        # サビアンシンボル
        'sabian_symbols': [
            {
                'planet': '太陽',
                'degree': int(astro_data["sun_longitude"]) + 1,
                'sign': astro_data["sun_sign"],
                'symbol_text': SABIAN_SYMBOLS.get(str(int(astro_data["sun_longitude"]) + 1), {}).get('symbol', 'シンボル情報'),
                'health_meaning': SABIAN_SYMBOLS.get(str(int(astro_data["sun_longitude"]) + 1), {}).get('health_meaning', '健康への影響')
            },
            {
                'planet': '月',
                'degree': int(astro_data["moon_longitude"]) + 1,
                'sign': astro_data["moon_sign"],
                'symbol_text': SABIAN_SYMBOLS.get(str(int(astro_data["moon_longitude"]) + 1), {}).get('symbol', 'シンボル情報'),
                'health_meaning': SABIAN_SYMBOLS.get(str(int(astro_data["moon_longitude"]) + 1), {}).get('health_meaning', '健康への影響')
            }
        ],

        # 健康管理タイミング
        'health_timing': [
            {
                'period': '朝（太陽の時間）',
                'recommended_activities': f'{astro_data["sun_element"]}系活動、積極的な運動',
                'precautions': 'エネルギー過多に注意'
            },
            {
                'period': '夜（月の時間）',
                'recommended_activities': f'{astro_data["moon_element"]}系活動、リラクゼーション',
                'precautions': '感情のバランスに注意'
            }
        ],

        # 月相・季節ガイダンス
        'lunar_seasonal_guidance': {
            'overview': f'{astro_data["moon_sign"]}月座の影響により、月相と季節の変化に敏感に反応します。',
            'moon_phases': [
                {
                    'phase_name': '新月',
                    'health_guidance': '新しい健康習慣の開始に適した時期'
                },
                {
                    'phase_name': '満月',
                    'health_guidance': 'エネルギーが最高潮、バランスに注意'
                }
            ],
            'seasons': [
                {
                    'season_name': '春',
                    'health_guidance': f'{astro_data["sun_element"]}エネルギーの活性化時期'
                },
                {
                    'season_name': '冬',
                    'health_guidance': f'{astro_data["moon_element"]}の調和と休息が重要'
                }
            ]
        }
    }

    return base_data

@app.route('/')
def index():
    return render_template('input.html')

@app.route('/basic', methods=['POST'])
def basic_diagnosis():
    try:
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        birth_time_str = request.form.get('birth_time')
        prefecture = request.form.get('prefecture')

        if not all([name, birth_date_str, birth_time_str, prefecture]):
            return "必要な情報が不足しています。", 400

        # 座標を取得
        latitude, longitude = PREFECTURES.get(prefecture, (35.6762, 139.6503))

        # 日時を解析
        birth_datetime = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M")

        # 占星術計算
        astro_data = calculate_planetary_positions(birth_datetime, latitude, longitude)

        # アーキタイプ判定
        archetype = get_sixteen_archetype(astro_data['sun_element'], astro_data['moon_element'])

        # 包括的データ生成
        comprehensive_data = generate_comprehensive_health_data(astro_data, archetype)

        # 基本診断用データを更新
        comprehensive_data.update({
            'birth_date': birth_date_str,
            'birth_time': birth_time_str,
            'birth_place': prefecture
        })

        return render_template('basic_report.html', data=comprehensive_data)

    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 400

@app.route('/detailed', methods=['POST'])
def detailed_diagnosis():
    try:
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        birth_time_str = request.form.get('birth_time')
        prefecture = request.form.get('prefecture')

        if not all([name, birth_date_str, birth_time_str, prefecture]):
            return "必要な情報が不足しています。", 400

        # 座標を取得
        latitude, longitude = PREFECTURES.get(prefecture, (35.6762, 139.6503))

        # 日時を解析
        birth_datetime = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M")

        # 占星術計算
        astro_data = calculate_planetary_positions(birth_datetime, latitude, longitude)

        # アーキタイプ判定
        archetype = get_sixteen_archetype(astro_data['sun_element'], astro_data['moon_element'])

        # 包括的データ生成
        comprehensive_data = generate_comprehensive_health_data(astro_data, archetype)

        # 詳細診断用データを更新
        comprehensive_data.update({
            'birth_date': birth_date_str,
            'birth_time': birth_time_str,
            'birth_place': prefecture
        })

        return render_template('detailed_report.html', data=comprehensive_data)

    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 400

if __name__ == '__main__':
    # Railway対応：PORT環境変数の動的取得
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
