---
name: narrative-reading
description: 織田剛のナラティブ鑑定書(第8版)を作る全工程。MyASPのインテークから天文計算・編集方針の設計・本文執筆・データ照合・一冊編集・組版・機械検品・納品まで。「鑑定書を作って」「◯◯さんの鑑定書」「第8版で生成」「神話版で」「鑑定書を再送」「鑑定書のプロンプトを直す」といった依頼で使う。鑑定書の品質改善・プロンプト改訂・検品ツールの修正もこのスキルの範囲。
---

# ナラティブ鑑定書 制作工程

## 0. これは何か

生年月日と出生時刻と出生地、そして本人の三つの答えだけから、約20,000字・35ページのPDF鑑定書を1件60〜70円で作る仕組み。**占星術の技法を、その人だけの物語として書き直したもの**を納品する。

読者の大半は女性。日本在住。占星術の知識は問わない。

### この鑑定書が目指すもの

> 読者を「深く理解される人」から「自分でも読み始める人」へ移す。

感嘆が「文章がうまい」に帰属すると受講につながらない。「技術がすごい」に帰属させる。そのために三つを開く。

| | 手段 |
|---|---|
| 文書を開く | 章末に【星を読まれる方へ】で読みの根拠を出す |
| 読者を開く | 【思い当たることはありませんか？】に記入欄を置く |
| 物語を開く | 完了宣言を禁止。価値は出し切り、扱う力は開いたまま渡す |

### 絶対に守る設計原則

**AIに計算させない。コードで確定して渡す。**

これが全ての事故対策の根幹。城主・元素の同点・トランジット接触・プロフェクション期間・サビアン原文は、すべてコードが確定してチャートテキストに注入する。AIは解釈と文章だけを担当する。

**プロンプトに書けば守られる、は成り立たない。**

モデルは第7版までの文章を大量に学習しているため、指示より記憶が勝つ。守らせたい規則は三層で塞ぐ。

```
1  プロンプトの先頭で指示（後ろに書くと埋もれる）
2  生成後にコードで機械置換
3  検品で検出して不合格にする
```

---

## 1. 七つの工程

```
工程1  データ確定       コードのみ。AIを介在させない
工程2  編集方針の設計    この人を貫く問いを先に決める
工程3  本文執筆         4便。工程2の方針を全便に引き継ぐ
工程4  データ照合       独立した校正。本文と確定データを突き合わせる
工程5  一冊としての編集  通しで読み、重複と一貫性を見る
工程6  組版            PDF化
工程7  機械検品         14項目。不合格なら工程4へ戻る
```

各工程の詳細は `references/` を参照。

| 工程 | 参照 |
|---|---|
| 1 データ確定 | `references/01-data.md` |
| 2 編集方針 | `references/02-brief.md` |
| 3 本文執筆 | `references/03-compose.md` |
| 4 データ照合 | `references/04-verify.md` |
| 5 一冊編集 | `references/05-edit.md` |
| 6 組版 | `references/06-layout.md` |
| 7 機械検品 | `references/07-check.md` |

あわせて必ず読む。

- `references/architecture.md` — ファイル構成・環境・どこに何があるか
- `references/troubleshooting.md` — 既知の事故と対処（**着手前に必読**）
- `references/design-decisions.md` — なぜその設計なのか。変更提案の前に読む

---

## 2. 最短手順（1名分を作る）

```bash
cd ~/CCAGI/astro-medical-system
```

**準備**

```bash
# エフェメリスAPI（未起動なら）
(.venv/bin/python3 app.py > /tmp/astro_api.log 2>&1 &) ; sleep 6
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5000/

# APIキー
set -a && source ~/.nexus/.env && set +a
```

**工程1〜3：生成**

```bash
MYTH=1 GEM_PATH=$PWD/gem_narrative_astrologer_v8_myth.md \
PERSON_JSON=/tmp/reading_v8/<slug>.person.json \
.venv/bin/python3 gen_v8.py
```

便ごとに実測字数・目標・累計・繰越がログに出る。目標比±15%外は「要確認」。

**工程4〜5：照合と編集**

`references/04-verify.md` と `05-edit.md` の手順に従い、生成された `.md` を読んで直す。**ここを飛ばさない。** 機械検品では拾えない矛盾がここにある。

**工程6：組版**

```bash
S=<scratchpad>
MYTH=1 python3 make_appendix.py /tmp/reading_v8/<slug>.person.json $S/chart8_<slug>.txt /tmp/reading_v8/ap_<slug>.html
MYTH=1 CHART_TXT=$S/chart8_<slug>.txt APPENDIX_HTML=/tmp/reading_v8/ap_<slug>.html \
python3 md_to_pdf.py $S/reading8_<slug>.md "◯◯ 様" "生年月日 時刻 出生地生まれ ／ 鑑定日 YYYY-MM-DD" "/tmp/reading_v8/out/◯◯様_鑑定書.pdf"
```

**工程7：検品**

```bash
MYTH=1 CHART_TXT=$S/chart8_<slug>.txt python3 check_reading.py $S/reading8_<slug>.md
```

**合格が出るまで納品しない。**

---

## 3. 複数名を作る

```bash
set -a && source ~/.nexus/.env && set +a
.venv/bin/python3 batch_v8.py "田畑 康子" "島村 拓史"
```

MyASPから該当者を引き、出生地を都道府県へ解決し、person.json を作って順に生成する。出生地が地名テーブルにない場合はHaikuが判定する（**黙って東京都にしない**）。

並列で回すなら `PERSON_JSON` を変えて `gen_v8.py` を複数起動する。slug でファイル名が分かれるので衝突しない。

---

## 4. 版の切り替え

三つの世界観がある。**現行の採用版は神話版。**

| 版 | プロンプト | 環境変数 |
|---|---|---|
| **神話版（採用）** | `gem_narrative_astrologer_v8_myth.md` | `MYTH=1` |
| 庭版 | `..._v8_garden.md` | `GARDEN=1` |
| 王国版（旧） | `gem_narrative_astrologer_v8.md` | なし |

環境変数は図版・章扉のラベル・検品の別名表に効く。**プロンプトと環境変数は必ず対で指定する。** 片方だけだと図版のラベルが別の版になる。

---

## 5. 納品

PDFは2.2MB前後あり、ツール経由でメール添付できない。**Driveへ上げてリンクを送る。**

```bash
cd ~/nexus-os/infra/scripts
python3 drive_upload.py "/tmp/reading_v8/out/◯◯様_鑑定書.pdf" root --mime application/pdf
```

権限は**ご本人のアドレスにのみ reader を付与**する。Googleアカウントのないアドレス（icloud/docomo等）は `sendNotificationEmail=True` が必須。詳細は `references/06-layout.md`。

**送信前に必ず文面をODAに見せて承認を取る。** 顧客へODA名義で出るため。

---

## 6. やってはいけないこと

- **検品が不合格のまま納品する**
- 工程4・5を飛ばして組版へ進む
- プロンプトを直したあと、生成せずに「直った」と報告する
- 過去の出来事をインテークで聞く（心当たりの機能が死ぬ）
- 自由記述のインテーク項目を増やす（思考コストが跳ねる）
- 数字だけ見て成功と判断する（**ページ数の落差が最良の異常検知**）
- 編集方針に「各章の役割」を書く（字数が膨らむ。章の内容は 03-compose.md の仕事）
- 生成時に字数を絞ろうとする（**モデルは目標を守らない。工程5で削る**）
