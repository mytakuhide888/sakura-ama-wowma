# CODEX

## 1. このプロジェクトの全体像
- 目的: Django 3.2 ベースの業務アプリ。au PAY マーケット（Wowma）、Qoo10、Amazon SP-API 連携で商品/注文/在庫を取得・更新し、管理画面・バッチで運用する。
- 環境/パス: ローカルは Windows11 上の WSL2 Ubuntu、作業パス `/home/niiya/sakura-ama-wowma`（VSCode から `\\wsl.localhost\Ubuntu\home\niiya\sakura-ama-wowma` を開く）。本番はさくら VPS `/home/django/sample`（venv `/home/django/djangoenv/`）。GitHub を経由して push/pull し、VPS では `git pull`→`source /home/django/djangoenv/bin/activate`→`pkill -HUP gunicorn` / `sudo systemctl restart nginx` / `sudo systemctl restart gunicorn` / 必要なら `gunicorn --bind 127.0.0.1:8000 sample.wsgi -D` で反映。
- 構成: プロジェクトモジュール `sample/`、メインアプリ `yaget/`（画面・業務ロジック・管理コマンド）、簡易サンプル `helloworld/`、全体テンプレート `templates/`。外部連携ユーティリティがリポジトリ直下に配置（`wowma_access.py`, `qoo10_access.py`, `gmail_access.py`, `chrome_driver.py`, `buyers_info.py`, `batch_status.py`）。
- 主要ディレクトリ:  
  - `sample/`…Django 設定 (`settings.py` は SQLite/ConoHa MariaDB 設定と logging 定義、テンプレート dir 追加)。  
  - `yaget/`…モデル・ビュー・フォーム・URL・管理コマンド群（Wowma/Qoo10/Buyma/SP-API/カテゴリーマッチング）。`templates/yaget/` に画面多数。  
  - `category/amazon/`…Amazon BTG（ブラウズツリーガイド）Excel 群。`category/wowma/`…Wowma カテゴリ Excel。  
  - `docs/category_mapping/`…カテゴリ対応の補助ファイル（level_1_cat.txt, synonyms.tsv, review TSV）。  
  - `templates/`…トップや共通テンプレート。  
  - `codex_out/`…調査/ハンドオフノート。  
- 起動方法（ローカル開発・Secrets は .env に入れる）:
  1. `python -m venv .venv && source .venv/bin/activate`（Windows PowerShell なら `./.venv/Scripts/Activate.ps1`）
  2. `pip install -r requirements.txt`
  3. `.env` をプロジェクト直下に配置（DB 認証・API キー類は必ずここへ。リポジトリにコミットしない）
  4. `python manage.py migrate`（開発は SQLite デフォルト。MariaDB を使う場合は `DATABASES['conoha_mariadb']` を .env 経由で上書きしてから実行）
  5. `python manage.py runserver 0.0.0.0:8000`（管理画面は `/admin/`）
- よく使うコマンド例:
  - 環境確認: `python --version`, `pip list | head`
  - DB 初期化: `python manage.py migrate`
  - 管理ユーザー作成: `python manage.py createsuperuser`
  - ローカル起動: `python manage.py runserver 0.0.0.0:8000`
  - 静的収集（本番用）: `python manage.py collectstatic`
  - 管理コマンド（一例）: `python manage.py wowma_stock_chk`, `python manage.py wowma_register_item`, `python manage.py wowma_order_chk`, `python manage.py qoo_order_chk`, `python manage.py upload_goods_info`, `python manage.py get_wowma_buyers_list`, `python manage.py get_buyma_buyers_list`, `python manage.py spapi_catalog_item`, `python manage.py spapi_ping`
  - カテゴリ同期: `python manage.py import_categories --source amazon|wowma --truncate`、マッチング `python manage.py match_categories --synonyms docs/category_mapping/synonyms.tsv --level1-map docs/category_mapping/level_1_cat.txt --outdir codex_out --auto-threshold 0.7 --review-threshold 0.4`

## 2. Parallel Workflows（並列作業）
- 役割分担: PM（要件/優先度）、FE（テンプレート/スタイル）、BE（Django ビュー・管理コマンド・API連携）、DB（スキーマ/マイグレーション/接続切替）、Security（秘密情報/権限/監査）、QA（テスト計画/結果管理）。役割が重なる場合も担当者を明示。
- 衝突回避: 事前に担当領域を `yaget/` 内ファイル単位で宣言。マイグレーション/モデル変更は専任者を一人にし、同時に走らせない。テンプレートとビューの同時編集は PR を分ける。管理コマンド編集中はファイルロック的に担当を周知。
- ブランチ運用: 機能ごとに短命ブランチ（例: `feature/wowma-stock-fix`）。小さく積む。force push 禁止。リベースは自ブランチのみ。
- 成果物の受け渡し: 作業完了時に `codex_out/handoff.md`（ない場合は新規作成）へ概要・変更ファイル・動作確認コマンド・残課題を記載し、PR 説明にリンク。データサンプルやログは `.gitignore` 対象を尊重して別送。

## 3. Model & Strategy（モデルと戦略）
- 原則「重い推論・方針設計は AI、最終判断は人間」。要件→設計→実装の各段階で AI が案を出し、PM/該当担当が GO/NOGO を出す。
- 作業ループ: 調査（コード・設定・API 仕様）→仮説立案→小さな検証（ローカル/テスト環境）→修正→再検証→レビュー/ハンドオフ。
- AI に任せる: コード読み解き、設計ドラフト、テスト観点列挙、ログ解析の初期案作成、リファクタリング案。人間が判断: ビジネス上の優先順位、外部サービスの利用範囲、機微データの取り扱い、例外的な本番操作。
- 仮説の扱い: 不明点は「暫定」と明記し、検証結果で更新。API 変更など外部依存はソースとバージョンを記録。

## 4. Shared Project Rules（共通ルール）
- コーディング: PEP8 準拠、関数は短く。ログ/コメントは日本語可だが機微は書かない。外部キーやユニーク制約はモデルで明示。長大ファイルはセクションコメントで区切る。
- Secrets/設定: `.env` に集約（DB 認証、API キー、LWA/AWS 認証、メール設定等）。リポジトリには絶対コミットしない。`settings.py` の直書き値は順次外部化する。ログファイルパス（`/home/django/sample/log/...`）は環境ごとに上書きし、ローカルでは `log/` へフォールバックする。
- Git 運用: 既存変更は勝手に戻さない。`apply_patch` か最小差分を原則。コミットは粒度小さくメッセージ明快。`git reset --hard` や強制 push は不可。レビュー依頼時は変更理由と動作確認手順をセットで提示。
- 依存/環境: 変更時は `requirements.txt` を更新し、インストール手順も記載。Python 3.8+ を前提。仮想環境を必ず使用。
- ログ/セキュリティ: DEBUG は開発のみ。個人情報/トークンをログ・画面に出さない。外部 API のリクエスト/レスポンスはサニタイズして保存。公開鍵/証明書は `.gitignore` 済みの場所に置く。
- 生成物形式: 仕様/調査は Markdown（`codex_out/` 推奨）。コード変更は diff/patch で共有。大きなデータは添付せず場所のみ示す。

## 5. Session Management（セッション運用）
- 流れ: 着手時に Plan を共有→タスクを細分化（目安 30–90 分単位）→実装/調査→結果と次の一手を記録→最終 Edits/ハンドオフ。小さいタスクは Plan を省略してもよいが、2 ステップ以上なら明示。
- 分割基準: 新規機能は「データモデル」「ビュー/API」「テンプレート」「管理コマンド」「テスト」に分ける。外部 API を叩く作業はモック検証と本番検証を分ける。
- ロールバック: 作業前に `git status` でスナップショット把握。誤り時は自ブランチで `git restore <file>` または `git checkout -p` を使う。大規模誤りは `git stash` で退避し再度適用。DB 変更はマイグレーション番号で戻せるよう履歴を管理。
- 共有終了時: 変更点・確認手順・未解決事項を必ず記載し、必要ならスクリーンショット/ログの保存場所を示す。

## 6. Commands & Tooling（コマンドとツール統合）
- セットアップ:  
  - `python -m venv .venv && source .venv/bin/activate`  
  - `pip install -r requirements.txt`
- サーバー/DB:  
  - `python manage.py migrate`（DB 準備）  
  - `python manage.py runserver 0.0.0.0:8000`  
  - `python manage.py shell` で簡易デバッグ。必要に応じて `DJANGO_SETTINGS_MODULE` や DB 接続先を .env で上書き。
- 管理コマンド主要例（ログ設定 `.config` が隣接。多くが外部 API を叩くためテスト環境に注意）:  
  - Wowma 在庫/登録/受注: `wowma_stock_chk`, `wowma_register_item`, `wowma_order_chk`, `wowma_do_buyers_order`, `wowma_send_gmail`  
  - Qoo10 注文/ASIN: `qoo_order_chk`, `qoo_do_buyers_order`, `exec_get_qoo_asin_detail_upd_csv`  
  - バイヤーズ/ヤフオク取得: `get_buyma_buyers_list`, `get_wowma_buyers_list`, `get_wowma_buyers_list_1`, `get_ya_buyers_list`, `get_ya_src`  
  - 商品アップロード/削除: `upload_goods_info`, `delete_goods_info`  
  - SP-API 動作確認: `spapi_catalog_item`, `spapi_ping`  
  - 動作テスト用: `test_test`
- カテゴリ運用:  
  - BTG/Wowma 取り込み: `python manage.py import_categories --source amazon --truncate` / `--source wowma --truncate`（元データは `category/amazon/*.xls*`, `category/wowma/category.xlsx`）  
  - マッチング: `python manage.py match_categories --synonyms docs/category_mapping/synonyms.tsv --level1-map docs/category_mapping/level_1_cat.txt --outdir codex_out --auto-threshold 0.7 --review-threshold 0.4`（レビュー TSV を確認後、反映コマンドは別途追加予定）
- デプロイ（VPS）:  
  - `ssh django@133.167.75.151` → `source /home/django/djangoenv/bin/activate` → `cd /home/django/sample` → `git pull`  
  - 反映: `pkill -HUP gunicorn`、`sudo systemctl restart nginx`、`sudo systemctl restart gunicorn`、必要なら `gunicorn --bind 127.0.0.1:8000 sample.wsgi -D`
- デバッグ/計測:  
  - ログ: `sample/logging` 設定を活用。必要に応じて `.config` を渡して `logging.config.fileConfig` で出力先を切り替える。  
  - クエリ確認: Django Debug Toolbar は未導入。必要ならローカルのみ導入してもよい。  
  - パフォーマンス簡易チェック: `python -m cProfile -m manage runserver` などでホットスポット確認。  
  - Lint/Format: 未設定。導入する場合は `ruff`/`black` を提案し、設定ファイル追加前に合意を取る。
- テスト: 既存の自動テストは実質なし。新規実装時は `unittest` か `pytest` を追加し、`python -m pytest` を標準化する方針を推奨（導入時は requirements 追記）。管理コマンドはモックで外部 API を止める。

## 7. 継続改善（改善ループ）
- 新しい学び/手順は `codex_out/` に日付付き Markdown で追記し、必要に応じて本 CODEX.md を更新。重大な運用変更（DB/認証/外部 API）は必ず即日反映。
- FAQ/便利コマンドは章 6 に追記。テンプレートや再利用スクリプトは `templates/` もしくは `scripts/` ディレクトリを新設して集約。
- チケット駆動: チケット（例: `EC-xxxxx.md`）を `codex_out/` に置き、背景・完了条件・確認手順を明記。作業後はチケット内に結果リンクと次アクションを記録。

## 8. すぐ使える指示テンプレ集（最重要）
- バグ調査依頼:  
  - 「症状: …、再現手順: …、期待結果: …、発生環境 (.env 以外): …、関連ログ/スクショの場所: …。`<branch>` で再現調査し、原因候補と修正案を列挙して」
- UI 改善依頼:  
  - 「対象画面: `templates/yaget/<file>.html`、目的: …（例: 入力エラー可視化）、制約: 色/フォント/ブランド指針…。改善案 2-3 件とワイヤフレーム（テキストで可）、実装 diff と確認手順を提示して」
- 性能改善依頼:  
  - 「対象処理: `yaget/views.py` の `<function>`、現状指標: …（例: 3s/リクエスト）、計測方法: …。ボトルネック仮説→測定→改善案→結果比較（数値）→副作用をレポートして」
- セキュリティ点検依頼:  
  - 「対象: 認証/外部 API 呼び出し/ログ出力。`.env` に依存する値は伏せたまま。リスク一覧（重大度付き）と修正優先度、`settings.py`/`views.py` の該当行を引用して提案して」
- DB 整合性点検依頼:  
  - 「対象モデル: `<ModelName>`。期待制約: …。現行データの確認クエリ、検出した不整合、修正手順（マイグレーション/SQL/管理コマンド）を提示して。変更前後のレコード数も記録」
