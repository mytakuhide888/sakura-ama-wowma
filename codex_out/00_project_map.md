# 00 Project Map (Python/Django scope)

対象リポジトリ: `/home/niiya/sakura-ama-wowma`

本レポートは Python/Django 関連ファイルのみを俯瞰し、主要エントリ・設定・アプリ・モデル・コマンド位置を示します。

## 概要

- Django プロジェクト構成を確認
  - `manage.py` あり: `manage.py:1`
  - プロジェクトモジュール: `sample/` に各種設定・エントリ
  - アプリケーション: `yaget/`, `helloworld/`
  - テンプレート: `templates/`
- 依存定義ファイルは未検出（requirements.txt, pyproject.toml 等なし）

## ルート直下（Python/Django 関連）

- `manage.py:1`
- `sample/`（Django プロジェクト）
  - `sample/settings.py:1`（INSTALLED_APPS, MIDDLEWARE, DATABASES, LOGGING 等）
  - `sample/urls.py:1`（ルート URL ルーティング）
  - `sample/wsgi.py:1`（WSGI エントリ）
  - `sample/asgi.py:1`（ASGI エントリ）
  - `sample/views.py:1`（ヘルスチェック、簡易ビュー）
- アプリ: `yaget/`
  - `yaget/apps.py:1`
  - `yaget/models.py:1`（多数の商品・注文・カテゴリ等のモデルを包含）
  - `yaget/views.py:1`（機能多数。Ajax 系やバックエンド処理のトリガ入口）
  - `yaget/urls.py:1`（アプリ内 URL。Wowma/Qoo10 関連多数）
  - `yaget/admin.py:1`（管理画面登録。Wowma 注文情報など）
  - `yaget/forms.py:1`（各種フォーム、Wowma カテゴリ編集フォーム含む）
  - `yaget/modules.py:1`（Wowma/Qoo10 連携や実行モジュール）
  - `yaget/migrations/`（初期化含む）
  - `yaget/management/commands/`（バッチコマンド群）
    - 例: `wowma_register_item.py:1`, `wowma_stock_chk.py:1`, `wowma_order_chk.py:1`,
      `get_wowma_buyers_list.py:1`, `upload_goods_info.py:1` など
- アプリ: `helloworld/`
  - `helloworld/models.py:1`（空定義）
  - `helloworld/views.py:1`
  - `helloworld/urls.py:1`
  - `helloworld/admin.py:1`
- 連携ユーティリティ
  - `wowma_access.py:1`（Wowma API 直接呼び出し・Bearer 認証）
  - `qoo10_access.py:1`（Qoo10 連携）
  - `gmail_access.py:1`（Gmail 連携）
  - `chrome_driver.py:1`（Selenium Chrome ドライバ管理）
  - `buyers_info.py:1`（バイヤーズサイト解析・CSV/在庫・カテゴリ推定）
  - `batch_status.py:1`（バッチステータス更新ユーティリティ）

## Django 主要ファイルの所在

- manage.py: `manage.py:1`
- settings: `sample/settings.py:1`
- urls: `sample/urls.py:1`
- wsgi: `sample/wsgi.py:1`
- asgi: `sample/asgi.py:1`

## Django アプリの主要要素

- yaget
  - models: `yaget/models.py:1`
  - views: `yaget/views.py:1`
  - urls: `yaget/urls.py:1`
  - admin: `yaget/admin.py:1`
  - apps: `yaget/apps.py:1`
  - forms: `yaget/forms.py:1`
  - management/commands: `yaget/management/commands/`（Wowma/Qoo10 関連コマンド多数）
  - AmaSPApi（SP-API 実装）: `yaget/AmaSPApi.py:1`
- helloworld（サンプル）

## モデル・シリアライザ・ビュー・タスク

- モデル
  - 商品/在庫/価格/カテゴリ関連: `yaget/models.py:258`（`YaBuyersItemDetail` 等）
  - Amazon 商品詳細（ASIN 単位）: `yaget/models.py:1345`（`AsinDetail`）
  - カテゴリマスタ: `yaget/models.py:1416`（`AmaCategory`）, `yaget/models.py:1461`（`WowCategory`）, `yaget/models.py:1480`（`QooCategory`）
- シリアライザ
  - DRF の `serializers.py` は未検出
- ビュー
  - `yaget/views.py:1`（Ajax/API 風エンドポイント多）
- タスク/スケジューラ
  - `celery.py` や `tasks.py`、beat/crontab の記述は未検出

## 依存・環境ファイルの有無

- requirements*.txt: なし
- pyproject.toml / poetry.lock: なし
- Pipfile*: なし
- setup.cfg: なし
- .env*: プロジェクト直下は未検出（`sample/wsgi.py:9` で `.env` ロード試行あり）
- Dockerfile* / docker-compose*.yml: 未検出

## 参考: API/外部サービス連携の入口

- Amazon SP-API 実装: `yaget/AmaSPApi.py:1`（`sp_api` ライブラリ利用と LWA 認証変数）
- Wowma API: `wowma_access.py:1`（`https://api.manager.wowma.jp/wmshopapi/` へ Bearer 認証）
- Qoo10 連携: `qoo10_access.py:1`

