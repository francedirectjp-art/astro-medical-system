# サーバー管理ガイド

## 🚀 サーバーの起動・停止

### 起動
```bash
./start_server.sh
```

### 停止
```bash
./stop_server.sh
```

### 再起動
```bash
./stop_server.sh && sleep 2 && ./start_server.sh
```

---

## 📊 ログの確認

### アクセスログ
```bash
tail -f /tmp/gunicorn_access.log
```

### エラーログ
```bash
tail -f /tmp/gunicorn_error.log
```

---

## 🔧 トラブルシューティング

### 問題: "Too many open files" エラー

**原因:** Flask開発サーバーではファイルディスクリプタが枯渇する

**解決策:** 
1. Gunicornを使用する（本スクリプトで対応済み）
2. サーバーを再起動する

```bash
./stop_server.sh && sleep 2 && ./start_server.sh
```

### 問題: ポート5000が使用中

**確認:**
```bash
lsof -i :5000
```

**強制停止:**
```bash
pkill -9 -f "gunicorn.*app:app"
pkill -9 -f "python.*app.py"
```

---

## ⚙️ 設定

### Gunicorn設定（start_server.sh内）

- **ワーカー数**: 2
- **タイムアウト**: 120秒
- **ポート**: 5000
- **バインドアドレス**: 0.0.0.0

### ワーカー数の変更

`start_server.sh` の `--workers` を変更：

```bash
--workers 4  # 4ワーカーに増やす場合
```

**推奨:** CPU数 × 2 + 1

---

## 📈 パフォーマンス改善

### 1. Gunicorn使用（✅実装済み）
- 本番用WSGIサーバー
- マルチワーカー対応
- ファイルディスクリプタの適切な管理

### 2. ワーカー数の調整
- 同時接続数に応じて調整
- メモリ使用量に注意

### 3. タイムアウトの調整
- 重い計算がある場合は増やす
- デフォルト: 120秒

---

## 🌐 デプロイ環境

### 現在の環境
- **Platform**: Sandbox
- **Python**: 3.12
- **WSGI Server**: Gunicorn 21.2.0
- **Framework**: Flask 2.3.3

### Railway/Heroku等へのデプロイ

`Procfile` を作成：
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
```

---

## ✅ 動作確認

### ヘルスチェック
```bash
curl http://localhost:5000/api/health
```

### レスポンス例
```json
{
  "status": "healthy",
  "swiss_ephemeris": "pyswisseph 2.10.3.2",
  "available_bodies": ["Sun", "Moon", ...]
}
```

---

## 📝 メンテナンス

### 定期的な再起動
アクセスが多い場合は、定期的に再起動を推奨：

```bash
# 毎日午前4時に再起動（cron例）
0 4 * * * cd /home/user/webapp && ./stop_server.sh && sleep 2 && ./start_server.sh
```

---

**作成日**: 2025-12-22
**バージョン**: 1.0
