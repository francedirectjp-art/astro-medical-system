# 工程6 組版と納品

## 巻末資料

```bash
MYTH=1 python3 make_appendix.py <person.json> <chart.txt> <out.html>
```

三重円（内円=ネイタル／中円 緑=進行の太陽と月／外円 青=鑑定日のトランジット）と、データ表5種（ネイタル天体／**エッセンシャルディグニティの採点表**／プロフェクション／プログレス／トランジット／ソーラーリターン）。

トランジットは全12天体をAPIから取り直す（チャートテキストには外惑星3つしかないため）。

## PDF

```bash
MYTH=1 CHART_TXT=<chart.txt> APPENDIX_HTML=<ap.html> \
python3 md_to_pdf.py <reading.md> "◯◯ 様" "生年月日 時刻 出生地生まれ ／ 鑑定日 YYYY-MM-DD" <out.pdf>
```

Chrome headless で組む。約33ページ。

### 図版（12点）

| 図 | 位置 |
|---|---|
| 手（十本の指） | 各章末。2→5→8→10と灯る |
| 四大元素の炉 | 第2章扉 |
| 十二の領域図 | 第3章扉 |
| 時間の三層年表 | 第8章扉 |
| 三重円 | 巻末 |
| データ表 | 巻末 |

**差し込み位置はコード側で確定**。モデルにマーカーを書かせない。

### 組版でよくある事故

- 章題行（`# 見出し`）がないと**章扉が全滅**してページ数が激減する
- 三点セットを `##` 形式で書かれると章題と誤認される（正規化で吸収済み）
- 見出し直後の空行で囲みが閉じ、中身が箱の外に出る（修正済み）

**ページ数が普段より大きく違ったら、まず構造を疑う。**

## 納品

PDFは2.2MB前後。**ツール経由でメール添付できない**（base64がツール呼び出しの上限を超える）。Driveへ上げてリンクを送る。

```bash
cd ~/nexus-os/infra/scripts
python3 drive_upload.py "<pdf>" root --mime application/pdf
```

権限は**ご本人のアドレスにのみ reader**。

```python
svc.permissions().create(fileId=fid, sendNotificationEmail=False,
                         body={'type':'user','role':'reader','emailAddress':mail}).execute()
```

**Googleアカウントのないアドレス**（icloud.com / docomo.ne.jp 等）は `sendNotificationEmail=True` が必須。Driveからの共有通知が別途届く。

### 送信

**必ず文面をODAに見せて承認を取る。** 顧客へODA名義で出る。

出生地の誤りなど、こちらの不備で作り直した場合は**お詫びを明記**する。

> 先にお届けした鑑定書は、出生地の判定に誤りがあり、渋川市を東京都として計算しておりました。生まれた場所が変わると、城門の位置と部屋の割り当てが変わります。つまり前の版は、島村さまの図として正しいものではありませんでした。
