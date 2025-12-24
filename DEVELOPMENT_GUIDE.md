# 高精度占星術アプリケーション開発ガイド

## 📚 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [技術選定の重要ポイント](#技術選定の重要ポイント)
3. [計算精度を保証する実装方法](#計算精度を保証する実装方法)
4. [よくある落とし穴と対策](#よくある落とし穴と対策)
5. [パフォーマンスと安定性](#パフォーマンスと安定性)
6. [テストとデバッグ](#テストとデバッグ)
7. [デプロイと運用](#デプロイと運用)

---

## プロジェクト概要

### 完成したアプリケーション
**西洋占星術プロンプトジェネレーター**
- Swiss Ephemeris（±0.001度精度）による高精度天体計算
- 12天体 + ASC/MC のネイタルチャート
- セカンダリープログレッション（進行図）
- 3年間のトランジット予測
- 日本47都道府県対応

### 技術スタック
- **バックエンド**: Python 3.12 + Flask 2.3.3
- **天体計算**: pyswisseph 2.10.3.2
- **WSGIサーバー**: Gunicorn 21.2.0
- **フロントエンド**: Pure HTML/CSS/JavaScript

---

## 技術選定の重要ポイント

### 1. 天体計算エンジンの選択

#### ❌ 避けるべき選択
```javascript
// JavaScriptの簡易計算ライブラリ
// 精度が不十分（±1度以上の誤差）
const astro = require('some-simple-astro-lib');
```

#### ✅ 推奨される選択
```python
# Swiss Ephemeris - 天文学レベルの精度
import swisseph as swe

# 精度: ±0.001度
# 対応期間: 紀元前13000年〜紀元後17000年
# NASA/JPL標準準拠
```

**なぜSwiss Ephemerisを選ぶべきか:**
1. **天文学レベルの精度**: NASAのJPL Ephemerisと同等
2. **業界標準**: プロの占星術師が使用する計算エンジン
3. **長期間対応**: 過去・未来の計算が可能
4. **小惑星対応**: Chiron, Lilithなど特殊な天体も計算可能

### 2. 言語とフレームワーク

#### なぜPython + Flaskを選んだか

```python
# Python選択の理由
1. pyswisseph の公式サポート
2. 科学計算ライブラリの充実
3. 数値計算の精度が高い
4. デバッグが容易
```

#### 代替案との比較

| 項目 | Python + pyswisseph | JavaScript + swisseph.js | PHP + sweph |
|------|-------------------|------------------------|-------------|
| 精度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| ドキュメント | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| メンテナンス性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 計算精度を保証する実装方法

### 1. タイムゾーン処理（最重要）

#### ❌ よくある間違い
```python
# 間違い1: JST時刻をそのままUTCとして使用
jd = swe.julday(year, month, day, hour + minute / 60.0)  # NG!

# 間違い2: タイムゾーン変換の方向を間違える
utc_hour = jst_hour + 9  # 逆！これは間違い
```

#### ✅ 正しい実装
```python
from datetime import datetime, timedelta

# JST → UTC変換（9時間引く）
jst_datetime = datetime(year, month, day, hour, minute)
utc_datetime = jst_datetime - timedelta(hours=9)

# Swiss Ephemerisに渡す
jd = swe.julday(
    utc_datetime.year,
    utc_datetime.month,
    utc_datetime.day,
    utc_datetime.hour + utc_datetime.minute / 60.0
)
```

**重要なポイント:**
1. Swiss Ephemerisは**常にUTC時刻**を期待する
2. ユーザー入力はローカル時刻（JST等）なので変換が必要
3. JST = UTC+9 なので、**9時間引く**（足すではない）
4. 日付をまたぐ場合も`datetime`で自動処理

### 2. エフェメリスファイルの管理

#### ファイル配置の重要性
```python
import os
import swisseph as swe

# プロジェクトルートからの相対パス
EPHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    'swisseph_data'
)

# パス設定（グローバルで効かない場合があるため注意）
if os.path.exists(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)
```

#### 必要なエフェメリスファイル
```bash
swisseph_data/
├── sepl_18.se1  # 惑星データ（1800-1899年）
├── sepl_19.se1  # 惑星データ（1900-1999年）
├── sepl_20.se1  # 惑星データ（2000-2099年）
├── sepl_21.se1  # 惑星データ（2100-2199年）
├── semo_18.se1  # 月データ
└── seas_18.se1  # 小惑星データ（Chiron等）
```

**ダウンロード元:**
```bash
# Swiss Ephemeris公式サイト
https://www.astro.com/ftp/swisseph/ephe/

# 必要最小限のファイル
wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/sepl_19.se1
wget https://www.astro.com/ftp/swisseph/ephe/sepl_20.se1
wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/seas_18.se1
```

### 3. 天体位置計算の実装

```python
def calculate_planet_position(jd, planet_id):
    """
    天体位置を計算（エラーハンドリング込み）
    """
    try:
        # エフェメリスパスを毎回設定（重要）
        swe.set_ephe_path(EPHE_PATH)
        
        # 計算実行
        result = swe.calc_ut(jd, planet_id)
        position = result[0]
        
        # 黄経（0-360度に正規化）
        longitude = position[0] % 360
        
        # サイン計算
        sign_index = int(longitude // 30) % 12
        degree_in_sign = longitude % 30
        
        return {
            'longitude': round(longitude, 6),     # 絶対黄経
            'sign': SIGNS[sign_index],            # サイン（英語）
            'signJP': SIGNS_JP[sign_index],       # サイン（日本語）
            'degree': round(degree_in_sign, 6),   # サイン内の度数
            'speed': round(position[3], 6),       # 速度
            'retrograde': position[3] < 0         # 逆行判定
        }
    except Exception as e:
        return {'error': str(e)}
```

**注意ポイント:**
1. `swe.set_ephe_path()` は関数内で毎回呼ぶ（グローバル設定が効かない場合がある）
2. 黄経は必ず `% 360` で正規化
3. サインインデックスも `% 12` で正規化（360度超えに対応）
4. 速度（speed）が負の場合は逆行

### 4. ハウス計算の実装

```python
def calculate_houses(jd, latitude, longitude, house_system='P'):
    """
    ハウスカスプとアングルを計算
    
    house_system:
        'P' = Placidus（最も一般的）
        'K' = Koch
        'E' = Equal House
        'W' = Whole Sign
    """
    try:
        # ハウス計算
        cusps, ascmc = swe.houses(
            jd, 
            latitude, 
            longitude, 
            house_system.encode()  # バイト文字列に変換
        )
        
        # cuspsはタプルなので最初の12要素のみ使用
        cusps_list = list(cusps)[:12]
        
        # ASC（アセンダント）とMC（天頂）
        asc = ascmc[0]
        mc = ascmc[1]
        
        # サイン計算（0-360度に正規化）
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
            }
        }
    except Exception as e:
        return {'error': str(e)}
```

**ハウスシステムの選択:**
- **Placidus (P)**: 最も一般的、時間ベース
- **Koch (K)**: ヨーロッパで人気
- **Equal House (E)**: シンプル、ASCから30度ずつ
- **Whole Sign (W)**: 古典占星術

### 5. プログレッション計算の注意点

```python
def calculate_progressions(birth_date, current_date, birth_hour, birth_minute):
    """
    セカンダリープログレッション（1日=1年方式）
    
    重要: 出生時刻の扱いがソフトウェアによって異なる
    """
    # 経過年数を日数に変換
    days_since_birth = (current_date - birth_date).days
    years_elapsed = days_since_birth / 365.25
    progressed_days = int(years_elapsed)
    
    # プログレス日 = 出生日 + 経過年数（日換算）
    progress_date = birth_date + timedelta(days=progressed_days)
    
    # 【重要】出生時刻の扱い
    # 方式1: 正午UTC基準（一般的）
    progress_jd = swe.julday(
        progress_date.year,
        progress_date.month,
        progress_date.day,
        12.0  # 正午UTC
    )
    
    # 方式2: 出生時刻をそのまま使用（一部ソフトウェア）
    # progress_jd = swe.julday(
    #     progress_date.year,
    #     progress_date.month,
    #     progress_date.day,
    #     birth_hour + birth_minute / 60.0
    # )
    
    # P-太陽、P-月を計算
    p_sun = calculate_planet_position(progress_jd, swe.SUN)
    p_moon = calculate_planet_position(progress_jd, swe.MOON)
    
    return {
        'p_sun': p_sun,
        'p_moon': p_moon,
        'progress_date': progress_date.isoformat()
    }
```

**プログレッション計算の落とし穴:**
1. ソフトウェアによって出生時刻の扱いが異なる
2. 標準は「正午UTC」だが、出生時刻を使うソフトもある
3. ユーザーの参照ソフトと合わせる必要がある場合は調整が必要

---

## よくある落とし穴と対策

### 落とし穴1: 度数表記の混乱

#### 問題
```python
# 太陽が牡羊座8.53度の場合
# これは「絶対黄経8.53度」ではなく
# 「牡羊座（0-30度）内の8.53度」を意味する
```

#### 解決策
```python
# 絶対黄経と相対度数を明確に分ける
absolute_longitude = 8.53      # 絶対黄経
sign_index = 0                 # 牡羊座
degree_in_sign = 8.53          # サイン内の度数

# 逆算
absolute_longitude = (sign_index * 30) + degree_in_sign
```

### 落とし穴2: サインインデックスのオーバーフロー

#### 問題
```python
# 黄経が360度を超える場合
longitude = 362.5  # エラーが発生する可能性
sign_index = int(longitude // 30)  # = 12（範囲外！）
```

#### 解決策
```python
# 必ず正規化してから計算
longitude = longitude % 360
sign_index = int(longitude // 30) % 12  # 0-11の範囲を保証
```

### 落とし穴3: ハウス判定のロジックミス

#### 問題
```python
# ハウスカスプが360度をまたぐ場合の判定ミス
# 例: 第12ハウスカスプ350度、第1ハウスカスプ10度
# 天体が355度の場合、どちらのハウス？
```

#### 解決策
```python
def get_planet_house(planet_longitude, house_cusps):
    """
    天体が入るハウスを判定（360度またぎ対応）
    """
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
    
    return 1  # デフォルト
```

### 落とし穴4: 逆行判定の見落とし

#### 問題
```python
# speedが負の場合の処理を忘れる
position = swe.calc_ut(jd, planet_id)
speed = position[0][3]  # 取得するだけで判定しない
```

#### 解決策
```python
# 明示的に逆行フラグを設定
retrograde = speed < 0

# 表示時に℞マークを追加
display_text = f"{planet_name}: {sign} {degree:.2f}°"
if retrograde:
    display_text += " ℞"
```

---

## パフォーマンスと安定性

### 問題: "Too many open files" エラー

#### 原因
Flask開発サーバーはファイルディスクリプタを適切に管理しない

#### 解決策
```bash
# Gunicornを使用（本番環境）
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --log-level error \
  app:app
```

**推奨構成:**
- **ワーカー数**: CPU数 × 2 + 1
- **タイムアウト**: 120秒以上（天体計算は重い）
- **ログレベル**: error（本番）、info（開発）

### エフェメリスファイルの最適化

```python
# アプリケーション起動時に一度だけパス設定
import swisseph as swe
import os

EPHE_PATH = os.path.join(os.path.dirname(__file__), 'swisseph_data')
swe.set_ephe_path(EPHE_PATH)

# ただし、関数内でも念のため設定
def calculate_planet_position(jd, planet_id):
    swe.set_ephe_path(EPHE_PATH)  # 保険
    # ... 計算処理
```

---

## テストとデバッグ

### 基準データの準備

```python
# 既知の計算結果でテスト
TEST_CASES = [
    {
        'name': '基準ケース1',
        'date': datetime(1990, 3, 21, 15, 30),
        'location': (35.6762, 139.6503),  # 東京
        'expected': {
            'Sun': {'sign': 'Aries', 'degree': 0.75},
            'Moon': {'sign': 'Capricorn', 'degree': 24.10}
        }
    }
]
```

### ユーザーデータとの比較

```python
def compare_with_user_data(calculated, user_provided):
    """
    他の占星術ソフトとの比較（±1度以内なら許容）
    """
    tolerance = 1.0  # 度
    
    for planet, calc_data in calculated.items():
        user_data = user_provided.get(planet)
        if user_data:
            # 絶対黄経で比較
            calc_long = calc_data['longitude']
            user_long = user_data['longitude']
            
            diff = abs(calc_long - user_long)
            if diff > tolerance:
                print(f"⚠️  {planet}: 差異 {diff:.2f}度")
```

### デバッグ情報の出力

```python
# デバッグモードでの詳細ログ
if DEBUG:
    print(f"ユリウス日: {jd:.6f}")
    print(f"UTC時刻: {utc_datetime}")
    print(f"エフェメリスパス: {EPHE_PATH}")
    print(f"計算結果: {result}")
```

---

## デプロイと運用

### Railway/Herokuへのデプロイ

#### Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
```

#### requirements.txt
```
Flask==2.3.3
gunicorn==21.2.0
pyswisseph==2.10.3.2
flask-cors==4.0.0
```

#### runtime.txt（オプション）
```
python-3.12
```

### エフェメリスファイルの配置

```bash
# デプロイ時にswisseph_dataディレクトリを含める
project/
├── app.py
├── swisseph_api.py
├── requirements.txt
├── Procfile
└── swisseph_data/
    ├── sepl_18.se1
    ├── sepl_19.se1
    ├── sepl_20.se1
    ├── semo_18.se1
    └── seas_18.se1
```

**重要:** エフェメリスファイルは約2.8MBあるため、`.gitignore`に含めないこと

### 環境変数の設定

```python
import os

# デバッグモード
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ポート番号
PORT = int(os.getenv('PORT', 5000))

# エフェメリスパス（カスタマイズ可能）
EPHE_PATH = os.getenv(
    'SWISSEPH_PATH',
    os.path.join(os.path.dirname(__file__), 'swisseph_data')
)
```

---

## まとめ: 成功するための10のチェックリスト

### ✅ 1. Swiss Ephemerisを使用している
- [ ] pyswisseph 2.10.3.2 以上をインストール
- [ ] エフェメリスファイルを正しく配置

### ✅ 2. タイムゾーン変換が正しい
- [ ] ユーザー入力（JST）→ UTC変換を実装
- [ ] datetimeモジュールで日付またぎに対応

### ✅ 3. 度数計算の正規化
- [ ] 黄経を `% 360` で正規化
- [ ] サインインデックスを `% 12` で正規化

### ✅ 4. エフェメリスパスの設定
- [ ] `swe.set_ephe_path()` を正しく設定
- [ ] 関数内でも念のため設定

### ✅ 5. エラーハンドリング
- [ ] try-except でエラーをキャッチ
- [ ] ユーザーにわかりやすいエラーメッセージ

### ✅ 6. ハウス計算
- [ ] 360度またぎのロジックを実装
- [ ] Placidusハウスシステムを使用

### ✅ 7. 逆行判定
- [ ] speedが負の場合を判定
- [ ] ℞マークで表示

### ✅ 8. テストデータとの照合
- [ ] 既知のケースでテスト
- [ ] 他ソフトとの比較（±1度以内）

### ✅ 9. 本番サーバーの使用
- [ ] Gunicornを使用
- [ ] ワーカー数を適切に設定

### ✅ 10. ドキュメント整備
- [ ] APIドキュメント
- [ ] 運用ガイド
- [ ] トラブルシューティング

---

## 参考資料

### 公式ドキュメント
- **Swiss Ephemeris**: https://www.astro.com/swisseph/
- **pyswisseph**: https://github.com/astrorigin/pyswisseph
- **Flask**: https://flask.palletsprojects.com/
- **Gunicorn**: https://gunicorn.org/

### 占星術の基礎知識
- **ハウスシステム**: https://www.astro.com/astrology/in_hsys_e.htm
- **プログレッション**: セカンダリープログレッション（1日=1年）が標準
- **エフェメリス**: 天体の位置表、Swiss Ephemerisは最高精度

### コミュニティ
- **Stack Overflow**: `[swisseph]` タグ
- **占星術プログラミング**: Astro-Seek, Astrodienst

---

**作成日**: 2025-12-22
**バージョン**: 1.0
**プロジェクト**: 西洋占星術プロンプトジェネレーター

このガイドは、実際の開発過程で遭遇した問題と解決策をまとめたものです。
他のエンジニアへの引き継ぎ、または新規プロジェクトの参考にしてください。
