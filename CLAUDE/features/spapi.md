# Amazon SP-API

最終更新: 2026-04-18

---

## 接続状態

| 項目 | 状態 |
|------|------|
| 接続確認 | **成功（2026-04-18）** |
| アプリ名 | wowma_api_pro |
| マーケットプレイス | Amazon.co.jp, Non-Amazon JP |
| アカウントID | amzn1.pa.o.A3MWLSTAJAI9R3 |
| アプリケーションID | amzn1.sp.solution.e9c9f8a5-c19b-42aa-8d1f-8bf0544a97ea |

---

## 認証情報の設定場所

### 環境変数（.env）

```
# LWA認証（wowma_api_pro アプリ）
LWA_CLIENT_ID=amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LWA_CLIENT_SECRET=amzn1.oa2-cs.v1.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LWA_REFRESH_TOKEN=Atzr|...（リフレッシュトークン）

# JP向けも同値
JP_LWA_CLIENT_ID=（同上）
JP_LWA_CLIENT_SECRET=（同上）
JP_LWA_REFRESH_TOKEN=（同上）

# AWS IAM キー（既存のまま利用）
AWS_ACCESS_KEY_ID=（.envに記載）
AWS_SECRET_ACCESS_KEY=（.envに記載）
```
> **注意**: 実際の値は `.env` ファイルに記載（git管理外）。GitHubにはコミットしないこと。

> **重要**: `.env` はgit管理外（.gitignore対象）。VPSの `.env` も別途同じ値に更新済み。

### DB（LwaCredentialテーブル）

コード上、リフレッシュトークンは **DBが .env より優先** される。

```python
# spapi_ping.py の優先順位
refresh_token = (
    LwaCredential.objects.values_list("refresh_token", flat=True).first()  # DB優先
    or env("LWA_REFRESH_TOKEN", default=None)  # フォールバック
)
```

VPS DBの `LwaCredential` も 2026-04-18 に新トークンへ更新済み。

---

## 疎通確認コマンド

```bash
# VPSで実行
source /home/django/djangoenv/bin/activate
cd /home/django/sample
python manage.py spapi_ping
```

**正常時の出力例:**
```
status=unknown marketplaces=['Amazon.co.jp', 'Non-Amazon JP']
```

---

## 既存の実装ファイル

| ファイル | 内容 |
|---------|------|
| `yaget/AmaSPApi.py` | SP-APIラッパークラス群（590行） |
| `yaget/management/commands/spapi_ping.py` | 疎通確認コマンド |
| `yaget/management/commands/spapi_catalog_item.py` | カタログアイテム取得（`--asin <ASIN>`） |
| `docs/spapi_setup.md` | セットアップ手順書 |

### AmaSPApi.py の主要クラス

| クラス | 用途 |
|--------|------|
| `AmaSPApi` | 基本クラス（LWAトークン取得・Sellers/Catalog/Products API） |
| `AmaSPApiAsinDetail` | ASIN詳細取得 + DB保存対応 |
| `AmaSPApiQooAsinDetail` | Qoo10向けASIN詳細取得 |

### 利用しているSP-APIエンドポイント

| API | 用途 |
|-----|------|
| `Sellers.get_marketplace_participations` | マーケットプレイス参加状況確認（ping） |
| `CatalogItems` v2022-04-01 | カタログアイテム取得 |
| `Catalog`（レガシー） | 旧カタログAPI |
| `Products` | 商品情報 |
| `Feeds` | フィード |

---

## ライブラリ

```
python-amazon-sp-api==0.16.0   # sp_api パッケージ
boto3==1.24.62                  # AWS SigV4署名
python-dotenv==0.20.0           # .env読み込み
```

---

## 認証フロー

```
1. LwaCredential（DB）または .env から refresh_token を取得
2. LWA endpoint (api.amazon.com) に POST してアクセストークン取得
3. AWS SigV4 で署名（IAMキー使用）
4. SP-API エンドポイント（sellingpartnerapi-fe.amazon.com）へリクエスト
```

---

## 次のステップ候補

- `spapi_catalog_item --asin <ASIN>` でAmazon商品情報検索
- ASIN から商品詳細（タイトル・価格・画像）を取得してDBに保存
- Wowma商品登録フローへの組み込み

---

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `unauthorized_client` (400) | DBの古いリフレッシュトークンが使われている | `LwaCredential` をDjangoシェルで更新 |
| `Missing LWA_CLIENT_ID` | .env の読み込み失敗 | .envファイルの存在・パスを確認 |
| `Missing AWS keys` | IAMキー未設定 | `.env` に `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` を設定 |
