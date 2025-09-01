#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第4ステップ最終システム APIサーバー - Phase 1 MVP版
12,000文字詳細鑑定書生成システム

修正内容：
- APIエンドポイント統一
- セキュリティ強化
- 免責事項追加
- ベータ版制限
- エラーハンドリング強化
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os
import json
import google.generativeai as genai
import logging
from functools import wraps

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS設定（セキュリティ強化）
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, 
     origins=allowed_origins, 
     methods=["GET", "POST", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Beta-Key"])

# レート制限設定
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"],
    storage_uri="memory://"
)

# 環境変数チェック
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BETA_PASSWORD = os.getenv('BETA_PASSWORD', 'astro2024beta')

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY環境変数が設定されていません")
    raise ValueError("GEMINI_API_KEY環境変数が必要です")

# Gemini API設定
try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API設定完了")
except Exception as e:
    logger.error(f"Gemini API設定エラー: {e}")
    raise

# Swiss Ephemeris設定
SWISSEPH_PATH = os.getenv('SWISSEPH_PATH', '/usr/share/swisseph')

def init_swisseph():
    """Swiss Ephemerisを初期化"""
    try:
        if os.path.exists(SWISSEPH_PATH):
            swe.set_ephe_path(SWISSEPH_PATH)
            logger.info(f"Swiss Ephemeris パス設定: {SWISSEPH_PATH}")
        else:
            logger.warning(f"Swiss Ephemerisパスが見つかりません: {SWISSEPH_PATH}")
            # デフォルトパスを試行
            swe.set_ephe_path('')
    except Exception as e:
        logger.error(f"Swiss Ephemeris設定エラー: {e}")
        swe.set_ephe_path('')

# ベータ版認証デコレータ
def beta_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 開発環境では認証をスキップ
        if os.getenv('FLASK_ENV') == 'development':
            return f(*args, **kwargs)

        beta_key = (request.headers.get('X-Beta-Key') or 
                   request.args.get('beta') or 
                   request.json.get('beta_key') if request.json else None)

        if beta_key != BETA_PASSWORD:
            return jsonify({
                'success': False, 
                'error': 'ベータ版アクセスキーが必要です。お問い合わせください。'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# 都道府県の座標データ（完全版）
PREFECTURE_COORDINATES = {
    '北海道': (43.0642, 141.3469),
    '青森県': (40.8244, 140.7400),
    '岩手県': (39.7036, 141.1527),
    '宮城県': (38.2682, 140.8721),
    '秋田県': (39.7186, 140.1024),
    '山形県': (38.2404, 140.3633),
    '福島県': (37.7503, 140.4676),
    '茨城県': (36.3418, 140.4468),
    '栃木県': (36.5657, 139.8836),
    '群馬県': (36.3911, 139.0608),
    '埼玉県': (35.8617, 139.6455),
    '千葉県': (35.6074, 140.1065),
    '東京都': (35.6762, 139.6503),
    '神奈川県': (35.4478, 139.6425),
    '新潟県': (37.9026, 139.0232),
    '富山県': (36.6959, 137.2113),
    '石川県': (36.5946, 136.6256),
    '福井県': (36.0652, 136.2217),
    '山梨県': (35.6642, 138.5683),
    '長野県': (36.6513, 138.1810),
    '岐阜県': (35.3912, 136.7223),
    '静岡県': (34.9756, 138.3828),
    '愛知県': (35.1802, 136.9066),
    '三重県': (34.7303, 136.5086),
    '滋賀県': (35.0045, 135.8686),
    '京都府': (35.0211, 135.7556),
    '大阪府': (34.6937, 135.5023),
    '兵庫県': (34.6913, 135.1830),
    '奈良県': (34.6851, 135.8048),
    '和歌山県': (34.2261, 135.1675),
    '鳥取県': (35.5038, 134.2384),
    '島根県': (35.4723, 133.0505),
    '岡山県': (34.6617, 133.9341),
    '広島県': (34.3963, 132.4596),
    '山口県': (34.1859, 131.4706),
    '徳島県': (34.0658, 134.5594),
    '香川県': (34.3401, 134.0434),
    '愛媛県': (33.8416, 132.7657),
    '高知県': (33.5597, 133.5311),
    '福岡県': (33.6064, 130.4181),
    '佐賀県': (33.2494, 130.2989),
    '長崎県': (32.7503, 129.8677),
    '熊本県': (32.7898, 130.7417),
    '大分県': (33.2382, 131.6126),
    '宮崎県': (31.9077, 131.4202),
    '鹿児島県': (31.5602, 130.5581),
    '沖縄県': (26.2124, 127.6792)
}

# 星座とエレメントのマッピング
SIGN_ELEMENTS = {
    '牡羊座': '火', 'Aries': '火',
    '牡牛座': '地', 'Taurus': '地',
    '双子座': '風', 'Gemini': '風',
    '蟹座': '水', 'Cancer': '水',
    '獅子座': '火', 'Leo': '火',
    '乙女座': '地', 'Virgo': '地',
    '天秤座': '風', 'Libra': '風',
    '蠍座': '水', 'Scorpio': '水',
    '射手座': '火', 'Sagittarius': '火',
    '山羊座': '地', 'Capricorn': '地',
    '水瓶座': '風', 'Aquarius': '風',
    '魚座': '水', 'Pisces': '水'
}

# 16元型データベース
ARCHETYPE_DATABASE = {
    ('火', '火'): 'The Supernova（超新星）',
    ('火', '地'): 'The Magma（マグマ）',
    ('火', '風'): 'The Evangelist（伝道師）',
    ('火', '水'): 'The Geyser（間欠泉）',
    ('地', '火'): 'The Volcano（火山）',
    ('地', '地'): 'The Bedrock（岩盤）',
    ('地', '風'): 'The Garden（庭園）',
    ('地', '水'): 'The Spring（泉）',
    ('風', '火'): 'The Lightning（稲妻）',
    ('風', '地'): 'The Breeze（そよ風）',
    ('風', '風'): 'The Hurricane（ハリケーン）',
    ('風', '水'): 'The Mist（霧）',
    ('水', '火'): 'The Steam（蒸気）',
    ('水', '地'): 'The River（川）',
    ('水', '風'): 'The Rain（雨）',
    ('水', '水'): 'The Ocean（海）'
}

def get_sign_name_japanese(sign_num):
    """星座番号から日本語星座名を取得"""
    signs = [
        '牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
        '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'
    ]
    return signs[sign_num] if 0 <= sign_num < 12 else '未知の星座'

def calculate_planet_position(julian_day, planet_id):
    """指定された天体の位置を計算"""
    try:
        result = swe.calc_ut(julian_day, planet_id)
        longitude = result[0][0]

        # 星座を計算（30度ごと）
        sign_num = int(longitude // 30)
        degree_in_sign = longitude % 30

        sign_name = get_sign_name_japanese(sign_num)
        element = SIGN_ELEMENTS.get(sign_name, '不明')

        return {
            'sign': sign_name,
            'degree': round(degree_in_sign, 2),
            'longitude': round(longitude, 2),
            'element': element
        }
    except Exception as e:
        logger.error(f"天体位置計算エラー: {e}")
        return None

@app.route('/api/calculate-planets', methods=['POST'])
@limiter.limit("5 per minute")
@beta_required
def calculate_planets():
    """7天体位置計算API"""
    try:
        data = request.get_json()

        # 入力データの検証
        required_fields = ['name', 'birth_year', 'birth_month', 'birth_day', 
                          'birth_hour', 'birth_minute', 'birth_prefecture']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'{field}が不足しています'}), 400

        # データ型チェック
        try:
            year = int(data['birth_year'])
            month = int(data['birth_month'])
            day = int(data['birth_day'])
            hour = int(data['birth_hour'])
            minute = int(data['birth_minute'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '日時データの形式が正しくありません'}), 400

        # 日付の妥当性チェック
        if not (1900 <= year <= 2100):
            return jsonify({'success': False, 'error': '年は1900-2100年の範囲で入力してください'}), 400
        if not (1 <= month <= 12):
            return jsonify({'success': False, 'error': '月は1-12の範囲で入力してください'}), 400
        if not (1 <= day <= 31):
            return jsonify({'success': False, 'error': '日は1-31の範囲で入力してください'}), 400
        if not (0 <= hour <= 23):
            return jsonify({'success': False, 'error': '時は0-23の範囲で入力してください'}), 400
        if not (0 <= minute <= 59):
            return jsonify({'success': False, 'error': '分は0-59の範囲で入力してください'}), 400

        # 出生地の座標を取得
        prefecture = data['birth_prefecture']
        if prefecture not in PREFECTURE_COORDINATES:
            return jsonify({'success': False, 'error': '無効な都道府県です'}), 400

        latitude, longitude = PREFECTURE_COORDINATES[prefecture]

        # 日本時間をUTCに変換（JST = UTC+9）
        try:
            birth_datetime_jst = datetime(year, month, day, hour, minute)
            birth_datetime_utc = birth_datetime_jst - timedelta(hours=9)
        except ValueError as e:
            return jsonify({'success': False, 'error': f'無効な日付です: {e}'}), 400

        # ユリウス日を計算
        julian_day = swe.julday(
            birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
            birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0
        )

        # Swiss Ephemerisを初期化
        init_swisseph()

        # 7天体の位置を計算
        planets = {}
        planet_ids = {
            'sun': swe.SUN,
            'moon': swe.MOON,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN
        }

        for planet_name, planet_id in planet_ids.items():
            position = calculate_planet_position(julian_day, planet_id)
            if position:
                planets[planet_name] = position
            else:
                return jsonify({'success': False, 'error': f'{planet_name}の計算に失敗しました'}), 500

        logger.info(f"天体計算完了: {data['name']}")

        return jsonify({
            'success': True,
            'planets': planets,
            'birth_info': {
                'name': data['name'],
                'birth_datetime_jst': birth_datetime_jst.strftime('%Y年%m月%d日 %H時%M分'),
                'birth_prefecture': prefecture
            },
            'disclaimer': '本結果はエンターテインメント目的です。医療診断ではありません。'
        })

    except Exception as e:
        logger.error(f"天体計算エラー: {e}")
        return jsonify({'success': False, 'error': f'計算エラー: システム管理者にお問い合わせください'}), 500

@app.route('/api/simple-diagnosis', methods=['POST'])
@limiter.limit("3 per minute")
@beta_required
def simple_diagnosis():
    """簡易診断API"""
    try:
        data = request.get_json()

        # 入力データの検証
        if 'name' not in data or 'planets' not in data:
            return jsonify({'success': False, 'error': '必要なデータが不足しています'}), 400

        planets = data['planets']
        name = data['name']

        # 太陽と月のエレメントを取得
        if 'sun' not in planets or 'moon' not in planets:
            return jsonify({'success': False, 'error': '太陽と月のデータが必要です'}), 400

        sun_element = planets['sun']['element']
        moon_element = planets['moon']['element']

        # 16元型を判定
        archetype = ARCHETYPE_DATABASE.get((sun_element, moon_element), '不明な元型')

        # エレメントバランスを計算
        element_counts = {'火': 0, '地': 0, '風': 0, '水': 0}
        for planet_data in planets.values():
            element = planet_data.get('element', '不明')
            if element in element_counts:
                element_counts[element] += 1

        total_planets = len(planets)
        element_balance = {
            '火': round((element_counts['火'] / total_planets) * 100, 1) if total_planets > 0 else 0,
            '地': round((element_counts['地'] / total_planets) * 100, 1) if total_planets > 0 else 0,
            '風': round((element_counts['風'] / total_planets) * 100, 1) if total_planets > 0 else 0,
            '水': round((element_counts['水'] / total_planets) * 100, 1) if total_planets > 0 else 0
        }

        # Gemini APIで診断文章を生成
        diagnosis_text = generate_diagnosis_text(name, archetype, sun_element, moon_element, element_balance, planets)

        logger.info(f"簡易診断完了: {name}")

        return jsonify({
            'success': True,
            'archetype': archetype,
            'element_balance': element_balance,
            'diagnosis_text': diagnosis_text,
            'sun_element': sun_element,
            'moon_element': moon_element,
            'disclaimer': '本結果はエンターテインメント目的です。医療診断や治療の代替ではありません。'
        })

    except Exception as e:
        logger.error(f"簡易診断エラー: {e}")
        return jsonify({'success': False, 'error': f'診断エラー: システム管理者にお問い合わせください'}), 500

def generate_diagnosis_text(name, archetype, sun_element, moon_element, element_balance, planets):
    """Gemini APIを使用して診断文章を生成"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # プロンプトを構築
        prompt = f"""
あなたは占星医学の専門家です。以下の情報に基づいて、{name}さんの簡易体質診断を1,000文字程度で作成してください。

【重要な注意】
- これはエンターテインメント目的の体質傾向分析です
- 医療診断ではありません
- 「傾向」「可能性」という表現を使用してください
- 断定的な医療的判断は避けてください

【基本情報】
- 名前: {name}さん
- 16元型: {archetype}
- 太陽のエレメント: {sun_element}
- 月のエレメント: {moon_element}

【エレメントバランス】
- 火: {element_balance.get('火', 0)}%
- 地: {element_balance.get('地', 0)}%
- 風: {element_balance.get('風', 0)}%
- 水: {element_balance.get('水', 0)}%

【7天体の配置】
- 太陽: {planets['sun']['sign']} ({sun_element})
- 月: {planets['moon']['sign']} ({planets['moon']['element']})
- 水星: {planets['mercury']['sign']} ({planets['mercury']['element']})
- 金星: {planets['venus']['sign']} ({planets['venus']['element']})
- 火星: {planets['mars']['sign']} ({planets['mars']['element']})
- 木星: {planets['jupiter']['sign']} ({planets['jupiter']['element']})
- 土星: {planets['saturn']['sign']} ({planets['saturn']['element']})

【診断文章の要件】
1. 16元型の特徴を中心に説明
2. エレメントバランスの特徴を分析
3. 体質的な傾向と注意点（医療診断ではないことを明記）
4. 日常生活でのアドバイス
5. 温かく励ましのある文体
6. 1,000文字程度
7. 「傾向がある」「可能性がある」などの表現を使用

診断文章を作成してください。
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        logger.error(f"Gemini API エラー: {e}")
        # フォールバック用の簡易診断文章
        return f"""
{name}さんの体質診断結果をお伝えいたします。

あなたの16元型は「{archetype}」の傾向を示しています。太陽が{sun_element}のエレメント、月が{moon_element}のエレメントという組み合わせから、この特別な元型の可能性が導き出されました。

エレメントバランスを見ると、火が{element_balance['火']}%、地が{element_balance['地']}%、風が{element_balance['風']}%、水が{element_balance['水']}%となっています。

この配置は、あなたの内なる情熱と外向きの表現が調和した、バランスの取れた体質傾向を示している可能性があります。日常生活では、自分の直感を大切にしながらも、現実的な判断力を活かすことで、より充実した人生を送ることができるかもしれません。

体質的には、季節の変化に敏感な傾向があり、特に気温や湿度の変化に注意を払うことが大切です。規則正しい生活リズムを心がけ、適度な運動と十分な休息を取ることで、本来の力を発揮できる可能性があります。

あなたの持つ独特な魅力と才能を信じて、自分らしい道を歩んでください。

※本結果はエンターテインメント目的の体質傾向分析です。医療診断ではありません。
"""

# 修正：エンドポイント名を統一
@app.route('/api/generate-detailed-report', methods=['POST'])
@limiter.limit("1 per minute")
@beta_required
def generate_detailed_diagnosis():
    """12,000文字詳細鑑定書を分割生成で作成（修正版）"""
    try:
        data = request.json

        # 必要なデータの取得
        name = data.get('name', '未設定')
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour = data.get('hour')
        minute = data.get('minute')
        birth_prefecture = data.get('birth_prefecture')

        # まず天体位置を計算
        planets_data = {
            'name': name,
            'birth_year': year,
            'birth_month': month,
            'birth_day': day,
            'birth_hour': hour,
            'birth_minute': minute,
            'birth_prefecture': birth_prefecture
        }

        # 天体位置計算を内部で実行
        planets_response = calculate_planets_internal(planets_data)
        if not planets_response.get('success'):
            return jsonify(planets_response), 400

        planets = planets_response['planets']

        # 16元型の判定
        sun_element = planets.get('sun', {}).get('element', '火')
        moon_element = planets.get('moon', {}).get('element', '水')
        archetype = ARCHETYPE_DATABASE.get((sun_element, moon_element), 'The Bedrock（岩盤）')

        # エレメントバランスの計算
        element_balance = calculate_element_balance(planets)

        birth_date = f"{year}年{month}月{day}日"
        birth_time = f"{hour}時{minute}分"
        birth_place = birth_prefecture

        # 分割生成で詳細鑑定書を作成
        sections = generate_diagnosis_sections(name, birth_date, birth_time, birth_place, 
                                             planets, archetype, element_balance)

        # 全セクションを結合
        full_diagnosis = '\n\n'.join(sections.values())

        logger.info(f"詳細鑑定書生成完了: {name}, 文字数: {len(full_diagnosis)}")

        return jsonify({
            'success': True,
            'detailed_report': full_diagnosis,
            'sections': sections,
            'character_count': len(full_diagnosis),
            'archetype': archetype,
            'element_balance': element_balance,
            'disclaimer': '本鑑定書はエンターテインメント目的です。医療診断や治療の代替ではありません。'
        })

    except Exception as e:
        logger.error(f"詳細鑑定書生成エラー: {e}")
        return jsonify({
            'success': False,
            'error': 'システムエラーが発生しました。管理者にお問い合わせください。'
        }), 500

def calculate_planets_internal(data):
    """内部用天体計算関数"""
    try:
        # バリデーション
        required_fields = ['name', 'birth_year', 'birth_month', 'birth_day', 
                          'birth_hour', 'birth_minute', 'birth_prefecture']
        for field in required_fields:
            if field not in data:
                return {'success': False, 'error': f'{field}が不足しています'}

        # 出生地の座標を取得
        prefecture = data['birth_prefecture']
        if prefecture not in PREFECTURE_COORDINATES:
            return {'success': False, 'error': '無効な都道府県です'}

        latitude, longitude = PREFECTURE_COORDINATES[prefecture]

        # 日本時間をUTCに変換（JST = UTC+9）
        birth_datetime_jst = datetime(
            data['birth_year'], data['birth_month'], data['birth_day'],
            data['birth_hour'], data['birth_minute']
        )
        birth_datetime_utc = birth_datetime_jst - timedelta(hours=9)

        # ユリウス日を計算
        julian_day = swe.julday(
            birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
            birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0
        )

        # Swiss Ephemerisを初期化
        init_swisseph()

        # 7天体の位置を計算
        planets = {}
        planet_ids = {
            'sun': swe.SUN,
            'moon': swe.MOON,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN
        }

        for planet_name, planet_id in planet_ids.items():
            position = calculate_planet_position(julian_day, planet_id)
            if position:
                planets[planet_name] = position
            else:
                return {'success': False, 'error': f'{planet_name}の計算に失敗しました'}

        return {
            'success': True,
            'planets': planets,
            'birth_info': {
                'name': data['name'],
                'birth_datetime_jst': birth_datetime_jst.strftime('%Y年%m月%d日 %H時%M分'),
                'birth_prefecture': prefecture
            }
        }

    except Exception as e:
        logger.error(f"内部天体計算エラー: {e}")
        return {'success': False, 'error': f'計算エラー: {str(e)}'}

def generate_diagnosis_sections(name, birth_date, birth_time, birth_place, planets, archetype, element_balance):
    """6セクションに分割して詳細鑑定書を生成"""

    # Gemini Flash モデルの設定
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        logger.error(f"Gemini モデル設定エラー: {e}")
        return generate_fallback_sections(name, archetype)

    sections = {}

    try:
        # セクション1: 序章
        sections['intro'] = generate_intro_section(model, name, birth_date, birth_time, birth_place)

        # セクション2: 第1部（魂のコアパターン）
        sections['core_pattern'] = generate_core_pattern_section(model, name, planets, archetype, element_balance)

        # セクション3: 第2部（魂の評議会）
        sections['soul_council'] = generate_soul_council_section(model, name, planets)

        # セクション4: 第3部（体質分析）
        sections['constitution'] = generate_constitution_section(model, name, element_balance)

        # セクション5: 第4部（処方箋）
        sections['prescription'] = generate_prescription_section(model, name, element_balance)

        # セクション6: 結び
        sections['conclusion'] = generate_conclusion_section(model, name)

    except Exception as e:
        logger.error(f"セクション生成エラー: {e}")
        return generate_fallback_sections(name, archetype)

    return sections

def generate_fallback_sections(name, archetype):
    """フォールバック用の簡易セクション生成"""
    return {
        'intro': f"# {name}様へ捧ぐ 占星医学体質鑑定書\n\n## 序章：星空からの招待状\n\n{name}様、この鑑定書はあなたの魂の設計図を解き明かすための特別な贈り物です。",
        'core_pattern': f"## 第1部：魂のコアパターン — {archetype}\n\n{name}様の魂の核心的なパターンをお伝えします。",
        'soul_council': f"## 第2部：あなたの魂の評議会\n\n{name}様の7惑星の詳細分析をお伝えします。",
        'constitution': f"## 第3部：占星医学体質分析\n\n{name}様の体質的特徴をお伝えします。",
        'prescription': f"## 第4部：統合ホリスティック処方箋\n\n{name}様の具体的なセルフケア提案をお伝えします。",
        'conclusion': f"## 結び：あなたという名の奇跡を生きる\n\n{name}様、あなたの人生は宇宙からの贈り物です。"
    }

# 以下、元のヘルパー関数群（省略されているが実装必要）
def generate_intro_section(model, name, birth_date, birth_time, birth_place):
    """序章生成"""
    try:
        prompt = f"""
{name}様の詳細鑑定書の序章を800-1000文字で作成してください。
出生データ: {birth_date} {birth_time} {birth_place}
温かく詩的な導入文で、エンターテインメント目的であることを自然に含めてください。
"""
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"# {name}様へ捧ぐ 占星医学体質鑑定書\n\n## 序章：星空からの招待状\n\n{name}様、この鑑定書はあなたの魂の設計図を解き明かすための特別な贈り物です。"

def generate_core_pattern_section(model, name, planets, archetype, element_balance):
    """コアパターン生成"""
    try:
        prompt = f"""
{name}様の16元型「{archetype}」について2000-2500文字で詳細分析してください。
エンターテインメント目的の体質傾向分析として、「傾向」「可能性」を使用してください。
"""
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"## 第1部：魂のコアパターン — {archetype}\n\n{name}様の魂の核心的なパターンをお伝えします。"

def generate_soul_council_section(model, name, planets):
    """魂の評議会生成"""
    try:
        prompt = f"{name}様の7惑星の詳細分析を2000-2500文字で作成してください。各惑星の傾向と活かし方を含めてください。"
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"## 第2部：あなたの魂の評議会\n\n{name}様の7惑星の詳細分析をお伝えします。"

def generate_constitution_section(model, name, element_balance):
    """体質分析生成"""
    try:
        prompt = f"{name}様の体質分析を1500-2000文字で作成してください。医療診断ではなく体質傾向として表現してください。"
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"## 第3部：占星医学体質分析\n\n{name}様の体質的特徴をお伝えします。"

def generate_prescription_section(model, name, element_balance):
    """処方箋生成"""
    try:
        prompt = f"{name}様の具体的なセルフケア処方箋を2000-2500文字で作成してください。食養生、アロマ、ライフスタイル提案を含めてください。"
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"## 第4部：統合ホリスティック処方箋\n\n{name}様の具体的なセルフケア提案をお伝えします。"

def generate_conclusion_section(model, name):
    """結び生成"""
    try:
        prompt = f"{name}様の鑑定書の結びを800-1000文字で作成してください。希望と励ましに満ちた内容で、最後にマントラを含めてください。"
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"## 結び：あなたという名の奇跡を生きる\n\n{name}様、あなたの人生は宇宙からの贈り物です。"

def determine_archetype(sun_sign, moon_sign):
    """太陽と月の星座から16元型を判定"""
    sun_element = SIGN_ELEMENTS.get(sun_sign, '火')
    moon_element = SIGN_ELEMENTS.get(moon_sign, '水')
    return ARCHETYPE_DATABASE.get((sun_element, moon_element), 'The Bedrock（岩盤）')

def calculate_element_balance(planets):
    """惑星配置からエレメントバランスを計算"""
    elements = {'火': 0, '地': 0, '風': 0, '水': 0}

    for planet_data in planets.values():
        element = planet_data.get('element', '火')
        if element in elements:
            elements[element] += 1

    total = sum(elements.values())
    if total > 0:
        return {k: round(v/total*100, 1) for k, v in elements.items()}
    return {'火': 25, '地': 25, '風': 25, '水': 25}

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy', 
        'service': '第4ステップ最終システム API - Phase 1 MVP版',
        'version': '1.0.0-beta',
        'endpoints': [
            '/api/calculate-planets',
            '/api/simple-diagnosis', 
            '/api/generate-detailed-report',
            '/health'
        ]
    })

@app.route('/', methods=['GET'])
def root():
    """ルートエンドポイント"""
    return jsonify({
        'service': '第4ステップ最終システム API - Phase 1 MVP版',
        'version': '1.0.0-beta',
        'status': 'beta',
        'description': '占星医学体質鑑定システム - エンターテインメント目的',
        'endpoints': {
            '/api/calculate-planets': '7天体位置計算',
            '/api/simple-diagnosis': '簡易体質診断',
            '/api/generate-detailed-report': '12,000文字詳細鑑定書生成',
            '/health': 'ヘルスチェック'
        },
        'note': 'ベータ版です。本結果はエンターテインメント目的であり、医療診断ではありません。'
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    """レート制限エラーハンドラ"""
    return jsonify({
        'success': False,
        'error': 'リクエストが多すぎます。しばらく時間をおいてから再試行してください。'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """内部エラーハンドラ"""
    logger.error(f"Internal error: {error}")
    return jsonify({
        'success': False,
        'error': 'システムエラーが発生しました。管理者にお問い合わせください。'
    }), 500

if __name__ == '__main__':
    print("🌟 第4ステップ最終システム APIサーバー - Phase 1 MVP版を起動中...")
    print("ポート: 8107")
    print("12,000文字詳細鑑定書生成システム")
    print("⚠️  ベータ版：エンターテインメント目的")

    # 環境変数チェック
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
    else:
        print("✅ Gemini API設定完了")

    print(f"🔑 ベータパスワード: {BETA_PASSWORD}")

    app.run(host='0.0.0.0', port=8107, debug=os.getenv('FLASK_ENV') == 'development')
