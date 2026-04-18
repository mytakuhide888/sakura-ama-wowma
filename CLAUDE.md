# sakura-ama-wowma プロジェクト固有ルール

## プロジェクト状態の把握

新しいチャットを開始する際は、まず以下を読む:

1. **`CLAUDE/README.md`** - インデックス（現状サマリ・次のアクション）
2. **`CLAUDE/project.md`** - プロジェクト全体概要
3. 作業内容に応じて参照:
   - `CLAUDE/features/category_matching.md` - カテゴリマッチング詳細
   - `CLAUDE/features/spapi.md` - SP-API設定・利用状況
   - `CLAUDE/ops/server.md` - VPS接続・デプロイ手順

## 現在の状態（2026-04-18更新）

| 機能 | 状態 |
|------|------|
| カテゴリマッチング | **完了** Phase 27。VPS DB反映済み（auto 21,147件/98.6%） |
| SP-API接続 | **完了** wowma_api_pro アプリで接続確認済み |
| 次のステップ | SP-APIを使ったAmazon商品情報取得・Wowma登録フロー |

## プロジェクト固有の注意事項

- **Django設定**: `sample.settings`（`/home/django/sample` が本番パス）
- **Python**: 3.8+（venv: `/home/django/djangoenv/`）
- **DB**: SQLite（開発）/ MariaDB（本番）
- **ローカル制約**: ログディレクトリ権限なし、Django起動不可。VPSでのみmanage.py実行可能
- **LwaCredential**: SP-APIリフレッシュトークンはDBが.envより優先される（要注意）
