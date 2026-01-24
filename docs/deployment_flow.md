# 開発環境とデプロイフローまとめ

## 環境構成
- ローカル: Windows 11 上の WSL2 Ubuntu。作業ディレクトリ `\\wsl.localhost\Ubuntu\home\niiya\sakura-ama-wowma`（WSL では `/home/niiya/sakura-ama-wowma`）。VSCode でこのフォルダを開き、Git で GitHub の origin に push。
- 本番/VPS: さくら VPS 上の `django@133.167.75.151`。プロジェクトパス `/home/django/sample`、venv は `/home/django/djangoenv/`。
- 公開 URL 例: `https://boasolte.com/`, `https://boasolte.com/yaget/buyers_goods_detail_list/`。

## ローカル→GitHub→VPS 反映フロー
1. ローカル (WSL) で編集。必要なら `.venv` を作り `pip install -r requirements.txt`。
2. `git status` で確認し、コミット & `git push origin main`。
3. VPS へ SSH: `ssh django@133.167.75.151`。
4. venv 有効化: `source /home/django/djangoenv/bin/activate`。
5. `/home/django/sample` へ移動して `git pull`。
6. 依存が増えた場合のみ: `pip install -r requirements.txt`（venv 内）。
7. アプリ再起動（必要最小限で実行）:
   - アプリのみ: `pkill -HUP gunicorn`
   - サービス経由: `sudo systemctl restart gunicorn`
   - Web サーバ: `sudo systemctl restart nginx`
   - 手動起動（デバッグ用）: `cd /home/django/sample && gunicorn --bind 127.0.0.1:8000 sample.wsgi -D`

## ファイル更新の扱い
- `.env` は VPS 側で直接編集（Git 管理外）。`spapi_secrets.local.env` はローカルテンプレートのみで、実値は入れずに push しない。
- マイグレーションが発生した場合: VPS で venv 有効化後 `python manage.py migrate` を実行。

## SP-API 疎通確認（どこで実行するか）
- ローカル WSL で可能: `pip install -r requirements.txt` を済ませ、`spapi_secrets.local.env` に実値を入れて `set -a; source spapi_secrets.local.env; set +a` 後に `python manage.py spapi_ping` / `python manage.py spapi_catalog_item --asin <ASIN> --marketplace-id A1VC38T7YXB528` を実行。秘密情報を Git に含めないこと。
- VPS での確認: venv を有効化し、`.env` に同じ値を追記またはシェルで `export`。上記コマンドを `/home/django/sample` で実行。ログイン中セッションのみで使う場合はシェルで `export` を推奨。
- どちらで実施しても結果は同じだが、ネットワークや環境差異を考慮し、本番接続確認は VPS 側で行うのが安全。ローカルは事前検証用。

## SP-API 用環境変数の配置ポリシー
- ローカル: `spapi_secrets.local.env` にのみ記入し、Git には含めない。VSCode ターミナルで `set -a; source spapi_secrets.local.env; set +a`。
- VPS: `/home/django/sample/.env` に追記するか、都度 `export LWA_CLIENT_ID=...` などで設定。`.env` は Git 管理外で秘密保持。

