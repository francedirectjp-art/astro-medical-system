#!/bin/bash
# 西洋占星術プロンプトジェネレーター - 本番サーバー起動スクリプト（改善版）

# 既存プロセスを停止
pkill -9 -f "gunicorn.*app:app" 2>/dev/null
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 3

# Gunicornで起動（本番用WSGIサーバー）
# 改善点:
# - ワーカー数: 1（メモリ不足対策）
# - タイムアウト: 300秒（複雑な計算に対応）
# - max-requests: 500（メモリリーク対策で定期的に再起動）
# - max-requests-jitter: 50（再起動をランダム化）
# - ログレベル: warning（より詳細なログ）
# - graceful-timeout: 30秒（優雅な終了）
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
echo "📊 ログ:"
echo "  - アクセスログ: /tmp/gunicorn_access.log"
echo "  - エラーログ: /tmp/gunicorn_error.log"
echo ""
echo "🌐 URL: http://localhost:5000/prompt-generator/"
