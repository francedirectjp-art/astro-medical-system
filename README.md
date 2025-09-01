# 占星医学体質鑑定システム - Phase 1 MVP版

![Version](https://img.shields.io/badge/version-1.0.0--beta-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 システム概要

占星医学体質鑑定システムは、出生データから7天体の位置を計算し、16元型による個性分析とエレメントバランスに基づく体質傾向診断を行うエンターテインメント目的のWebアプリケーションです。

### 主な機能

- **天体位置計算**: Swiss Ephemeris による正確な7天体位置計算
- **16元型診断**: 太陽×月のエレメント組み合わせによる個性分析  
- **簡易診断**: 1,000文字の体質傾向レポート
- **詳細鑑定書**: 12,000文字の詳細分析レポート
- **AI生成**: Gemini 1.5 Flash による高品質な診断文章生成

### ⚠️ 重要な注意事項

**本システムはエンターテインメント目的です。医療診断や治療の代替ではありません。**

## 🚀 クイックスタート

### 前提条件

- Python 3.8 以上
- Gemini AI APIキー
- Git

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd astro-system-mvp
```

### 2. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

```bash
# .env.example を .env にコピー
cp .env.example .env

# .env ファイルを編集して APIキーを設定
GEMINI_API_KEY=your_actual_api_key_here
```

### 5. アプリケーションの起動

```bash
python astro_step4_ultimate_api_fixed.py
```

サーバーは http://localhost:8107 で起動します。

## 📂 ファイル構成

```
astro-system-mvp/
├── astro_step4_ultimate_api_fixed.py    # APIサーバー（バックエンド）
├── astro_step4_ultimate_fixed.html      # Webインターフェース（フロントエンド）
├── requirements.txt                     # Python依存関係
├── .env.example                        # 環境変数テンプレート
├── README.md                           # このファイル
└── deploy_guide.md                     # デプロイガイド
```

## 🔧 API エンドポイント

### 基本情報

- **Base URL**: `http://localhost:8107`
- **認証**: ベータキー必須（ヘッダー: `X-Beta-Key`）
- **レート制限**: あり

### エンドポイント一覧

#### 1. ヘルスチェック
```http
GET /health
```

#### 2. 天体位置計算
```http
POST /api/calculate-planets
Content-Type: application/json
X-Beta-Key: astro2024beta

{
  "name": "山田太郎",
  "birth_year": 1990,
  "birth_month": 5,
  "birth_day": 15,
  "birth_hour": 14,
  "birth_minute": 30,
  "birth_prefecture": "東京都"
}
```

#### 3. 簡易診断
```http
POST /api/simple-diagnosis
Content-Type: application/json
X-Beta-Key: astro2024beta

{
  "name": "山田太郎",
  "planets": { /* 天体位置データ */ }
}
```

#### 4. 詳細鑑定書生成
```http
POST /api/generate-detailed-report
Content-Type: application/json  
X-Beta-Key: astro2024beta

{
  "name": "山田太郎",
  "year": 1990,
  "month": 5,
  "day": 15,
  "hour": 14,
  "minute": 30,
  "birth_prefecture": "東京都"
}
```

## 🔑 Gemini API キー取得方法

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. "Create API Key" をクリック
4. 生成されたキーを `.env` ファイルに設定

## 🐳 デプロイ方法

詳細は [deploy_guide.md](deploy_guide.md) を参照してください。

### Railway.app（推奨）

1. [Railway.app](https://railway.app) でアカウント作成
2. GitHubリポジトリを連携
3. 環境変数を設定
4. 自動デプロイ

### 必要な環境変数

```bash
GEMINI_API_KEY=your_gemini_api_key
BETA_PASSWORD=your_beta_password
FLASK_ENV=production
```

## 🧪 テスト方法

### ローカルテスト

```bash
# APIサーバー起動
python astro_step4_ultimate_api_fixed.py

# 別ターミナルでテスト
curl -X POST http://localhost:8107/api/calculate-planets \
  -H "Content-Type: application/json" \
  -H "X-Beta-Key: astro2024beta" \
  -d '{
    "name": "テスト太郎",
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 12,
    "birth_minute": 0,
    "birth_prefecture": "東京都"
  }'
```

## 🛡️ セキュリティ機能

- **レート制限**: DDoS攻撃対策
- **入力検証**: SQLインジェクション対策
- **ベータ版制限**: 不正アクセス防止
- **CORS設定**: クロスオリジン制御
- **エラーハンドリング**: 情報漏洩防止

## 📊 技術スタック

- **バックエンド**: Flask, Python 3.8+
- **天文計算**: Swiss Ephemeris (pyswisseph)
- **AI生成**: Google Gemini 1.5 Flash
- **フロントエンド**: HTML5, CSS3, Vanilla JavaScript
- **デプロイ**: Railway.app / Heroku / Vercel

## 🔄 更新履歴

### v1.0.0-beta (2024-01-01)
- 初回リリース
- 天体位置計算機能
- 16元型診断機能
- 簡易・詳細診断機能
- ベータ版アクセス制限

## 🤝 コントリビューション

現在はクローズドベータ版のため、コントリビューションは受け付けておりません。

## 📄 ライセンス

このプロジェクトは MIT ライセンスのもとで公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 📞 サポート

- **技術的な問題**: Issues を作成してください
- **ビジネスに関する問い合わせ**: [お問い合わせフォーム](mailto:support@example.com)

---

**免責事項**: 本システムで提供される診断結果は、エンターテインメント目的のものであり、医療診断や治療の代替となるものではありません。健康に関する相談は、必ず医療機関にご相談ください。
