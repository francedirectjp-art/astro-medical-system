# 🚀 デプロイメントガイド

## 📦 静的ホスティング対応

このアプリケーションは完全な静的SPA（Single Page Application）として設計されているため、以下のプラットフォームで簡単にデプロイできます。

## 1. GitHub Pages

### 手順

#### Option A: メインブランチからデプロイ

```bash
# 1. GitHubリポジトリにpush
git add prompt-generator/
git commit -m "Deploy Anti-Gravity Prompt Builder"
git push origin main

# 2. GitHub Pagesの設定
# リポジトリ → Settings → Pages
# Source: Deploy from a branch
# Branch: main / /prompt-generator
# Save
```

#### Option B: gh-pagesブランチ専用

```bash
# 1. gh-pagesブランチを作成
git checkout --orphan gh-pages
git rm -rf .
cp -r prompt-generator/* .
git add .
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages

# 2. GitHub Pages設定
# Branch: gh-pages / / (root)
```

### アクセスURL
```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/prompt-generator/
```

## 2. Vercel

### 自動デプロイ（推奨）

1. [Vercel](https://vercel.com/)にログイン
2. 「New Project」をクリック
3. GitHubリポジトリをインポート
4. プロジェクト設定:
   ```
   Framework Preset: Other
   Root Directory: prompt-generator
   Build Command: (空白)
   Output Directory: (空白 - 自動検出)
   ```
5. 「Deploy」をクリック

### CLI デプロイ

```bash
# Vercel CLIをインストール
npm install -g vercel

# prompt-generatorディレクトリに移動
cd prompt-generator

# デプロイ
vercel --prod
```

### カスタムドメイン設定
```bash
# Vercel Dashboard → Domains → Add
your-domain.com → prompt-generator.vercel.app
```

## 3. Netlify

### ドラッグ&ドロップデプロイ

1. [Netlify](https://www.netlify.com/)にログイン
2. 「Add new site」→「Deploy manually」
3. `prompt-generator/` フォルダをドラッグ&ドロップ
4. デプロイ完了！

### Git連携デプロイ（推奨）

1. Netlify Dashboard → 「Add new site」→「Import an existing project」
2. GitHubリポジトリを選択
3. ビルド設定:
   ```
   Base directory: prompt-generator
   Build command: (空白)
   Publish directory: . (または空白)
   ```
4. 「Deploy site」をクリック

### Netlify CLI

```bash
# Netlify CLIをインストール
npm install -g netlify-cli

# ログイン
netlify login

# デプロイ
cd prompt-generator
netlify deploy --prod --dir .
```

## 4. Cloudflare Pages

### Git連携デプロイ

1. [Cloudflare Pages](https://pages.cloudflare.com/)にログイン
2. 「Create a project」→ GitHubリポジトリを接続
3. ビルド設定:
   ```
   Production branch: main
   Build command: (空白)
   Build output directory: /prompt-generator
   Root directory: prompt-generator
   ```
4. 「Save and Deploy」

### Wrangler CLI

```bash
# Wrangler CLIをインストール
npm install -g wrangler

# ログイン
wrangler login

# デプロイ
cd prompt-generator
wrangler pages publish . --project-name=anti-gravity-prompt
```

## 5. Firebase Hosting

### 初期設定

```bash
# Firebase CLIをインストール
npm install -g firebase-tools

# ログイン
firebase login

# 初期化
cd prompt-generator
firebase init hosting

# 設定:
# Public directory: . (現在のディレクトリ)
# Configure as SPA: Yes
# Automatic builds: No
```

### デプロイ

```bash
firebase deploy --only hosting
```

### firebase.json 設定例

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**",
      "generate_sabian.py"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

## 6. AWS S3 + CloudFront

### S3バケット作成とアップロード

```bash
# AWS CLIをインストール済みとする
aws s3 mb s3://anti-gravity-prompt-builder

# ファイルをアップロード
cd prompt-generator
aws s3 sync . s3://anti-gravity-prompt-builder --exclude "*.py"

# 静的ウェブサイトホスティングを有効化
aws s3 website s3://anti-gravity-prompt-builder \
  --index-document index.html \
  --error-document index.html
```

### パブリックアクセス設定

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::anti-gravity-prompt-builder/*"
    }
  ]
}
```

### CloudFront 配信（オプション）

- S3バケットをオリジンとしてCloudFront Distributionを作成
- HTTPSを有効化
- カスタムドメインを設定可能

## 7. カスタムサーバー（Nginx/Apache）

### Nginx 設定例

```nginx
server {
    listen 80;
    server_name prompt-builder.example.com;
    root /var/www/anti-gravity-prompt-builder;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # JSONファイルのMIMEタイプ設定
    location ~* \.json$ {
        add_header Content-Type application/json;
    }

    # キャッシュ設定
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Apache 設定例 (.htaccess)

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

# MIMEタイプ設定
<IfModule mod_mime.c>
  AddType application/json .json
</IfModule>

# キャッシュ設定
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/json "access plus 1 week"
</IfModule>
```

## 📋 デプロイ前チェックリスト

- [ ] すべてのファイルパスが相対パスになっているか
- [ ] CDNリンク（Astronomy Engine）が正しく機能するか
- [ ] サビアンシンボルJSON（360個）が正しく読み込まれるか
- [ ] CORS設定が必要なAPIがないか確認
- [ ] モバイルブラウザでの動作確認
- [ ] HTTPSで動作するか（クリップボードAPI要件）

## 🔧 環境変数・設定

このアプリケーションは環境変数を使用しません。すべてクライアントサイドで完結します。

## 🌐 カスタムドメイン設定

### DNS設定例（Cloudflare DNS）

```
Type: CNAME
Name: prompt
Target: your-vercel-deployment.vercel.app
Proxy: Yes (Orange Cloud)
```

### SSL証明書

- Let's Encrypt（無料）: Netlify/Vercel/Cloudflareで自動
- 独自証明書: カスタムサーバーの場合は手動設定

## 📊 パフォーマンス最適化

### 推奨設定

1. **CDNキャッシュ**
   - HTML: 短いTTL（5分）
   - CSS/JS: 長いTTL（1年）
   - JSON: 中程度のTTL（1週間）

2. **Gzip/Brotli圧縮**
   - ほとんどのホスティングサービスで自動有効

3. **HTTP/2 有効化**
   - 最新のホスティングサービスでデフォルト有効

## 🐛 トラブルシューティング

### 404 Not Found
- ルートディレクトリが正しく設定されているか確認
- `index.html` がルートに存在するか確認

### JSON読み込みエラー
- MIMEタイプが `application/json` に設定されているか確認
- ファイルパスが正しいか確認

### Astronomy Engine読み込みエラー
- CDNリンクが最新か確認
- ネットワークアクセスが許可されているか確認

### クリップボード機能が動作しない
- HTTPSまたはlocalhostでアクセスしているか確認
- ブラウザがクリップボードAPIをサポートしているか確認

## 📞 サポート

デプロイに関する質問は、GitHubのIssuesまでお願いします。

---

**© 2024 Anti-Gravity Prompt Builder**
