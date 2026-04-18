# sakura-ama-wowma プロジェクト概要

## 1. プロジェクトの目的
Django 3.2ベースの業務アプリケーション。以下のECプラットフォームと連携し、商品/注文/在庫の管理を行う。
- au PAYマーケット（Wowma）
- Qoo10
- Amazon SP-API

## 2. 環境構成

### ローカル環境
- **OS**: Windows 11 + WSL2 Ubuntu
- **作業パス**: `/home/niiya/sakura-ama-wowma`
- **VSCode**: `\\wsl.localhost\Ubuntu\home\niiya\sakura-ama-wowma`
- **DB**: SQLite（開発用）

### 本番環境
- **サーバー**: さくらVPS（Ubuntu）
- **IPアドレス**: 133.167.75.151
- **本番パス**: `/home/django/sample`
- **venvパス**: `/home/django/djangoenv/`
- **ドメイン**: boasolte.com / www.boasolte.com
- **DB**: ConoHa MariaDB

### デプロイフロー
1. ローカルで編集
2. GitHub経由でpush
3. VPSで `git pull`
4. `pkill -HUP gunicorn` または `sudo systemctl restart gunicorn`

## 3. ディレクトリ構成

```
sakura-ama-wowma/
├── sample/              # Django設定（settings.py, urls.py等）
├── yaget/               # メインアプリ
│   ├── models.py        # データモデル定義
│   ├── views.py         # ビュー（323KB - 大規模）
│   ├── forms.py         # フォーム
│   ├── urls.py          # URLルーティング
│   ├── AmaSPApi.py      # Amazon SP-API連携
│   ├── modules.py       # 共通モジュール
│   ├── templates/yaget/ # 画面テンプレート
│   └── management/commands/  # 管理コマンド群
├── helloworld/          # 簡易サンプルアプリ
├── templates/           # 全体テンプレート
├── category/            # カテゴリデータ
│   ├── amazon/          # Amazon BTG Excelファイル群
│   └── wowma/           # Wowmaカテゴリデータ
├── docs/                # ドキュメント
│   └── category_mapping/ # カテゴリマッピング補助ファイル
├── codex_out/           # 調査/ハンドオフノート
├── log/                 # ログファイル
├── .env                 # 環境変数（秘匿情報）
├── CODEX.md             # プロジェクトルール（codex作成）
└── 外部連携ユーティリティ（リポジトリ直下）
    ├── wowma_access.py
    ├── qoo10_access.py
    ├── gmail_access.py
    ├── chrome_driver.py
    ├── buyers_info.py
    └── batch_status.py
```

## 4. 主要な管理コマンド

### Wowma関連
- `wowma_stock_chk` - 在庫チェック
- `wowma_register_item` - 商品登録
- `wowma_order_chk` - 注文チェック
- `wowma_do_buyers_order` - バイヤー注文実行
- `wowma_send_gmail` - Gmail送信

### Qoo10関連
- `qoo_order_chk` - 注文チェック
- `qoo_do_buyers_order` - バイヤー注文実行
- `exec_get_qoo_asin_detail_upd_csv` - ASIN詳細CSV更新

### バイヤーズ取得
- `get_buyma_buyers_list` - Buymaバイヤーリスト取得
- `get_wowma_buyers_list` - Wowmaバイヤーリスト取得
- `get_ya_buyers_list` - ヤフオクバイヤーリスト取得

### Amazon SP-API
- `spapi_catalog_item` - カタログアイテム取得
- `spapi_ping` - SP-API接続確認

### カテゴリ関連
- `import_categories` - カテゴリインポート
- `match_categories` - カテゴリマッチング

### 商品管理
- `upload_goods_info` - 商品情報アップロード
- `delete_goods_info` - 商品情報削除

## 5. 主要なモデル（yaget/models.py）

### Yahoo/ヤフオク関連
- `YaListUrl` / `YaShopListUrl` - URLリスト
- `YaItemList` / `YaShopItemList` - アイテムリスト
- `YaItemDetail` - アイテム詳細
- `YaAmaGoodsDetail` / `YaShopAmaGoodsDetail` - Amazon商品詳細

### カテゴリ関連
- `AmazonCategory` - Amazonカテゴリ
- `WowmaCategory` - Wowmaカテゴリ
- `CategoryMapping` - カテゴリマッピング

## 6. 技術スタック

- **フレームワーク**: Django 3.2.9
- **Python**: 3.8+
- **DB**: SQLite（開発）/ MariaDB（本番）
- **主要ライブラリ**:
  - python-amazon-sp-api - Amazon SP-API連携
  - boto3 - AWS SDK
  - selenium - ブラウザ自動化
  - beautifulsoup4 - HTMLパース
  - requests - HTTP通信
  - django-widget-tweaks - フォームウィジェット
  - openpyxl, xlrd - Excel操作

## 7. 注意事項

### セキュリティ
- 秘匿情報は `.env` に集約（リポジトリにコミットしない）
- `settings.py` に一部直書きの認証情報あり（要外部化）
- ログに個人情報/トークンを出力しない

### 運用ルール
- 既存仕様（API/画面/戻り値/文言）を勝手に変更しない
- 変更は最小差分で実施
- git add/commit/push/branch操作は人間が実施
- マイグレーション/モデル変更は担当者一人で実施

## 8. 参照ドキュメント

- `/home/niiya/sakura-ama-wowma/CODEX.md` - プロジェクトルール（codex作成）
- `/home/niiya/sakura-ama-wowma/docs/spapi_setup.md` - SP-APIセットアップ手順
- `/home/niiya/sakura-ama-wowma/docs/deployment_flow.md` - デプロイフロー
- `/home/niiya/sakura-ama-wowma/codex_out/` - 調査/ハンドオフノート群
