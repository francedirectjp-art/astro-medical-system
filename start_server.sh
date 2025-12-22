#!/bin/bash
# 西洋占星術プロンプトジェネレーター - 本番サーバー起動スクリプト

# 既存プロセスを停止
pkill -9 -f "gunicorn.*app:app" 2>/dev/null
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 2

# Gunicornで起動（本番用WSGIサーバー）
# - ワーカー数: 2
# - タイムアウト: 120秒
# - ログレベル: error（本番環境用）
# - ファイルディスクリプタの適切な管理
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --log-level error \
  --access-logfile /tmp/gunicorn_access.log \
  --error-logfile /tmp/gunicorn_error.log \
  --daemon \
  app:app

echo "✅ サーバーが起動しました"
echo "📊 ログ:"
echo "  - アクセスログ: /tmp/gunicorn_access.log"
echo "  - エラーログ: /tmp/gunicorn_error.log"
echo ""
echo "🌐 URL: http://localhost:5000/prompt-generator/"
