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

### Wowmaショップ商品スクレイピング → ASIN検索パイプライン
- **状態**: 実装完了・動作確認済み（2026-04-18）
- **コマンド**: `get_wowma_shop_items --user-id 69303756`
- **DB**: `WowmaShopItem`（VPS MariaDB migrate済み）
- **テスト**: 5件 → scrape成功 / match 5/5 ASIN HIT
- **対象ショップ規模**: Marron Store 40,154件
- **全件実行**: screen/nohup推奨（~23時間）
- 詳細 → [sessions/20260418_1/summary.md](sessions/20260418_1/summary.md)

### 次のアクション候補
- Wowmaショップ全件スクレイピング実行（screen/nohupで）
- 複数ショップ対応
- マッチング精度向上
- Wowmaへの商品登録フロー整備（ASIN情報を使って）
