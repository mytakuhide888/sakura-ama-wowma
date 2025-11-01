# 01 Python Environment and Dependencies

本レポートは、コードから推定される Python/Django/主要ライブラリのバージョン候補と依存候補を整理します（ローカルの requirements 等は未検出）。

## バージョン候補

- Python: 3.8+（推定。Django 3.2 系が利用可能な範囲）
- Django: 3.2.9（`sample/settings.py:3` のコメントに明記）

## 主要ライブラリ（コードから推定）

- Django 関連
  - `django`（フレームワーク本体）
  - `django-widget-tweaks`（`sample/settings.py:24` の `widget_tweaks`）
- 認証・API 関連
  - `python-amazon-sp-api`（`sp_api` モジュール。`yaget/AmaSPApi.py:23`）
  - `requests`（HTTP クライアント。`wowma_access.py:18`, `yaget/AmaSPApi.py:32` 等）
  - `oauth2client`（Google API 認証。`yaget/AmaSPApi.py:20`, `yaget/views.py:22`）
  - `gspread`（Google スプレッドシート。`yaget/modules.py:5`, `yaget/views.py:10`）
  - `environ`（Django-environ。`yaget/views.py:15`）
- 解析・スクレイピング
  - `lxml`（HTML 解析。`wowma_access.py:16`）
  - `selenium` / `webdriver-manager`（ヘッドレス Chrome。`chrome_driver.py:21`）
- ロギング
  - Python 標準 logging（`sample/settings.py:95` LOGGING 設定、`wowma_access.py` で `logging.config.fileConfig`）

依存定義ファイルが無いため、上記は import からの推定です。環境再現には各ライブラリのインストールが必要です。

## 依存一覧（推定・抜粋）

```
django==3.2.*
django-widget-tweaks
python-amazon-sp-api
requests
oauth2client
gspread
environ
lxml
selenium
webdriver-manager
```

## SP-API / au PAY マーケット関連の候補パッケージ

- Amazon SP-API 直接関連
  - `python-amazon-sp-api`（import 名: `sp_api`）
- 間接/補助
  - `requests`（HTTP 呼び出し）
- au PAY マーケット（Wowma）
  - 専用 SDK は未使用。`requests` による `wmshopapi` 直叩き（`wowma_access.py:1`）

## 探索キーワードの出現状況（簡易）

- SP-API 系
  - `sp_api` import: `yaget/AmaSPApi.py:23`
  - LWA/refresh token 等: `yaget/AmaSPApi.py:604-608`, `yaget/AmaSPApi.py:1500-1516` ほか
- Wowma/au PAY マーケット系
  - API エンドポイント: `wowma_access.py:51`（`https://api.manager.wowma.jp/wmshopapi/`）
  - Bearer 認証ヘッダ: `wowma_access.py:66-74`

## 関連しそうな文字列（スキャン）

- Amazon 関連: `sp_api`, `Catalog`, `Products`, `LWA`, `refresh_token`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `SELLER_ID`
- Wowma/au PAY 関連: `wowma`, `wmshopapi`, `Authorization: Bearer`, `category`, `item_code`, `item_price`, `stock`, `delivery_method_id`

依存ファイル（requirements, Pipfile, pyproject）は未検出のため、導入時は上記推定に基づき環境を整備してください。

