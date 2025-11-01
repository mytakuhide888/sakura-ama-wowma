# 02 Django Settings Summary

`sample/settings.py` を中心に、主要設定を要約します（機微情報はマスク）。

## INSTALLED_APPS

- `sample/settings.py:21`
```
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'helloworld',
    'yaget',
]
```

## MIDDLEWARE

- `sample/settings.py:33`
```
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## DATABASES

- `sample/settings.py:57`
```
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
  },
  'conoha_mariadb': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': '********',
    'USER': '********',
    'PASSWORD': '********',
    'HOST': '********',
    'PORT': '3306',
  }
}
```

補足
- 運用は MySQL 相当（ConoHa MariaDB）接続も想定。接続情報はコード直書きのため要外部化推奨。

## CACHES

- 未定義（Django 既定のローカルメモリキャッシュ想定）。

## LANGUAGE_CODE / TIME_ZONE

- `sample/settings.py:91`
```
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_TZ = True
```

## STATIC / MEDIA

- `sample/settings.py:106`
```
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static_collected'
STATICFILES_DIRS = [BASE_DIR / 'static']
```
- MEDIA 設定は未記述。

## LOGGING

- `sample/settings.py:114`
  - `RotatingFileHandler` によるファイル出力が定義
  - 出力先例: `/home/django/sample/log/debug.log`, `.../django_only_debug.log`, `.../django_debug.log`
  - `console` も DEBUG で有効

## セキュリティ関連

- `SECRET_KEY`: 直書き（マスク対象）。外部化推奨。
- `DEBUG = True`（運用時は False 推奨）
- `ALLOWED_HOSTS`: `boasolte.com` 等を含む（`sample/settings.py:18`）
- `CSRF_TRUSTED_ORIGINS`: `https://boasolte.com` など（`sample/settings.py:19`）
- `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`（`sample/settings.py:78`）

## .env / 環境変数

- `.env` ロード
  - `sample/wsgi.py:9` で `dotenv` のロードを試行（`.env` はリポジトリ直下未検出）

- SP-API / AWS / LWA 関連（コードから抽出。値は環境変数で取得）
  - `LWA_CLIENT_ID`（`yaget/AmaSPApi.py:607`）
  - `LWA_CLIENT_SECRET`（`yaget/AmaSPApi.py:608`）
  - `LWA_REFRESH_TOKEN`（`yaget/AmaSPApi.py:606`）
  - リージョン別: `US_LWA_*`, `JP_LWA_*`（`yaget/AmaSPApi.py:1504-1516`）
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SELLER_ID`（`yaget/AmaSPApi.py:104-106`）
  - リージョン別 AWS: `US_AWS_*`, `JP_AWS_*`（`yaget/AmaSPApi.py:1507-1516`）

- Wowma/au PAY マーケット関連
  - 現状は `wowma_access.py` に API キー/Shop ID が直書き（`wowma_access.py:54-60`）。
  - 推奨キー名（例）: `WOWMA_API_KEY`, `WOWMA_SHOP_ID`, `WOWMA_API_BASE`

機微情報は原則として `.env` 等に移し、`settings.py`/コードからは参照のみとする構成が望ましいです。

