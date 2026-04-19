# タスク記録
## 概要
- 背景：WowmaショップのスクレイピングとSP-APIを使ったASINマッチングパイプラインの実装
- ゴール：指定ショップの商品一覧取得 → 商品名取得 → AmazonでASIN検索 → DBに保存
- 影響範囲：yaget/models.py（WowmaShopItem追加）、管理コマンド（get_wowma_shop_items.py新規）
- 期限/優先度：高（今セッション中に完了）

## 現状（事実）
- 対象ショップ: Marron Store（user_id=69303756）、商品総数 40,154件
- DBテーブル: WowmaShopItem（VPS MariaDBにmigrate済み）
- 管理コマンド: VPS /home/django/sample/yaget/management/commands/get_wowma_shop_items.py に配備済み
- 動作確認: 5件テスト実行 → scrape 5件保存、match 5/5 ASIN HIT

## Plan（編集前）
実施内容参照

## 調査ログ
### Wowma catalog API の問題
- 当初実装: `/catalog/api/search/items?user=69303756&ipp=40&page=1&uads=0&acc_filter=N`
  → `emptySearch:true`, totalCount=0（ブラウザ内fetchでも同様）
- ネットワークログキャプチャで実際のAPIリクエストを特定:
  ```
  /catalog/api/search/items?uads=0&user=69303756&acc_filter=N&ad_coup_pos=search&shop_only=Y&ref_id=catalog_list2&mode=pc
  ```
- **原因**: `shop_only=Y` パラメータが必須。これがないとキーワード検索モードになりemptySearch=true
- **修正後**: totalCount=40,154、hitItems=40（1ページ40件、1,004ページ分）

### SP-API matchフェーズ
- 5件 → 全件ASIN HIT (100%)
  - 688169017 → B0B2R7MKVH
  - 708138357 → B06XDJB4MW
  - 735057425 → B0D4MM1PR6
  - 733444891 → B09XHNXK4S
  - 768283457 → B0FW4HLQ1S

## 実装内容
### 変更ファイル
| ファイル | 変更内容 |
|---------|---------|
| `yaget/models.py` | WowmaShopItemモデル追加 |
| `yaget/management/commands/get_wowma_shop_items.py` | 新規（415行） |

### get_wowma_shop_items.py 修正内容（セッション内）
- catalog API URL: `shop_only=Y&ref_id=catalog_list2&mode=pc` パラメータ追加（必須パラメータ）
- 1行変更のみ（最小差分）

### アーキテクチャ
```
Phase 1 (scrape):
  Selenium → wowma.jp SPA読み込み → browser context fetch API (shop_only=Y) 
  → 全商品ID収集 → 各商品detail page (requests) → og:title抽出 → WowmaShopItem保存

Phase 2 (match):
  WowmaShopItem(status=PENDING) → SP-API CatalogItems.search_catalog_items 
  → ASIN/ASIN名取得 → WowmaShopItem更新(status=MATCHED)
```

## 検証結果
```bash
# scrapeテスト (limit=5)
python manage.py get_wowma_shop_items --user-id 69303756 --phase scrape --limit 5
# 結果: 5件 DB保存成功

# matchテスト
python manage.py get_wowma_shop_items --user-id 69303756 --phase match
# 結果: 5/5 ASIN HIT
```

---

## 追加実装（2026-04-19）: Web UI + Amazon詳細取得

### 追加変更ファイル
| ファイル | 変更内容 |
|---------|---------|
| `yaget/models.py` | `AmazonItemDetail`モデル追加、`WowmaShopItem`にFKフィールド・STATUS_DETAIL_FETCHED追加 |
| `yaget/management/commands/get_wowma_shop_items.py` | Phase 3追加（CatalogItems + Products.get_item_offers）、`--max-ship-hours`オプション追加 |
| `yaget/views.py` | `wowma_match_top/status_ajax/list/detail`ビュー追加 |
| `yaget/urls.py` | wowma_match関連URL追加 |
| `yaget/templates/yaget/wowma_match_top.html` | 操作画面（フォーム+ポーリング）|
| `yaget/templates/yaget/wowma_match_list.html` | 結果一覧（フィルタ+ページネーション） |
| `yaget/templates/yaget/wowma_match_detail.html` | ASIN詳細（FBA判定テーブル） |

### Web UI URL
- `/yaget/wowma_match/` - 操作画面
- `/yaget/wowma_match/list/` - 結果一覧
- `/yaget/wowma_match/<pk>/detail/` - ASIN詳細
- `/yaget/wowma_match/status/` - Ajaxポーリング用

### SP-API注意事項
- `ProductPricing` は `from sp_api.api import Products as ProductPricing` で代替（v0.16.0）
- ShippingTimeのキーはcamelCase: `minimumHours`, `maximumHours`, `availabilityType`
- PrimeInformationは `PrimeInformation.IsPrime` に nested

### 動作確認済み（VPS）
```
[1] B0B2R7MKVH: ✓出品可 FBA=True ship=0h avail=NOW
[2] B06XDJB4MW: ✓出品可 FBA=True ship=0h avail=NOW
[3] B0D4MM1PR6: ✓出品可 FBA=True ship=0h avail=NOW
[4] B09XHNXK4S: ✓出品可 FBA=True ship=0h avail=NOW
[5] B0FW4HLQ1S: ✓出品可 FBA=True ship=0h avail=NOW
```
全エンドポイント HTTP 200 確認

## 次のアクション

### 人間が行う作業
```bash
# ローカルでgit commit & push
git add yaget/management/commands/get_wowma_shop_items.py
git commit -m "Fix catalog API: add shop_only=Y parameter for shop item listing"
git push

# VPSでgit pull（VPSには既にSCP済みだが、git pullで同期）
ssh django@133.167.75.151
source /home/django/djangoenv/bin/activate && cd /home/django/sample
git pull
```

### 全件スクレイピング実行（ユーザー判断で）
40,154件の全件処理は長時間かかるため、screen/nohupで実行推奨:
```bash
# VPSで
screen -S wowma_scrape
source /home/django/djangoenv/bin/activate && cd /home/django/sample

# 全商品scrapeのみ
python manage.py get_wowma_shop_items --user-id 69303756 --phase scrape
# → 約16時間（40,154件 × 1.5秒）

# scrape完了後、matchを実行
python manage.py get_wowma_shop_items --user-id 69303756 --phase match
# → 約6.7時間（40,154件 × 0.6秒）

# Ctrl+A, D でdetach
```

### 処理時間見積もり
| フェーズ | 件数 | 間隔 | 推定時間 |
|---------|------|------|---------|
| scrape | 40,154件 | 1.5秒/件 | ~16.7時間 |
| match | 40,154件 | 0.6秒/件 | ~6.7時間 |
| 合計 | | | ~23時間 |

### TODO（将来）
- [ ] scrapeフェーズのページ並列化（効率化）
- [ ] 複数ショップ対応
- [ ] 定期バッチ化（cron）
- [ ] マッチング精度向上（keyword精度改善、複数候補の選択ロジック）
