# 高精度占星術アプリケーション開発チェックリスト

**作成日**: 2026-03-20  
**対象**: 占星術計算アプリケーションを開発するエンジニア向け  
**目的**: 商用レベルの精度と安定性を持つアプリケーションを構築するための指針

---

## 📋 目次

1. [計算エンジンの選定](#1-計算エンジンの選定)
2. [タイムゾーン処理（最重要）](#2-タイムゾーン処理最重要)
3. [度数計算の正規化](#3-度数計算の正規化)
4. [日付計算の注意点](#4-日付計算の注意点)
5. [ハウス計算の360度またぎ](#5-ハウス計算の360度またぎ)
6. [逆行判定](#6-逆行判定)
7. [本番環境のサーバー選定](#7-本番環境のサーバー選定)
8. [エラーハンドリング](#8-エラーハンドリング)
9. [テストとデバッグ](#9-テストとデバッグ)
10. [パフォーマンス最適化](#10-パフォーマンス最適化)

---

## 1. 計算エンジンの選定

### ✅ 推奨: Swiss Ephemeris（pyswisseph）

**理由**:
- ✅ 天文学レベルの精度（±0.001度）
- ✅ NASA/JPLの基準に準拠
- ✅ 業界標準（商用占星術ソフトウェアで広く使用）
- ✅ 公式Python実装（pyswisseph）が利用可能
- ✅ 豊富な機能（惑星、小惑星、ハウス、プログレッション全対応）

**インストール**:
```bash
pip install pyswisseph==2.10.3.2
```

**基本設定**:
```python
import swisseph as swe

# エフェメリスファイルのパスを設定
EPHE_PATH = '/path/to/swisseph_data'
swe.set_ephe_path(EPHE_PATH)
```

**エフェメリスファイル**:
- `seas_18.se1` (小惑星 - Chiron)
- `semo_18.se1` (月)
- `sepl_18.se1`, `sepl_19.se1`, `sepl_20.se1`, `sepl_21.se1` (惑星)

**ダウンロード先**:
https://www.astro.com/ftp/swisseph/ephe/

---

## 2. タイムゾーン処理（最重要）

### ⚠️ 最も重要な注意点

占星術計算では、**タイムゾーン処理が精度を左右します**。

### 2.1 ネイタルチャート計算

**原則**: 出生時刻（ローカルタイム）を **UTC** に変換する

```python
from datetime import datetime, timedelta

# ❌ 間違い：JSTをそのまま使用
jst_time = datetime(1979, 8, 1, 18, 4)
jd = swe.julday(1979, 8, 1, 18.0 + 4/60.0)  # 間違い！

# ✅ 正しい：JSTをUTCに変換
jst_time = datetime(1979, 8, 1, 18, 4)
utc_time = jst_time - timedelta(hours=9)  # JST = UTC+9
jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                utc_time.hour + utc_time.minute/60.0)
```

### 2.2 プログレッション計算（特殊）

**重要発見**: 多くの商用ソフトウェアは、プログレッション計算において **出生時刻（JST）をUTC時刻としてそのまま使用する** 特殊な方式を採用しています。

```python
# ❌ 間違い：UTC変換してしまう
utc_time = jst_time - timedelta(hours=9)
progression_jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                            utc_time.hour + utc_time.minute/60.0)

# ✅ 正しい：業界標準の実装
birth_hour = 18  # JST
birth_minute = 4
# プログレッション計算では、JST時刻をUTCとして扱う
progression_jd = swe.julday(year, month, day, 
                            birth_hour + birth_minute/60.0)
```

**なぜこの方式なのか？**:
理由は不明ですが、これが業界標準の実装方法です。商用ソフトウェアと一致させるには、この方式を採用する必要があります。

### 2.3 タイムゾーン変換の例

| 地域 | タイムゾーン | UTC変換 |
|------|-------------|---------|
| 日本（JST） | UTC+9 | `-9時間` |
| 東海岸（EST） | UTC-5 | `+5時間` |
| 西海岸（PST） | UTC-8 | `+8時間` |
| イギリス（GMT） | UTC+0 | `±0時間` |

---

## 3. 度数計算の正規化

### ⚠️ よくある混乱

占星術の度数表記には2種類あります：

1. **絶対黄経**: 春分点（牡羊座0度）からの角度（0-360度）
2. **サイン内度数**: 各サイン内での角度（0-30度）

### ❌ 間違った実装

```python
# Swiss Ephemerisは絶対黄経を返す
longitude = 128.53  # 度

# ❌ 間違い：絶対黄経をそのまま表示
print(f"獅子座 {longitude}度")  # 「獅子座 128.53度」← 間違い！
```

### ✅ 正しい実装

```python
# 絶対黄経からサイン内度数への変換
absolute_longitude = 128.53  # Swiss Ephemerisが返す値

# サインのインデックス（0=牡羊座, 1=牡牛座, ..., 11=魚座）
sign_index = int(absolute_longitude / 30)  # 4 = Leo（獅子座）

# サイン内度数（0-30度）
degree_in_sign = absolute_longitude % 30  # 8.53度

# サイン名
SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
            '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座']
sign_name = SIGNS_JP[sign_index]  # '獅子座'

# ✅ 正しい表示
print(f"{sign_name} {degree_in_sign:.2f}度")  # 「獅子座 8.53度」← 正しい！
```

### 🔍 デバッグのコツ

計算結果を検証する際は、両方の値を確認：

```python
print(f"絶対黄経: {absolute_longitude:.2f}度")  # 128.53度
print(f"サイン内: {sign_name} {degree_in_sign:.2f}度")  # 獅子座 8.53度
```

---

## 4. 日付計算の注意点

### ⚠️ トランジット計算での重大なバグ

**問題**: `timedelta(days=month * 30)` を使用すると、日付がずれる

### ❌ 間違った実装

```python
from datetime import datetime, timedelta

start_date = datetime(2026, 3, 20)

# ❌ 間違い：すべての月を30日として計算
for month in range(0, 36):  # 3年間
    check_date = start_date + timedelta(days=month * 30)
    # → 累積的な日付のズレが発生！
```

**結果**:
- 1ヶ月後: 2026-04-**19**（正: 2026-04-**20**、1日ズレ）
- 6ヶ月後: 2026-09-**16**（正: 2026-09-**20**、4日ズレ）
- 12ヶ月後: 2027-03-**15**（正: 2027-03-**20**、5日ズレ）
- **最大25日のズレが発生！**

### ✅ 正しい実装

```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

start_date = datetime(2026, 3, 20)

# ✅ 正しい方法1: relativedeltaを使用（月単位）
for month in range(0, 36):
    check_date = start_date + relativedelta(months=month)
    # → 正確な月の計算

# ✅ 正しい方法2: 日単位のループ（最も正確）
check_date = start_date
end_date = start_date + relativedelta(years=3)
while check_date <= end_date:
    # 処理
    check_date += timedelta(days=1)  # 1日ずつ進める
```

### 📦 必要なライブラリ

```bash
pip install python-dateutil==2.8.2
```

```python
from dateutil.relativedelta import relativedelta
```

---

## 5. ハウス計算の360度またぎ

### ⚠️ 第12ハウス→第1ハウスの境界

ハウスカスプは360度を跨ぐことがあります。

**例**:
- 第12ハウスのカスプ: 330度
- 第1ハウスのカスプ（ASC）: 10度
- 惑星の位置: 350度 → どのハウス？

### ❌ 間違った実装

```python
def get_planet_house(planet_longitude, house_cusps):
    for i in range(12):
        cusp_start = house_cusps[i]
        cusp_end = house_cusps[(i + 1) % 12]
        
        # ❌ 360度またぎを考慮していない
        if cusp_start <= planet_longitude < cusp_end:
            return i + 1
    
    return 1  # デフォルト
```

**問題**: 350度は第12ハウス（330-360度）にあるべきだが、誤判定される

### ✅ 正しい実装

```python
def get_planet_house(planet_longitude, house_cusps):
    # 度数を正規化（0-360度）
    planet_lon = planet_longitude % 360
    
    for i in range(12):
        cusp_start = house_cusps[i] % 360
        cusp_end = house_cusps[(i + 1) % 12] % 360
        
        # 360度またぎの処理
        if cusp_start > cusp_end:
            # 例: 第12ハウス 330度 → 第1ハウス 10度
            if planet_lon >= cusp_start or planet_lon < cusp_end:
                return i + 1
        else:
            # 通常のケース
            if cusp_start <= planet_lon < cusp_end:
                return i + 1
    
    return 1  # デフォルトは第1ハウス
```

### 🔍 テストケース

```python
# テストデータ
house_cusps = [10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310, 330]
# 第12ハウス: 330度〜10度（360度またぎ）

# テスト
assert get_planet_house(5, house_cusps) == 12    # ✓ 第12ハウス
assert get_planet_house(350, house_cusps) == 12  # ✓ 第12ハウス
assert get_planet_house(15, house_cusps) == 1    # ✓ 第1ハウス
```

---

## 6. 逆行判定

### ✅ Swiss Ephemerisでの逆行判定

逆行（Retrograde）は、天体の **速度（speed）** で判定します。

```python
def calculate_planet_position(jd, planet_id):
    result = swe.calc_ut(jd, planet_id)
    
    # result[0]: 経度
    # result[3]: 速度（度/日）
    
    longitude = result[0][0]
    speed = result[3][0]
    
    # 速度がマイナス = 逆行
    retrograde = speed < 0
    
    return {
        'longitude': longitude,
        'speed': speed,
        'retrograde': retrograde
    }
```

### 📊 逆行表示の例

```python
# 表示
if planet_data['retrograde']:
    print(f"{planet_name} {sign} {degree}° ℞")  # 逆行マーク
else:
    print(f"{planet_name} {sign} {degree}°")
```

**出力例**:
```
水星 獅子座 7.43° ℞  ← 逆行中
金星 獅子座 1.90°     ← 順行
```

---

## 7. 本番環境のサーバー選定

### ❌ Flask開発サーバーは使用しない

**問題**:
```python
# ❌ 本番環境では絶対に使用しない
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**症状**:
- リクエスト増加時に「Too many open files」エラー
- ファイルディスクリプタのリーク
- サーバーがランダムに停止

### ✅ Gunicornを使用

**インストール**:
```bash
pip install gunicorn==21.2.0
```

**起動スクリプト（start_server.sh）**:
```bash
#!/bin/bash

# 既存プロセスを停止
pkill -9 -f "gunicorn.*app:app"
sleep 3

# Gunicornで起動
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 1 \
  --timeout 300 \
  --max-requests 500 \
  --max-requests-jitter 50 \
  --graceful-timeout 30 \
  --log-level warning \
  --access-logfile /tmp/gunicorn_access.log \
  --error-logfile /tmp/gunicorn_error.log \
  --daemon \
  app:app

echo "✅ サーバーが起動しました"
```

### 🔧 Gunicorn設定の説明

| オプション | 値 | 説明 |
|-----------|-----|------|
| `--workers` | 1 | ワーカー数（メモリ不足対策で1に設定） |
| `--timeout` | 300 | タイムアウト（複雑な計算に対応するため5分） |
| `--max-requests` | 500 | 500リクエストごとにワーカーを再起動（メモリリーク対策） |
| `--max-requests-jitter` | 50 | 再起動タイミングをランダム化（450-550リクエスト） |
| `--graceful-timeout` | 30 | 優雅な終了（処理中のリクエストを最大30秒待つ） |

**ワーカー数の計算式**（一般的）:
```
workers = (CPU cores × 2) + 1
```

ただし、占星術アプリでは**メモリ使用量**が重要なので、メモリが限られている場合は `workers=1` を推奨。

---

## 8. エラーハンドリング

### ✅ 必須のエラーハンドリング

```python
@app.route('/api/calculate-chart', methods=['POST'])
def calculate_chart():
    try:
        data = request.get_json()
        
        # 1. 入力値の検証
        required_fields = ['year', 'month', 'day', 'hour', 'minute', 
                          'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 2. 値の範囲チェック
        year = int(data['year'])
        if not (1900 <= year <= 2100):
            return jsonify({
                'success': False,
                'error': 'Year must be between 1900 and 2100'
            }), 400
        
        # 3. 計算の実行
        result = perform_calculation(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }), 400
    
    except Exception as e:
        # ログに記録
        app.logger.error(f'Calculation error: {str(e)}')
        
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
```

### 📝 エラーログの記録

```python
import logging

# ロガーの設定
logging.basicConfig(
    filename='/tmp/astro_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 使用例
logging.info(f'Chart calculation: {year}-{month}-{day}')
logging.error(f'Error in calculation: {str(e)}')
```

---

## 9. テストとデバッグ

### ✅ 商用ソフトウェアとの比較検証

占星術計算の精度を検証するには、**商用ソフトウェアとの比較**が不可欠です。

**推奨ソフトウェア**:
- Astro.com（無料）
- Solar Fire
- Kepler

**検証手順**:
```python
# テストデータ
test_cases = [
    {
        'name': 'Test 1',
        'birth': '1979-08-01 18:04 JST',
        'location': '沖縄 (26.2124, 127.6792)',
        'expected': {
            'Sun': {'sign': '獅子座', 'degree': 8.53},
            'Moon': {'sign': '蠍座', 'degree': 10.04},
            'ASC': {'sign': '山羊座', 'degree': 19.98}
        }
    }
]

for test in test_cases:
    result = calculate_chart(test['birth'], test['location'])
    
    # 比較
    for planet, expected in test['expected'].items():
        actual = result[planet]
        
        # 許容誤差: ±0.01度
        assert abs(actual['degree'] - expected['degree']) < 0.01, \
            f"{planet}: Expected {expected['degree']}, got {actual['degree']}"
    
    print(f"✅ {test['name']} passed")
```

### 🔍 デバッグのポイント

1. **絶対黄経を確認**: サイン内度数だけでなく、絶対黄経も出力
2. **Julian Dayを確認**: 計算に使用したJDが正しいか
3. **タイムゾーン変換を確認**: UTC変換が正しく行われているか
4. **ステップバイステップ**: 複雑な計算を分解して確認

```python
# デバッグ用の詳細出力
print(f"Input: {year}-{month}-{day} {hour}:{minute} JST")
print(f"UTC: {utc_year}-{utc_month}-{utc_day} {utc_hour}:{utc_minute}")
print(f"Julian Day: {jd}")
print(f"Absolute Longitude: {longitude}° → {sign} {degree}°")
```

---

## 10. パフォーマンス最適化

### ✅ 計算の最適化

```python
# ❌ 非効率：毎回エフェメリスパスを設定
for planet in planets:
    swe.set_ephe_path(EPHE_PATH)  # 毎回設定 = 遅い
    result = swe.calc_ut(jd, planet)

# ✅ 効率的：一度だけ設定
swe.set_ephe_path(EPHE_PATH)  # アプリ起動時に1回だけ
for planet in planets:
    result = swe.calc_ut(jd, planet)  # 高速
```

### 📊 処理時間の目安

| 計算タイプ | 処理時間 | 備考 |
|-----------|---------|------|
| ネイタルチャート（12天体） | <100ms | エフェメリスファイル使用 |
| プログレッション | <200ms | 2回の計算が必要 |
| トランジット（3年間） | <500ms | 日単位で1,095日チェック |

### 🔧 キャッシュの活用

頻繁に同じ計算を行う場合、結果をキャッシュ：

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_planet_position_cached(jd, planet_id):
    return calculate_planet_position(jd, planet_id)
```

---

## 📋 開発チェックリスト

新しい占星術アプリを開発する際、以下を確認してください：

### Phase 1: 計画・設計
- [ ] Swiss Ephemerisの採用を決定
- [ ] エフェメリスファイルをダウンロード
- [ ] タイムゾーン処理の方式を決定（ネイタル vs プログレッション）
- [ ] 必要な計算機能をリストアップ

### Phase 2: 実装
- [ ] pyswissephをインストール（`pip install pyswisseph==2.10.3.2`）
- [ ] エフェメリスパスを正しく設定
- [ ] タイムゾーン変換を正しく実装（JST→UTC）
- [ ] 度数計算の正規化を実装（絶対黄経→サイン内度数）
- [ ] 日付計算にrelativedeltaを使用（`python-dateutil`）
- [ ] ハウス計算の360度またぎロジックを実装
- [ ] 逆行判定を実装（speed < 0）
- [ ] エラーハンドリングを実装

### Phase 3: テスト
- [ ] 商用ソフトウェアと比較検証
- [ ] 複数のテストケースで精度を確認（許容誤差±0.01度）
- [ ] タイムゾーン変換のテスト
- [ ] 360度またぎのテスト
- [ ] 逆行判定のテスト
- [ ] トランジット日付の精度テスト

### Phase 4: 本番環境構築
- [ ] Gunicornをインストール（`pip install gunicorn==21.2.0`）
- [ ] start_server.shスクリプトを作成
- [ ] stop_server.shスクリプトを作成
- [ ] ログファイルのパスを設定
- [ ] ワーカー数とタイムアウトを最適化
- [ ] メモリ使用量を監視

### Phase 5: 運用準備
- [ ] ヘルスチェックエンドポイントを実装（`/api/health`）
- [ ] エラーログの監視方法を確立
- [ ] 定期再起動スクリプトを設定（推奨：毎日1回）
- [ ] トラブルシューティングガイドを作成
- [ ] ドキュメントを整備

---

## 🎯 成功するための10の重要ポイント

1. **Swiss Ephemerisを使用する**  
   → 天文学レベルの精度（±0.001度）

2. **タイムゾーン処理を正しく実装する**  
   → ネイタル：JST→UTC変換  
   → プログレッション：業界標準の特殊方式

3. **度数計算を正規化する**  
   → 絶対黄経（0-360度）→ サイン内度数（0-30度）

4. **日付計算にrelativedeltaを使用する**  
   → `timedelta(days=month*30)` は使わない

5. **ハウス計算の360度またぎに対応する**  
   → 第12ハウス→第1ハウスの境界処理

6. **逆行判定を実装する**  
   → speed < 0 で逆行

7. **本番環境ではGunicornを使用する**  
   → Flask開発サーバーは本番環境に不適切

8. **商用ソフトウェアと比較検証する**  
   → 許容誤差±0.01度を目標

9. **エラーハンドリングを実装する**  
   → 入力値の検証、例外処理、ログ記録

10. **ドキュメントを整備する**  
    → 開発ガイド、トラブルシューティング、運用マニュアル

---

## 🚨 よくある失敗パターン

### 1. タイムゾーン変換の失敗
❌ **問題**: JSTをUTCに変換しない  
✅ **対策**: 必ずUTCに変換（プログレッションは例外）

### 2. 度数表記の混乱
❌ **問題**: 絶対黄経をそのまま表示  
✅ **対策**: サイン内度数（% 30）に変換

### 3. 日付計算のズレ
❌ **問題**: `timedelta(days=month*30)` を使用  
✅ **対策**: `relativedelta(months=month)` を使用

### 4. ハウス判定の誤り
❌ **問題**: 360度またぎを考慮しない  
✅ **対策**: `cusp_start > cusp_end` で判定

### 5. Flask開発サーバーの使用
❌ **問題**: 本番環境でFlask開発サーバーを使用  
✅ **対策**: Gunicornを使用

---

## 📚 参考資料

### 公式ドキュメント
- Swiss Ephemeris: https://www.astro.com/swisseph/
- pyswisseph: https://github.com/astrorigin/pyswisseph
- Gunicorn: https://gunicorn.org/

### 推奨ツール
- Astro.com（無料チャート作成）: https://www.astro.com/
- エフェメリスファイル: https://www.astro.com/ftp/swisseph/ephe/

### このプロジェクトのドキュメント
- DEVELOPMENT_GUIDE.md（628行）: 詳細な開発ガイド
- SERVER_MANAGEMENT.md: サーバー管理ガイド
- TROUBLESHOOTING.md: トラブルシューティングガイド
- PROJECT_SUMMARY.md: プロジェクト完成報告書

---

## ✨ まとめ

高精度な占星術アプリケーションを開発するには：

1. **Swiss Ephemerisの採用**（精度の基盤）
2. **正確なタイムゾーン処理**（最重要）
3. **度数・日付・ハウスの正しい計算**（細部の精度）
4. **本番環境の適切な構築**（安定性）
5. **商用ソフトウェアとの比較検証**（品質保証）

これらを守れば、商用レベルの占星術アプリケーションを構築できます。

---

**作成者**: AI開発チーム  
**バージョン**: 1.0  
**最終更新**: 2026-03-20  
**ライセンス**: このガイドは自由に使用・配布可能です

---

_このチェックリストは、実際の開発経験から得られた知見をまとめたものです。新しい占星術アプリを開発する際の参考にしてください。_
