#!/bin/bash
# サーバー停止スクリプト

echo "🛑 サーバーを停止しています..."

# Gunicornプロセスを停止
pkill -9 -f "gunicorn.*app:app" 2>/dev/null

# Flask開発サーバーも停止
pkill -9 -f "python.*app.py" 2>/dev/null

sleep 2

# プロセスが残っていないか確認
if pgrep -f "gunicorn.*app:app" > /dev/null || pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  一部のプロセスが残っています"
else
    echo "✅ すべてのサーバープロセスを停止しました"
fi
