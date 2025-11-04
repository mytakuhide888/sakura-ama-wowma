**目的**
- 本プロジェクトの SP-API 接続作業を別チャットへ円滑に引き継ぐための要点と手順を整理します。

**プロジェクト構成（codex_out から読み取り）**
- `codex_out/00_project_map.md` — リポジトリ全体のマップ概要
- `codex_out/01_python_env_and_deps.md` — Python 環境と必要依存の整理
- `codex_out/02_django_settings_summary.md` — Django の設定要点（環境変数まとめあり）
- `codex_out/04_spapi_scan.md` — SP-API まわりの実装/変数のスキャン結果
- `codex_out/05_aupay_wowma_scan.md` — Wowma/Qoo10 まわりの実装メモ
- `codex_out/99_findings_and_next_actions.md` — 課題と次アクションのサマリ
- SP-API 関連コード（参照位置の例）
  - `yaget/AmaSPApi.py`（LWA/環境変数参照あり: 例 `yaget/AmaSPApi.py:606-608`, `yaget/AmaSPApi.py:1300-1516`）
  - Django 管理コマンド: `yaget/management/commands/spapi_ping.py`, `yaget/management/commands/spapi_catalog_item.py`
  - Web 側: `yaget/urls.py`, `yaget/views.py`

**本チャットで確認できたこと（現状）**
- `yaget/views.py` は文字化けが断続的に発生。最終的に「修正前に戻す」対応済み（= 追加した OAuth ハンドラは未導入）。
- `yaget/urls.py` は以下のルーティングが残っています（有効）。
  - `path('spapi/oauth/start/', views.spapi_oauth_start, name='spapi_oauth_start')`
  - `path('spapi/oauth/callback/', views.spapi_oauth_callback, name='spapi_oauth_callback')`
- 現状は `views.py` に上記ハンドラ定義がないため、アクセスすると AttributeError になります。
- `views.py` のエンコーディングは UTF-8（BOMなし）+ CRLF に正規化済み。ただし、過去に壊れた日本語リテラルは一部プレースホルダへ置換されている箇所があります（必要なら原文で再入力）。

**これから追加/修正すべき機能（Web 側）**
- `spapi_oauth_start`
  - LWA の認可画面へ 302 リダイレクト
  - パラメータ: `client_id`, `response_type=code`, `redirect_uri`, `scope`（用途に応じて）, `state`
  - `redirect_uri` は本番ドメインの `https://<host>/yaget/spapi/oauth/callback/` を Developer Console 側にも登録
- `spapi_oauth_callback`
  - `code` を受けて `https://api.amazon.com/auth/o2/token`（authorization_code）でトークン交換
  - `access_token`/`refresh_token`/`expires_in` を取得
  - 取得トークンの保管（最低でも `refresh_token`）
    - 簡易: `.env`（推奨せず）
    - 推奨: DB モデル（例: `LwaCredential`）や Secrets Manager 等
  - 例外時のログ、ユーザ向けメッセージ、`state` 検証、HTTPS 前提
- 文字化け対策
  - すべて UTF-8（BOMなし）+ CRLF。可能なら `.editorconfig` で保存規則を固定

**SP-API 接続の方針（ライブラリ別）**
- ライブラリA: `python-amazon-sp-api`（0.19.x 系推奨）
  - 署名: AWS SigV4（JP は `endpoint=https://sellingpartnerapi-fe.amazon.com`, `region=us-west-2`）
  - 参照される環境変数（0.19.x 実装ベース）
    - `LWA_APP_ID`（または `LWA_CLIENT_ID`）
    - `LWA_CLIENT_SECRET`
    - `SP_API_REFRESH_TOKEN`
    - `SP_API_ACCESS_KEY`
    - `SP_API_SECRET_KEY`
    - 任意: `SP_API_ROLE_ARN`（AssumeRole 時。`...:role/...`。`user/...` は不可）
    - 任意: `SP_API_DEFAULT_MARKETPLACE`（例: `JP`）
  - 最小疎通（例）
    - `python manage.py spapi_ping`（LWA/接続の検証）
    - あるいはシェル: `from sp_api.api import Sellers; print(Sellers().get_account())`
- ライブラリB: 既存の `yaget/AmaSPApi.py`
  - 参照環境変数（例）
    - `LWA_REFRESH_TOKEN`, `LWA_CLIENT_ID`, `LWA_CLIENT_SECRET`（`yaget/AmaSPApi.py:606-608`）
    - リージョン別: `US_LWA_*`, `JP_LWA_*`（`yaget/AmaSPApi.py:1300-1516`）
  - どちらを採用するかを一本化（両立は混乱の元）

**.env（例・本番は必ず秘匿管理）**
- `python-amazon-sp-api`（0.19.x）想定
  - `LWA_APP_ID=amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxxx`
  - `LWA_CLIENT_SECRET=amzn1.oa2-cs.v1.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
  - `SP_API_REFRESH_TOKEN=Atzr|IwEBI...`
  - `SP_API_ACCESS_KEY=AKIA...`
  - `SP_API_SECRET_KEY=xxxxxxxxxxxxxxxxxxxx`
  - `SP_API_DEFAULT_MARKETPLACE=JP`
  - （AssumeRole）`SP_API_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/YourSpApiRole`
- `AmaSPApi.py` 想定
  - `LWA_CLIENT_ID=...`
  - `LWA_CLIENT_SECRET=...`
  - `LWA_REFRESH_TOKEN=...`
  - （必要なら）`US_LWA_*`, `JP_LWA_*`
- 注意
  - `.env` は絶対にコミットしない
  - Django 側で `environ` を用いて読み込む（`environ.Env.read_env()`）

**LWA（Login With Amazon）側の設定**
- Developer Console で以下を確認
  - `.env` と一致する `Client ID` / `Client Secret`
  - `Allowed Return URLs`: `https://<host>/yaget/spapi/oauth/callback/`
  - セラーが本アプリを認可済み（当該アプリ発行の refresh token を使用）

**IAM / AWS（SigV4）**
- ロール未使用
  - `SP_API_ACCESS_KEY`/`SP_API_SECRET_KEY` で署名
- ロール使用（推奨）
  - `arn:aws:iam::...:role/...` を作成し、Trust policy に署名ユーザーを Principal として `sts:AssumeRole` 許可
  - ユーザーにも対象ロールへの `sts:AssumeRole` 許可
  - `.env` に `SP_API_ROLE_ARN`

**接続確認のステップ（推奨）**
- LWA のトークン交換
  - `POST https://api.amazon.com/auth/o2/token`（refresh_token）で 200 を確認
- Sellers API
  - `from sp_api.api import Sellers; print(Sellers().get_account())`
- Catalog（JP）
  - `from sp_api.api import Catalog; print(Catalog().get_item(asin='B0C5Y2KX3F', marketplaceIds=['A1VC38T7YXB528']))`

**トラブルシューティング**
- `Unauthorized / token expired` が出る
  - LWA と AWS 署名/リージョンの不整合の可能性
  - refresh token と client の組合せ、JP の `endpoint/region` を再確認
- `AssumeRole` 失敗
  - `SP_API_ROLE_ARN` が `user/...` になっていないか、Trust policy/権限を確認
- 文字化け/構文エラー
  - UTF-8（BOMなし）+ CRLF で保存。壊れた文字列は一旦英語に置換し動作優先→後で原文に戻す

**次にやること（引き継ぎ先向け TODO）**
- `views.py` に `spapi_oauth_start` / `spapi_oauth_callback` を実装
- 取得 `refresh_token` の安全な保存方法を決める（DB or Secrets）
- `.env` を整備し、`environ` で読み込む
- 管理コマンド（`spapi_ping.py` / `spapi_catalog_item.py`）で疎通確認
- SP-API ライブラリの採用を一本化
- 必要な日本語文言の原文復元

以上。OAuth ハンドラ実装と .env 設定の整備から再開してください。

