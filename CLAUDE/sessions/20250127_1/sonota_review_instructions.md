# 「その他」カテゴリ レビュー手順書

## 概要

- **対象ファイル**: `codex_out/sonota_review.tsv`
- **レビュー対象**: 255件
- **目的**: 「その他」に振り分けられたマッピングの正確性確認

---

## 手順

### Step 1: TSVファイルをGoogle Spreadsheetにインポート

1. Google Driveで新規スプレッドシートを作成
2. 「ファイル」→「インポート」→「アップロード」
3. `codex_out/sonota_review.tsv` をアップロード
4. インポート設定:
   - 区切り文字: **タブ**
   - 既存のスプレッドシートに追加

### Step 2: 列の説明

| 列名 | 説明 | 入力要否 |
|------|------|---------|
| row_no | 行番号 | - |
| source | データソース (auto/review/review_l2) | - |
| ama_id | Amazon カテゴリID | - |
| ama_path | Amazon フルパス | - |
| ama_l1〜l4 | Amazon 各階層 | - |
| wow_id | Wowma カテゴリID | - |
| wow_path | Wowma フルパス（現在の振り分け先） | - |
| wow_l1/l2 | Wowma 各階層 | - |
| score | マッチングスコア | - |
| **judgment** | **判定結果** | **入力必須** |
| **correct_wow_path** | **正しいパス（NGの場合）** | **NGの場合入力** |
| **notes** | **メモ** | 任意 |

### Step 3: レビュー実施

各行について以下を確認:

1. **Amazon パス** (`ama_path`) を確認
2. **現在の Wowma パス** (`wow_path`) が適切か判断
3. `judgment` 列に判定を入力:

| 判定値 | 意味 | 説明 |
|--------|------|------|
| **OK** | 正しい | 「その他」への振り分けが適切 |
| **NG** | 誤り | より適切なカテゴリがある |
| **SKIP** | 判断保留 | 判断が難しい場合 |

4. **NGの場合**: `correct_wow_path` に正しいWowmaカテゴリパスを入力
   - 例: `グルメ・食品/野菜・きのこ/トマト`
   - 分からない場合は `correct_wow_path` に「要確認」と記入

### Step 4: レビュー完了後

1. スプレッドシートをTSVでエクスポート
   - 「ファイル」→「ダウンロード」→「タブ区切りの値(.tsv)」
2. ファイル名: `sonota_review_completed.tsv`
3. Claudeに提供

---

## フィードバック形式

完了したTSVをClaudeに渡す際、以下のように伝えてください:

```
「その他」レビューが完了しました。
結果ファイル: [ファイルパス]
```

Claudeが行う対応:
- NG判定の分析
- 必要に応じてsynonyms.tsvまたはlevel_2_cat.txtの修正
- 修正内容のレポート

---

## レビューのポイント

### 判断基準

| 状況 | 判定 |
|------|------|
| 「その他」が適切（具体カテゴリがWowmaにない） | OK |
| より具体的なWowmaカテゴリがある | NG |
| Amazon側が特殊すぎて判断困難 | SKIP |

### よくあるNGパターン

1. **野菜の誤マッチ**
   - Amazon: `Fresh Vegetables/Peppers`
   - 現在: `その他野菜`
   - 正解: `野菜・きのこ/ピーマン・パプリカ`

2. **スポーツの誤マッチ**
   - Amazon: `Team Sports/Tennis`
   - 現在: `その他ラケット`
   - 正解: `テニス/テニスラケット`

3. **サプリの誤マッチ**
   - Amazon: `Supplements/Fish Oil`
   - 現在: `その他サプリ`
   - 正解: `サプリメント/オメガ脂肪酸`

---

## ファイル配置

```
codex_out/
├── sonota_review.tsv          # レビュー対象（Claudeが作成）
└── sonota_review_completed.tsv # レビュー完了後（人間が作成）
```

---

*作成: Claude Code*
