# トラブルシューティングガイド - 西洋占星術プロンプトジェネレーター

## 🚨 サーバーが見れない時の対処法

### 症状チェックリスト

#### 1. サーバープロセスの確認
```bash
cd /home/user/webapp
ps aux | grep gunicorn | grep -v grep
```

**正常**: 2つ以上のgunicornプロセスが表示される  
**異常**: 何も表示されない → サーバーが停止している

#### 2. ポートの確認
```bash
lsof -i :5000
```

**正常**: gunicornがポート5000をLISTENしている  
**異常**: 何も表示されない → サーバーが起動していない

#### 3. APIヘルスチェック
```bash
curl -s http://localhost:5000/api/health | python3 -m json.tool
```

**正常**: JSONレスポンスが返る（status: "healthy"）  
**異常**: エラーまたは無応答 → サーバーが応答していない

---

## 🔧 原因と解決策

### 原因1: WORKER TIMEOUT（最も一般的）

**症状**:
- ページが表示されない
- APIが応答しない
- エラーログに「WORKER TIMEOUT」が記録される

**確認方法**:
```bash
tail -50 /tmp/gunicorn_error.log | grep "TIMEOUT"
```

**原因**:
- 複雑な計算が120秒（旧設定）を超過
- ワーカープロセスが応答しなくなる

**解決策**:
```bash
cd /home/user/webapp
./stop_server.sh && sleep 3 && ./start_server.sh
```

**恒久対策**:
タイムアウトを300秒に延長済み（改善版start_server.sh）

---

### 原因2: メモリ不足（Out of Memory）

**症状**:
- ワーカーが突然終了する
- エラーログに「SIGKILL! Perhaps out of memory?」

**確認方法**:
```bash
tail -50 /tmp/gunicorn_error.log | grep "SIGKILL"
```

**原因**:
- 複数のワーカーがメモリを消費
- メモリリークの可能性

**解決策**:
```bash
cd /home/user/webapp
./stop_server.sh && sleep 3 && ./start_server.sh
```

**恒久対策**:
1. ワーカー数を2→1に削減済み（改善版）
2. `max-requests: 500`で定期的にワーカーを再起動

---

### 原因3: 古いプロセスの残存

**症状**:
- サーバーを再起動しても改善しない
- 複数のgunicornプロセスが存在

**確認方法**:
```bash
ps aux | grep gunicorn | grep -v grep
```

**解決策**:
```bash
cd /home/user/webapp
pkill -9 -f "gunicorn.*app:app"
sleep 5
./start_server.sh
```

---

## 📋 標準的な復旧手順

### ステップ1: 現状確認
```bash
cd /home/user/webapp
ps aux | grep gunicorn | grep -v grep
curl -s http://localhost:5000/api/health
```

### ステップ2: サーバー再起動
```bash
./stop_server.sh && sleep 3 && ./start_server.sh
```

### ステップ3: 動作確認
```bash
# APIヘルスチェック
curl -s http://localhost:5000/api/health | python3 -m json.tool

# フロントエンド確認
curl -s http://localhost:5000/prompt-generator/ | head -20
```

### ステップ4: 外部アクセス確認
ブラウザで以下にアクセス:
```
https://5000-iax7vsi3pyzys6nzqn4ai-583b4d74.sandbox.novita.ai/prompt-generator/
```

---

## 🛡️ 予防策

### 1. 定期的な再起動（推奨）

**毎日1回の再起動を推奨**:
```bash
# cronジョブに登録する場合
0 3 * * * cd /home/user/webapp && ./stop_server.sh && sleep 3 && ./start_server.sh >> /tmp/server_restart.log 2>&1
```

### 2. ログの定期確認

**週に1回のログチェック**:
```bash
# エラーログの確認
tail -100 /tmp/gunicorn_error.log | grep -E "Error|CRITICAL|TIMEOUT|SIGKILL"

# アクセスログの確認
tail -100 /tmp/gunicorn_access.log
```

### 3. メモリ使用量の監視

**メモリ使用状況の確認**:
```bash
ps aux | grep gunicorn | awk '{sum+=$6} END {print "Total memory: " sum/1024 " MB"}'
```

---

## 🔍 詳細なデバッグ方法

### エラーログの詳細確認
```bash
# 最近のエラーを時系列で確認
tail -200 /tmp/gunicorn_error.log | less

# 特定のエラーを検索
grep "CRITICAL" /tmp/gunicorn_error.log | tail -20
grep "TIMEOUT" /tmp/gunicorn_error.log | tail -20
grep "SIGKILL" /tmp/gunicorn_error.log | tail -20
```

### プロセスの詳細確認
```bash
# Gunicornプロセスの詳細
ps aux | grep gunicorn | grep -v grep

# ポート5000の使用状況
lsof -i :5000

# メモリ使用量の詳細
ps aux --sort=-%mem | head -20
```

### リクエストのテスト
```bash
# シンプルなGETリクエスト
curl -v http://localhost:5000/api/health

# ネイタルチャート計算のテスト
curl -X POST http://localhost:5000/api/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"year":1990,"month":1,"day":1,"hour":12,"minute":0,"latitude":35.6762,"longitude":139.6503}' \
  | python3 -m json.tool
```

---

## 📊 改善版サーバー設定の詳細

### 現在の設定（start_server.sh）

```bash
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 1              # メモリ不足対策で1に削減
  --timeout 300            # 120秒→300秒に延長
  --max-requests 500       # 500リクエストごとにワーカー再起動
  --max-requests-jitter 50 # ランダム化で一斉再起動を防止
  --graceful-timeout 30    # 優雅な終了（処理中のリクエストを待つ）
  --log-level warning      # より詳細なログ
  --access-logfile /tmp/gunicorn_access.log
  --error-logfile /tmp/gunicorn_error.log
  --daemon \
  app:app
```

### 設定の意図

1. **`--workers 1`**  
   メモリ不足を防ぐため、ワーカー数を削減

2. **`--timeout 300`**  
   複雑な占星術計算（プログレッション、トランジット）に対応

3. **`--max-requests 500`**  
   メモリリーク対策で、500リクエストごとにワーカーを自動再起動

4. **`--max-requests-jitter 50`**  
   450〜550リクエストの間でランダムに再起動（全ワーカーの一斉再起動を防止）

5. **`--graceful-timeout 30`**  
   処理中のリクエストを最大30秒待ってから終了

---

## 🆘 それでも解決しない場合

### 完全クリーンアップ

すべてのプロセスを強制終了し、ログをクリアして再起動:

```bash
cd /home/user/webapp

# すべてのGunicornプロセスを強制終了
pkill -9 -f "gunicorn"
pkill -9 -f "python.*app.py"

# ログファイルのバックアップとクリア
mv /tmp/gunicorn_error.log /tmp/gunicorn_error.log.backup
mv /tmp/gunicorn_access.log /tmp/gunicorn_access.log.backup

# 10秒待機
sleep 10

# 再起動
./start_server.sh

# 5秒待機
sleep 5

# 動作確認
curl -s http://localhost:5000/api/health | python3 -m json.tool
```

### 開発サーバーでの緊急起動（非推奨）

本番環境では使用しないでください。デバッグ目的のみ:

```bash
cd /home/user/webapp
pkill -9 -f "gunicorn"
python3 app.py
```

**注意**: Flask開発サーバーは本番環境に不適切です。デバッグ後は必ずGunicornに戻してください。

---

## 📞 サポート情報

### ログの場所
- アクセスログ: `/tmp/gunicorn_access.log`
- エラーログ: `/tmp/gunicorn_error.log`

### 関連ドキュメント
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - 開発ガイド
- [SERVER_MANAGEMENT.md](SERVER_MANAGEMENT.md) - サーバー管理
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - プロジェクト概要

### GitHub
- Repository: https://github.com/francedirectjp-art/astro-medical-system
- Pull Request: https://github.com/francedirectjp-art/astro-medical-system/pull/1

---

## 📝 更新履歴

- **2026-01-18**: 初版作成
  - WORKER TIMEOUT対策
  - メモリ不足対策
  - 改善版サーバー設定

---

_このドキュメントは、サーバーが見れなくなった時の対処法を網羅しています。_
