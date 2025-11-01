# 06 Category Mapping Surface

カテゴリマスタ／マッピングの有無を探索し、データ構造と I/F を整理します。

## 既存コードのカテゴリ関連

- Amazon カテゴリ（SP-API 由来）
  - モデル: `yaget/models.py:1416`（`AmaCategory`）主キー `product_cat_id: yaget/models.py:1433`
  - 階層名: `level_1_cat_name`〜`level_8_cat_name`（`yaget/models.py:1444-1451`）
  - 外部マッピング: `qoo_cat_id`, `wow_cat_id`（`yaget/models.py:1452-1453`）

- Wowma カテゴリ
  - モデル: `yaget/models.py:1461`（`WowCategory`）主キー `product_cat_id: yaget/models.py:1464`
  - 階層名: `level_1_cat_name`〜`level_4_cat_name`（`yaget/models.py:1466-1469`）
  - Amazon 側対応名: `ama_level_1_cat_name`〜`ama_level_3_cat_name`（`yaget/models.py:1473-1475`）

- Qoo10 カテゴリ
  - モデル: `yaget/models.py:1480`（`QooCategory`）主キー `s_cat_id: yaget/models.py:1486`
  - 中/大カテゴリ ID/名称: `m_cat_id`, `l_cat_id`（`yaget/models.py:1488-1491`）

## 画面/I/F 入口

- `yaget/urls.py:71-76`
  - `wowma_cat_list`, `wowma_cat_detail`, `wowma_cat_update`, `wowma_cat_model_list`
  - `yaget/forms.py:717`（`WowCategoryForm`）, `yaget/forms.py:793`（`WowCategoryModelForm`）

## まとめ

- すでに Amazon⇄Wowma⇄Qoo10 のカテゴリマスタがモデル化され、相互参照用のフィールド（`qoo_cat_id`, `wow_cat_id`, `ama_level_*`）が存在
- I/F は Django ビュー＋フォームで整備済み（DRF エンドポイントは未検出）

## （未検出の場合の）設計叩き台

本リポジトリはカテゴリマッピングが実装済みのため、以下は補足方針です。

- Amazon 側
  - SP-API Catalog/Product Type からカテゴリメタ（ID/階層/属性）を定期同期
  - `AmaCategory` を基準に `product_type_name` など属性を拡張
- Wowma 側
  - Wowma API のカテゴリ一覧を取得し `WowCategory` を充足
  - 属性差（必須項目、階層深度）をメタとして保持
- マッピング
  - `AmaCategory.wow_cat_id` を一次マップとし、不一致箇所はフォーム/管理コマンドで手当
  - 曖昧一致（キーワード/パス経路）の補助テーブルを追加する場合は中間モデルで管理

