# 99 Findings and Next Actions

## サマリ（要点）

- Django 3.2 系のプロジェクト（`sample/`）に、事業ロジックの大半は `yaget/` アプリへ集約
- 依存定義ファイル（requirements/pyproject 等）は未検出。import から `python-amazon-sp-api` / `requests` / `lxml` / `selenium` / `gspread` / `oauth2client` などが必要
- Amazon SP-API
  - 実装: `yaget/AmaSPApi.py:1`
  - LWA/AWS 資格情報は環境変数から取得（`LWA_*`, `AWS_*`, `*_LWA_*`, `*_AWS_*`）
  - `.env` はリポジトリ直下未検出。実行環境での設定が前提
- au PAY マーケット（Wowma）
  - 直呼び出し: `wowma_access.py:1`（`wmshopapi` に Bearer 認証）
  - API キー/Shop ID がコード直書き（マスク済）。`.env` への外部化推奨
- ドメインモデル
  - 商品・在庫・価格・カテゴリ: `YaBuyersItemDetail`（`yaget/models.py:258`）
  - Amazon 商品詳細: `AsinDetail`（`yaget/models.py:1345`）
  - カテゴリマスタ: `AmaCategory` / `WowCategory` / `QooCategory`（マッピング前提の設計）
- ビュー/コマンド
  - 画面/URL: `yaget/urls.py:1`（Wowma/Qoo10 管理/更新系多数）
  - 管理コマンド: `yaget/management/commands/`（Wowma/Qoo10 の受注/在庫/商品登録/CSV）

## 推奨 ToDo（優先順）

1) 環境変数・機微情報の外部化と依存定義
   - `.env` に `LWA_CLIENT_ID`, `LWA_CLIENT_SECRET`, `LWA_REFRESH_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SELLER_ID`, `WOWMA_API_KEY`, `WOWMA_SHOP_ID` 等
   - `requirements.txt` を整備（`django==3.2.*`, `python-amazon-sp-api`, `requests`, `lxml`, `selenium`, `webdriver-manager`, `gspread`, `oauth2client`, `django-widget-tweaks`, `environ`）

2) SP-API 接続検証（認証〜最小 API 叩き）
   - 手順
     - 依存導入 → LWA/AWS 環境変数設定
     - `Sellers().get_marketplace_participations()` を実行して 200/エラー応答を確認
   - 成功基準: 正常レスポンス/認証エラー解消

3) Wowma API での商品更新 PoC（認証〜単品更新）
   - `.env` に `WOWMA_API_KEY`/`WOWMA_SHOP_ID` を格納し、`wowma_access.py` の直書きを環境参照に移行
   - `wowma_update_item_price` か `wowma_update_item_info` を単品で叩き、`res_code` と API 応答 XML を確認

4) カテゴリ正規化とマッピング設計
   - `AmaCategory` を軸に `WowCategory`/`QooCategory` を突合
   - 不一致・未マッピングを抽出する管理コマンド（dry-run / CSV 出力）を追加
   - 商品側（`YaBuyersItemDetail.wow_ctid`）の自動補完ロジック（キーワード/階層パス）をモジュール化

5) ロギング/監視の見直し
   - ログレベルと出力先の整備（本番は DEBUG 不可・構造化ログ検討）
   - 機微情報（キー/トークン）のログ出力抑止

## 留意事項

- `sample/settings.py` に秘匿情報（SECRET_KEY, DB 認証）が直書き。運用前に環境変数化を必須とする
- `DEBUG=True` は本番で無効化

