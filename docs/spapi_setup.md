# SP-API セットアップと疎通確認手順

目的: リポジトリ実装（`yaget/management/commands/spapi_ping.py`, `spapi_catalog_item.py`, `yaget/AmaSPApi.py`, `yaget/views.py` の LWA OAuth）に合わせて、必要な認証情報を準備し、疎通確認と商品情報取得を再現できるようにする。

## 1. 必須情報のチェックリスト（Seller Central / Developer Console）
- LWA Client ID (`LWA_CLIENT_ID` または `LWA_APP_ID`) — 開発者コンソールのセキュアクライアント ID。
- LWA Client Secret (`LWA_CLIENT_SECRET`) — 開発者コンソールのセキュアクライアントシークレット。
- LWA Refresh Token (`LWA_REFRESH_TOKEN` または `SP_API_REFRESH_TOKEN`) — OAuth 実行後に得られるリフレッシュトークン。`yaget/views.py:127-220` の OAuth エンドポイントでも取得可能。
- AWS 認証（いずれか）  
  - 直指定: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`（`spapi_ping.py:38-41`）  
  - 代替名: `SP_API_ACCESS_KEY`, `SP_API_ACCESS_KEY_ID`, `SP_API_SECRET_KEY`（`spapi_ping.py:37-40`）  
  - またはロール: `ROLE_ARN` もしくは `SP_API_ROLE_ARN`（`spapi_ping.py:41`）
- Marketplace ID（デフォルト JP は `A1VC38T7YXB528`）— `spapi_catalog_item.py:22` で `SPAPI_MARKETPLACE_ID` を参照。
- リージョン/エンドポイント: JP は `https://sellingpartnerapi-fe.amazon.com` (`us-west-2`), US は `https://sellingpartnerapi-na.amazon.com` (`us-east-1`) — `yaget/AmaSPApi.py:612-619`, `:1506-1527`。
  - 参考: https://developer-docs.amazon.com/sp-api/docs/marketplace-ids

## 2. ローカル環境準備
1. 仮想環境を用意し依存を導入（Django 未導入だと管理コマンドが起動しないため）  
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. `spapi_secrets.local.env` に取得した値をセットし、公開しないこと。Git にはコミットしない（`.gitignore` で除外済み）。
3. WSL シェルで環境変数を読み込み（`set -a` で export を有効化）  
   ```
   set -a
   source spapi_secrets.local.env
   set +a
   ```

## 3. コマンド仕様と実行手順
- `python manage.py spapi_ping`  
  - 参照する環境変数: `LWA_REFRESH_TOKEN` or `SP_API_REFRESH_TOKEN`（DB `LwaCredential` 優先）、`LWA_CLIENT_ID`/`LWA_APP_ID`, `LWA_CLIENT_SECRET`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` もしくは `ROLE_ARN`。(`yaget/management/commands/spapi_ping.py:28-45`)  
  - 動作: Sellers API `get_marketplace_participations` を JP マーケットプレイスで呼び出し、HTTP ステータスと marketplace 名の一覧を出力。
- `python manage.py spapi_catalog_item --asin <ASIN> [--marketplace-id <ID>]`  
  - 参照する環境変数: `SP_API_REFRESH_TOKEN` または `LWA_REFRESH_TOKEN`, `LWA_APP_ID`/`LWA_CLIENT_ID`, `LWA_CLIENT_SECRET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, （任意）`ROLE_ARN`, `SPAPI_MARKETPLACE_ID`。(`yaget/management/commands/spapi_catalog_item.py:20-38`)  
  - 動作: Catalog Items v2022-04-01 `get_catalog_item` → 取れなければ `search_catalog_items` で ASIN をキーワード検索し、`asin` と商品名を出力。
- 補足（画面連携）: `yaget/views.py:6219-6431` で ASIN CSV/単体入力を受け、`exec_get_qoo_asin_detail_upd_csv` 管理コマンドをサブプロセス起動して SP-API で商品詳細を取得・DB 登録するフローを提供。

## 4. 成功判定と失敗時の切り分け
- 合格基準  
  - `spapi_ping`: `status=200` など 2xx ステータスが表示され、`marketplaces` に少なくとも JP (`A1VC38T7YXB528`) が含まれる。  
  - `spapi_catalog_item`: 標準出力に `asin=<ASIN> name=<商品名>` が出る（空でない名称が期待）。  
- 代表的な失敗パターン  
  - `401 Unauthorized`: LWA クライアント/リフレッシュトークン不整合、または期限切れ。`LWA_*`/`SP_API_REFRESH_TOKEN` を再取得。  
  - `403 Forbidden`: 出品者権限不足（SP-API 権限未付与）または Marketplace 不一致。Seller Central のロール付与と Marketplace ID を確認。  
  - `InvalidSignatureException`/`Request signature we calculated does not match`: AWS キー/リージョンの不整合、`sellingpartnerapi-na` vs `-fe` 混在を確認。  
  - `MissingAuthenticationToken`/`AccessDenied`: ROLE_ARN/アクセスキー未設定。`spapi_ping` のエラーメッセージを参照して再設定。  
  - `TypeError` in `get_catalog_item`: `sp_api` ライブラリの古いシグネチャ。`spapi_catalog_item.py` 内でフォールバック実装済みだが、`pip install --upgrade python-amazon-sp-api` で改善する場合あり。

## 5. 検証手順まとめ
1. 依存導入（上記 2.1）。  
2. `spapi_secrets.local.env` を編集し、`set -a; source spapi_secrets.local.env; set +a`。  
3. `python manage.py spapi_ping` で 200 系と marketplace 名が出ることを確認。  
4. `python manage.py spapi_catalog_item --asin B00EXAMPLE --marketplace-id A1VC38T7YXB528` を実行し、`asin=... name=...` が返ることを確認。  
5. UI 経由で CSV/単体 ASIN を登録する場合は、`/yaget/get_qoo_asin_detail_upd_csv` または `/yaget/get_qoo_asin_detail_single` を開き、バックグラウンドで `exec_get_qoo_asin_detail_upd_csv` が動くことをログで確認。

## 6. 安全上の注意
- リフレッシュトークンやシークレットは `spapi_secrets.local.env` のみに保持し、コミット・ログ出力しない。  
- 本番用キーをローカルで使う場合は IP 制限やロール分離を推奨。  
- ログにリクエスト/レスポンス全文を残す場合は、個人情報やトークンをマスクすること。  
- 失敗時に画面から得たリフレッシュトークンは `LwaCredential` モデル（DB）に保存されるため、DB ダンプの取り扱いにも注意。
