#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開運言霊占星術師 - Flaskアプリケーション
誕生日から開運アドバイスプロンプトを生成
"""

from flask import Flask, render_template, request, redirect, url_for
from fortune_calculator import calculate_full_fortune_data
from fortune_prompt_generator import generate_fortune_prompt
from datetime import datetime

app = Flask(__name__, template_folder='fortune_templates')


@app.route('/')
def index():
    """トップページ - 入力フォーム"""
    return render_template('fortune_input.html')


@app.route('/generate-fortune', methods=['POST'])
def generate_fortune():
    """フォームデータを受け取り、開運プロンプトを生成"""
    try:
        # フォームデータを取得
        birth_date = request.form.get('birth_date')
        birth_time = request.form.get('birth_time')
        prefecture = request.form.get('prefecture')
        
        # 日付と時刻をパース
        date_parts = birth_date.split('-')
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        
        time_parts = birth_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # 占星術計算を実行
        fortune_data = calculate_full_fortune_data(year, month, day, hour, minute, prefecture)
        
        # プロンプトを生成
        prompt = generate_fortune_prompt(fortune_data)
        
        # 結果ページに表示するデータを準備
        result_data = {
            'prompt': prompt,
            'birth_info': fortune_data['birth_info'],
            'natal': fortune_data['natal'],
            'progression': fortune_data['progression'],
            'transits': fortune_data['transits'],
            'solar_return': fortune_data['solar_return']
        }
        
        return render_template('fortune_result.html', **result_data)
    
    except Exception as e:
        # エラーが発生した場合
        error_message = f"エラーが発生しました: {str(e)}"
        return f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>エラー</title>
            <style>
                body {{
                    font-family: sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .error-box {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                }}
                h1 {{
                    color: #e74c3c;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #555;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                a {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                }}
                a:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>⚠️ エラー</h1>
                <p>{error_message}</p>
                <p>入力内容を確認して、もう一度お試しください。</p>
                <a href="/">← 入力フォームに戻る</a>
            </div>
        </body>
        </html>
        """


@app.route('/health')
def health():
    """ヘルスチェック用エンドポイント"""
    return {
        'status': 'healthy',
        'app': '開運言霊占星術師',
        'timestamp': datetime.now().isoformat()
    }


if __name__ == '__main__':
    print("="*60)
    print("🌟 開運言霊占星術師 - アプリケーション起動 🌟")
    print("="*60)
    print("\n📍 アクセス先: http://localhost:8000/")
    print("💡 Ctrl+C で終了します\n")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
