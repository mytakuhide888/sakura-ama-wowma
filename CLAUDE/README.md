# sakura-ama-wowma CLAUDE ドキュメント

> 新しいチャットを開始したらまずこのファイルを読む

## クイックリファレンス

| やりたいこと | 参照先 |
|------------|--------|
| プロジェクト全体像を把握したい | [project.md](project.md) |
| VPSに接続・デプロイしたい | [ops/server.md](ops/server.md) |
| カテゴリマッチングの現状を知りたい | [features/category_matching.md](features/category_matching.md) |
| SP-APIの設定・使い方を確認したい | [features/spapi.md](features/spapi.md) |
| 過去セッションの詳細ログを見たい | [sessions/](sessions/) |

---

## 現在の状態（2026-04-18 更新）

### カテゴリマッチング
- **状態**: 全件自動化達成（Phase 27完了）
- **auto**: 21,147件 / 21,446件（98.6%）
- **VPS DB反映**: 済み（2026-04-18）
- 詳細 → [features/category_matching.md](features/category_matching.md)

### SP-API
- **状態**: 接続成功（2026-04-18 確認済み）
- **アプリ名**: wowma_api_pro
- **マーケットプレイス**: Amazon.co.jp, Non-Amazon JP
- 詳細 → [features/spapi.md](features/spapi.md)

### 次のアクション候補
- SP-APIを使ったAmazon商品情報検索の実装
- Wowmaへの商品登録フロー整備
