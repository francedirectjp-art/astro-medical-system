# Decision: 第2版鑑定システムを CCAGI 非経由で直接実装する

- 日付: 2026-09-05
- 承認: ODA（セッション内で明示承認）

## 背景

「The Narrative Astrologer 第2版」プロンプトを使った一気通貫鑑定システム
（入力→天体計算→Claude APIで約2万字の鑑定書→PDF保存）を
astro-medical-system に組み込む。

GLOBAL GUARDRAILS rule 1 は実装作業を CCAGI 経由で行うことを求めるが、
本セッションでは CCAGI 系 MCP サーバー（ccagi-tools / cc-grag / cc-vrag 等）が
接続失敗しており利用不能だった。

## 決定

ODA の明示承認のもと、例外として Claude が直接 Edit/Write で実装・コミットする。

## スコープ

- gem_narrative_astrologer_v2.md 追加（第2版プロンプト）
- claude_reading.py: Gem バージョン選択 + max_tokens 拡張
- 新ページ /reading/（フォーム→自動6ブロック生成→鑑定書表示→印刷/PDF）
- 日食・月食計算は省略（ODA 指示 2026-09-05）
