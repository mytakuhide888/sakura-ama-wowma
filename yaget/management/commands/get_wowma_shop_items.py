# -*- coding: utf-8 -*-
"""
Wowmaショップの商品一覧を取得し、SP-API でAmazon ASINを検索してDBに保存する。

使い方:
  python manage.py get_wowma_shop_items --user-id 69303756
  python manage.py get_wowma_shop_items --user-id 69303756 --phase scrape
  python manage.py get_wowma_shop_items --user-id 69303756 --phase match
  python manage.py get_wowma_shop_items --user-id 69303756 --limit 50

フェーズ:
  scrape : Seleniumでショップ商品一覧取得 → og:titleで商品名取得 → DB保存
  match  : DBのPENDINGレコードをSP-APIでASIN検索 → DB更新
  all    : scrape → match を順に実行（デフォルト）
"""
import sys
import time
import logging
import traceback

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.conf import settings

import environ

from yaget.models import WowmaShopItem, LwaCredential

from sp_api.api import CatalogItems
from sp_api.base.marketplaces import Marketplaces
from sp_api.base import SellingApiException

logger = logging.getLogger(__name__)

WOWMA_BASE_URL  = 'https://wowma.jp'
CATALOG_API_URL = f'{WOWMA_BASE_URL}/catalog/api/search/items'
ITEM_DETAIL_URL = f'{WOWMA_BASE_URL}/item/{{item_id}}'
SHOP_LIST_URL   = f'{WOWMA_BASE_URL}/user/{{user_id}}/list'

SCRAPE_INTERVAL = 1.5   # ページ取得間隔（秒）
SPAPI_INTERVAL  = 0.6   # SP-APIコール間隔（秒・クォータ2req/秒）
IPP             = 40    # 1ページあたりの商品数


class Command(BaseCommand):
    help = 'Wowmaショップ商品一覧取得 → SP-APIでASIN検索 → DB保存'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', required=True, help='WowmaショップのユーザーID（例: 69303756）')
        parser.add_argument(
            '--phase', choices=['scrape', 'match', 'all'], default='all',
            help='実行フェーズ（scrape/match/all）'
        )
        parser.add_argument('--limit', type=int, default=0, help='scrapeフェーズで取得する商品数の上限（0=無制限）')

    # ------------------------------------------------------------------
    # エントリポイント
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        user_id = options['user_id']
        phase   = options['phase']
        limit   = options['limit']

        self.stdout.write(f'=== get_wowma_shop_items 開始 user_id={user_id} phase={phase} ===')

        if phase in ('scrape', 'all'):
            self._phase_scrape(user_id, limit)

        if phase in ('match', 'all'):
            self._phase_match(user_id)

        self.stdout.write(self.style.SUCCESS('=== 完了 ==='))

    # ------------------------------------------------------------------
    # Phase 1: Wowma商品一覧取得
    # ------------------------------------------------------------------
    def _phase_scrape(self, user_id, limit):
        self.stdout.write('[Phase 1] Wowmaショップ商品一覧取得開始')
        driver = None
        try:
            driver = self._init_selenium()
            shop_url = SHOP_LIST_URL.format(user_id=user_id)
            self.stdout.write(f'  ショップページ読み込み: {shop_url}')
            driver.get(shop_url)
            time.sleep(4)  # SPA初期レンダリング待ち

            # ブラウザ内JSでカタログAPIを叩き、全ページの商品IDを収集
            item_ids = self._fetch_all_item_ids_via_js(driver, user_id, limit)
            self.stdout.write(f'  商品ID取得数: {len(item_ids)}')

            if not item_ids:
                self.stdout.write(self.style.WARNING('  商品が見つかりませんでした'))
                return

            # 各商品の詳細ページから商品名を取得してDB保存
            saved = 0
            for i, item_id in enumerate(item_ids, 1):
                try:
                    item_name = self._get_item_name(item_id)
                    if not item_name:
                        self.stdout.write(f'  [{i}/{len(item_ids)}] {item_id}: 商品名取得失敗、スキップ')
                        continue

                    obj, created = WowmaShopItem.objects.update_or_create(
                        wow_item_id=str(item_id),
                        defaults={
                            'shop_user_id': user_id,
                            'item_name':    item_name,
                            'item_url':     ITEM_DETAIL_URL.format(item_id=item_id),
                        }
                    )
                    action = '新規' if created else '更新'
                    self.stdout.write(f'  [{i}/{len(item_ids)}] {item_id}: {item_name[:40]}... → {action}')
                    saved += 1
                    time.sleep(SCRAPE_INTERVAL)
                except Exception as e:
                    self.stdout.write(f'  [{i}/{len(item_ids)}] {item_id}: エラー {e}')
                    logger.debug(traceback.format_exc())

            self.stdout.write(f'[Phase 1] 完了: {saved}/{len(item_ids)} 件保存')

        except Exception as e:
            logger.debug(traceback.format_exc())
            self.stderr.write(f'[Phase 1] エラー: {e}')
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _fetch_all_item_ids_via_js(self, driver, user_id, limit):
        """Seleniumブラウザ内でfetch()を実行してカタログAPIから商品IDを収集"""
        item_ids = []
        page = 1

        while True:
            script = f"""
var callback = arguments[arguments.length - 1];
fetch('/catalog/api/search/items?user={user_id}&ipp={IPP}&page={page}&uads=0&acc_filter=N', {{
    headers: {{'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}}
}})
.then(function(r) {{ return r.json(); }})
.then(function(data) {{ callback(data); }})
.catch(function(e) {{ callback({{error: e.toString()}}); }});
"""
            try:
                data = driver.execute_async_script(script)
            except Exception as e:
                self.stdout.write(f'  JS実行エラー page={page}: {e}')
                break

            if not data or data.get('error'):
                self.stdout.write(f'  APIエラー page={page}: {data}')
                break

            pg_info = data.get('pageInformation', {})
            total_pages = pg_info.get('totalPages', 0)
            total_count = pg_info.get('totalCount', 0)
            hit_items   = data.get('hitItems', [])

            self.stdout.write(f'  page={page}/{total_pages} totalCount={total_count} hitItems={len(hit_items)}')

            if not hit_items:
                # ブラウザ内JSでも取得できない場合はDOM fallback
                if page == 1:
                    self.stdout.write('  APIから商品が取れません。DOM scraping に切り替えます')
                    return self._fetch_item_ids_from_dom(driver, user_id, limit)
                break

            for item in hit_items:
                lot_no = item.get('lotNo')
                if lot_no:
                    item_ids.append(str(lot_no))

            if limit and len(item_ids) >= limit:
                item_ids = item_ids[:limit]
                break

            if page >= total_pages:
                break

            page += 1
            time.sleep(1)

        return item_ids

    def _fetch_item_ids_from_dom(self, driver, user_id, limit):
        """カタログAPIが失敗した場合のDOMスクレイピングによるフォールバック"""
        import re
        item_ids = []
        page = 1

        while True:
            url = f'{WOWMA_BASE_URL}/user/{user_id}/list?page={page}'
            driver.get(url)
            time.sleep(4)

            html = driver.page_source
            # /item/数字 のリンクを抽出
            found = list(dict.fromkeys(re.findall(r'/item/(\d+)', html)))
            self.stdout.write(f'  DOM page={page}: {len(found)} 件')

            if not found:
                break

            item_ids.extend(found)

            if limit and len(item_ids) >= limit:
                item_ids = item_ids[:limit]
                break

            # 次のページボタンの確認
            try:
                next_btn = driver.find_element('css selector', 'a[aria-label="次のページ"], .pagination-next a, [data-page="next"]')
                if next_btn:
                    page += 1
                    time.sleep(1)
                else:
                    break
            except Exception:
                break

        return list(dict.fromkeys(item_ids))

    def _get_item_name(self, item_id):
        """商品詳細ページのog:titleから商品名を取得（SSR確認済み）"""
        url = ITEM_DETAIL_URL.format(item_id=item_id)
        try:
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            og = soup.find('meta', property='og:title')
            if not og:
                return None
            raw = og.get('content', '')
            # "商品名｜au PAY マーケット" → 商品名だけを抽出
            name = raw.split('｜')[0].strip()
            return name or None
        except Exception as e:
            logger.debug(f'_get_item_name error item_id={item_id}: {e}')
            return None

    # ------------------------------------------------------------------
    # Phase 2: SP-APIでASIN検索
    # ------------------------------------------------------------------
    def _phase_match(self, user_id):
        self.stdout.write('[Phase 2] SP-API ASIN検索開始')

        sp_client = self._build_spapi_client()
        if not sp_client:
            self.stderr.write('[Phase 2] SP-APIクライアント初期化失敗')
            return

        targets = WowmaShopItem.objects.filter(
            shop_user_id=user_id,
            status=WowmaShopItem.STATUS_PENDING,
        ).order_by('id')

        self.stdout.write(f'  対象: {targets.count()} 件')
        matched = not_found = error = 0

        for i, item in enumerate(targets, 1):
            try:
                asin, asin_name = self._search_asin(sp_client, item.item_name)

                if asin:
                    item.asin      = asin
                    item.asin_name = asin_name
                    item.status    = WowmaShopItem.STATUS_MATCHED
                    self.stdout.write(f'  [{i}] HIT  {item.wow_item_id}: {item.item_name[:30]}... → {asin}')
                    matched += 1
                else:
                    item.status = WowmaShopItem.STATUS_NOT_FOUND
                    self.stdout.write(f'  [{i}] MISS {item.wow_item_id}: {item.item_name[:30]}...')
                    not_found += 1

                item.save()
                time.sleep(SPAPI_INTERVAL)

            except SellingApiException as e:
                item.status = WowmaShopItem.STATUS_ERROR
                item.save()
                self.stdout.write(f'  [{i}] ERR  {item.wow_item_id}: SP-API {e.code} {e.status_code}')
                error += 1
                time.sleep(2)
            except Exception as e:
                item.status = WowmaShopItem.STATUS_ERROR
                item.save()
                self.stdout.write(f'  [{i}] ERR  {item.wow_item_id}: {e}')
                logger.debug(traceback.format_exc())
                error += 1

        self.stdout.write(
            f'[Phase 2] 完了: matched={matched} not_found={not_found} error={error}'
        )

    def _search_asin(self, client, item_name):
        """商品名でSP-API Catalog Items を検索してASINを返す"""
        # 商品名が長すぎる場合は先頭50文字に絞る
        keyword = item_name[:50].strip()
        marketplace_id = 'A1VC38T7YXB528'  # Amazon.co.jp

        try:
            res = client.search_catalog_items(
                keywords=[keyword],
                marketplaceIds=[marketplace_id],
                includedData=['summaries', 'identifiers'],
            )
        except TypeError:
            # 旧バージョンのライブラリ対応
            res = client.search_catalog_items(
                keywords=[keyword],
                marketplaceIds=[marketplace_id],
            )

        payload = getattr(res, 'payload', {}) or {}
        # レスポンス構造の正規化
        if isinstance(payload, dict) and 'payload' in payload:
            payload = payload['payload']

        items = payload.get('items') or []
        if not items:
            return None, None

        # 最初の1件を採用
        first = items[0]
        asin = first.get('asin')
        summaries = first.get('summaries') or []
        asin_name = summaries[0].get('itemName') if summaries else None

        return asin, asin_name

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------
    def _init_selenium(self):
        """ヘッドレスChromeを初期化して返す"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,1024')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        try:
            # VPS環境: system chromedriver を優先
            from selenium.webdriver.chrome.service import Service
            driver = webdriver.Chrome(service=Service('/usr/bin/chromedriver'), options=options)
        except Exception:
            # フォールバック: ChromeDriverManager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=options
                )
            except Exception as e:
                raise RuntimeError(f'ChromeDriver初期化失敗: {e}')

        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        return driver

    def _build_spapi_client(self):
        """SP-APIクライアントを構築して返す"""
        env = environ.Env()
        try:
            env.read_env(str(getattr(settings, 'BASE_DIR', '.')) + '/.env')
        except Exception:
            pass

        refresh_token = (
            LwaCredential.objects.values_list('refresh_token', flat=True).first()
            or env('SP_API_REFRESH_TOKEN', default=None)
            or env('LWA_REFRESH_TOKEN', default=None)
        )
        lwa_app_id      = env('LWA_CLIENT_ID', default=None) or env('LWA_APP_ID', default=None)
        lwa_client_secret = env('LWA_CLIENT_SECRET', default=None)
        aws_access_key  = env('AWS_ACCESS_KEY_ID', default=None)
        aws_secret_key  = env('AWS_SECRET_ACCESS_KEY', default=None)
        role_arn        = env('ROLE_ARN', default=None) or env('SP_API_ROLE_ARN', default=None)

        if not refresh_token or not lwa_app_id or not lwa_client_secret:
            self.stderr.write('SP-API LWA認証情報が不足しています')
            return None
        if not role_arn and (not aws_access_key or not aws_secret_key):
            self.stderr.write('SP-API AWS認証情報が不足しています')
            return None

        creds = {
            'refresh_token':    refresh_token,
            'lwa_app_id':       lwa_app_id,
            'lwa_client_secret': lwa_client_secret,
        }
        if role_arn:
            creds['role_arn'] = role_arn
        else:
            creds['aws_access_key'] = aws_access_key
            creds['aws_secret_key'] = aws_secret_key

        return CatalogItems(credentials=creds, marketplace=Marketplaces.JP)
