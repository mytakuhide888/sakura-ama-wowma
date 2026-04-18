# VPS・サーバー運用

<!-- このファイルは .gitignore 対象 - git に push しないこと -->

## SSH接続

```
ホスト: 133.167.75.151
ユーザー: django
PW: _Kuurie778
```

## 本番パス

| 項目 | パス |
|------|------|
| アプリ | `/home/django/sample` |
| venv | `/home/django/djangoenv/` |
| ログ | `/home/django/sample/yaget/log` |
| .env | `/home/django/sample/.env` |

## よく使うコマンド

### 定番の前置き（venv有効化）

```bash
source /home/django/djangoenv/bin/activate && cd /home/django/sample
```

### サービス操作

```bash
sudo systemctl status sample.socket
sudo systemctl status sample.service
sudo systemctl restart gunicorn

# gunicorn 直接起動
cd /home/django/sample/
gunicorn --bind 127.0.0.1:8000 sample.wsgi -D
```

### DB更新（マイグレーション）

```bash
source /home/django/djangoenv/bin/activate
cd /home/django/sample
python manage.py makemigrations yaget
python manage.py migrate
```

### match_categories 実行

```bash
source /home/django/djangoenv/bin/activate
cd /home/django/sample
git pull
python manage.py match_categories \
  --synonyms docs/category_mapping/synonyms.tsv \
  --level1-map docs/category_mapping/level_1_cat.txt \
  --level2-map docs/category_mapping/level_2_cat.txt \
  --outdir codex_out \
  --auto-threshold 0.595 --review-threshold 0.35
```

## デプロイフロー

```
1. ローカルで編集・コミット
2. GitHub に push
3. VPS で git pull
4. 必要に応じて makemigrations / migrate
5. gunicorn 再起動（コード変更時）
```

## サービスURL

- 本番: http://boasolte.com/yaget/top/

## ローカル環境の制約

- ローカルWSLにはDjango環境なし（python3はあるがDjangoモジュール未インストール）
- `makemigrations` / `migrate` は VPS でのみ実行可能
- 構文チェックは `python3 -c "import ast; ast.parse(open('file.py').read())"` で代用可能
