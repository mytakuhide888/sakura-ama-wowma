# 04 SP-API Scan (Amazon Selling Partner API)

コード・設定・依存から SP-API 利用の痕跡を抽出します。該当箇所が無い場合は導入に必要な欠落点も列挙します。

## 痕跡（ファイルと抜粋）

- `yaget/AmaSPApi.py:23-25`
```
from sp_api.api import Feeds
from sp_api.api import Sellers, Catalog, Products, CatalogItems
from sp_api.base.marketplaces import Marketplaces
```

- LWA クレデンシャル/トークン（環境変数）
  - `yaget/AmaSPApi.py:604-608`
```
self.target_url = "https://api.amazon.com/auth/o2/token"
self.grant_type = "refresh_token"
self.refresh_token = os.getenv('LWA_REFRESH_TOKEN', '')
self.client_id = os.getenv('LWA_CLIENT_ID', '')
self.client_secret = os.getenv('LWA_CLIENT_SECRET', '')
```

- リージョン別 LWA/AWS キー
  - `yaget/AmaSPApi.py:1500-1516`
```
self.us_refresh_token = os.getenv('US_LWA_REFRESH_TOKEN', '')
self.us_client_id = os.getenv('US_LWA_CLIENT_ID', '')
self.us_client_secret = os.getenv('US_LWA_CLIENT_SECRET', '')
self.jp_refresh_token = os.getenv('JP_LWA_REFRESH_TOKEN', '')
self.jp_client_id = os.getenv('JP_LWA_CLIENT_ID', '')
self.jp_client_secret = os.getenv('JP_LWA_CLIENT_SECRET', '')
self.jp_aws_access_key = os.getenv('JP_AWS_ACCESS_KEY_ID', '')
self.jp_aws_secret_access_key = os.getenv('JP_AWS_SECRET_ACCESS_KEY', '')
```

- AWS 資格情報（環境変数）
  - `yaget/AmaSPApi.py:103-106`
```
AMAZON_CREDENTIAL = {
  'SELLER_ID': os.getenv('AWS_SELLER_ID', ''),
  'ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', ''),
  'ACCESS_SECRET': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
}
```

- SP-API クライアント生成（抜粋）
  - `yaget/AmaSPApi.py:623-628` ほか（`refresh_token`, `lwa_app_id`, `lwa_client_secret` を指定）

## 依存パッケージ

- `python-amazon-sp-api`（import 名 `sp_api`）が前提

## 現状の整備状況の要約

- コード上は LWA リフレッシュトークン/クライアント ID/シークレット、および AWS アクセスキー/シークレット/セラー ID を環境変数から取得する実装が存在
- 実リポジトリ内に `.env`/`requirements.txt` が無いため、実行環境側で環境変数と依存導入が必要

## もし未導入なら必要な欠落点

- パッケージ導入
  - `python-amazon-sp-api`, `requests` 等
- 認証・資格情報
  - `LWA_CLIENT_ID`, `LWA_CLIENT_SECRET`, `LWA_REFRESH_TOKEN`
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SELLER_ID`
  - 必要に応じて `ROLE_ARN`（STS AssumeRole）
- 設定
  - マーケットプレイス ID やエンドポイント（`Marketplaces.JP` 等）
- HTTP 署名/再試行
  - `python-amazon-sp-api` が署名周りを抽象化。レート制限に応じたリトライ設計が必要

## 最小接続検証（方針）

1) 環境変数を設定（上記 LWA/AWS 系）
2) `python-amazon-sp-api` を導入
3) `Sellers().get_marketplace_participations()` など読み取り系 API を 1 本叩いて 200/エラー応答を確認

エラー時は LWA/AWS 資格情報と出品者アカウントの権限（SP-API 権限・リージョン）が正しいかを確認します。

