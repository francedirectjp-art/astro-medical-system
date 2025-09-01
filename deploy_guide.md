# デプロイガイド - 占星医学体質鑑定システム

## 🎯 Phase 1: MVP デプロイ戦略

このガイドでは、占星医学体質鑑定システムをクラウドサービスにデプロイする手順を説明します。

## 📋 デプロイ前チェックリスト

### ✅ 必須アイテム
- [ ] Gemini AI APIキー取得済み
- [ ] GitHubアカウント作成済み
- [ ] デプロイ先サービスのアカウント作成済み
- [ ] 修正版ファイル一式準備済み

### 📂 必要ファイル
```
astro-system-mvp/
├── astro_step4_ultimate_api_fixed.py    # バックエンドAPI
├── astro_step4_ultimate_fixed.html      # フロントエンド
├── requirements.txt                     # Python依存関係
├── .env.example                        # 環境変数テンプレート
├── README.md                           # セットアップガイド
└── deploy_guide.md                     # このファイル
```

## 🚀 推奨デプロイ方法 1: Railway.app

### メリット
- 🎯 **シンプル**: GitHubリポジトリから自動デプロイ
- 💰 **コスパ**: 月$5から利用可能  
- 🔧 **簡単設定**: 環境変数設定が直感的
- 📊 **監視**: ログとメトリクス標準搭載

### ステップ1: GitHubリポジトリ準備

```bash
# 1. GitHubで新しいリポジトリ作成（例: astro-system-mvp）
# 2. ローカルにクローン
git clone https://github.com/your-username/astro-system-mvp.git
cd astro-system-mvp

# 3. ファイルを配置
# astro_step4_ultimate_api_fixed.py
# astro_step4_ultimate_fixed.html  
# requirements.txt
# .env.example
# README.md

# 4. コミット & プッシュ
git add .
git commit -m "Initial commit: Phase 1 MVP"
git push origin main
```

### ステップ2: Railway.appデプロイ

```bash
# 1. Railway.app にアクセス
# https://railway.app

# 2. GitHub でサインアップ/ログイン

# 3. "New Project" → "Deploy from GitHub repo"

# 4. リポジトリを選択: astro-system-mvp

# 5. 自動でビルド開始
```

### ステップ3: 環境変数設定

Railway.app ダッシュボードで：

```bash
# Variables タブで以下を設定:
GEMINI_API_KEY = "your_actual_gemini_api_key"
BETA_PASSWORD = "your_custom_beta_password"  
FLASK_ENV = "production"
PORT = "8107"
```

### ステップ4: カスタムドメイン設定（オプション）

```bash
# 1. Settings → Networking
# 2. Generate Domain （無料サブドメイン）
# または
# 3. Custom Domain → Add Domain （独自ドメイン）
```

### 💰 Railway.app 料金

```
Starter Plan: $5/月
- 512MB RAM
- 1GB Storage  
- 100GB Transfer
- カスタムドメイン対応
```

## 🌐 代替デプロイ方法 2: Render.com

### メリット
- 🆓 **無料枠**: 月750時間無料
- 🔒 **セキュリティ**: 自動SSL証明書
- 📈 **スケーラブル**: トラフィック増加に対応

### 手順

```bash
# 1. Render.com でアカウント作成
# 2. New → Web Service 
# 3. Connect GitHub repository
# 4. 設定:
#    Name: astro-system-mvp
#    Environment: Python 3
#    Build Command: pip install -r requirements.txt
#    Start Command: python astro_step4_ultimate_api_fixed.py
# 5. Environment Variables で API キー設定
```

## ☁️ 代替デプロイ方法 3: Google Cloud Run

### メリット
- 🚀 **高性能**: Google インフラ
- 💰 **従量課金**: 使った分だけ
- 🔧 **コンテナ**: Docker対応

### 必要な追加ファイル

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "astro_step4_ultimate_api_fixed.py"]
```

### 手順

```bash
# 1. Google Cloud Console でプロジェクト作成
# 2. Cloud Run API 有効化
# 3. gcloud CLI インストール

# 4. デプロイ
gcloud run deploy astro-system \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,BETA_PASSWORD=your_password
```

## 🌍 フロントエンド単独デプロイ: Netlify

フロントエンドとバックエンドを分離する場合：

### 手順

```bash
# 1. Netlify.com でアカウント作成
# 2. Sites → Add new site → Deploy manually
# 3. astro_step4_ultimate_fixed.html を含むフォルダをドラッグ&ドロップ
# 4. HTML内のAPI_BASE_URLを本番URLに変更
```

### HTML修正例

```javascript
// 修正前
const API_BASE_URL = 'http://localhost:8107';

// 修正後  
const API_BASE_URL = 'https://your-railway-app.railway.app';
```

## 🔐 セキュリティ設定

### 環境変数チェック

デプロイ後、以下のエンドポイントで設定確認：

```bash
# ヘルスチェック
curl https://your-app-url.railway.app/health

# 期待する応答
{
  "status": "healthy",
  "service": "第4ステップ最終システム API - Phase 1 MVP版",
  "version": "1.0.0-beta"
}
```

### ベータ版アクセステスト

```bash
# 正常なリクエスト
curl -X POST https://your-app-url.railway.app/api/calculate-planets \
  -H "Content-Type: application/json" \
  -H "X-Beta-Key: your_beta_password" \
  -d '{"name":"テスト","birth_year":1990,"birth_month":1,"birth_day":1,"birth_hour":12,"birth_minute":0,"birth_prefecture":"東京都"}'

# 期待する応答: 200 OK + 天体データ
```

## 📊 監視とログ

### Railway.app
- **ログ**: Deployments → View Logs
- **メトリクス**: Metrics タブで CPU/メモリ使用量確認

### 重要な監視ポイント
- **レスポンス時間**: 3秒以内
- **メモリ使用量**: 512MB以内（Railway Starter）
- **エラー率**: 5%以下
- **Gemini API使用量**: 1000リクエスト/日以内（無料枠）

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. Swiss Ephemeris エラー
```bash
# 症状: 天体計算エラー
# 原因: Swiss Ephemerisデータファイル不足
# 解決: requirements.txt でバージョン指定
pyswisseph==2.10.3.2
```

#### 2. Gemini API エラー  
```bash
# 症状: 診断文生成失敗
# 原因: APIキー未設定/無効
# 解決: 環境変数 GEMINI_API_KEY を確認
```

#### 3. CORS エラー
```bash  
# 症状: フロントエンドからAPI呼び出し失敗
# 原因: CORS設定
# 解決: ALLOWED_ORIGINS 環境変数を設定
ALLOWED_ORIGINS=https://your-frontend-domain.netlify.app
```

#### 4. メモリ不足
```bash
# 症状: アプリケーションクラッシュ
# 原因: Gemini API レスポンス処理でメモリ使用過多
# 解決: プラン上位変更またはレスポンスサイズ制限
```

## 💰 コスト見積もり

### 月額コスト（予想）

```
Railway.app Starter:     $5
独自ドメイン（任意）:      $10-15  
Gemini API使用料:       $0-20（使用量次第）
―――――――――――――――――――――――
合計:                  $15-40/月
```

### 無料枠活用パターン

```
Render.com（無料）:      $0  
Netlify（無料）:         $0
Gemini API（無料枠）:     $0
―――――――――――――――――――――――
合計:                   $0/月（制限あり）
```

## 🚀 Phase 2 準備

Phase 1 が安定稼働したら、以下の機能追加を検討：

- **ユーザー登録**: Firebase Auth
- **決済機能**: Stripe Integration  
- **データベース**: PostgreSQL（Railway標準）
- **API Analytics**: Google Analytics
- **パフォーマンス**: Redis キャッシュ

## 📞 サポート

デプロイで困った場合：

1. **GitHub Issues**: 技術的な問題
2. **Railway Discord**: Railway固有の問題  
3. **Google AI Studio**: Gemini API関連

---

**Next Steps**: Phase 1 デプロイ完了後は、ユーザーフィードバックを収集してPhase 2の機能を決定しましょう！
