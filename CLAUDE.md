# sakura-ama-wowma プロジェクト固有ルール

## プロジェクト状態の把握

新しいチャットを開始する際は、以下のファイルを **この順番で** 読み込むこと:

1. **`CLAUDE/current_status.md`** - 現在の進捗状況、残課題、人間の作業手順
2. **`CLAUDE/project_overview.md`** - プロジェクト全体概要（技術スタック、ディレクトリ構成等）
3. **`CLAUDE/20250127_1/summary.md`** - 全フェーズの詳細記録（必要に応じて参照）

## 現在のタスク概要（2025-01-28時点）

### タスク: Amazon/Wowma カテゴリマッチング精度改善

- **状態**: Phase 8完了。マッピングデータ作成は完了。本番実行待ち。
- **成果**: auto（自動採用）0件 → 4,911件（実測）/ 7,500件+（予測）
- **カバレッジ**: L1〜L5 全階層100%達成

### 残課題

**人間の作業（未実施）:**
1. git commit & push（変更ファイル4つ）
2. 「その他」255件の手動レビュー（`codex_out/sonota_review.tsv`）
3. 本番サーバーでのmatch_categories実行

**システム側（Claude対応可能）:**
1. 「その他」レビュー結果のsynonyms/L2マップ反映
2. 本番実行後の結果分析・追加調整

### 主要変更ファイル

```
yaget/management/commands/match_categories.py  # コア修正
docs/category_mapping/level_1_cat.txt           # L1マッピング（46件）
docs/category_mapping/level_2_cat.txt           # L2マッピング（553件）★新規
docs/category_mapping/synonyms.tsv              # 同義語辞書（8,517件）
```

## プロジェクト固有の注意事項

- **Django設定**: `config.settings`（`/home/django/sample` が本番パス）
- **Python**: 3.8+（venv: `/home/niiya/sakura-ama-wowma/.venv3_8`）
- **DB**: SQLite（開発）/ MariaDB（本番）
- **ログディレクトリ**: `/home/django/sample/yaget/log/`（ローカルでは権限なし、Django起動不可の場合あり）
- **match_categoriesの実行**: ログディレクトリの権限問題があるため、ローカルでの完全テストは制限あり。部分的なPythonスクリプトで検証可能。
