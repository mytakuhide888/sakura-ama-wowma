# 05 au PAY Market (Wowma) Scan

コード・設定・依存から au PAY マーケット（Wowma）API 利用の痕跡を抽出します。該当箇所が無い場合は導入に必要な欠落点を列挙します。

## 痕跡（ファイルと抜粋）

- エンドポイント/認証（Bearer）
  - `wowma_access.py:51-60`
```
self.target_url = "https://api.manager.wowma.jp/wmshopapi/"  # 本番
self.api_key = "********"  # 本番用（直書き、要外部化）
self.shop_id = "********"
self.get_headers = {
  'Authorization': 'Bearer ' + self.api_key,
  'Content-type': 'application/x-www-form-urlencoded',
  'charset': 'UTF-8',
}
self.post_headers = {
  'Authorization': 'Bearer ' + self.api_key,
  'Content-type': 'application/xml',
  'charset': 'UTF-8',
}
```

- 機能別 API 呼び出し
  - 在庫更新: `wowma_access.py:110` 付近 `wowma_update_stock(item_code, stock_count, sales_status)`
  - 価格更新: `wowma_access.py:141` 付近 `wowma_update_item_price(item_code, item_price, item_fixed_price)`
  - 商品登録/更新: `wowma_access.py:167` 付近 `wowma_update_item_info(...)`
  - 受注取得・ステータス更新: `wowma_access.py:87`, `wowma_access.py:120`, `wowma_access.py:123` 等

- 業務ロジックからの呼び出し
  - `yaget/modules.py:20` で `from wowma_access import WowmaAccess`
  - 商品更新実行: `modules.py:442-722`（`ExecWowma.exec_wowma_goods_update`）
  - 画面/Ajax 入口: `yaget/views.py` の `wow_goods_upsert_ajax` など（`yaget/urls.py:33`）
  - バッチ: `yaget/management/commands/wowma_register_item.py:1` ほか多数

## もし未導入なら必要な欠落点

- 認証・設定の外部化
  - `WOWMA_API_KEY`, `WOWMA_SHOP_ID`, `WOWMA_API_BASE` のような .env 管理
- I/F 設計
  - 最小: 在庫更新、価格更新、商品登録/更新、受注取得/更新
  - パラメータ: `item_code`, `category_id`, 送料/配送方法、検索タグ、販売ステータス
- レート制限/リトライ
  - HTTP ステータス監視、429/5xx の指数バックオフ
- ログと監視
  - 現状 `RotatingFileHandler` で記録。外部出力（構造化ログ/可観測性）検討

## 参考ソース抜粋

```
path: wowma_access.py:195
def wowma_update_item_info(self, item_name, item_code, item_gcode, item_price, item_fixed_price,
                           postage_segment, postage, delivery_method_id, description,
                           category_id, keyword, tagid, sale_status, stock, images):

path: yaget/modules.py:508
ret_obj_list = self._wowma_access.wowma_update_item_info(
  item_name=myobj.wow_gname,
  item_code=myobj.gid,
  item_gcode=myobj.gcode,
  item_price=myobj.wow_price,
  ...
  category_id=myobj.wow_ctid,
  tagid=myobj.wow_tagid,
  stock=myobj.stock,
  images=images,
)
```

