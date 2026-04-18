# sakura-ama-wowma プロジェクト概要

最終更新: 2026-04-18

---

## 目的

Django製の業務アプリ。ECプラットフォーム間の商品/注文/在庫を管理する。

| プラットフォーム | 連携状況 |
|----------------|---------|
| au PAYマーケット（Wowma） | 稼働中（注文・在庫・商品登録） |
| Qoo10 | 稼働中（注文・在庫） |
| Amazon SP-API | 接続確認済み（2026-04-18）、実装拡張中 |

---

## 環境構成

| 環境 | 詳細 |
|------|------|
| ローカル | Windows 11 + WSL2 Ubuntu、作業パス `/home/niiya/sakura-ama-wowma` |
| 本番VPS | さくらVPS Ubuntu、IP `133.167.75.151`、パス `/home/django/sample` |
| DB（開発） | SQLite |
| DB（本番） | ConoHa MariaDB |
| ドメイン | boasolte.com |

詳細 → [ops/server.md](ops/server.md)

---

## ディレクトリ構成

```
sakura-ama-wowma/
├── sample/              # Django設定（settings.py, urls.py等）
├── yaget/               # メインアプリ
│   ├── models.py        # データモデル定義
│   ├── views.py         # ビュー（大規模）
│   ├── AmaSPApi.py      # Amazon SP-API連携クラス群
│   └── management/commands/  # 管理コマンド群
├── category/
│   ├── amazon/          # Amazon BTG Excelファイル
│   └── wowma/           # Wowmaカテゴリデータ
├── docs/
│   ├── category_mapping/ # カテゴリマッピング補助ファイル
│   └── spapi_setup.md   # SP-APIセットアップ手順書
├── codex_out/           # 実行結果TSV・調査ノート
├── CLAUDE/              # このドキュメント群
└── .env                 # 環境変数（秘匿情報・git管理外）
```

---

## 主要な管理コマンド

### Amazon SP-API
| コマンド | 用途 |
|---------|------|
| `spapi_ping` | 接続疎通確認 |
| `spapi_catalog_item --asin <ASIN>` | カタログアイテム取得 |

### カテゴリ
| コマンド | 用途 |
|---------|------|
| `import_categories --source amazon` | Amazonカテゴリインポート |
| `import_categories --source wowma` | Wowmaカテゴリインポート |
| `match_categories` | Amazon↔Wowmaカテゴリ自動マッチング |

### Wowma
| コマンド | 用途 |
|---------|------|
| `wowma_stock_chk` | 在庫チェック |
| `wowma_register_item` | 商品登録 |
| `wowma_order_chk` | 注文チェック |
| `wowma_do_buyers_order` | バイヤー注文実行 |

### Qoo10
| コマンド | 用途 |
|---------|------|
| `qoo_order_chk` | 注文チェック |
| `exec_get_qoo_asin_detail_upd_csv` | ASIN詳細CSV更新 |

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| フレームワーク | Django 3.2.9 |
| Python | 3.8+ |
| SP-APIライブラリ | python-amazon-sp-api 0.16.0 |
| AWS SDK | boto3 1.24.62 |
| その他 | selenium, beautifulsoup4, openpyxl, xlrd |

---

## 主要モデル（yaget/models.py）

| モデル | 用途 |
|--------|------|
| `AmaCategory` | Amazonカテゴリ（`wow_cat_id` でWowmaと紐づけ） |
| `WowCategory` | Wowmaカテゴリ |
| `LwaCredential` | SP-APIリフレッシュトークン（DB管理、.envより優先） |

---

## 運用ルール

- 秘匿情報は `.env` に集約（git管理外）
- git add/commit/push は人間が実施
- 変更は最小差分で実施
- マイグレーションはVPS上でのみ実行
