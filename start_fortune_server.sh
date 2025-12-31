#!/bin/bash
# 開運言霊占星術師 - サーバー起動スクリプト

echo "=========================================="
echo "🌟 開運言霊占星術師 起動中... 🌟"
echo "=========================================="
echo ""

# 既存のプロセスを確認
if lsof -i :8000 >/dev/null 2>&1; then
    echo "⚠️  ポート8000は既に使用されています"
    echo "既存のプロセスを停止してください: pkill -f fortune_app.py"
    exit 1
fi

# Pythonアプリケーションをバックグラウンドで起動
cd "$(dirname "$0")"
nohup python3 fortune_app.py > fortune_app.log 2>&1 &
PID=$!

echo "✅ サーバーを起動しました (PID: $PID)"
echo ""
echo "📍 アクセス先: http://localhost:8000/"
echo "📄 ログファイル: fortune_app.log"
echo ""
echo "停止方法: pkill -f fortune_app.py"
echo "ログ確認: tail -f fortune_app.log"
echo ""
echo "=========================================="
