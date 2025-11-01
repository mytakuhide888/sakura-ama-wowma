# 03 Domain Model: Products/Inventory/Price/Category

商品・在庫・価格・カテゴリに関するモデル定義を読み取り、主キーや識別子（ASIN/SKU/JAN/外部ID/カテゴリID）を整理します。関連ビュー/コマンドの所在も付記します。

## モデル（抜粋）

### YaBuyersItemDetail（バイヤーズ商品詳細・Wowma/Qoo10 連携）

- 定義: `yaget/models.py:258`
- 主キー: `gid`（`yaget/models.py:259`）
- 主なフィールド（商品・在庫・価格・カテゴリ）
  - `gcode` バイヤーズ商品コード（`yaget/models.py:268`）
  - `stock` 在庫数（`yaget/models.py:269`）
  - Wowma 関連
    - `wow_on_flg` 出品ステータス（`yaget/models.py:273`）
    - `wow_gname`/`wow_gdetail`（商品名/詳細、`yaget/models.py:274-275`）
    - `wow_price`/`wow_fixed_price`（価格/固定価格、`yaget/models.py:279-280`）
    - `wow_postage_segment`/`wow_postage`/`wow_delivery_method_id`（送料・配送、`yaget/models.py:281-283`）
    - `wow_ctid` カテゴリID（`yaget/models.py:284`）
    - `wow_tagid` タグID（`yaget/models.py:285`）
  - Qoo10 関連
    - `qoo_upd_status`/`qoo_on_flg`/`qoo_gname` など（`yaget/models.py:287-293` 付近）

用途
- Wowma への商品登録・更新時に、名称・価格・在庫・カテゴリ ID・検索タグなどの I/F を満たす構造が揃っています。

### AsinDetail（Amazon 商品詳細）

- 定義: `yaget/models.py:1345`
- 主キー: `asin`（`yaget/models.py:1348`）
- 主なフィールド
  - `title`, `brand`, `color`, サイズ・重量等属性（`yaget/models.py:1349-1364`）
  - ランキングやカテゴリ情報: `product_category_id`, `product_category_rank`（`yaget/models.py:1386-1387`）
  - 価格: `list_price_amount`/`list_price_currency_code`（`yaget/models.py:1373-1374`）

用途
- SP-API からの商品メタデータ格納先。カテゴリ正規化やマッピングのベースに利用可能。

### AmaCategory（Amazon カテゴリマスタ）

- 定義: `yaget/models.py:1416`
- 主キー: `product_cat_id`（`yaget/models.py:1433`）
- 概要: Amazon カテゴリ階層名・関連情報。`wow_cat_id`/`qoo_cat_id` を持ち、外部モールとマッピング可能（`yaget/models.py:1452-1453`）。

### WowCategory（Wowma カテゴリマスタ）

- 定義: `yaget/models.py:1461`
- 主キー: `product_cat_id`（`yaget/models.py:1464`）
- 概要: Wowma の階層カテゴリ名に加え、`ama_level_*` で Amazon 側の対応カテゴリ名を保持（`yaget/models.py:1470-1475`）。

### QooCategory（Qoo10 カテゴリマスタ）

- 定義: `yaget/models.py:1480`
- 主キー: `s_cat_id`（`yaget/models.py:1486`）
- 概要: 小・中・大カテゴリの ID/名称（`yaget/models.py:1486-1491`）。

## 関連ビュー/エンドポイント（DRF ではなく Django ビュー）

- Wowma カテゴリ関連の画面系
  - `yaget/urls.py:71-76` 付近
    - `wowma_cat_list`, `wowma_cat_detail`, `wowma_cat_update`, `wowma_cat_model_list`
- 商品更新/在庫系 Ajax
  - `yaget/urls.py:33-45` 付近
    - `wow_goods_upsert_ajax`, `wow_get_order_info_ajax_res` など

## 管理コマンド/バッチ（Wowma/Qoo10 連携）

- `yaget/management/commands/wowma_register_item.py:1`（Wowma 商品登録・更新系）
- `yaget/management/commands/wowma_stock_chk.py:1`（在庫チェック）
- `yaget/management/commands/wowma_order_chk.py:1`（受注チェック）
- `yaget/management/commands/upload_goods_info.py:1`（商品情報一括アップロード）

## 識別子の扱い（ASIN/SKU/JAN 等）

- ASIN: `AsinDetail.asin` を主キー管理（`yaget/models.py:1348`）
- SKU/JAN: モデル定義からは専用フィールドは未確認（テキスト中に含む可能性はあり）。
- 外部商品コード: `YaBuyersItemDetail.gcode`（`yaget/models.py:268`）、Wowma 側 `item_code` は API 呼出引数で使用（`wowma_access.py:202` 付近）
- カテゴリ ID: `wow_ctid`（Wowma）、`product_category_id`（Amazon）、`s_cat_id`（Qoo10）

## 参考ソース抜粋

```
path: yaget/models.py:259
gid = models.CharField('商品ID', max_length=30, primary_key=True)

path: yaget/models.py:279-285
wow_price = models.IntegerField('wowma価格', ...)
wow_fixed_price = models.IntegerField('wowma固定価格', ...)
wow_ctid = models.IntegerField('カテゴリID', ...)
wow_tagid = models.TextField('タグID', ...)

path: yaget/models.py:1348-1354
asin = models.CharField(max_length=12, default='', primary_key=True)
title = models.TextField(...)
brand = models.TextField(...)
```

