# sakura-ama-wowma 現在の進捗状況

最終更新: 2026-03-24

---

## 1. 進行中タスク: Amazon/Wowma カテゴリマッチング精度改善

### 背景
- Amazon商品カテゴリ（英語）とWowma商品カテゴリ（日本語）を自動マッチングする `match_categories` コマンドの精度が極めて低かった
- 改善前: auto（自動採用）= **0件**、auto rate = **0%**

### 目標
- 全Amazonカテゴリ（約26,000件）をWowmaカテゴリ（約7,800件）にマッピング
- autoの最大化、人間の手動判断の最小化

---

## 2. 完了した作業（Phase 1〜8）

### 最終実績（Phase 3検証時点の実測値）

| 指標 | 改善前 | Phase 3後（実測） | 2026-03-24現在 |
|------|-------|------------------|----------------|
| auto | 0件 | **4,911件** | **7,666件** |
| review | 3,304件 | 14,349件 | 16,431件 |
| review_level2 | 215件 | 2,139件 | 2,188件 |
| auto rate | 0% | **22.9%** | **〜29%** |

> 2026-03-24: synonymsバグ修正・追加とコード改善でさらに+1,005件達成（6,661→7,666件）

### フェーズ別の実施内容

| Phase | 内容 | 主な成果 |
|-------|------|---------|
| **1** | 正規表現バグ修正、synonyms修正 | auto 0→261件 |
| **2** | level_2_cat.txt新規作成、`--level2-map`オプション追加 | auto 261→3,473件 |
| **3** | L2拡張、「その他」フォールバック実装 | auto 3,473→4,911件 |
| **4** | level_1_cat.txt修正（Books大文字化、Office Products/Watches追加、表記統一） | +5,309件が対象化 |
| **5** | Electronics/Clothing L3詳細マッピング、ブランド名・製品名synonyms追加 | L2: 219→345件 |
| **6** | 全L1カテゴリのL2完全化、L3キーワードsynonyms追加 | L2: 345→553件 |
| **7** | L3/L4カバレッジ分析、L4キーワードsynonyms追加 | L3: 99.8%達成 |
| **8** | L4/L5完全カバレッジ確認・達成 | **全階層100%** |

### 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `yaget/management/commands/match_categories.py` | **修正** | 正規表現修正、`--level2-map`オプション、`idx_by_wow_l1l2`インデックス、`sonota_by_l1`/`sonota_by_l1l2`、`_find_sonota_fallback()` |
| `docs/category_mapping/level_1_cat.txt` | **修正** | books→Books大文字化、Office Products・Watches追加（計46エントリ） |
| `docs/category_mapping/level_2_cat.txt` | **新規** | L2マッピング553件（全19カテゴリ対応） |
| `docs/category_mapping/synonyms.tsv` | **修正** | 7,735→8,517件（+782件: ブランド名、製品名、技術用語、L3-L5キーワード） |

### カバレッジ達成状況

| 階層 | カバレッジ | 詳細 |
|------|----------|------|
| L1 | **100%** | 19/19カテゴリ |
| L2 | **100%** | 553件マッピング |
| L3 | **99.8%** | 565/566種類 |
| L4 | **100%** | 1,846/1,846語 |
| L5 | **100%** | 1,727/1,727語 |

---

## 3. 残課題

### 3.1 システム側の残課題（Claudeが対応可能）

| # | 課題 | 優先度 | 内容 |
|---|------|--------|------|
| S1 | 「その他」レビュー結果の反映 | 高 | 人間がレビュー完了後、NGの修正をsynonyms/L2マップに反映 |
| S2 | 本番実行後の結果分析 | 中 | 本番でmatch_categories実行後、auto/review数値の確認・追加調整 |
| S3 | reviewファイルの品質分析 | 低 | review（約14,000件）の中からauto昇格可能な候補の特定 |
| S4 | 閾値の微調整 | 低 | auto_threshold/review_thresholdの最適化（現在: 0.6/0.35） |

### 3.2 人間が行う残課題

| # | 課題 | 優先度 | 手順 |
|---|------|--------|------|
| H1 | **git commit & push** | **最優先** | 下記コマンド参照 |
| H2 | **「その他」255件の手動レビュー** | 高 | `codex_out/sonota_review.tsv` をGoogle Spreadsheetでレビュー |
| H3 | **本番でのmatch_categories実行** | 高 | 本番サーバーでコマンド実行 |
| H4 | review結果の最終承認 | 中 | `codex_out/category_match_review.tsv` の確認 |

---

## 4. 人間の作業手順

### H1: git commit & push

```bash
cd /home/niiya/sakura-ama-wowma
git add yaget/management/commands/match_categories.py
git add docs/category_mapping/level_1_cat.txt
git add docs/category_mapping/level_2_cat.txt
git add docs/category_mapping/synonyms.tsv
git commit -m "カテゴリマッチング精度改善: auto 7,666件達成 (synonymsバグ修正・拡充、level2 auto化)"
git push
```

### H2: 「その他」レビュー

1. `codex_out/sonota_review.tsv` をGoogle Spreadsheetにインポート
2. `judgment` 列に OK / NG / SKIP を入力
3. NGの場合 `correct_wow_path` に正しいパスを入力
4. TSVエクスポート → `codex_out/sonota_review_completed.tsv`
5. Claudeに提供して修正反映

詳細手順: `CLAUDE/20250127_1/sonota_review_instructions.md`

### H3: 本番実行

```bash
# 本番サーバーで実行
cd /home/django/sample
git pull
pkill -HUP gunicorn  # または sudo systemctl restart gunicorn

python manage.py match_categories \
  --synonyms docs/category_mapping/synonyms.tsv \
  --level1-map docs/category_mapping/level_1_cat.txt \
  --level2-map docs/category_mapping/level_2_cat.txt \
  --outdir codex_out \
  --auto-threshold 0.6 --review-threshold 0.35
```

---

## 5. 技術的なポイント（次のClaude向け）

### マッチングの仕組み
1. **level_1_cat.txt**: Amazon L1 → Wowma L1 のマッピング（検索範囲の絞り込み）
2. **level_2_cat.txt**: Amazon (L1, L2) → Wowma (L1, L2) のマッピング（+0.15スコアボーナス）
3. **synonyms.tsv**: 英語→日本語の同義語辞書（fuzzy matchingの精度向上）
4. **sonota fallback**: スコアが低い場合に「その他」カテゴリへ自動振り分け

### コード上の主要変更箇所
- `match_categories.py`: `load_level2_map()`, `build_wow_index()`, `_find_sonota_fallback()`
- 正規表現: `[^0-9a-zA-Zぁ-んァ-ヶー一-龥\s]+`（カタカナ長音「ー」を許可）

### 注意事項
- level_1_cat.txt と level_2_cat.txt で**Wowmaカテゴリ名の表記を統一すること**（例: 「本・雑誌・コミック」）
- Amazon L1カテゴリ名は**大文字/小文字を正確に一致させること**（例: 「Books」not「books」）
- synonyms.tsvのコメント行は `#` で始まる

---

## 6. ドキュメント一覧

| ファイル | 内容 |
|---------|------|
| `CLAUDE/project_overview.md` | プロジェクト全体概要（技術スタック、ディレクトリ構成等） |
| `CLAUDE/current_status.md` | **本ファイル** - 現在の進捗と残課題 |
| `CLAUDE/20250127_1/summary.md` | 全フェーズの詳細記録（Phase 1〜8） |
| `CLAUDE/20250127_1/category_matching_analysis.md` | 初期調査分析レポート |
| `CLAUDE/20250127_1/category_matching_roadmap.md` | 改善ロードマップ |
| `CLAUDE/20250127_1/l3_l4_coverage_report.md` | L3/L4カバレッジ詳細レポート |
| `CLAUDE/20250127_1/sonota_review_instructions.md` | 「その他」レビュー手順書 |
| `codex_out/sonota_review.tsv` | 「その他」レビュー対象255件 |
