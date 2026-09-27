# 構成と環境

## リポジトリ

```
~/CCAGI/astro-medical-system
ブランチ  feature/anti-gravity-prompt-builder   ← 本番系。mainではない
GitHub    francedirectjp-art/astro-medical-system
Railway   fortunate-manifestation / grand-vision（push で自動デプロイ）
```

## ファイル

| ファイル | 役割 |
|---|---|
| `gem_narrative_astrologer_v8_myth.md` | **現行プロンプト（神話版・採用）** |
| `gem_narrative_astrologer_v8_garden.md` | 庭版 |
| `gem_narrative_astrologer_v8.md` | 王国版（旧） |
| `gen_v8.py` | 生成本体。チャート計算＋4便の制御ループ＋後処理 |
| `batch_v8.py` | MyASPから複数名を引いて一括生成。出生地のAI判定つき |
| `figures.py` | 図版テンプレート（手・元素・領域図・二極図・年表） |
| `make_appendix.py` | 巻末（三重円＋データ表） |
| `md_to_pdf.py` | 組版。Chrome headless |
| `check_reading.py` | 機械検品 |
| `myasp_mcp.py` | MyASP の最小クライアント |
| `app.py` | Swiss Ephemeris API（localhost:5000） |
| `reading_engine.py` | **本番ワーカーの生成エンジン。現在まだ第7版** |
| `auto_reading_worker.py` | MyASPポーリング→自動発行 |

## 環境

```bash
.venv/lib/python3.9/site-packages      # swisseph, anthropic
~/.nexus/.env                          # ANTHROPIC_API_KEY, MYASP_API_KEY
localhost:5000                         # app.py（エフェメリス）
~/nexus-os/infra/scripts/drive_upload.py   # Drive書き込み
```

```bash
set -a && source ~/.nexus/.env && set +a
(.venv/bin/python3 app.py > /tmp/astro_api.log 2>&1 &) ; sleep 6
```

## 環境変数

| 変数 | 用途 |
|---|---|
| `MYTH=1` | 神話版（図版・検品の別名表） |
| `GARDEN=1` | 庭版 |
| `GEM_PATH` | 使うプロンプト |
| `PERSON_JSON` | 対象者データ |
| `CHART_TXT` | 検品・組版が参照する確定データ |
| `APPENDIX_HTML` | 巻末 |
| `PARTS` | 便数（既定5） |

## 本番の経路

```
MyASPフォーム https://frdirect-asp.com/p/r/N2hq9AJ5
  → auto_reading_worker.py（3分ポーリング）
  → reading_engine.py（★第7版のまま。第8版未切替）
  → PDF → /data 永続ボリューム
  → /r/<token>.pdf
  → free10 書き戻し
  → 30分後ステップメール
```

**本番はまだ第7版。** 第8版へ切り替えるには `reading_engine.py` の `GEM_PATH` と便構成を差し替える。未着手。

## コスト

```
1件  約19,000字・33ページ・53〜64円
```

出力トークンが大半。便を重ねるたび前便の全文を入力として再送するため、字数を減らすと二重に効く。

**同じAPIキーを nexus-os の自動化20本が共有している。** クレジット切れが5回発生。Auto-reload の設定を推奨。
