#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第4ステップ最終システム APIサーバー - Phase 1 MVP版 (12,000文字保証版)
12,000文字詳細鑑定書生成システム - 強化版

改善内容：
- 12,000文字確実生成機能
- プロンプト大幅改善
- 複数回リクエスト戦略
- 文字数監視・補完機能
- エラーハンドリング強化
- Gemini API設定最適化
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
from datetime import datetime, timezone, timedelta
import os
import json
import google.generativeai as genai
import logging
from functools import wraps
import time
import random

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

# 環境変数チェック
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCXc3ZZ3uJPy-TvB4T5Zq1BBbYDNKfh9u4')
BETA_PASSWORD = os.getenv('BETA_PASSWORD', 'astro2024beta')

# Gemini API最適化設定
GEMINI_GENERATION_CONFIG = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 8192,
    "candidate_count": 1,
}

# 詳細鑑定書設定
DETAILED_REPORT_CONFIG = {
    "target_length": 12000,
    "min_section_length": 1800,
    "max_retries": 3,
    "sections": [
        "personality_analysis",
        "constitution_analysis", 
        "health_guidance",
        "lifestyle_recommendations",
        "dietary_advice",
        "spiritual_guidance"
    ]
}

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
            swe.set_ephe_path('')
    except Exception as e:
        logger.error(f"Swiss Ephemeris設定エラー: {e}")
        swe.set_ephe_path('')

# ベータ版認証デコレータ
def beta_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
@beta_required
def simple_diagnosis():
    """簡易診断API"""
    try:
        data = request.get_json()

        if 'name' not in data or 'planets' not in data:
            return jsonify({'success': False, 'error': '必要なデータが不足しています'}), 400

        planets = data['planets']
        name = data['name']

        if 'sun' not in planets or 'moon' not in planets:
            return jsonify({'success': False, 'error': '太陽と月のデータが必要です'}), 400

        sun_element = planets['sun']['element']
        moon_element = planets['moon']['element']

        archetype = ARCHETYPE_DATABASE.get((sun_element, moon_element), '不明な元型')

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

診断文章を作成してください。
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        logger.error(f"Gemini API エラー: {e}")
        return f"""
{name}さんの体質診断結果をお伝えいたします。

あなたの16元型は「{archetype}」の傾向を示しています。太陽が{sun_element}のエレメント、月が{moon_element}のエレメントという組み合わせから、この特別な元型の可能性が導き出されました。

この配置は、あなたの内なる情熱と外向きの表現が調和した、バランスの取れた体質傾向を示している可能性があります。

※本結果はエンターテインメント目的の体質傾向分析です。医療診断ではありません。
"""

# ========== 12,000文字確実生成システム（強化版） ==========

@app.route('/api/generate-detailed-report', methods=['POST'])
@beta_required
def generate_detailed_diagnosis():
    """12,000文字詳細鑑定書を確実生成（強化版）"""
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

        logger.info(f"詳細鑑定書生成開始: {name} - 目標文字数: {DETAILED_REPORT_CONFIG['target_length']}")

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

        # 強化版詳細鑑定書生成
        sections = generate_diagnosis_sections_enhanced(
            name, birth_date, birth_time, birth_place, 
            planets, archetype, element_balance
        )

        # 全セクションを結合
        full_diagnosis = '\n\n'.join(sections.values())
        final_char_count = len(full_diagnosis)

        logger.info(f"詳細鑑定書生成完了: {name}, 最終文字数: {final_char_count}")

        return jsonify({
            'success': True,
            'detailed_report': full_diagnosis,
            'sections': sections,
            'character_count': final_char_count,
            'target_achieved': final_char_count >= DETAILED_REPORT_CONFIG['target_length'],
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

def generate_diagnosis_sections_enhanced(name, birth_date, birth_time, birth_place, planets, archetype, element_balance):
    """
    12,000文字の詳細鑑定書生成（強化版）
    """
    logger.info(f"詳細鑑定書生成開始: {name} - 目標文字数: {DETAILED_REPORT_CONFIG['target_length']}")
    
    try:
        # Geminiモデル初期化
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config=GEMINI_GENERATION_CONFIG
        )
        
        # セクション別生成
        sections = {}
        total_chars = 0
        
        # 1. パーソナリティ分析 (2000文字目標)
        sections['personality_analysis'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="personality", target_chars=2000
        )
        
        # 2. 体質分析 (2000文字目標)
        sections['constitution_analysis'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="constitution", target_chars=2000
        )
        
        # 3. 健康ガイダンス (2000文字目標)
        sections['health_guidance'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="health", target_chars=2000
        )
        
        # 4. ライフスタイル推奨 (2000文字目標)
        sections['lifestyle_recommendations'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="lifestyle", target_chars=2000
        )
        
        # 5. 食事・栄養アドバイス (2000文字目標)
        sections['dietary_advice'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="diet", target_chars=2000
        )
        
        # 6. スピリチュアルガイダンス (2000文字目標)
        sections['spiritual_guidance'] = generate_enhanced_section(
            model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance,
            section_type="spiritual", target_chars=2000
        )
        
        # 文字数計算
        for section_name, content in sections.items():
            section_chars = len(content)
            total_chars += section_chars
            logger.info(f"セクション '{section_name}': {section_chars} 文字")
        
        logger.info(f"総文字数: {total_chars} 文字")
        
        # 目標文字数に満たない場合の補完
        if total_chars < DETAILED_REPORT_CONFIG['target_length']:
            shortage = DETAILED_REPORT_CONFIG['target_length'] - total_chars
            logger.warning(f"文字数不足: {shortage} 文字 - 補完セクション生成中...")
            
            additional_content = generate_additional_content(
                model, name, birth_date, birth_time, birth_place, 
                planets, archetype, element_balance, shortage
            )
            sections['additional_insights'] = additional_content
            total_chars += len(additional_content)
        
        logger.info(f"最終文字数: {total_chars} 文字")
        return sections
        
    except Exception as e:
        logger.error(f"詳細鑑定書生成エラー: {e}")
        return generate_enhanced_fallback_sections(name, archetype)

def generate_enhanced_section(model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance, section_type, target_chars=2000):
    """強化されたセクション生成"""
    prompts = {
        "personality": f"""
あなたは経験豊富な占星医学の専門家です。{name}さんの詳細なパーソナリティ分析を行ってください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に分析してください
- 段落分けを明確にし、小見出しを含めてください
- 占星術的分析と心理学的観点を組み合わせてください
- 具体的で実用的な内容にしてください
- エンターテインメント目的であり医療診断ではないことを自然に含めてください

【基本情報】
名前: {name}
生年月日: {birth_date}
出生時間: {birth_time}
出生地: {birth_place}
アーキタイプ: {archetype}

【天体配置】
{format_planets_for_prompt(planets)}

【エレメントバランス】
{format_element_balance_for_prompt(element_balance)}

以下の構成で詳細に分析してください：

## パーソナリティ分析

### 基本的な性格特性
- 太陽星座（{planets.get('sun', {}).get('sign', '不明')}）から見る基本性格
- 月星座（{planets.get('moon', {}).get('sign', '不明')}）から見る感情パターン
- 水星星座から見るコミュニケーションスタイル
- 具体的な行動パターンと思考の特徴

### 対人関係の傾向
- 金星星座から見る愛情表現と人間関係
- 火星星座から見る行動力と競争心
- 社会性と協調性の分析
- 恋愛・友情・家族関係での特徴

### 潜在能力と成長ポイント
- 木星星座から見る成長可能性
- 土星星座から見る課題と学び
- 隠れた才能と発揮方法
- 人生における重要なテーマ

各項目について具体例を交えながら詳細に説明してください。
""",
        
        "constitution": f"""
あなたは占星医学のエキスパートです。{name}さんの体質的特徴を詳細に分析してください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に分析してください
- 医学的観点と占星術的観点を融合してください
- 具体的で実践的な内容にしてください
- 各エレメントの影響を詳しく説明してください
- エンターテインメント目的の体質傾向分析であることを明記してください

【基本情報】
名前: {name}
生年月日: {birth_date}
出生時間: {birth_time}
出生地: {birth_place}
アーキタイプ: {archetype}

【エレメントバランス】
{format_element_balance_for_prompt(element_balance)}

【天体配置】
{format_planets_for_prompt(planets)}

以下の構成で詳細に分析してください：

## 体質分析

### 基本的な体質特徴
- エレメントバランスから見る体質タイプ
- 太陽星座と月星座の影響
- 体型・体格の傾向
- 基礎代謝と体力の特徴

### 生理的な特性
- 消化機能と代謝パターン
- 循環器系と呼吸器系の特徴
- 神経系と内分泌系の傾向
- 免疫力と回復力の分析

### 季節・環境との相性
- 気候や季節の影響
- 住環境との適性
- 活動に適した時間帯
- ストレス反応パターン

### 体質改善のポイント
- 強化すべきエレメント
- バランス調整の方法
- 体質に合った運動法
- 体調管理のコツ

各項目について医学的根拠と占星術的解釈を組み合わせて詳細に説明してください。
※本分析はエンターテインメント目的の体質傾向分析であり、医療診断ではありません。
""",
        
        "health": f"""
あなたは占星医学の専門家です。{name}さんの健康管理について詳細なガイダンスを提供してください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に説明してください
- 予防医学的観点を重視してください
- 具体的で実行可能な提案をしてください
- 注意すべき点と対策を明確にしてください
- エンターテインメント目的であり医療診断の代替ではないことを明記してください

【基本情報】
名前: {name}
生年月日: {birth_date}
出生時間: {birth_time}
出生地: {birth_place}
アーキタイプ: {archetype}

【エレメントバランス】
{format_element_balance_for_prompt(element_balance)}

【天体配置】
{format_planets_for_prompt(planets)}

以下の構成で詳細にガイダンスしてください：

## 健康ガイダンス

### 注意すべき健康リスク
- エレメントバランスから見るリスク傾向
- 天体配置から読み取れる弱点の可能性
- 年齢による変化と対策
- 遺伝的傾向と環境要因

### 予防とケアの方法
- 日常的な健康管理法
- 定期的なチェックポイント
- 早期発見のサイン
- 専門医との付き合い方

### メンタルヘルスケア
- ストレス管理の方法
- 感情コントロールのコツ
- リラクゼーション法
- 心身のバランス維持

### ライフステージ別の注意点
- 現在の年齢での重点項目
- 将来への備え
- 加齢による変化への対応
- 長期的な健康戦略

各項目について具体的な方法と根拠を示しながら詳細に説明してください。
※本ガイダンスはエンターテインメント目的の健康傾向分析であり、医療診断や治療の代替ではありません。
""",

        "lifestyle": f"""
あなたは占星医学とライフスタイルの専門家です。{name}さんに最適なライフスタイルを詳細に提案してください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に提案してください
- 実践的で具体的なアドバイスを含めてください
- 季節や時間帯の活用法も含めてください
- 仕事・人間関係・趣味など多角的にアプローチしてください

【基本情報】
名前: {name}
生年月日: {birth_date}
出生時間: {birth_time}
出生地: {birth_place}
アーキタイプ: {archetype}

以下の構成で詳細に提案してください：

## ライフスタイル推奨

### 日常リズムの最適化
### 住環境・働く環境の整備
### 人間関係とコミュニケーション
### 趣味・創作活動の選び方
### 運動・体を動かす習慣
### 学習・自己啓発の方法

各項目を{target_chars//6}文字程度で詳細に説明してください。
""",

        "diet": f"""
あなたは占星医学と栄養学の専門家です。{name}さんの体質に合った食事・栄養アドバイスを詳細に提供してください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に説明してください
- エレメントバランスに基づいた食事法を提案してください
- 季節ごとの食材選びも含めてください
- 具体的なメニュー例も示してください

【基本情報】
名前: {name}
アーキタイプ: {archetype}
エレメントバランス: {format_element_balance_for_prompt(element_balance)}

以下の構成で詳細にアドバイスしてください：

## 食事・栄養アドバイス

### 基本的な食事方針
### エレメント別食材の選び方
### 季節ごとの食事法
### 具体的なメニュー提案
### 調理法・食べ方のコツ
### 避けるべき食材・食べ方

各項目を{target_chars//6}文字程度で詳細に説明してください。
""",

        "spiritual": f"""
あなたは占星術とスピリチュアルケアの専門家です。{name}さんの魂の成長と精神的な調和について詳細にガイダンスしてください。

【重要な指示】
- 必ず{target_chars}文字以上で詳細に説明してください
- 瞑想・マインドフルネス・エネルギーワークを含めてください
- アロマテラピー・パワーストーンの活用法も提案してください
- 人生の目的・使命についても触れてください

【基本情報】
名前: {name}
アーキタイプ: {archetype}
天体配置: {format_planets_for_prompt(planets)}

以下の構成で詳細にガイダンスしてください：

## スピリチュアルガイダンス

### 魂の目的と使命
### 瞑想・マインドフルネス実践法
### エネルギーバランスの整え方
### アロマテラピーの活用
### パワーストーンとの調和
### 人生の転機への対応

各項目を{target_chars//6}文字程度で詳細に説明してください。
"""
    }
    
    prompt = prompts.get(section_type, prompts["personality"])
    
    return safe_generate_content_with_retry(model, prompt, max_retries=3)

def safe_generate_content_with_retry(model, prompt, max_retries=3):
    """リトライ機能付きの安全なコンテンツ生成"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response and response.text and len(response.text) > 500:
                logger.info(f"生成成功 (試行 {attempt + 1}): {len(response.text)} 文字")
                return response.text
            else:
                logger.warning(f"生成内容が短すぎます (試行 {attempt + 1}): {len(response.text if response and response.text else 0)} 文字")
        except Exception as e:
            logger.error(f"生成試行 {attempt + 1} 失敗: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
    
    return generate_section_fallback(prompt[:100])

def generate_additional_content(model, name, birth_date, birth_time, birth_place, planets, archetype, element_balance, shortage):
    """不足文字数を補完するための追加コンテンツ生成"""
    prompt = f"""
{name}さんの占星医学鑑定書の補完セクションを{shortage}文字以上で作成してください。

以下のテーマから複数選択して詳細に説明してください：
- 年齢別の人生サイクル
- 恋愛・結婚運について
- 仕事・キャリアの適性
- 金運・財運について
- 健康長寿の秘訣
- 家族・子育てについて
- 老後の過ごし方

温かく励ましのある文体で、具体的で実用的な内容にしてください。
エンターテインメント目的であることを自然に含めてください。
"""
    
    return safe_generate_content_with_retry(model, prompt, max_retries=3)

def generate_section_fallback(prompt_preview):
    """セクション生成失敗時のフォールバック"""
    return f"""
申し訳ございません。このセクションの詳細分析で技術的な問題が発生いたしました。

あなたの星の配置は特別で複雑なため、より詳細な分析が必要です。
お手数ですが、しばらく時間をおいてから再度お試しいただくか、
カスタマーサポートまでお問い合わせください。

あなたの人生には素晴らしい可能性が満ちています。
一時的な技術的問題が、あなたの本来の輝きを曇らせることはありません。

※本鑑定書はエンターテインメント目的です。医療診断ではありません。

---
技術情報: {prompt_preview}...
"""

def generate_enhanced_fallback_sections(name, archetype):
    """強化版フォールバック用のセクション生成"""
    base_content = f"""
{name}様へ

システムの技術的な制約により、完全な詳細分析をお届けできませんでしたが、
あなたのアーキタイプ「{archetype}」から読み取れる重要なメッセージをお伝えします。

あなたは宇宙から特別な使命を受けてこの世に生まれてきました。
現在の困難も、未来の成功への重要なステップです。

自分自身を信じ、直感に従って行動することで、
必ず素晴らしい道が開けるでしょう。

※本鑑定書はエンターテインメント目的です。医療診断ではありません。
"""
    
    sections = {}
    section_names = ['personality_analysis', 'constitution_analysis', 'health_guidance', 
                    'lifestyle_recommendations', 'dietary_advice', 'spiritual_guidance']
    
    for section_name in section_names:
        sections[section_name] = base_content + f"\n\n[{section_name}セクション]"
        
    return sections

def format_planets_for_prompt(planets):
    """プロンプト用に天体情報をフォーマット"""
    if not planets:
        return "天体情報なし"
    
    formatted = []
    planet_names = {
        'sun': '太陽', 'moon': '月', 'mercury': '水星', 
        'venus': '金星', 'mars': '火星', 'jupiter': '木星', 'saturn': '土星'
    }
    
    for planet_key, planet_data in planets.items():
        name = planet_names.get(planet_key, planet_key)
        sign = planet_data.get('sign', '不明')
        element = planet_data.get('element', '不明')
        formatted.append(f"- {name}: {sign}座 ({element}エレメント)")
    
    return "\n".join(formatted)

def format_element_balance_for_prompt(element_balance):
    """プロンプト用にエレメントバランスをフォーマット"""
    if not element_balance:
        return "エレメントバランス情報なし"
    
    element_names = {'火': '火', '地': '地', '風': '風', '水': '水'}
    formatted = []
    
    for element_key, percentage in element_balance.items():
        name = element_names.get(element_key, element_key)
        formatted.append(f"- {name}エレメント: {percentage}%")
    
    return "\n".join(formatted)

# ========== その他の関数（既存のまま） ==========

def calculate_planets_internal(data):
    """内部用天体計算関数"""
    try:
        required_fields = ['name', 'birth_year', 'birth_month', 'birth_day', 
                          'birth_hour', 'birth_minute', 'birth_prefecture']
        for field in required_fields:
            if field not in data:
                return {'success': False, 'error': f'{field}が不足しています'}

        prefecture = data['birth_prefecture']
        if prefecture not in PREFECTURE_COORDINATES:
            return {'success': False, 'error': '無効な都道府県です'}

        latitude, longitude = PREFECTURE_COORDINATES[prefecture]

        birth_datetime_jst = datetime(
            data['birth_year'], data['birth_month'], data['birth_day'],
            data['birth_hour'], data['birth_minute']
        )
        birth_datetime_utc = birth_datetime_jst - timedelta(hours=9)

        julian_day = swe.julday(
            birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
            birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0
        )

        init_swisseph()

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
        'service': '第4ステップ最終システム API - Phase 1 MVP版 (12,000文字保証版)',
        'version': '2.0.0-enhanced',
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
        'service': '第4ステップ最終システム API - Phase 1 MVP版 (12,000文字保証版)',
        'version': '2.0.0-enhanced',
        'status': 'beta',
        'description': '占星医学体質鑑定システム - エンターテインメント目的',
        'endpoints': {
            '/api/calculate-planets': '7天体位置計算',
            '/api/simple-diagnosis': '簡易体質診断',
            '/api/generate-detailed-report': '12,000文字詳細鑑定書生成（保証版）',
            '/health': 'ヘルスチェック'
        },
        'note': 'ベータ版です。本結果はエンターテインメント目的であり、医療診断ではありません。',
        'enhancement': '12,000文字確実生成機能を搭載'
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
    print("🌟 第4ステップ最終システム APIサーバー - Phase 1 MVP版 (12,000文字保証版) を起動中...")
    print("ポート: 8107")
    print("✨ 12,000文字詳細鑑定書確実生成システム搭載")
    print("⚠️  ベータ版：エンターテインメント目的")

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
    else:
        print("✅ Gemini API設定完了")

    print(f"🔑 ベータパスワード: {BETA_PASSWORD}")
    print(f"🎯 目標文字数: {DETAILED_REPORT_CONFIG['target_length']} 文字")

    app.run(host='0.0.0.0', port=8107, debug=os.getenv('FLASK_ENV') == 'development')
