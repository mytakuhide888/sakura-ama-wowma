from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import generic
from django.urls import reverse_lazy
from django.contrib import messages
from django.forms import modelformset_factory

#from google import spreadsheet
import gspread
import subprocess
import io,sys
import os
import environ

import urllib



from urllib.parse import urlencode


import secrets
import requests
import datetime
import re

from io import TextIOWrapper, StringIO
from datetime import datetime as dt
import time
from django.utils import timezone
from oauth2client.service_account import ServiceAccountCredentials

# Create your views here.
from .models import (
    Friend, Message, YaItemList, YaItemDetail, YaListUrl,
    YaBuyersItemDetail, BatchStatus,AllOrderInfo, QooOrderInfo, WowmaOrderInfo,
    ErrorGoodsLog,YaBuyersItemBlackList, QooShopInfo, WowmaShopInfo, WowmaOrderDetail,
    WowmaBuyersOrderDetail,QooBuyersOrderDetail,QooAsinDetail,WowCategory
)
from .forms import FriendForm, MessageForm, YaItemListForm, YaSetListToSheet, KickYagetForm
from .forms import FindForm, UpdByersCtListForm, YaBuyersItemDetailSearchForm, YaImpSpapiUpdCsvForm
from .forms import BuyersGoodsDetailImportForm, BuyersGoodsDetailSmallImportForm, BuyersGoodsDeleteForm
from .forms import BatchStatusSearchForm, AllOrderInfoForm, ErrorGoodsLogSearchForm
from .forms import BlackListForm, QooShopInfoForm, WowShopInfoForm, QooOrderInfoForm, WowOrderInfoForm
from .forms import QooAsinUpdCsvForm, QooAsinDetailSearchForm, QooAsinUpdAsinForm, WowCategoryForm, WowCategoryModelForm


import xml.etree.ElementTree as ET
import xml.dom.minidom as md

from django.db.models import Q
from django.db.models import Count, Sum, Avg, Min, Max
from django.db.models import OuterRef, Subquery, IntegerField

from .forms import CheckForm
from .modules import GSpreadModule, TestMsgModule, ExecQoo10, ExecWowma
from .qoo10_access import Qoo10Access
from wowma_access import WowmaAccess, WowmaAccessExec

from buyers_info import BuyersInfo, BuyersBrandInfo
from .apps import YagetConfig
from django.core.paginator import Paginator
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse

import logging
import logging.config
import traceback

# ログ設定
# ※バッチを呼び出せない場合などは、こちらをONにする。しかしこちらがONのままだと、バッチのstdoutとかぶってるのか
# ログがこっちにしかはき出されなくなるので、片方だけにしよう。
# logging
#logging.basicConfig(filename='/home/django/sample/yaget/management/commands/log/yashop_amamws.log', level=logging.DEBUG)
#logging.config.fileConfig(fname="/home/django/sample/yaget/log/yaget_logging.config", disable_existing_loggers=False)

#logger = logging.getLogger(__name__)

# --- logger 設定 -----------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logger.setLevel(20)

# ログローテ設定

rh = logging.handlers.RotatingFileHandler(
    r'/home/django/sample/yaget/log/yaget_views.log',
    encoding='utf-8',
    maxBytes=1000000,
    backupCount=3
)
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
rh.setFormatter(fh_formatter)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
ch.setFormatter(ch_formatter)

logger.addHandler(rh)
logger.addHandler(ch)
# --- logger 設定 -----------------------------------------





# アップロードしたファイルを保存するディレクトリ
#env = environ.Env()
#env.read_env('.env')

#UPLOAD_DIR = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
UPLOAD_DIR = '/home/django/sample/yaget/yabuyers/dwcsv/'
myupdcsv_dir = "/home/django/sample/yaget/wowma_buyers/updcsv/"
mydeletecsv_dir = "/home/django/sample/yaget/wowma_buyers/deletecsv/"

#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# SP-API LWA OAuth start
def spapi_oauth_start(request):
    logger.info('spapi_oauth_start: begin')
    client_id = os.environ.get('LWA_APP_ID') or os.environ.get('LWA_CLIENT_ID')
    if not client_id:
        logger.error('LWA client id not configured (LWA_APP_ID/LWA_CLIENT_ID)')
        return HttpResponse('LWA client id not configured', status=500)

    try:
        callback_url = request.build_absolute_uri(reverse('yaget:spapi_oauth_callback'))
    except Exception:
        callback_url = request.build_absolute_uri('/spapi/oauth/callback/')

    scope = os.environ.get('SP_API_LWA_SCOPE') or 'sellingpartnerapi::migration'
    state = secrets.token_urlsafe(16)
    request.session['spapi_oauth_state'] = state

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': callback_url,
        'scope': scope,
        'state': state,
    }
    auth_url = 'https://www.amazon.com/ap/oa?' + urlencode(params)
    logger.info('spapi_oauth_start: redirect to LWA authorize')
    return redirect(auth_url)


# SP-API LWA OAuth callback
def spapi_oauth_callback(request):
    logger.info('spapi_oauth_callback: begin')
    err = request.GET.get('error')
    if err:
        logger.error(f'spapi_oauth_callback error: {err}')
        return HttpResponse(f'Authorization error: {err}', status=400)

    state = request.GET.get('state')
    code = request.GET.get('code')
    sess_state = request.session.get('spapi_oauth_state')
    if not state or not sess_state or state != sess_state:
        logger.error('spapi_oauth_callback: state mismatch')
        return HttpResponse('Invalid state', status=400)
    if not code:
        logger.error('spapi_oauth_callback: code missing')
        return HttpResponse('Authorization code missing', status=400)

    client_id = os.environ.get('LWA_APP_ID') or os.environ.get('LWA_CLIENT_ID')
    client_secret = os.environ.get('LWA_CLIENT_SECRET')
    if not client_id or not client_secret:
        logger.error('LWA client credentials not configured')
        return HttpResponse('LWA client credentials not configured', status=500)

    try:
        callback_url = request.build_absolute_uri(reverse('yaget:spapi_oauth_callback'))
    except Exception:
        callback_url = request.build_absolute_uri('/spapi/oauth/callback/')

    token_url = 'https://api.amazon.com/auth/o2/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': callback_url,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=15)
        resp.raise_for_status()
        body = resp.json()
    except Exception as e:
        logger.exception('spapi_oauth_callback: token exchange failed')
        return HttpResponse(f'Token exchange failed: {e}', status=502)

    refresh_token = body.get('refresh_token')
    access_token = body.get('access_token')
    expires_in = body.get('expires_in')
    if not refresh_token:
        logger.error(f'spapi_oauth_callback: no refresh_token in response: {body}')
        return HttpResponse('No refresh_token in response', status=502)

    request.session['spapi_refresh_token'] = refresh_token
    try:
        tail = refresh_token[-6:] if isinstance(refresh_token, str) else '******'
    except Exception:
        tail = '******'
    logger.info(f'spapi_oauth_callback: success, refresh_token=***{tail}, expires_in={expires_in}')

    messages.success(request, 'SP-API の認可が完了しました。refresh_token はセッションに保存しました。恒久保存は別途実装してください。')
    return HttpResponse('OK: SP-API OAuth completed. refresh_token stored in session.', status=200)


# Ajaxテスト
def ajax_test(request):
    # ajax test
    title = request.POST.get('title')
    msg = 'ajax_test'
    params = {
        'title': 'ajax test start',
        'message': msg,
    }
    return render(request, 'yaget/ajax_test.html', params)

# Ajaxテスト
def buyers_goods_detail_ajax_res(request):
    model = YaBuyersItemDetail
    logger.debug("--- buyers_goods_detail_ajax_res in")
    pk = request.POST.get('pk')
    if pk:
        goods = model.objects.get(pk=pk)
    else:
        d = {
            'gid': None,
            'gname': None,
            'msg': None,
            'ret_code': None,
        }
        return JsonResponse(d)

    # Qoo10にアクセス
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10の商品情報を検索
    #ret_code = qoo10obj.qoo10_items_lookup_get_all_goods_info('S0','1')
    #ret_code = qoo10obj.qoo10_items_lookup_get_all_goods_info('S1','1')
    ret_code = qoo10obj.qoo10_items_lookup_get_all_goods_info('S2','1')
    #ret_code = qoo10obj.qoo10_items_lookup_get_all_goods_info('S4','1')

    d = {
        'gid': goods.gid,
        'gname': goods.gname,
        'msg': msg,
        'ret_code': ret_code,
    }

    return JsonResponse(d)

def get_csv_writer(response, csvfilename):
    filename = urllib.parse.quote(csvfilename.encode("utf8"))
    #response = HttpResponse(content_type='text/csv; charset=UTF-8')
    #response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
    #response = HttpResponse(content_type='text/plain; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(filename)
    #response['Content-Disposition'] = 'attachment; filename{urllib.parse.quote(filename)}'
    #response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(filename)

    #mywriter = csv.writer(response, lineterminator='\n')
    mywriter = UnicodeCsvWriter(response, lineterminator='\n')
    #mywriter.encoding = 'cp932'
    return mywriter


class UnicodeCsvWriter:

    def __init__(self, myobj, dialect='excel', encoding='utf-8', *args, **kwds):
        #self.writer = csv.writer(myobj, dialect, *args, **kwds)
        self.writer = csv.writer(myobj, dialect, *args, **kwds)
        self.dialect = dialect
        self.encoding = encoding


    def writerow(self, seq):
        row_seq = []
        for elem in seq:
          if isinstance(elem, str):
            #row_seq.append(elem.encode(self.encoding))
            row_seq.append(elem)
          else:
            row_seq.append(elem)
        self.writer.writerow(row_seq)


    def writerows(self, seq_of_seq):
        for seq in seq_of_seq:
          self.writerow(seq)


# qoo10 から商品情報の取得
def qoo_goods_detail_info_ajax(request):
    model = YaBuyersItemDetail
    logger.debug("--- qoo_goods_detail_info_ajax in")
    pk = request.POST.get('pk')
    if pk:
        logger.debug(" pk ok.[{}]".format(pk))
        goods = model.objects.get(pk=pk)
    else:
        logger.debug(" pk ng")
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # Qoo10にアクセス
    qoo10obj = Qoo10Access(logger)
    msg = 'qoo商品情報：'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10の商品情報を検索
    # Qoo10に登録済みであれば　goods.qoo_gdno　に値が入っている(もしくはqoo_seller_codeだけの場合も)
    if goods.qoo_gdno or goods.qoo_seller_code:
        # 更新
        ret_obj_list = qoo10obj.qoo10_items_lookup_get_item_detail_info(goods)
        chk_flg = 0
        for ret_obj in ret_obj_list:
            if ret_obj['res_code'] != "0":
                logger.debug("--- qoo_goods_detail_info_ajax qoo10 商品情報の取得でエラー [{}][{}]".format(ret_obj['res_code'],
                                                                                          ret_obj['res_msg']))
                chk_flg = 1  # なにかエラーになってた
                break
        if chk_flg == 0:
            # 取得成功
            msg += '[ok][{}][{}]'.format(ret_obj['res_msg'],ret_obj['res_obj'])
            logger.debug("--- qoo_goods_detail_info_ajax qoo10 商品情報の取得ok [{}][{}]".format(ret_obj['res_code'],
                                                                                            ret_obj['res_msg']))
        else:
            # 取得失敗
            msg += '[ng]['
            msg += str(ret_obj['res_msg']) + ']'

    else:
        # 呼び出し失敗
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    msg += ret_obj['res_msg']
    d = {
        'msg': msg,
        'ret_code': ret_obj['res_code'],
    }

    return JsonResponse(d)


# qoo10 商品登録・更新
def qoo_goods_upsert_ajax(request):
    model = YaBuyersItemDetail
    logger.debug("--- qoo_goods_u"
                 "psert_ajax in")
    pk = request.POST.get('pk')
    if pk:
        goods = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # Qoo10にアクセス
    #qoo10obj = Qoo10Access(logger)
    #msg = 'start[' + YagetConfig.verbose_name + ']'
    #qoo10obj.qoo10_create_cert_key()

    msg = ''
    status = False
    qoo10obj = ExecQoo10(logger)

    try:
        # Qoo10の商品情報を検索
        # Qoo10に登録済みであれば　goods.qoo_gdno　に値が入っている
        status, msg = qoo10obj.exec_qoo10_goods_update(goods)
        """
        if goods.qoo_gdno:
            # 更新
            qoo10obj.qoo10_items_basic_update_goods(goods)
            # 更新に成功している。続けて更新時のみ、商品詳細を更新
            qoo10obj.qoo10_items_contents_edit_goods_contents(goods)
            # 更新に成功している。続けてステータスを更新
            qoo10obj.qoo10_items_basic_edit_goods_status(goods)
            # 更新成功している。続けてマルチ画像を更新
            qoo10obj.qoo10_items_contents_edit_goods_multi_image(goods)
            # 最後に在庫数を更新
            qoo10obj.qoo10_items_order_set_goods_price_qty(goods)
        else:
            # 新規登録
            qoo10obj.qoo10_items_basic_set_new_goods(goods)
            # 更新に成功している。続けてステータスを更新
            qoo10obj.qoo10_items_basic_edit_goods_status(goods)
            # 更新成功している。続けてマルチ画像を更新
            qoo10obj.qoo10_items_contents_edit_goods_multi_image(goods)
            # 最後に在庫数を更新
            qoo10obj.qoo10_items_order_set_goods_price_qty(goods)
        """
    except:
        # 更新時にエラー？
        logger.debug(
            '--> error. qoo_goods_upsert_ajax 1 gid:[{}] msg[{}] '.format(
                goods.gid, traceback.format_exc()))
        msg += traceback.format_exc()

    d = {
        'gid': goods.gid,
        'gname': goods.gname,
        'msg': msg,
        #'ret_code': 1,
        'ret_code': status,
    }

    return JsonResponse(d)

# wowma 商品登録・更新
def wow_goods_upsert_ajax(request):
    model = YaBuyersItemDetail
    logger.debug("--- wow_goods_upsert_ajax in")
    pk = request.POST.get('pk')
    taglist_upd_flg = request.POST.get('taglist_upd_flg')
    if not taglist_upd_flg:
        taglist_upd_flg = 0
    if pk:
        goods = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    msg = ''
    status = False
    wowma_obj = ExecWowma(logger)

    try:
        # wowmaの商品情報を検索
        status, msg = wowma_obj.exec_wowma_goods_update(goods, taglist_upd_flg)
    except:
        # 更新時にエラー？
        logger.debug(
            '--> error. wow_goods_upsert_ajax 1 gid:[{}] msg[{}] '.format(
                goods.gid, traceback.format_exc()))
        msg += traceback.format_exc()

    d = {
        'gid': goods.gid,
        'gname': goods.gname,
        'msg': msg,
        'ret_code': status,
    }

    return JsonResponse(d)


def ajax_test_add(request):
    # ajax test
    title = request.POST.get('title')
    #post = Post.objects.create(title=title)
    post = str(title) + '_test_received'
    d = {
        'title': post,
        #'title': post.title,
    }
    return JsonResponse(d)


# Qoo10 接続テスト
def qoo10_cert_test(request):
    # Qoo10のアクセサを初期化して呼び出してみる
    qoo10obj = Qoo10Access(logger)
    #msg = ' call qoo10_cert_test start..'
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()
    params = {
        'title': 'qoo10 certification test',
        'message': msg,
    }

    return render(request, 'yaget/qoo10_cert_test.html', params)


# 在庫チェック
def stock_chk(request):
    # サブプロセスでyagetのコマンドをキックする
    if (request.method == 'POST'):
        msg = ' start stock check.. <br>'
        # ここでサププロセスをキック
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_stock_chk 123"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)
    else:
        msg = ' call stock_chk ..'
    params = {
        'title': '在庫チェック開始します',
        'message': msg,
    }

    return render(request, 'yaget/stock_chk.html', params)


def top(request):
    return render(request, 'yaget/top.html')

"""
--- google spread sheet ---
参考：https://a-zumi.net/python-google-spreadsheet-api/
使い方
if __name__ == '__main__':
  worksheet = WorkSheet("spreadsheetId")

  # A列からC列までの値を取得
  print(worksheet.get_values('A:C'))

  # E1とG1に値を挿入
  worksheet.update('E1:G1', {'values': [1,2]})

"""
"""
class WorkSheet(object):

  spreadsheetId = ''

  def __init__(self, spreadsheetId):
    self.spreadsheetId = spreadsheetId

  def get(self, range):
    result = spreadsheet().spreadsheets().values().get(
        spreadsheetId=self.spreadsheetId, range=range
    ).execute()
    return result.get('values', [])

  def update(self, range, body):
    spreadsheet().spreadsheets().values().update(
        spreadsheetId=self.spreadsheetId, range=range,
        valueInputOption="USER_ENTERED", body=body
    ).execute()
"""


class GSpread(object):
    scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

    def __init__(self, mykeyfilename = None):
        if mykeyfilename is not None:
            self.keyfilename = mykeyfilename
        else:
            self.keyfilename = '/home/django/sample/yaget/test-app-flex-1-542896fdd03c.json'

    def get_gsheet(self, gsheetname):
        # シートをopenして返却する。とりあえずシートは sheet1 で固定
        if gsheetname is None:
            return None
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.keyfilename, self.scope)
        gc = gspread.authorize(credentials)
        wks = gc.open(gsheetname).sheet1
        return wks


# --- 以下はsampleから抜粋
def check(request):
    params = {
        'title': 'Hello',
        'message':'check validation.',
        'form': FriendForm(),
    }
    if (request.method == 'POST'):
        obj = Friend()
        form = FriendForm(request.POST, instance=obj)
        params['form'] = form
        if (form.is_valid()):
            params['message'] = 'OK!'
        else:
            params['message'] = 'no good.'
    return render(request, 'hello/check.html', params)


def index(request, num=1):

    data = YaItemList.objects.all()
    page = Paginator(data, 3)
    params = {
            'title': 'Hello ya_item_list',
            'message':'',
            'data': page.get_page(num),
        }
    return render(request, 'yaget/index.html', params)
"""
    data = Friend.objects.all()
    page = Paginator(data, 3)
    params = {
            'title': 'Hello',
            'message':'',
            'data': page.get_page(num),
        }
    return render(request, 'hello/index.html', params)
"""


def test_mail(request, num=1):

    data = YaItemList.objects.all()

    page = Paginator(data, 3)
    params = {
            'title': 'テストメール　配信できるか',
            'message':'テストメール　配信できるかな',
            'data': page.get_page(num),
        }
    return render(request, 'yaget/test_mail.html', params)


# send_mail
def send_my_mail(request, num=1):
    data = YaItemList.objects.all()
    page = Paginator(data, 3)
    params = {
        'title': 'メール送りました',
        'message': 'メール送りましたよ',
        'data': page.get_page(num),
    }
    if (request.method == 'POST'):
        if 'button_1' in request.POST:
            params = {
                'title': 'メール送りました',
                'message': 'おくります' + request.POST['button_1'],
                'data': page.get_page(num),
            }
            return render(request, 'yaget/test_mail.html', params)
    else:
        params = {
            'title': 'メール送ります',
            'message': 'メール送りますよ',
            'data': page.get_page(num),
        }
        return render(request, 'yaget/test_mail.html', params)


def showdetail(request, num=1):
    """ 詳細の登録済みレコードを一覧で返す """
    data = YaItemDetail.objects.all()
    page = Paginator(data, 3)
    params = {
            'title': 'Hello ya_item_detail !',
            'message':'',
            'data': page.get_page(num),
        }
    return render(request, 'yaget/showdetail.html', params)


def getdetail(request):
    return HttpResponse("Hello yaget getdetail!")


def getlist(request):
    mytestmsg = TestMsgModule()
    return HttpResponse(mytestmsg.get_message())


def read_s_sheet(request):
    mygs = GSpread()
    mygsobj = mygs.get_gsheet('test_trans_sheet')
    sample_value = mygsobj.acell('A4')
    return HttpResponse("Hello yaget read_s_sheet [" + str(sample_value))


def kick_yaget(request):
    # サブプロセスでyagetのコマンドをキックする
    if (request.method == 'POST'):
        yaurl = request.POST['YaUrl']
        form = KickYagetForm(request.POST)
        msg = ' be on kick [' + yaurl + ']'
        # ここでサププロセスをキック
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py get_ya_src "
        cmd += yaurl
        msg += ' cmd[' + cmd + ']'
        #cmd = "pwd"
        #p = subprocess.Popen(cmd)
        p = subprocess.Popen(cmd, shell=True)
        #msg += ' maybe ok.' + p.stdout.readline()
        msg += ' maybe ok.' + str(p.pid)
    else:
        yaurl = 'enter search url..'
        form = KickYagetForm()
        msg = ' call kick_yaget post..'
    params = {
        'title': 'Hello',
        'message': msg,
        'form': form,
    }

    return render(request, 'yaget/kick_yaget.html', params)


# アップロードされたファイルのハンドル
def handle_uploaded_file(f):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='cp932')
    path = os.path.join(UPLOAD_DIR, f.name)
    #with open(path, 'wb+', encoding='cp932') as destination:
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def upd_byers_ct_list_done(request):
    return render(request, 'yaget/upd_byers_ct_list_done.html')


def upd_byers_ct_list(request):
    try:
        # サブプロセスでbyersのコマンドをキックする
        if (request.method == 'POST'):

            yaurl = request.POST['YaUrl']
            #form = UpdByersCtListForm(request.POST, request.FILES)
            form = UpdByersCtListForm(request.POST)
            if form.is_valid():
                msg = ' be on kick upd_byers_ct_list'
                #handle_uploaded_file(request.FILES['file'])
                # ここでサププロセスをキック
                #cmd = "cd /home/django/sample/yaget/management/commands; source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py get_ya_buyers_list "
                cmd = "cd /home/django/sample/yaget/management/commands; source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py get_wowma_buyers_list "

                # 今は引数を見てない・・が仮に登録しておく
                cmd += "12345"
                msg += ' cmd[' + cmd + ']'
                # cmd = "pwd"
                ##p = subprocess.Popen(cmd)
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()

                # リアルタイムに取得　デバッグしたいときにONにすれば画面のmsgに標準出力を出せる

                #p = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                """
                while p.poll() is None:
                    #print('status:', p.poll(), p.stdout.readline().decode().strip())
                    #msg += 'status:' + str(p.poll()) + p.stdout.readline().decode().strip() + '<br />'
                    msg += p.stdout.readline().decode().strip() + '<br />'
                """

                msg += ' maybe ok.' + str(p.pid)
                # アップロード完了画面にリダイレクト
                params = {
                    'title': 'データ更新開始しました',
                    'message': msg,
                    'form': form,
                }

                return render(request, 'yaget/upd_byers_ct_list.html', params)

                #return redirect('yaget:upd_byers_ct_list_done')
            else:
                form = UpdByersCtListForm()
        else:
            form = UpdByersCtListForm()
            msg = ' call upd_byers_ct_list post..'
            #logger.debug("--- upd_byers_ct_list get in")
        params = {
            'title': 'Hello',
            'message': msg,
            'form': form,
        }
    except Exception as e:
        msg = ' call upd_byers_ct_list exception occurred.[{}]'.format(traceback.format_exc())
        params = {
            'title': 'Hello <exception occurred>',
            'message': msg,
            'form': form,
        }
        #logger.debug("=== (NG)  upd_byers_ct_list exception occurred.{}".format(traceback.format_exc()))

    return render(request, 'yaget/upd_byers_ct_list.html', params)


"""
# update
wks.update_acell('A4', '3')

# get
print(wks.acell('A4'))
print(wks.acell('B1'))

# 行数
print(wks.row_count)

# 行を全て取得
print(wks.row_values(2))

# 範囲を全て取得
print(wks.range('A2:C4'))

"""


# add list
def addlist(request):
    params = {
        'title': 'Hello add ya list.',
        'form': YaItemListForm(),
    }
    if (request.method == 'POST'):
        obj = YaItemList()
        yaitemlist = YaItemListForm(request.POST, instance=obj)
        yaitemlist.save()
        return redirect(to='/yaget')
    return render(request, 'yaget/addlist.html', params)


# list のデータをspreadsheetに展開する
def set_list_to_sheet(request):
    return HttpResponse("Hello yaget getdetail!")
    """
    if (request.method == 'POST'):
        sheetnum = request.POST['sheetnum']
        form = YaSetListToSheet(request.POST)
        # とりあえず全件
        data = YaItemList.objects.all()
        msg = 'after post..'

        # シートにセットする
        worksheet = WorkSheet(sheetnum)

        # E1とG1に値を挿入
        worksheet.update('E1:G1', {'values': [1, 2]})

    else:
        msg = 'sheeet num...'
        form = YaSetListToSheet()
        # とりあえず全件
        data = YaItemList.objects.all()


    params = {
        'title': 'Hello set list to sheet.',
        'message': msg,
        'form':form,
        'data':data,
    }

    # とりあえず全件
    data = YaItemList.objects.all()

    # シートにセットする
    worksheet = WorkSheet(sheetnum)

    # E1とG1に値を挿入
    worksheet.update('E1:G1', {'values': [1, 2]})

    # 上が通ったら・・ data の内容を展開してみたい
    # dataは、1件だけ（all じゃなくfirst）ならいけるか
    #worksheet.update('A2:G2', {'values': data})


    page = Paginator(data, 3)
    params = {
            'title': 'Hello set_list_to_sheet',
            'message': msg,
            'form': form,
            'data': page.get_page(num),
        }
    return render(request, 'yaget/set_list_to_sheet.html', params)
    """


# create model
def create(request):
    params = {
        'title': 'Hello',
        'form': FriendForm(),
    }
    if (request.method == 'POST'):
        obj = Friend()
        friend = FriendForm(request.POST, instance=obj)
        friend.save()
        return redirect(to='/hello')
    return render(request, 'hello/create.html', params)


# edit model
def edit(request, num):
    obj = Friend.objects.get(id=num)
    if (request.method == 'POST'):
        friend = FriendForm(request.POST, instance=obj)
        friend.save()
        return redirect(to='/hello')
    params = {
        'title': 'Hello',
        'id':num,
        'form': FriendForm(instance=obj),
    }
    return render(request, 'hello/edit.html', params)


# delete model
def delete(request, num):
    friend = Friend.objects.get(id=num)
    if (request.method == 'POST'):
        friend.delete()
        return redirect(to='/hello')
    params = {
        'title': 'Hello',
        'id':num,
        'obj': friend,
    }
    return render(request, 'hello/delete.html', params)


# find model
def find(request):
    if (request.method == 'POST'):
        msg = request.POST['find']
        form = FindForm(request.POST)
        sql = 'select * from hello_friend'
        if (msg != ''):
            sql += ' where ' + msg
        data = Friend.objects.raw(sql)
        msg = sql
    else:
        msg = 'search words...'
        form = FindForm()
        data =Friend.objects.all()
    params = {
        'title': 'Hello',
        'message': msg,
        'form':form,
        'data':data,
    }
    return render(request, 'hello/find.html', params)


# from .models import Friend, Message
# from .forms import FriendForm, MessageForm

def message(request, page=1):
    if (request.method == 'POST'):
        obj = Message()
        form = MessageForm(request.POST, instance=obj)
        form.save()
    data = Message.objects.all().reverse()
    paginator = Paginator(data, 5)
    params = {
        'title': 'Message',
        'form': MessageForm(),
        'data': paginator.get_page(page),
    }
    return render(request, 'hello/message.html', params)


class BuyersGoodsDetailList(generic.ListView):
    """
    YaBuyersItemDetailテーブルの一覧表作成
    """
    model = YaBuyersItemDetail
    template_name = 'yaget/buyers_goods_detail_list.html'
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        form_value_buyers_goods_detail_list = [
            self.request.POST.get('gid', None),
            self.request.POST.get('glink', None),
            self.request.POST.get('gname', None),
            self.request.POST.get('gdetail', None),
            self.request.POST.get('gnormalprice', None),
            self.request.POST.get('gspprice', None),
            self.request.POST.get('gcode', None),
            self.request.POST.get('bu_ctid', None),
            self.request.POST.get('stock', None),
            self.request.POST.get('wow_upd_status', None),
            self.request.POST.get('wow_on_flg', None),
            self.request.POST.get('wow_lotnum', None),
            self.request.POST.get('wow_gname', None),
            self.request.POST.get('wow_gdetail', None),
            self.request.POST.get('wow_worn_key', None),
            self.request.POST.get('wow_price', None),
            self.request.POST.get('wow_fixed_price', None),
            self.request.POST.get('wow_postage_segment', None),
            self.request.POST.get('wow_postage', None),
            self.request.POST.get('wow_delivery_method_id', None),
            self.request.POST.get('wow_ctid', None),
            self.request.POST.get('qoo_upd_status', None),
            self.request.POST.get('qoo_on_flg', None),
            self.request.POST.get('qoo_seller_code', None),
            self.request.POST.get('qoo_gdno', None),
            self.request.POST.get('qoo_gname', None),
            self.request.POST.get('qoo_gdetail', None),
            self.request.POST.get('qoo_worn_key', None),
            self.request.POST.get('qoo_price', None),
            self.request.POST.get('qoo_fixed_price', None),
            self.request.POST.get('qoo_shipping_no', None),
            self.request.POST.get('qoo_postage', None),
            self.request.POST.get('qoo_delivery_method_id', None),
            self.request.POST.get('qoo_ctid', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_buyers_goods_detail_list'] = form_value_buyers_goods_detail_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_buyers_goods_detail_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_buyers_goods_detail_list' in self.request.session:
            form_value_buyers_goods_detail_list = self.request.session['form_value_buyers_goods_detail_list']
            gid = form_value_buyers_goods_detail_list[0]
            glink = form_value_buyers_goods_detail_list[1]
            gname = form_value_buyers_goods_detail_list[2]
            gdetail = form_value_buyers_goods_detail_list[3]
            gnormalprice = form_value_buyers_goods_detail_list[4]
            gspprice = form_value_buyers_goods_detail_list[5]
            gcode = form_value_buyers_goods_detail_list[6]
            bu_ctid = form_value_buyers_goods_detail_list[7]
            stock = form_value_buyers_goods_detail_list[8]
            wow_upd_status = form_value_buyers_goods_detail_list[9]
            wow_on_flg = form_value_buyers_goods_detail_list[10]
            wow_lotnum = form_value_buyers_goods_detail_list[11]
            wow_gname = form_value_buyers_goods_detail_list[12]
            wow_gdetail = form_value_buyers_goods_detail_list[13]
            wow_worn_key = form_value_buyers_goods_detail_list[14]
            wow_price = form_value_buyers_goods_detail_list[15]
            wow_fixed_price = form_value_buyers_goods_detail_list[16]
            wow_postage_segment = form_value_buyers_goods_detail_list[17]
            wow_postage = form_value_buyers_goods_detail_list[18]
            wow_delivery_method_id = form_value_buyers_goods_detail_list[19]
            wow_ctid = form_value_buyers_goods_detail_list[20]
            qoo_upd_status = form_value_buyers_goods_detail_list[21]
            qoo_on_flg = form_value_buyers_goods_detail_list[22]
            qoo_seller_code = form_value_buyers_goods_detail_list[23]
            qoo_gdno = form_value_buyers_goods_detail_list[24]
            qoo_gname = form_value_buyers_goods_detail_list[25]
            qoo_gdetail = form_value_buyers_goods_detail_list[26]
            qoo_worn_key = form_value_buyers_goods_detail_list[27]
            qoo_price = form_value_buyers_goods_detail_list[28]
            qoo_fixed_price = form_value_buyers_goods_detail_list[29]
            qoo_shipping_no = form_value_buyers_goods_detail_list[30]
            qoo_postage = form_value_buyers_goods_detail_list[31]
            qoo_delivery_method_id = form_value_buyers_goods_detail_list[32]
            qoo_ctid = form_value_buyers_goods_detail_list[33]
            create_date_from = form_value_buyers_goods_detail_list[34]
            create_date_to = form_value_buyers_goods_detail_list[35]
            # 検索条件
            condition_gid = Q()
            condition_glink = Q()
            condition_gname = Q()
            condition_gdetail = Q()
            condition_gnormalprice = Q()
            condition_gspprice = Q()
            condition_gcode = Q()
            condition_bu_ctid = Q()
            condition_stock = Q()
            condition_wow_upd_status = Q()
            condition_wow_on_flg = Q()
            condition_wow_lotnum = Q()
            condition_wow_gname = Q()
            condition_wow_gdetail = Q()
            condition_wow_worn_key = Q()
            condition_wow_price = Q()
            condition_wow_fixed_price = Q()
            condition_wow_postage_segment = Q()
            condition_wow_postage = Q()
            condition_wow_delivery_method_id = Q()
            condition_wow_ctid = Q()
            condition_qoo_upd_status = Q()
            condition_qoo_on_flg = Q()
            condition_qoo_seller_code = Q()
            condition_qoo_gdno = Q()
            condition_qoo_gname = Q()
            condition_qoo_gdetail = Q()
            condition_qoo_worn_key = Q()
            condition_qoo_price = Q()
            condition_qoo_fixed_price = Q()
            condition_qoo_shipping_no = Q()
            condition_qoo_postage = Q()
            condition_qoo_delivery_method_id = Q()
            condition_qoo_ctid = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(gid) != 0 and gid[0]:
                condition_gid = Q(gid__icontains=gid)
            if len(glink) != 0 and glink[0]:
                condition_glink = Q(glink__icontains=glink)
            if len(gname) != 0 and gname[0]:
                condition_gname = Q(gname__icontains=gname)
            if len(gdetail) != 0 and gdetail[0]:
                condition_gdetail = Q(gdetail__icontains=gdetail)
            if len(gnormalprice) != 0 and gnormalprice[0]:
                condition_gnormalprice = Q(gnormalprice__icontains=gnormalprice)
            if len(gspprice) != 0 and gspprice[0]:
                condition_gspprice = Q(gspprice__icontains=gspprice)
            if len(gcode) != 0 and gcode[0]:
                condition_gcode = Q(gcode__icontains=gcode)
            if len(bu_ctid) != 0 and bu_ctid[0]:
                condition_bu_ctid = Q(bu_ctid__icontains=bu_ctid)
            if len(stock) != 0 and stock[0]:
                condition_stock = Q(stock__icontains=stock)
            if len(wow_upd_status) != 0 and wow_upd_status[0]:
                condition_wow_upd_status = Q(wow_upd_status__icontains=wow_upd_status)
            if len(wow_on_flg) != 0 and wow_on_flg[0]:
                condition_wow_on_flg = Q(wow_on_flg__icontains=wow_on_flg)
            if len(wow_lotnum) != 0 and wow_lotnum[0]:
                condition_wow_lotnum = Q(wow_lotnum__icontains=wow_lotnum)
            if len(wow_gname) != 0 and wow_gname[0]:
                condition_wow_gname = Q(wow_gname__icontains=wow_gname)
            if len(wow_gdetail) != 0 and wow_gdetail[0]:
                condition_wow_gdetail = Q(wow_gdetail__icontains=wow_gdetail)
            if len(wow_worn_key) != 0 and wow_worn_key[0]:
                condition_wow_worn_key = Q(wow_worn_key__icontains=wow_worn_key)
            if len(wow_price) != 0 and wow_price[0]:
                condition_wow_price = Q(wow_price__icontains=wow_price)
            if len(wow_fixed_price) != 0 and wow_fixed_price[0]:
                condition_wow_fixed_price = Q(wow_fixed_price__icontains=wow_fixed_price)
            if len(wow_postage_segment) != 0 and wow_postage_segment[0]:
                condition_wow_postage_segment = Q(wow_postage_segment__icontains=wow_postage_segment)
            if len(wow_postage) != 0 and wow_postage[0]:
                condition_wow_postage = Q(wow_postage__icontains=wow_postage)
            if len(wow_delivery_method_id) != 0 and wow_delivery_method_id[0]:
                condition_wow_delivery_method_id = Q(wow_delivery_method_id__icontains=wow_delivery_method_id)
            if len(wow_ctid) != 0 and wow_ctid[0]:
                condition_wow_ctid = Q(wow_ctid__icontains=wow_ctid)
            if len(qoo_upd_status) != 0 and qoo_upd_status[0]:
                condition_qoo_upd_status = Q(qoo_upd_status__icontains=qoo_upd_status)
            if len(qoo_on_flg) != 0 and qoo_on_flg[0]:
                condition_qoo_on_flg = Q(qoo_on_flg__icontains=qoo_on_flg)
            if len(qoo_seller_code) != 0 and qoo_seller_code[0]:
                condition_qoo_seller_code = Q(qoo_seller_code__icontains=qoo_seller_code)
            if len(qoo_gdno) != 0 and qoo_gdno[0]:
                condition_qoo_gdno = Q(qoo_gdno__icontains=qoo_gdno)
            if len(qoo_gname) != 0 and qoo_gname[0]:
                condition_qoo_gname = Q(qoo_gname__icontains=qoo_gname)
            if len(qoo_gdetail) != 0 and qoo_gdetail[0]:
                condition_qoo_gdetail = Q(qoo_gdetail__icontains=qoo_gdetail)
            if len(qoo_worn_key) != 0 and qoo_worn_key[0]:
                condition_qoo_worn_key = Q(qoo_worn_key__icontains=qoo_worn_key)
            if len(qoo_price) != 0 and qoo_price[0]:
                condition_qoo_price = Q(qoo_price__icontains=qoo_price)
            if len(qoo_fixed_price) != 0 and qoo_fixed_price[0]:
                condition_qoo_fixed_price = Q(qoo_fixed_price__icontains=qoo_fixed_price)
            if len(qoo_shipping_no) != 0 and qoo_shipping_no[0]:
                condition_qoo_shipping_no = Q(qoo_shipping_no__icontains=qoo_shipping_no)
            if len(qoo_postage) != 0 and qoo_postage[0]:
                condition_qoo_postage = Q(qoo_postage__icontains=qoo_postage)
            if len(qoo_delivery_method_id) != 0 and qoo_delivery_method_id[0]:
                condition_qoo_delivery_method_id = Q(qoo_delivery_method_id__icontains=qoo_delivery_method_id)
            if len(qoo_ctid) != 0 and qoo_ctid[0]:
                condition_qoo_ctid = Q(qoo_ctid__icontains=qoo_ctid)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return YaBuyersItemDetail.objects.select_related().filter(
                condition_gid &
                condition_glink &
                condition_gname &
                condition_gdetail &
                condition_gnormalprice &
                condition_gspprice &
                condition_gcode &
                condition_bu_ctid &
                condition_stock &
                condition_wow_upd_status &
                condition_wow_on_flg &
                condition_wow_lotnum &
                condition_wow_gname &
                condition_wow_gdetail &
                condition_wow_worn_key &
                condition_wow_price &
                condition_wow_fixed_price &
                condition_wow_postage_segment &
                condition_wow_postage &
                condition_wow_delivery_method_id &
                condition_wow_ctid &
                condition_qoo_upd_status &
                condition_qoo_on_flg &
                condition_qoo_seller_code &
                condition_qoo_gdno &
                condition_qoo_gname &
                condition_qoo_gdetail &
                condition_qoo_worn_key &
                condition_qoo_price &
                condition_qoo_fixed_price &
                condition_qoo_shipping_no &
                condition_qoo_postage &
                condition_qoo_delivery_method_id &
                condition_qoo_ctid &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return YaBuyersItemDetail.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        gid = ''
        glink = ''
        gname = ''
        gdetail = ''
        gnormalprice = ''
        gspprice = ''
        gcode = ''
        bu_ctid = ''
        stock = ''
        wow_upd_status = ''
        wow_on_flg = ''
        wow_lotnum = ''
        wow_gname = ''
        wow_gdetail = ''
        wow_worn_key = ''
        wow_price = ''
        wow_fixed_price = ''
        wow_postage_segment = ''
        wow_postage = ''
        wow_delivery_method_id = ''
        wow_ctid = ''
        qoo_upd_status = ''
        qoo_on_flg = ''
        qoo_seller_code = ''
        qoo_gdno = ''
        qoo_gname = ''
        qoo_gdetail = ''
        qoo_worn_key = ''
        qoo_price = ''
        qoo_fixed_price = ''
        qoo_shipping_no = ''
        qoo_postage = ''
        qoo_delivery_method_id = ''
        qoo_ctid = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_buyers_goods_detail_list' in self.request.session:
            form_value_buyers_goods_detail_list = self.request.session['form_value_buyers_goods_detail_list']
            gid = form_value_buyers_goods_detail_list[0]
            glink = form_value_buyers_goods_detail_list[1]
            gname = form_value_buyers_goods_detail_list[2]
            gdetail = form_value_buyers_goods_detail_list[3]
            gnormalprice = form_value_buyers_goods_detail_list[4]
            gspprice = form_value_buyers_goods_detail_list[5]
            gcode = form_value_buyers_goods_detail_list[6]
            bu_ctid = form_value_buyers_goods_detail_list[7]
            stock = form_value_buyers_goods_detail_list[8]
            wow_upd_status = form_value_buyers_goods_detail_list[9]
            wow_on_flg = form_value_buyers_goods_detail_list[10]
            wow_lotnum = form_value_buyers_goods_detail_list[11]
            wow_gname = form_value_buyers_goods_detail_list[12]
            wow_gdetail = form_value_buyers_goods_detail_list[13]
            wow_worn_key = form_value_buyers_goods_detail_list[14]
            wow_price = form_value_buyers_goods_detail_list[15]
            wow_fixed_price = form_value_buyers_goods_detail_list[16]
            wow_postage_segment = form_value_buyers_goods_detail_list[17]
            wow_postage = form_value_buyers_goods_detail_list[18]
            wow_delivery_method_id = form_value_buyers_goods_detail_list[19]
            wow_ctid = form_value_buyers_goods_detail_list[20]
            qoo_upd_status = form_value_buyers_goods_detail_list[21]
            qoo_on_flg = form_value_buyers_goods_detail_list[22]
            qoo_seller_code = form_value_buyers_goods_detail_list[23]
            qoo_gdno = form_value_buyers_goods_detail_list[24]
            qoo_gname = form_value_buyers_goods_detail_list[25]
            qoo_gdetail = form_value_buyers_goods_detail_list[26]
            qoo_worn_key = form_value_buyers_goods_detail_list[27]
            qoo_price = form_value_buyers_goods_detail_list[28]
            qoo_fixed_price = form_value_buyers_goods_detail_list[29]
            qoo_shipping_no = form_value_buyers_goods_detail_list[30]
            qoo_postage = form_value_buyers_goods_detail_list[31]
            qoo_delivery_method_id = form_value_buyers_goods_detail_list[32]
            qoo_ctid = form_value_buyers_goods_detail_list[33]
            create_date_from = form_value_buyers_goods_detail_list[34]
            create_date_to = form_value_buyers_goods_detail_list[35]
        default_data = {
                    'gid': gid, # gid
                    'glink': glink, # glink
                    'gname': gname, # gname
                    'gdetail': gdetail, # gdetail
                    'gnormalprice': gnormalprice, # gnormalprice
                    'gspprice': gspprice, # gspprice
                    'gcode': gcode, # gcode
                    'bu_ctid': bu_ctid, # bu_ctid
                    'stock': stock, # stock
                    'wow_upd_status': wow_upd_status, # wow_upd_status
                    'wow_on_flg': wow_on_flg, # wow_on_flg
                    'wow_lotnum': wow_lotnum, # wow_lotnum
                    'wow_gname': wow_gname, # wow_gname
                    'wow_gdetail': wow_gdetail, # wow_gdetail
                    'wow_worn_key': wow_worn_key, # wow_worn_key
                    'wow_price': wow_price, # wow_price
                    'wow_fixed_price': wow_fixed_price, # wow_fixed_price
                    'wow_postage_segment': wow_postage_segment, # wow_postage_segment
                    'wow_postage': wow_postage, # wow_postage
                    'wow_delivery_method_id': wow_delivery_method_id, # wow_delivery_method_id
                    'wow_ctid': wow_ctid, # wow_ctid
                    'qoo_upd_status': qoo_upd_status, # qoo_upd_status
                    'qoo_on_flg': qoo_on_flg, # qoo_on_flg
                    'qoo_seller_code': qoo_seller_code, # qoo_seller_code
                    'qoo_gdno': qoo_gdno, # qoo_gdno
                    'qoo_gname': qoo_gname, # qoo_gname
                    'qoo_gdetail': qoo_gdetail, # qoo_gdetail
                    'qoo_worn_key': qoo_worn_key, # qoo_worn_key
                    'qoo_price': qoo_price, # qoo_price
                    'qoo_fixed_price': qoo_fixed_price, # qoo_fixed_price
                    'qoo_shipping_no': qoo_shipping_no, # qoo_shipping_no
                    'qoo_postage': qoo_postage, # qoo_postage
                    'qoo_delivery_method_id': qoo_delivery_method_id, # qoo_delivery_method_id
                    'qoo_ctid': qoo_ctid, # qoo_ctid
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = YaBuyersItemDetailSearchForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'バイヤーズ商品リストです'
        ctx['title'] = 'バイヤーズ商品リスト タイトル'
        ctx['obj_all_cnt'] = YaBuyersItemDetail.objects.all().count()
        return ctx


def BuyersGoodsDetailExport(request):
    """
    YaBuyersItemDetail、CSVファイルを作成してresponseに出力します。
    """
    response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
    #response = HttpResponse(content_type='text/csv; charset=UTF-8')
    tdatetime = dt.now()
    tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
    csvfilename = ''

    if 'form_value_buyers_goods_detail_list' in request.session:
        form_value_buyers_goods_detail_list = request.session['form_value_buyers_goods_detail_list']
        gid = form_value_buyers_goods_detail_list[0]
        glink = form_value_buyers_goods_detail_list[1]
        gname = form_value_buyers_goods_detail_list[2]
        gdetail = form_value_buyers_goods_detail_list[3]
        gnormalprice = form_value_buyers_goods_detail_list[4]
        gspprice = form_value_buyers_goods_detail_list[5]
        gcode = form_value_buyers_goods_detail_list[6]
        bu_ctid = form_value_buyers_goods_detail_list[7]
        stock = form_value_buyers_goods_detail_list[8]
        wow_upd_status = form_value_buyers_goods_detail_list[9]
        wow_on_flg = form_value_buyers_goods_detail_list[10]
        wow_lotnum = form_value_buyers_goods_detail_list[11]
        wow_gname = form_value_buyers_goods_detail_list[12]
        wow_gdetail = form_value_buyers_goods_detail_list[13]
        wow_worn_key = form_value_buyers_goods_detail_list[14]
        wow_price = form_value_buyers_goods_detail_list[15]
        wow_fixed_price = form_value_buyers_goods_detail_list[16]
        wow_postage_segment = form_value_buyers_goods_detail_list[17]
        wow_postage = form_value_buyers_goods_detail_list[18]
        wow_delivery_method_id = form_value_buyers_goods_detail_list[19]
        wow_ctid = form_value_buyers_goods_detail_list[20]
        qoo_upd_status = form_value_buyers_goods_detail_list[21]
        qoo_on_flg = form_value_buyers_goods_detail_list[22]
        qoo_seller_code = form_value_buyers_goods_detail_list[23]
        qoo_gdno = form_value_buyers_goods_detail_list[24]
        qoo_gname = form_value_buyers_goods_detail_list[25]
        qoo_gdetail = form_value_buyers_goods_detail_list[26]
        qoo_worn_key = form_value_buyers_goods_detail_list[27]
        qoo_price = form_value_buyers_goods_detail_list[28]
        qoo_fixed_price = form_value_buyers_goods_detail_list[29]
        qoo_shipping_no = form_value_buyers_goods_detail_list[30]
        qoo_postage = form_value_buyers_goods_detail_list[31]
        qoo_delivery_method_id = form_value_buyers_goods_detail_list[32]
        qoo_ctid = form_value_buyers_goods_detail_list[33]
        create_date_from = form_value_buyers_goods_detail_list[34]
        create_date_to = form_value_buyers_goods_detail_list[35]

        # 検索条件
        condition_gid = Q()
        condition_glink = Q()
        condition_gname = Q()
        condition_gdetail = Q()
        condition_gnormalprice = Q()
        condition_gspprice = Q()
        condition_gcode = Q()
        condition_bu_ctid = Q()
        condition_stock = Q()
        condition_wow_upd_status = Q()
        condition_wow_on_flg = Q()
        condition_wow_lotnum = Q()
        condition_wow_gname = Q()
        condition_wow_gdetail = Q()
        condition_wow_worn_key = Q()
        condition_wow_price = Q()
        condition_wow_fixed_price = Q()
        condition_wow_postage_segment = Q()
        condition_wow_postage = Q()
        condition_wow_delivery_method_id = Q()
        condition_wow_ctid = Q()
        condition_qoo_upd_status = Q()
        condition_qoo_on_flg = Q()
        condition_qoo_seller_code = Q()
        condition_qoo_gdno = Q()
        condition_qoo_gname = Q()
        condition_qoo_gdetail = Q()
        condition_qoo_worn_key = Q()
        condition_qoo_price = Q()
        condition_qoo_fixed_price = Q()
        condition_qoo_shipping_no = Q()
        condition_qoo_postage = Q()
        condition_qoo_delivery_method_id = Q()
        condition_qoo_ctid = Q()
        condition_create_date_from = Q()
        condition_create_date_to = Q()
        if len(gid) != 0 and gid[0]:
            condition_gid = Q(gid__icontains=gid)
        if len(glink) != 0 and glink[0]:
            condition_glink = Q(glink__icontains=glink)
        if len(gname) != 0 and gname[0]:
            condition_gname = Q(gname__icontains=gname)
        if len(gdetail) != 0 and gdetail[0]:
            condition_gdetail = Q(gdetail__icontains=gdetail)
        if len(gnormalprice) != 0 and gnormalprice[0]:
            condition_gnormalprice = Q(gnormalprice__icontains=gnormalprice)
        if len(gspprice) != 0 and gspprice[0]:
            condition_gspprice = Q(gspprice__icontains=gspprice)
        if len(gcode) != 0 and gcode[0]:
            condition_gcode = Q(gcode__icontains=gcode)
        if len(bu_ctid) != 0 and bu_ctid[0]:
            condition_bu_ctid = Q(bu_ctid__icontains=bu_ctid)
        if len(stock) != 0 and stock[0]:
            condition_stock = Q(stock__icontains=stock)
        if len(wow_upd_status) != 0 and wow_upd_status[0]:
            condition_wow_upd_status = Q(wow_upd_status__icontains=wow_upd_status)
        if len(wow_on_flg) != 0 and wow_on_flg[0]:
            condition_wow_on_flg = Q(wow_on_flg__icontains=wow_on_flg)
        if len(wow_lotnum) != 0 and wow_lotnum[0]:
            condition_wow_lotnum = Q(wow_lotnum__icontains=wow_lotnum)
        if len(wow_gname) != 0 and wow_gname[0]:
            condition_wow_gname = Q(wow_gname__icontains=wow_gname)
        if len(wow_gdetail) != 0 and wow_gdetail[0]:
            condition_wow_gdetail = Q(wow_gdetail__icontains=wow_gdetail)
        if len(wow_worn_key) != 0 and wow_worn_key[0]:
            condition_wow_worn_key = Q(wow_worn_key__icontains=wow_worn_key)
        if len(wow_price) != 0 and wow_price[0]:
            condition_wow_price = Q(wow_price__icontains=wow_price)
        if len(wow_fixed_price) != 0 and wow_fixed_price[0]:
            condition_wow_fixed_price = Q(wow_fixed_price__icontains=wow_fixed_price)
        if len(wow_postage_segment) != 0 and wow_postage_segment[0]:
            condition_wow_postage_segment = Q(wow_postage_segment__icontains=wow_postage_segment)
        if len(wow_postage) != 0 and wow_postage[0]:
            condition_wow_postage = Q(wow_postage__icontains=wow_postage)
        if len(wow_delivery_method_id) != 0 and wow_delivery_method_id[0]:
            condition_wow_delivery_method_id = Q(wow_delivery_method_id__icontains=wow_delivery_method_id)
        if len(wow_ctid) != 0 and wow_ctid[0]:
            condition_wow_ctid = Q(wow_ctid__icontains=wow_ctid)
        if len(qoo_upd_status) != 0 and qoo_upd_status[0]:
            condition_qoo_upd_status = Q(qoo_upd_status__icontains=qoo_upd_status)
        if len(qoo_on_flg) != 0 and qoo_on_flg[0]:
            condition_qoo_on_flg = Q(qoo_on_flg__icontains=qoo_on_flg)
        if len(qoo_seller_code) != 0 and qoo_seller_code[0]:
            condition_qoo_seller_code = Q(qoo_seller_code__icontains=qoo_seller_code)
        if len(qoo_gdno) != 0 and qoo_gdno[0]:
            condition_qoo_gdno = Q(qoo_gdno__icontains=qoo_gdno)
        if len(qoo_gname) != 0 and qoo_gname[0]:
            condition_qoo_gname = Q(qoo_gname__icontains=qoo_gname)
        if len(qoo_gdetail) != 0 and qoo_gdetail[0]:
            condition_qoo_gdetail = Q(qoo_gdetail__icontains=qoo_gdetail)
        if len(qoo_worn_key) != 0 and qoo_worn_key[0]:
            condition_qoo_worn_key = Q(qoo_worn_key__icontains=qoo_worn_key)
        if len(qoo_price) != 0 and qoo_price[0]:
            condition_qoo_price = Q(qoo_price__icontains=qoo_price)
        if len(qoo_fixed_price) != 0 and qoo_fixed_price[0]:
            condition_qoo_fixed_price = Q(qoo_fixed_price__icontains=qoo_fixed_price)
        if len(qoo_shipping_no) != 0 and qoo_shipping_no[0]:
            condition_qoo_shipping_no = Q(qoo_shipping_no__icontains=qoo_shipping_no)
        if len(qoo_postage) != 0 and qoo_postage[0]:
            condition_qoo_postage = Q(qoo_postage__icontains=qoo_postage)
        if len(qoo_delivery_method_id) != 0 and qoo_delivery_method_id[0]:
            condition_qoo_delivery_method_id = Q(qoo_delivery_method_id__icontains=qoo_delivery_method_id)
        if len(qoo_ctid) != 0 and qoo_ctid[0]:
            condition_qoo_ctid = Q(qoo_ctid__icontains=qoo_ctid)
        if len(create_date_from) != 0 and create_date_from[0]:
            condition_create_date_from = Q(create_date__gte=create_date_from)
        if len(create_date_to) != 0 and create_date_to[0]:
            condition_create_date_to = Q(create_date__lte=create_date_to)

        csvfilename = tstr + '_buyers_item_detail.csv'
        csvfilename = csvfilename.replace(' ','').replace('>','_').replace('、','-')
        writer = get_csv_writer(response, csvfilename)

        # ヘッダ行セット
        writer.writerow([
            '商品ID',
            '商品リンク',
            '商品名',
            '商品詳細',
            '通常価格',
            '大量発注価格',
            'バイヤーズ商品コード',
            '在庫数',
            'wow掲載状況',
            'wowステータス',
            'wow商品名',
            'wow商品詳細',
            'wow注意キーワード',
            'wow価格',
            'wow固定価格',
            'wow送料設定区分',
            'wow個別送料',
            'wow送料設定区分',
            'wowカテゴリID',
            'qoo掲載状況',
            'qooステータス',
            'qoo販売者コード',
            'qoo商品コード',
            'qoo商品名',
            'qoo商品詳細',
            'qoo注意キーワード',
            'qoo価格',
            'qoo固定価格',
            'qoo送料設定区分',
            'qoo個別送料',
            'qoo送料設定区分',
            'qooカテゴリID',
            '作成日',
            '更新日',
        ])

        for retobj in YaBuyersItemDetail.objects.select_related().filter(
                condition_gid &
                condition_glink &
                condition_gname &
                condition_gdetail &
                condition_gnormalprice &
                condition_gspprice &
                condition_gcode &
                condition_bu_ctid &
                condition_stock &
                condition_wow_upd_status &
                condition_wow_on_flg &
                condition_wow_lotnum &
                condition_wow_gname &
                condition_wow_gdetail &
                condition_wow_worn_key &
                condition_wow_price &
                condition_wow_fixed_price &
                condition_wow_postage_segment &
                condition_wow_postage &
                condition_wow_delivery_method_id &
                condition_wow_ctid &
                condition_qoo_upd_status &
                condition_qoo_on_flg &
                condition_qoo_seller_code &
                condition_qoo_gdno &
                condition_qoo_gname &
                condition_qoo_gdetail &
                condition_qoo_worn_key &
                condition_qoo_price &
                condition_qoo_fixed_price &
                condition_qoo_shipping_no &
                condition_qoo_postage &
                condition_qoo_delivery_method_id &
                condition_qoo_ctid &
                condition_create_date_from &
                condition_create_date_to
        ).order_by("-update_date")[:10000]:
            # 変換する文字。shift-jis変換でコケた文字はここに登録
            tmpgname = retobj.gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpgname = re.sub(exchange_words[0], exchange_words[1], tmpgname)

            tmpwow_gname = retobj.wow_gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpwow_gname = re.sub(exchange_words[0], exchange_words[1], tmpwow_gname)

            tmpqoo_gname = retobj.qoo_gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpqoo_gname = re.sub(exchange_words[0], exchange_words[1], tmpqoo_gname)

            tmpgdetail = retobj.gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpgdetail = re.sub(exchange_words[0], exchange_words[1], tmpgdetail)

            tmpwow_gdetail_1 = retobj.wow_gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpwow_gdetail_1 = re.sub(exchange_words[0], exchange_words[1], tmpwow_gdetail_1)

            tmpqoo_gdetail_1 = retobj.qoo_gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpqoo_gdetail_1 = re.sub(exchange_words[0], exchange_words[1], tmpqoo_gdetail_1)

            writer.writerow([
                retobj.gid,
                retobj.glink,
                tmpgname, #retobj.gname,
                tmpgdetail, #retobj.gdetail,
                retobj.gnormalprice,
                retobj.gspprice,
                retobj.gcode,
                retobj.stock,
                retobj.wow_upd_status,
                retobj.wow_on_flg,
                tmpwow_gname, #retobj.wow_gname,
                tmpwow_gdetail_1, #retobj.wow_gdetail,
                retobj.wow_worn_key,
                retobj.wow_price,
                retobj.wow_fixed_price,
                retobj.wow_postage_segment,
                retobj.wow_postage,
                retobj.wow_delivery_method_id,
                retobj.wow_ctid,
                retobj.qoo_upd_status,
                retobj.qoo_on_flg,
                retobj.qoo_seller_code,
                retobj.qoo_gdno,
                tmpqoo_gname, #retobj.qoo_gname,
                tmpqoo_gdetail_1, #retobj.qoo_gdetail,
                retobj.qoo_worn_key,
                retobj.qoo_price,
                retobj.qoo_fixed_price,
                retobj.qoo_shipping_no,
                retobj.qoo_postage,
                retobj.qoo_delivery_method_id,
                retobj.qoo_ctid,
                retobj.create_date,
                retobj.update_date,
            ])
    else:
        csvfilename = tstr + '_buyers_item_detail_all.csv'
        writer = get_csv_writer(response, csvfilename)

        # ヘッダ行セット
        writer.writerow([
            '商品ID',
            '商品リンク',
            '商品名',
            '商品詳細',
            '通常価格',
            '大量発注価格',
            'バイヤーズ商品コード',
            '在庫数',
            'wow掲載状況',
            'wowステータス',
            'wow商品名',
            'wow商品詳細',
            'wow注意キーワード',
            'wow価格',
            'wow固定価格',
            'wow送料設定区分',
            'wow個別送料',
            'wow送料設定区分',
            'wowカテゴリID',
            'qoo掲載状況',
            'qooステータス',
            'qoo販売者コード',
            'qoo商品コード',
            'qoo商品名',
            'qoo商品詳細',
            'qoo注意キーワード',
            'qoo価格',
            'qoo固定価格',
            'qoo送料設定区分',
            'qoo個別送料',
            'qoo送料設定区分',
            'qooカテゴリID',
            '作成日',
            '更新日',
        ])

        for retobj in YaBuyersItemDetail.objects.all():
            writer.writerow([

                retobj.gid,
                retobj.glink,
                retobj.gname,
                retobj.gdetail,
                retobj.gnormalprice,
                retobj.gspprice,
                retobj.gcode,
                retobj.stock,
                retobj.wow_upd_status,
                retobj.wow_on_flg,
                retobj.wow_gname,
                retobj.wow_gdetail,
                retobj.wow_worn_key,
                retobj.wow_price,
                retobj.wow_fixed_price,
                retobj.wow_postage_segment,
                retobj.wow_postage,
                retobj.wow_delivery_method_id,
                retobj.wow_ctid,
                retobj.qoo_upd_status,
                retobj.qoo_on_flg,
                retobj.qoo_seller_code,
                retobj.qoo_gdno,
                retobj.qoo_gname,
                retobj.qoo_gdetail,
                retobj.qoo_worn_key,
                retobj.qoo_price,
                retobj.qoo_fixed_price,
                retobj.qoo_shipping_no,
                retobj.qoo_postage,
                retobj.qoo_delivery_method_id,
                retobj.qoo_ctid,
                retobj.create_date,
                retobj.update_date,
            ])
    return response


def BuyersGoodsDetailSmallExport(request):
    """
    YaBuyersItemDetail、商品説明などに項目を絞り込んだCSVファイルを作成してresponseに出力します。
    """
    response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
    #response = HttpResponse(content_type='text/csv; charset=UTF-8')
    tdatetime = dt.now()
    tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
    csvfilename = ''

    if 'form_value_buyers_goods_detail_list' in request.session:
        form_value_buyers_goods_detail_list = request.session['form_value_buyers_goods_detail_list']
        gid = form_value_buyers_goods_detail_list[0]
        glink = form_value_buyers_goods_detail_list[1]
        gname = form_value_buyers_goods_detail_list[2]
        gdetail = form_value_buyers_goods_detail_list[3]
        gnormalprice = form_value_buyers_goods_detail_list[4]
        gspprice = form_value_buyers_goods_detail_list[5]
        gcode = form_value_buyers_goods_detail_list[6]
        bu_ctid = form_value_buyers_goods_detail_list[7]
        stock = form_value_buyers_goods_detail_list[8]
        wow_upd_status = form_value_buyers_goods_detail_list[9]
        wow_on_flg = form_value_buyers_goods_detail_list[10]
        wow_lotnum = form_value_buyers_goods_detail_list[11]
        wow_gname = form_value_buyers_goods_detail_list[12]
        wow_gdetail = form_value_buyers_goods_detail_list[13]
        wow_worn_key = form_value_buyers_goods_detail_list[14]
        wow_price = form_value_buyers_goods_detail_list[15]
        wow_fixed_price = form_value_buyers_goods_detail_list[16]
        wow_postage_segment = form_value_buyers_goods_detail_list[17]
        wow_postage = form_value_buyers_goods_detail_list[18]
        wow_delivery_method_id = form_value_buyers_goods_detail_list[19]
        wow_ctid = form_value_buyers_goods_detail_list[20]
        qoo_upd_status = form_value_buyers_goods_detail_list[21]
        qoo_on_flg = form_value_buyers_goods_detail_list[22]
        qoo_seller_code = form_value_buyers_goods_detail_list[23]
        qoo_gdno = form_value_buyers_goods_detail_list[24]
        qoo_gname = form_value_buyers_goods_detail_list[25]
        qoo_gdetail = form_value_buyers_goods_detail_list[26]
        qoo_worn_key = form_value_buyers_goods_detail_list[27]
        qoo_price = form_value_buyers_goods_detail_list[28]
        qoo_fixed_price = form_value_buyers_goods_detail_list[29]
        qoo_shipping_no = form_value_buyers_goods_detail_list[30]
        qoo_postage = form_value_buyers_goods_detail_list[31]
        qoo_delivery_method_id = form_value_buyers_goods_detail_list[32]
        qoo_ctid = form_value_buyers_goods_detail_list[33]
        create_date_from = form_value_buyers_goods_detail_list[34]
        create_date_to = form_value_buyers_goods_detail_list[35]

        # 検索条件
        condition_gid = Q()
        condition_glink = Q()
        condition_gname = Q()
        condition_gdetail = Q()
        condition_gnormalprice = Q()
        condition_gspprice = Q()
        condition_gcode = Q()
        condition_bu_ctid = Q()
        condition_stock = Q()
        condition_wow_upd_status = Q()
        condition_wow_on_flg = Q()
        condition_wow_lotnum = Q()
        condition_wow_gname = Q()
        condition_wow_gdetail = Q()
        condition_wow_worn_key = Q()
        condition_wow_price = Q()
        condition_wow_fixed_price = Q()
        condition_wow_postage_segment = Q()
        condition_wow_postage = Q()
        condition_wow_delivery_method_id = Q()
        condition_wow_ctid = Q()
        condition_qoo_upd_status = Q()
        condition_qoo_on_flg = Q()
        condition_qoo_seller_code = Q()
        condition_qoo_gdno  = Q()
        condition_qoo_gname = Q()
        condition_qoo_gdetail = Q()
        condition_qoo_worn_key = Q()
        condition_qoo_price = Q()
        condition_qoo_fixed_price = Q()
        condition_qoo_shipping_no = Q()
        condition_qoo_postage = Q()
        condition_qoo_delivery_method_id = Q()
        condition_qoo_ctid = Q()
        condition_create_date_from = Q()
        condition_create_date_to = Q()
        if len(gid) != 0 and gid[0]:
            condition_gid = Q(gid__icontains=gid)
        if len(glink) != 0 and glink[0]:
            condition_glink = Q(glink__icontains=glink)
        if len(gname) != 0 and gname[0]:
            condition_gname = Q(gname__icontains=gname)
        if len(gdetail) != 0 and gdetail[0]:
            condition_gdetail = Q(gdetail__icontains=gdetail)
        if len(gnormalprice) != 0 and gnormalprice[0]:
            condition_gnormalprice = Q(gnormalprice__icontains=gnormalprice)
        if len(gspprice) != 0 and gspprice[0]:
            condition_gspprice = Q(gspprice__icontains=gspprice)
        if len(gcode) != 0 and gcode[0]:
            condition_gcode = Q(gcode__icontains=gcode)
        if len(bu_ctid) != 0 and bu_ctid[0]:
            condition_bu_ctid = Q(bu_ctid__icontains=bu_ctid)
        if len(stock) != 0 and stock[0]:
            condition_stock = Q(stock__icontains=stock)
        if len(wow_upd_status) != 0 and wow_upd_status[0]:
            condition_wow_upd_status = Q(wow_upd_status__icontains=wow_upd_status)
        if len(wow_on_flg) != 0 and wow_on_flg[0]:
            condition_wow_on_flg = Q(wow_on_flg__icontains=wow_on_flg)
        if len(wow_lotnum) != 0 and wow_lotnum[0]:
            condition_wow_lotnum = Q(wow_lotnum__icontains=wow_lotnum)
        if len(wow_gname) != 0 and wow_gname[0]:
            condition_wow_gname = Q(wow_gname__icontains=wow_gname)
        if len(wow_gdetail) != 0 and wow_gdetail[0]:
            condition_wow_gdetail = Q(wow_gdetail__icontains=wow_gdetail)
        if len(wow_worn_key) != 0 and wow_worn_key[0]:
            condition_wow_worn_key = Q(wow_worn_key__icontains=wow_worn_key)
        if len(wow_price) != 0 and wow_price[0]:
            condition_wow_price = Q(wow_price__icontains=wow_price)
        if len(wow_fixed_price) != 0 and wow_fixed_price[0]:
            condition_wow_fixed_price = Q(wow_fixed_price__icontains=wow_fixed_price)
        if len(wow_postage_segment) != 0 and wow_postage_segment[0]:
            condition_wow_postage_segment = Q(wow_postage_segment__icontains=wow_postage_segment)
        if len(wow_postage) != 0 and wow_postage[0]:
            condition_wow_postage = Q(wow_postage__icontains=wow_postage)
        if len(wow_delivery_method_id) != 0 and wow_delivery_method_id[0]:
            condition_wow_delivery_method_id = Q(wow_delivery_method_id__icontains=wow_delivery_method_id)
        if len(wow_ctid) != 0 and wow_ctid[0]:
            condition_wow_ctid = Q(wow_ctid__icontains=wow_ctid)
        if len(qoo_upd_status) != 0 and qoo_upd_status[0]:
            condition_qoo_upd_status = Q(qoo_upd_status__icontains=qoo_upd_status)
        if len(qoo_on_flg) != 0 and qoo_on_flg[0]:
            condition_qoo_on_flg = Q(qoo_on_flg__icontains=qoo_on_flg)
        if len(qoo_seller_code) != 0 and qoo_seller_code[0]:
            condition_qoo_seller_code = Q(qoo_seller_code__icontains=qoo_seller_code)
        if len(qoo_gdno) != 0 and qoo_gdno[0]:
            condition_qoo_gdno = Q(qoo_gdno__icontains=qoo_gdno)
        if len(qoo_gname) != 0 and qoo_gname[0]:
            condition_qoo_gname = Q(qoo_gname__icontains=qoo_gname)
        if len(qoo_gdetail) != 0 and qoo_gdetail[0]:
            condition_qoo_gdetail = Q(qoo_gdetail__icontains=qoo_gdetail)
        if len(qoo_worn_key) != 0 and qoo_worn_key[0]:
            condition_qoo_worn_key = Q(qoo_worn_key__icontains=qoo_worn_key)
        if len(qoo_price) != 0 and qoo_price[0]:
            condition_qoo_price = Q(qoo_price__icontains=qoo_price)
        if len(qoo_fixed_price) != 0 and qoo_fixed_price[0]:
            condition_qoo_fixed_price = Q(qoo_fixed_price__icontains=qoo_fixed_price)
        if len(qoo_shipping_no) != 0 and qoo_shipping_no[0]:
            condition_qoo_shipping_no = Q(qoo_shipping_no__icontains=qoo_shipping_no)
        if len(qoo_postage) != 0 and qoo_postage[0]:
            condition_qoo_postage = Q(qoo_postage__icontains=qoo_postage)
        if len(qoo_delivery_method_id) != 0 and qoo_delivery_method_id[0]:
            condition_qoo_delivery_method_id = Q(qoo_delivery_method_id__icontains=qoo_delivery_method_id)
        if len(qoo_ctid) != 0 and qoo_ctid[0]:
            condition_qoo_ctid = Q(qoo_ctid__icontains=qoo_ctid)
        if len(create_date_from) != 0 and create_date_from[0]:
            condition_create_date_from = Q(create_date__gte=create_date_from)
        if len(create_date_to) != 0 and create_date_to[0]:
            condition_create_date_to = Q(create_date__lte=create_date_to)

        # 縮小版は s 始まりのルールにする
        csvfilename = 's_' + tstr + '_buyers_item_detail.csv'
        csvfilename = csvfilename.replace(' ','').replace('>','_').replace('、','-')
        writer = get_csv_writer(response, csvfilename)

        # ヘッダ行セット
        writer.writerow([
            '商品ID',
            '商品名',
            '商品詳細',
            '通常価格',
            '在庫数',
            'wow掲載状況',
            'wowステータス',
            'wow商品名',
            'wow商品詳細',
            'wow注意キーワード',
            'qoo掲載状況',
            'qooステータス',
            'qoo商品名',
            'qoo商品詳細',
            'qoo注意キーワード',
            '作成日',
            '更新日',
        ])

        for retobj in YaBuyersItemDetail.objects.select_related().filter(
                condition_gid &
                condition_glink &
                condition_gname &
                condition_gdetail &
                condition_gnormalprice &
                condition_gspprice &
                condition_gcode &
                condition_bu_ctid &
                condition_stock &
                condition_wow_upd_status &
                condition_wow_on_flg &
                condition_wow_lotnum &
                condition_wow_gname &
                condition_wow_gdetail &
                condition_wow_worn_key &
                condition_wow_price &
                condition_wow_fixed_price &
                condition_wow_postage_segment &
                condition_wow_postage &
                condition_wow_delivery_method_id &
                condition_wow_ctid &
                condition_qoo_upd_status &
                condition_qoo_on_flg &
                condition_qoo_seller_code &
                condition_qoo_gdno &
                condition_qoo_gname &
                condition_qoo_gdetail &
                condition_qoo_worn_key &
                condition_qoo_price &
                condition_qoo_fixed_price &
                condition_qoo_shipping_no &
                condition_qoo_postage &
                condition_qoo_delivery_method_id &
                condition_qoo_ctid &
                condition_create_date_from &
                condition_create_date_to
        ).order_by("-update_date")[:10000]:
            # 変換する文字。shift-jis変換でコケた文字はここに登録
            tmpgname = retobj.gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpgname = re.sub(exchange_words[0], exchange_words[1], tmpgname)
            tmpgdetail = retobj.gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmpgdetail = re.sub(exchange_words[0], exchange_words[1], tmpgdetail)
            tmp_wow_gname = retobj.wow_gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmp_wow_gname = re.sub(exchange_words[0], exchange_words[1], tmp_wow_gname)
            tmp_wow_gdetail = retobj.wow_gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmp_wow_gdetail = re.sub(exchange_words[0], exchange_words[1], tmp_wow_gdetail)
            tmp_qoo_gname = retobj.qoo_gname
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmp_qoo_gname = re.sub(exchange_words[0], exchange_words[1], tmp_qoo_gname)
            tmp_qoo_gdetail = retobj.qoo_gdetail
            for exchange_words in BuyersBrandInfo._MY_EXCHANGE_WORDS:
                tmp_qoo_gdetail = re.sub(exchange_words[0], exchange_words[1], tmp_qoo_gdetail)

            writer.writerow([
                retobj.gid,
                tmpgname,  #retobj.gname,
                tmpgdetail, #retobj.gdetail,
                retobj.gnormalprice,
                retobj.stock,
                retobj.wow_upd_status,
                retobj.wow_on_flg,
                tmp_wow_gname, #retobj.wow_gname,
                tmp_wow_gdetail, #retobj.wow_gdetail,
                retobj.wow_worn_key,
                retobj.qoo_upd_status,
                retobj.qoo_on_flg,
                tmp_qoo_gname,  #retobj.qoo_gname,
                tmp_qoo_gdetail,  #retobj.qoo_gdetail,
                retobj.qoo_worn_key,
                retobj.create_date,
                retobj.update_date,
            ])
    else:
        csvfilename = tstr + '_buyers_item_detail_all.csv'
        writer = get_csv_writer(response, csvfilename)

        # ヘッダ行セット
        writer.writerow([
            '商品ID',
            '商品名',
            '商品詳細',
            '通常価格',
            '在庫数',
            'wow掲載状況',
            'wowステータス',
            'wow商品名',
            'wow商品詳細',
            'wow注意キーワード',
            'qoo掲載状況',
            'qooステータス',
            'qoo商品名',
            'qoo商品詳細',
            'qoo注意キーワード',
            '作成日',
            '更新日',
        ])
        for retobj in YaBuyersItemDetail.objects.all():
            writer.writerow([
                retobj.gid,
                retobj.gname,
                retobj.gdetail,
                retobj.gnormalprice,
                retobj.stock,
                retobj.wow_upd_status,
                retobj.wow_on_flg,
                retobj.wow_gname,
                retobj.wow_gdetail,
                retobj.wow_worn_key,
                retobj.qoo_upd_status,
                retobj.qoo_on_flg,
                retobj.qoo_gname,
                retobj.qoo_gdetail,
                retobj.qoo_worn_key,
                retobj.create_date,
                retobj.update_date,
            ])
    return response


class BuyersGoodsDetailImport(generic.FormView):
    """
    YaBuyersItemDetailテーブルを全件検索して、CSVファイルを取り込みDBに格納します。
    """
    template_name = 'yaget/buyers_goods_detail_import.html'
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    form_class = BuyersGoodsDetailImportForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'BuyersGoodsDetailImport　です'
        return ctx

    def form_valid(self, form):
        """postされたTSVファイルを読み込み、YaBuyersItemDetail テーブルに登録します"""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        #csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 指定ディレクトリにcsvでカキコ
        self.write_csv(reader)

        # 書き込んだらバッチをキック
        mymsg = 'goods info update start. '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py upload_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        mymsg += ' maybe ok.' + str(p.pid)

        """
        #reader = csv.reader(csvfile, delimiter="\t")
        for i, row in enumerate(reader):
            if i == 0:
                continue # ヘッダ行は飛ばす

            #YaBuyersItemDetail テーブルをgid (primary key)で検索します
            try:
                #ya_b_item_detail, created = YaBuyersItemDetail.objects.get_or_create(gid=row[0])
                ya_b_item_detail = YaBuyersItemDetail.objects.get(gid=row[0])
            except Exception as e:
                # 該当レコードがなければパス
                continue

            #ya_b_item_detail.gid = row[0]
            ya_b_item_detail.glink = row[1]
            ya_b_item_detail.gname = row[2]
            ya_b_item_detail.gdetail = row[3]
            ya_b_item_detail.gnormalprice = row[4]
            ya_b_item_detail.gspprice = row[5]
            ya_b_item_detail.gcode = row[6]
            ya_b_item_detail.stock = row[7]
            ya_b_item_detail.wow_upd_status = row[8]
            ya_b_item_detail.wow_on_flg = row[9]
            ya_b_item_detail.wow_gname = row[10]
            ya_b_item_detail.wow_gdetail = row[11]
            ya_b_item_detail.wow_worn_key = row[12]
            ya_b_item_detail.wow_price = row[13]
            ya_b_item_detail.wow_fixed_price = row[14]
            ya_b_item_detail.wow_postage_segment = row[15]
            ya_b_item_detail.wow_postage = row[16]
            ya_b_item_detail.wow_delivery_method_id = row[17]
            ya_b_item_detail.wow_ctid = row[18]
            ya_b_item_detail.qoo_upd_status = row[19]
            ya_b_item_detail.qoo_on_flg = row[20]
            ya_b_item_detail.qoo_gname = row[21]
            ya_b_item_detail.qoo_gdetail = row[22]
            ya_b_item_detail.qoo_worn_key = row[23]
            ya_b_item_detail.qoo_price = row[24]
            ya_b_item_detail.qoo_fixed_price = row[25]
            ya_b_item_detail.qoo_shipping_no = row[26]
            ya_b_item_detail.qoo_postage = row[27]
            ya_b_item_detail.qoo_delivery_method_id = row[28]
            ya_b_item_detail.qoo_ctid = row[29]
            ya_b_item_detail.save()
        """
        return super().form_valid(form)

    # csvにファイル出力
    def write_csv(self, reader):
        logger.debug('write_csv in .')
        # csvはここで用意するか
        csvname = myupdcsv_dir + 'updcsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'

        # 以下はヘッダ行のみ
        """
        with open(csvname, 'w', encoding='cp932') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            writer.writerow([
                'gid',
                'glink',
                'gname',
                'gdetail',
                'gnormalprice',
                'gspprice',
                'gcode',
                'stock',
                'wow_upd_status',
                'wow_on_flg',
                'wow_gname',
                'wow_gdetail',
                'wow_worn_key',
                'wow_price',
                'wow_fixed_price',
                'wow_postage_segment',
                'wow_postage',
                'wow_delivery_method_id',
                'wow_ctid',
                'qoo_upd_status',
                'qoo_on_flg',
                'qoo_gname',
                'qoo_gdetail',
                'qoo_worn_key',
                'qoo_price',
                'qoo_fixed_price',
                'qoo_shipping_no',
                'qoo_postage',
                'qoo_delivery_method_id',
                'qoo_ctid',
            ])
        """
        # データ行は追記
        with open(csvname, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for item in reader:
                writer.writerow([
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    item[5],
                    item[6],
                    item[7],
                    item[8],
                    item[9],
                    item[10],
                    item[11],
                    item[12],
                    item[13],
                    item[14],
                    item[15],
                    item[16],
                    item[17],
                    item[18],
                    item[19],
                    item[20],
                    item[21],
                    item[22],
                    item[23],
                    item[24],
                    item[25],
                    item[26],
                    item[27],
                    item[28],
                    item[29],
                    item[30],
                    item[31],
                ])
        logger.debug('write_csv out .')
        return

class BuyersGoodsDetailSmallImport(generic.FormView):
    """
    YaBuyersItemDetailテーブルを全件検索して、CSVファイルを取り込みDBに格納します。
    絞り込み項目版
    """
    template_name = 'yaget/buyers_goods_detail_small_import.html'
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    form_class = BuyersGoodsDetailSmallImportForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'BuyersGoodsDetailSmallImport　です'
        return ctx

    def form_valid(self, form):
        logger.debug("--- BuyersGoodsDetailSmallImport in")

        """postされたTSVファイルを読み込み、YaBuyersItemDetail テーブルに登録します"""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        #csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 指定ディレクトリにcsvでカキコ
        self.write_csv(reader)

        # 書き込んだらバッチをキック
        mymsg = 'goods info update start. '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py upload_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        mymsg += ' maybe ok.' + str(p.pid)

        """
        #reader = csv.reader(csvfile, delimiter="\t")
        for i, row in enumerate(reader):
            if i == 0:
                logger.debug("--- BuyersGoodsDetailSmallImport i=0 continue")

                continue # ヘッダ行は飛ばす

            #YaBuyersItemDetail テーブルをmyshop_cat_all (primary key)で検索します

            try:
                #ya_b_item_detail, created = YaBuyersItemDetail.objects.get_or_create(gid=row[0])
                logger.debug("--- BuyersGoodsDetailSmallImport gid:[{}]".format(row[0]))
                ya_b_item_detail = YaBuyersItemDetail.objects.get(gid=row[0])
            except Exception as e:
                # 該当レコードがなければパス
                continue
            #ya_b_item_detail.gid = row[0]
            ya_b_item_detail.gname = row[1]
            ya_b_item_detail.gdetail = row[2]
            ya_b_item_detail.gnormalprice = row[3]
            ya_b_item_detail.stock = row[4]
            ya_b_item_detail.wow_upd_status = row[5]
            ya_b_item_detail.wow_on_flg = row[6]
            ya_b_item_detail.wow_gname = row[7]
            ya_b_item_detail.wow_gdetail = row[8]
            ya_b_item_detail.wow_worn_key = row[9]
            ya_b_item_detail.qoo_upd_status = row[10]
            ya_b_item_detail.qoo_on_flg = row[11]
            ya_b_item_detail.qoo_gname = row[12]
            ya_b_item_detail.qoo_gdetail = row[13]
            ya_b_item_detail.qoo_worn_key = row[14]
            ya_b_item_detail.save()
            logger.debug("--- BuyersGoodsDetailSmallImport wow_gdetail:[{}]".format(row[8]))
        """
        logger.debug("--- BuyersGoodsDetailSmallImport out")
        return super().form_valid(form)

    # csvにファイル出力(簡易版)
    def write_csv(self, reader):
        logger.debug('write_csv in .')
        # csvはここで用意するか
        csvname = myupdcsv_dir + 's_updcsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'

        # 以下はヘッダ行のみ
        """
        with open(csvname, 'w', encoding='cp932') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            writer.writerow([
                'gid',
                'gname',
                'gdetail',
                'gnormalprice',
                'stock',
                'wow_upd_status',
                'wow_on_flg',
                'wow_gname',
                'wow_gdetail',
                'wow_worn_key',
                'qoo_upd_status',
                'qoo_on_flg',
                'qoo_gname',
                'qoo_gdetail',
                'qoo_worn_key',
            ])
        """
        # データ行は追記
        with open(csvname, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for item in reader:
                writer.writerow([
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    item[5],
                    item[6],
                    item[7],
                    item[8],
                    item[9],
                    item[10],
                    item[11],
                    item[12],
                    item[13],
                    item[14],
                ])

        logger.debug('write_csv out .')
        return


class BuyersGoodsDelete(generic.FormView):
    """
    YaBuyersItemDetailテーブルから指定されたgidの商品を削除、wowmaとqoo10からも削除します
    """
    template_name = 'yaget/buyers_goods_delete.html'
    success_url = reverse_lazy('yaget:buyers_goods_delete_confirm')
    form_class = BuyersGoodsDeleteForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = '一括削除の画面です'
        return ctx

    def form_valid(self, form):
        logger.debug("--- BuyersGoodsDelete in")
        #ctx = {'form': form }
        #ctx['form_name'] = 'yaget'
        ctx = self.get_context_data()
        # 確認画面での処理
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        # csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 指定ディレクトリにcsvでカキコ
        ctx['item_list'] = self._write_csv(reader)
        ctx['message'] = '削除を実行しますよ'

        logger.debug("--- BuyersGoodsDelete confirm out")
        return render(self.request, 'yaget/buyers_goods_delete_confirm.html', ctx)
        #return super().form_valid(form)

        """
        if self.request.POST.get('next', '') == 'confirm':
            # 確認画面での処理
            csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
            # csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
            reader = csv.reader(csvfile)

            # 指定ディレクトリにcsvでカキコ
            ctx['item_list'] = self._write_csv(reader)
            ctx['message'] = '削除を実行しますよ'

            logger.debug("--- BuyersGoodsDelete confirm out")
            return render(self.request, 'yaget/buyers_goods_delete_confirm.html', ctx)

        if self.request.POST.get('next', '') == 'back':
            # 元に戻るだけ
            logger.debug("--- BuyersGoodsDelete back out")
            ctx['message'] = 'ファイルを選択し直してください'
            return render(self.request, 'yaget/buyers_goods_delete.html', ctx)

        if self.request.POST.get('next', '') == 'delete':
            # 確認OKなので削除バッチをたたく
            # 書き込んだらバッチをキック
            mymsg = '削除バッチを実行します・・ '
            cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
            p = subprocess.Popen(cmd, shell=True)
            mymsg += ' 開始しました。 ' + str(p.pid)

            logger.debug("--- BuyersGoodsDelete delete out")
            #return super().form_valid(form)
            ctx['message'] = mymsg
            return render(self.request, 'yaget/buyers_goods_delete.html', ctx)
        else:
            # 正常動作ではここは通らない。エラーページへの遷移でも良い
            logger.debug("--- BuyersGoodsDelete error occurred?")
            return redirect(reverse_lazy('yaget:buyers_goods_delete'))
        """


    # csvにファイル出力。商品idと商品名を辞書にして戻す
    def _write_csv(self, reader):
        logger.debug('write_csv in .')
        # csvはここで用意するか
        csvname = mydeletecsv_dir + 'deletecsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'
        item_list = {}
        # データ行は追記
        with open(csvname, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for item in reader:
                writer.writerow([
                    item[0],  # 商品id
                    item[1],  # 商品名
                ])
                item_list[item[0]] = item[1]

        logger.debug('write_csv out .')
        return item_list

class BuyersGoodsDeleteConfirm(generic.TemplateView):
    #def buyers_goods_delete_confirm(request):
    template_name = 'yaget/buyers_goods_delete_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        """
        # 書き込んだらバッチをキック
        msg = '削除バッチを実行します・・ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 開始しました。 ' + str(p.pid)
        """

        logger.debug("--- BuyersGoodsDelete delete out")
        # return super().form_valid(form)
        context['title'] = '商品削除を開始しますよタイトル'
        context['message'] = '商品削除を開始しますよー'
        return render(self.request, 'yaget/buyers_goods_delete_done.html', context)

        """
        params = {
            'title': '在庫チェック開始します',
            'message': msg,
        }
        return render(self.request, 'yaget/buyers_goods_delete_done.html', params)
        """


def buyers_goods_delete_done(request):
    # サブプロセスでyagetのコマンドをキックする
    if (request.method == 'POST'):
        # 書き込んだらバッチをキック
        msg = '削除バッチを実行します・・ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 開始しました。 ' + str(p.pid)

        logger.debug("--- BuyersGoodsDeleteDone delete out")
        # return super().form_valid(form)
        title = '商品削除を開始しましたタイトル'
        msg = '商品削除を開始しましたわ'
    else:
        title = '商品削除を開始しましたタイトル get'
        msg = ' buyers_goods_delete_done Get呼ばれました。 '

    params = {
        'title': title,
        'message': msg,
    }

    return render(request, 'yaget/buyers_goods_delete_done.html', params)

"""
class BuyersGoodsDeleteDone(generic.TemplateView):
#def buyers_goods_delete_confirm(request):
    template_name = 'yaget/buyers_goods_delete_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 書き込んだらバッチをキック
        msg = '削除バッチを実行します・・ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 開始しました。 ' + str(p.pid)

        logger.debug("--- BuyersGoodsDeleteDone delete out")
        # return super().form_valid(form)
        context['title'] = '商品削除を開始しましたタイトル'
        context['message'] = '商品削除を開始しましたわ'
        return context
"""


class BuyersGoodsDetailDetail(generic.DetailView):
    """
    YaBuyersItemDetailテーブルのレコード詳細
    """
    template_name = 'yaget/buyers_goods_detail_detail.html'
    model = YaBuyersItemDetail

    def get(self, request, *args, **kwargs):
        logger.debug("--- BuyersGoodsDetailDetail gin")
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        logger.debug("--- BuyersGoodsDetailDetail gid:{}".format(self.object.gid))
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '商品詳細です'
        context['message'] = '商品詳細メッセージです'
        return context


class BuyersGoodsDetailAjaxRes(generic.DetailView):
    """
    detailからqoo10更新用に呼ばれる
    """
    template_name = 'yaget/buyers_goods_detail_ajax_res.html'
    model = YaBuyersItemDetail

    def get(self, request, *args, **kwargs):
        logger.debug("--- BuyersGoodsDetailAjaxRes gin")
        # ajax test
        self.object = self.get_object()
        #title = request.POST.get('title')
        #post = str(title) + '_test_received'
        d = {
            'gid': self.object.gid,
            'gname': self.object.gname,
        }
        return JsonResponse(d)


class BuyersGoodsDetailDelete(generic.DeleteView):
    """
    YaBuyersItemDetailテーブルのレコード削除
    """
    template_name = 'yaget/buyers_goods_detail_delete.html'
    model = YaBuyersItemDetail
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- BuyersGoodsDetailDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10のステータスを削除に更新
            # Qoo10にアクセス
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)

            #goods_object = self.get_object()

            self.object.qoo_upd_status = 3  # 取引廃止

            # qoo10から削除
            # まず登録があるかどうか。なかったら処理しない
            ret_obj_list = qoo10obj.qoo10_items_lookup_get_item_detail_info(self.object)
            chk_flg = 0
            for ret_obj in ret_obj_list:
                if ret_obj['res_code'] != "0":
                    logger.debug("--- BuyersGoodsDetailDelete qoo10 商品検索でエラー [{}][{}]".format(ret_obj['res_code'],ret_obj['res_msg'] ))
                    chk_flg = 1  # なにかエラーになってた
            if chk_flg == 0:
                # 商品が見つかったときだけqoo10から削除
                qoo10obj.qoo10_items_basic_edit_goods_status(self.object)
                logger.debug("--- BuyersGoodsDetailDelete qoo10 削除更新 ok")
            else:
                logger.debug("--- BuyersGoodsDetailDelete qoo10 で対象商品が見つからないのでスルー。wowmaの処理に続く")

            # 続けてwowmaから削除
            # まず商品ステータスを変えてから
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 削除更新 ok')
                else:
                    messages.error(
                        self.request, 'wowmaから削除に失敗しました。[{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma で対象商品が見つからないのでスルー。DBから消す")

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '「{}」を削除しました'.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '削除に失敗しました。[{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- BuyersGoodsDetailDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- BuyersGoodsDetailDelete out")
        return result
        #     return render(request, 'hello/delete.html', params)


class BuyersGoodsDetailCreate(generic.CreateView):
    """
    YaBuyersItemDetailテーブルのレコード作成
    """
    template_name = 'yaget/buyers_goods_detail_create.html'
    model = YaBuyersItemDetail
    fields = [
        'gid',
        'glink',
        'ss_url',
        'gsrc',
        'gname',
        'gdetail',
        'gnormalprice',
        'gspprice',
        'gcode',
        'stock',
        'wow_upd_status',
        'wow_on_flg',
        'wow_gname',
        'wow_gdetail',
        'wow_worn_key',
        'wow_price',
        'wow_fixed_price',
        'wow_postage_segment',
        'wow_postage',
        'wow_delivery_method_id',
        'wow_ctid',
        'qoo_upd_status',
        'qoo_on_flg',
        'qoo_gname',
        'qoo_gdetail',
        'qoo_worn_key',
        'qoo_price',
        'qoo_fixed_price',
        'qoo_shipping_no',
        'qoo_postage',
        'qoo_delivery_method_id',
        'qoo_ctid',
        'g_img_src_1',
        'g_img_src_2',
        'g_img_src_3',
        'g_img_src_4',
        'g_img_src_5',
        'g_img_src_6',
        'g_img_src_7',
        'g_img_src_8',
        'g_img_src_9',
        'g_img_src_10',
        'g_img_src_11',
        'g_img_src_12',
        'g_img_src_13',
        'g_img_src_14',
        'g_img_src_15',
        'g_img_src_16',
        'g_img_src_17',
        'g_img_src_18',
        'g_img_src_19',
        'g_img_src_20',
    ]

    def get_success_url(self):
        return reverse('yaget:buyers_goods_detail_detail', kwargs={'pk': self.object.pk})


class BuyersGoodsDetailUpdate(generic.UpdateView):
    template_name = 'yaget/buyers_goods_detail_update.html'
    model = YaBuyersItemDetail
    fields = [
        'gid',
        'glink',
        'ss_url',
        'bu_ctid',
        'gsrc',
        'gname',
        'gdetail',
        'gnormalprice',
        'gspprice',
        'gcode',
        'stock',
        'wow_upd_status',
        'wow_on_flg',
        'wow_gname',
        'wow_gdetail',
        'wow_lotnum',
        'wow_keyword',
        'wow_worn_key',
        'wow_tagid',
        'wow_price',
        'wow_fixed_price',
        'wow_postage_segment',
        'wow_postage',
        'wow_delivery_method_id',
        'wow_ctid',
        'qoo_upd_status',
        'qoo_seller_code',
        'qoo_gdno',
        'qoo_on_flg',
        'qoo_gname',
        'qoo_promotion_name',
        'qoo_model_name',
        'qoo_gdetail',
        'qoo_keyword',
        'qoo_worn_key',
        'qoo_contact_info',
        'qoo_available_date_type',
        'qoo_available_date_value',
        'qoo_item_qty',
        'qoo_standard_img',
        'qoo_video_url',
        'qoo_additional_opt',
        'qoo_item_type',
        'qoo_expire_date',
        'qoo_adult_yn',
        'qoo_price',
        'qoo_fixed_price',
        'qoo_shipping_no',
        'qoo_postage',
        'qoo_delivery_method_id',
        'qoo_item_qty',
        'qoo_ctid',
        'qoo_standard_img',
        'g_img_src_1',
        'g_img_src_2',
        'g_img_src_3',
        'g_img_src_4',
        'g_img_src_5',
        'g_img_src_6',
        'g_img_src_7',
        'g_img_src_8',
        'g_img_src_9',
        'g_img_src_10',
        'g_img_src_11',
        'g_img_src_12',
        'g_img_src_13',
        'g_img_src_14',
        'g_img_src_15',
        'g_img_src_16',
        'g_img_src_17',
        'g_img_src_18',
        'g_img_src_19',
        'g_img_src_20',
    ]

    def get_success_url(self):
        return reverse('yaget:buyers_goods_detail_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '商品詳細 更新ページです'
        context['message'] = '商品詳細 更新ページ メッセージです'
        return context

    def get_form(self):
        form = super(BuyersGoodsDetailUpdate, self).get_form()
        form.fields['gid'].label = '商品ID'
        form.fields['glink'].label = '商品リンク'
        form.fields['ss_url'].label = 'リンク元リストページURL'
        form.fields['bu_ctid'].label = 'バイヤーズカテゴリID'
        form.fields['gsrc'].label = 'サムネイル画像URL'
        form.fields['gname'].label = '商品名'
        form.fields['gdetail'].label = '商品詳細'
        form.fields['wow_lotnum'].label = 'wowmaロット番号'
        form.fields['gnormalprice'].label = '通常価格'
        form.fields['gspprice'].label = '大量発注価格'
        form.fields['gcode'].label = 'バイヤーズ商品コード'
        form.fields['stock'].label = '在庫数'
        form.fields['wow_upd_status'].label = 'wow掲載状況'
        form.fields['wow_on_flg'].label = 'wowmaの出品ステータス'
        form.fields['wow_gname'].label = 'wow商品名'
        form.fields['wow_gdetail'].label = 'wow商品詳細'
        form.fields['wow_worn_key'].label = 'wow要注意キーワード'
        form.fields['wow_price'].label = 'wow価格'
        form.fields['wow_fixed_price'].label = 'wow固定価格'
        form.fields['wow_postage_segment'].label = 'wow送料設定区分'
        form.fields['wow_postage'].label = 'wow個別送料'
        form.fields['wow_delivery_method_id'].label = 'wow配送方法ID'
        form.fields['wow_ctid'].label = 'wowカテゴリID'
        form.fields['qoo_upd_status'].label = 'qoo掲載状況'
        form.fields['qoo_on_flg'].label = 'qooの出品ステータス'
        form.fields['qoo_gname'].label = 'qoo商品名'
        form.fields['qoo_gdetail'].label = 'qoo商品詳細'
        form.fields['qoo_worn_key'].label = 'qoo要注意キーワード'
        form.fields['qoo_price'].label = 'qoo価格'
        form.fields['qoo_fixed_price'].label = 'qoo固定価格'
        form.fields['qoo_shipping_no'].label = 'qoo送料コード'
        form.fields['qoo_postage'].label = 'qoo個別送料'
        form.fields['qoo_delivery_method_id'].label = 'qoo配送方法ID'
        form.fields['qoo_ctid'].label = 'qooカテゴリID'
        form.fields['qoo_item_qty'].label = 'qoo商品数量'
        form.fields['qoo_standard_img'].label = 'qoo商品代表画像URL'
        form.fields['g_img_src_1'].label = '画像URL_1'
        form.fields['g_img_src_2'].label = '画像URL_2'
        form.fields['g_img_src_3'].label = '画像URL_3'
        form.fields['g_img_src_4'].label = '画像URL_4'
        form.fields['g_img_src_5'].label = '画像URL_5'
        form.fields['g_img_src_6'].label = '画像URL_6'
        form.fields['g_img_src_7'].label = '画像URL_7'
        form.fields['g_img_src_8'].label = '画像URL_8'
        form.fields['g_img_src_9'].label = '画像URL_9'
        form.fields['g_img_src_10'].label = '画像URL_10'
        form.fields['g_img_src_11'].label = '画像URL_11'
        form.fields['g_img_src_12'].label = '画像URL_12'
        form.fields['g_img_src_13'].label = '画像URL_13'
        form.fields['g_img_src_14'].label = '画像URL_14'
        form.fields['g_img_src_15'].label = '画像URL_15'
        form.fields['g_img_src_16'].label = '画像URL_16'
        form.fields['g_img_src_17'].label = '画像URL_17'
        form.fields['g_img_src_18'].label = '画像URL_18'
        form.fields['g_img_src_19'].label = '画像URL_19'
        form.fields['g_img_src_20'].label = '画像URL_20'
        return form


class BatchStatusList(generic.ListView):
    """
    BatchStatusテーブルの一覧表作成
    """
    model = BatchStatus
    template_name = 'yaget/batch_status_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_value_batch_status_list = [
            self.request.POST.get('batch_id', None),
            self.request.POST.get('batch_name', None),
            self.request.POST.get('message', None),
            self.request.POST.get('batch_status', None),
            self.request.POST.get('start_date_from', None),
            self.request.POST.get('start_date_to', None),
            self.request.POST.get('end_date_from', None),
            self.request.POST.get('end_date_to', None),
            self.request.POST.get('stop_date_from', None),
            self.request.POST.get('stop_date_to', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_batch_status_list'] = form_value_batch_status_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_batch_status_list' in self.request.session:
            form_value_batch_status_list = self.request.session['form_value_batch_status_list']
            batch_id = form_value_batch_status_list[0]
            batch_name = form_value_batch_status_list[1]
            message = form_value_batch_status_list[2]
            batch_status = form_value_batch_status_list[3]
            start_date_from = form_value_batch_status_list[4]
            start_date_to = form_value_batch_status_list[5]
            end_date_from = form_value_batch_status_list[6]
            end_date_to = form_value_batch_status_list[7]
            stop_date_from = form_value_batch_status_list[8]
            stop_date_to = form_value_batch_status_list[9]
            create_date_from = form_value_batch_status_list[10]
            create_date_to = form_value_batch_status_list[11]
            # 検索条件
            condition_batch_id = Q()
            condition_batch_name = Q()
            condition_message = Q()
            condition_batch_status = Q()
            condition_start_date_from = Q()
            condition_start_date_to = Q()
            condition_end_date_from = Q()
            condition_end_date_to = Q()
            condition_stop_date_from = Q()
            condition_stop_date_to = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(batch_id) != 0 and batch_id[0]:
                condition_batch_id = Q(batch_id__icontains=batch_id)
            if len(batch_name) != 0 and batch_name[0]:
                condition_batch_name = Q(batch_name__icontains=batch_name)
            if len(message) != 0 and message[0]:
                condition_message = Q(message__icontains=message)
            if len(batch_status) != 0 and batch_status[0]:
                condition_batch_status = Q(batch_status__icontains=batch_status)
            if len(start_date_from) != 0 and start_date_from[0]:
                condition_start_date_from = Q(start_date_from__gte=start_date_from)
            if len(start_date_to) != 0 and start_date_to[0]:
                condition_start_date_to = Q(start_date__lte=start_date_to)
            if len(end_date_from) != 0 and end_date_from[0]:
                condition_end_date_from = Q(end_date_from__gte=end_date_from)
            if len(end_date_to) != 0 and end_date_to[0]:
                condition_end_date_to = Q(end_date__lte=end_date_to)
            if len(stop_date_from) != 0 and stop_date_from[0]:
                condition_stop_date_from = Q(stop_date_from__gte=stop_date_from)
            if len(stop_date_to) != 0 and stop_date_to[0]:
                condition_stop_date_to = Q(stop_date__lte=stop_date_to)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return BatchStatus.objects.select_related().filter(
                condition_batch_id &
                condition_batch_name &
                condition_message &
                condition_batch_status &
                condition_start_date_from &
                condition_start_date_to &
                condition_end_date_from &
                condition_end_date_to &
                condition_stop_date_from &
                condition_stop_date_to &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return BatchStatus.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        batch_id = ''
        batch_name = ''
        message = ''
        batch_status = ''
        start_date_from = ''
        start_date_to = ''
        end_date_from = ''
        end_date_to = ''
        stop_date_from = ''
        stop_date_to = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_batch_status_list' in self.request.session:
            form_value_batch_status_list = self.request.session['form_value_batch_status_list']
            batch_id = form_value_batch_status_list[0]
            batch_name = form_value_batch_status_list[1]
            message = form_value_batch_status_list[2]
            batch_status = form_value_batch_status_list[3]
            start_date_from = form_value_batch_status_list[4]
            start_date_to = form_value_batch_status_list[5]
            end_date_from = form_value_batch_status_list[6]
            end_date_to = form_value_batch_status_list[7]
            stop_date_from = form_value_batch_status_list[8]
            stop_date_to = form_value_batch_status_list[9]
            create_date_from = form_value_batch_status_list[10]
            create_date_to = form_value_batch_status_list[11]
        default_data = {
                    'batch_id': batch_id, # batch_id
                    'batch_name': batch_name, # batch_name
                    'message': message, # message
                    'batch_status': batch_status, # batch_status
                    'start_date_from': start_date_from,
                    'start_date_to': start_date_to,
                    'end_date_from': end_date_from,
                    'end_date_to': end_date_to,
                    'stop_date_from': stop_date_from,
                    'stop_date_to': stop_date_to,
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = BatchStatusSearchForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class BatchStatusDetail(generic.DetailView):
    """
    BatchStatusテーブルのレコード詳細
    """
    template_name = 'yaget/batch_status_detail.html'
    model = BatchStatus

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'バッチ実行状況の詳細です'
        context['message'] = 'バッチ実行状況の詳細(メッセージ)です'
        return self.render_to_response(context)


class BatchStatusDelete(generic.DeleteView):
    """
    BatchStatusのレコード削除
    """
    template_name = 'yaget/batch_status_delete.html'
    model = BatchStatus
    success_url = reverse_lazy('yaget:batch_status_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class BlackListList(generic.ListView):
    """
    YaBuyersItemBlackListテーブルの一覧表作成
    """
    model = YaBuyersItemBlackList
    template_name = 'yaget/black_list_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_value_black_list_list = [
            self.request.POST.get('gid', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_black_list_list'] = form_value_black_list_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_black_list_list' in self.request.session:
            form_value_black_list_list = self.request.session['form_value_black_list_list']
            gid = form_value_black_list_list[0]
            create_date_from = form_value_black_list_list[1]
            create_date_to = form_value_black_list_list[2]
            # 検索条件
            condition_gid = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(gid) != 0 and gid[0]:
                condition_gid = Q(gid__icontains=gid)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return YaBuyersItemBlackList.objects.select_related().filter(
                condition_gid &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return YaBuyersItemBlackList.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        gid = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_black_list_list' in self.request.session:
            form_value_black_list_list = self.request.session['form_value_black_list_list']
            gid = form_value_black_list_list[0]
            create_date_from = form_value_black_list_list[1]
            create_date_to = form_value_black_list_list[2]
        default_data = {
                    'gid': gid, # gid
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = BlackListForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class BlackListDetail(generic.DetailView):
    """
    YaBuyersItemBlackListテーブルのレコード詳細
    """
    template_name = 'yaget/black_list_detail.html'
    model = YaBuyersItemBlackList

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'バッチ実行状況の詳細です'
        return self.render_to_response(context)


class BlackListDelete(generic.DeleteView):
    """
    YaBuyersItemBlackListのレコード削除
    """
    template_name = 'yaget/black_list_delete.html'
    model = YaBuyersItemBlackList
    success_url = reverse_lazy('yaget:black_list_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class BlackListCreate(generic.CreateView):
    template_name = 'yaget/black_list_create.html'
    model = YaBuyersItemBlackList
    fields = ['gid']

    def get_success_url(self):
        return reverse('yaget:black_list_list')

    def get_form(self):
        form = super(BlackListCreate, self).get_form()
        form.fields['gid'].label = 'バイヤーズの商品id'
        form.fields['gid'].required = True
        return form


class WowmaCatList(generic.ListView):
    """
    WowCategoryテーブルの一覧表作成
    """
    model = WowCategory
    template_name = 'yaget/wowma_cat_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_value_wowma_cat_list = [
            self.request.POST.get('product_cat_id', None),
            self.request.POST.get('product_cat_name', None),
            self.request.POST.get('level_1_cat_name', None),
            self.request.POST.get('level_2_cat_name', None),
            self.request.POST.get('level_3_cat_name', None),
            self.request.POST.get('level_4_cat_name', None),
            self.request.POST.get('ama_level_1_cat_id', None),
            self.request.POST.get('ama_level_2_cat_id', None),
            self.request.POST.get('ama_level_3_cat_id', None),
            self.request.POST.get('ama_level_1_cat_name', None),
            self.request.POST.get('ama_level_2_cat_name', None),
            self.request.POST.get('ama_level_3_cat_name', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_wowma_cat_list'] = form_value_wowma_cat_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return WowmaCatList.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_wowma_cat_list' in self.request.session:
            form_value_wowma_cat_list = self.request.session['form_value_wowma_cat_list']
            product_cat_id = form_value_wowma_cat_list[0]
            product_cat_name = form_value_wowma_cat_list[1]
            level_1_cat_name = form_value_wowma_cat_list[2]
            level_2_cat_name = form_value_wowma_cat_list[3]
            level_3_cat_name = form_value_wowma_cat_list[4]
            level_4_cat_name = form_value_wowma_cat_list[5]
            ama_level_1_cat_id = form_value_wowma_cat_list[6]
            ama_level_2_cat_id = form_value_wowma_cat_list[7]
            ama_level_3_cat_id = form_value_wowma_cat_list[8]
            ama_level_1_cat_name = form_value_wowma_cat_list[9]
            ama_level_2_cat_name = form_value_wowma_cat_list[10]
            ama_level_3_cat_name = form_value_wowma_cat_list[11]
            create_date_from = form_value_wowma_cat_list[12]
            create_date_to = form_value_wowma_cat_list[13]
            # 検索条件
            condition_p_cat_id = Q()
            condition_p_cat_name = Q()
            condition_level_1_cat_name = Q()
            condition_level_2_cat_name = Q()
            condition_level_3_cat_name = Q()
            condition_level_4_cat_name = Q()
            condition_ama_1_cat_id = Q()
            condition_ama_2_cat_id = Q()
            condition_ama_3_cat_id = Q()
            condition_ama_1_cat_name = Q()
            condition_ama_2_cat_name = Q()
            condition_ama_3_cat_name = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if product_cat_id is not None:
                if len(product_cat_id) != 0 and product_cat_id[0]:
                    condition_p_cat_id = Q(product_cat_id__icontains=product_cat_id)
            if product_cat_name is not None:
                if len(product_cat_name) != 0 and product_cat_name[0]:
                    condition_p_cat_name = Q(product_cat_name__icontains=product_cat_name)
            if level_1_cat_name is not None:
                if len(level_1_cat_name) != 0 and level_1_cat_name[0]:
                    condition_level_1_cat_name = Q(level_1_cat_name__icontains=level_1_cat_name)
            if level_2_cat_name is not None:
                if len(level_2_cat_name) != 0 and level_2_cat_name[0]:
                    condition_level_2_cat_name = Q(level_2_cat_name__icontains=level_2_cat_name)
            if level_3_cat_name is not None:
                if len(level_3_cat_name) != 0 and level_3_cat_name[0]:
                    condition_level_3_cat_name = Q(level_3_cat_name__icontains=level_3_cat_name)
            if level_4_cat_name is not None:
                if len(level_4_cat_name) != 0 and level_4_cat_name[0]:
                    condition_level_4_cat_name = Q(level_4_cat_name__icontains=level_4_cat_name)
            if ama_level_1_cat_id is not None:
                if len(ama_level_1_cat_id) != 0 and ama_level_1_cat_id[0]:
                    condition_ama_1_cat_id = Q(ama_level_1_cat_id__icontains=ama_level_1_cat_id)
            if ama_level_2_cat_id is not None:
                if len(ama_level_2_cat_id) != 0 and ama_level_2_cat_id[0]:
                    condition_ama_2_cat_id = Q(ama_level_2_cat_id__icontains=ama_level_2_cat_id)
            if ama_level_3_cat_id is not None:
                if len(ama_level_3_cat_id) != 0 and ama_level_3_cat_id[0]:
                    condition_ama_3_cat_id = Q(ama_level_3_cat_id__icontains=ama_level_3_cat_id)
            if ama_level_1_cat_name is not None:
                if len(ama_level_1_cat_name) != 0 and ama_level_1_cat_name[0]:
                    condition_ama_1_cat_name = Q(ama_level_1_cat_name__icontains=ama_level_1_cat_name)
            if ama_level_2_cat_name is not None:
                if len(ama_level_2_cat_name) != 0 and ama_level_2_cat_name[0]:
                    condition_ama_2_cat_name = Q(ama_level_2_cat_name__icontains=ama_level_2_cat_name)
            if ama_level_3_cat_name is not None:
                if len(ama_level_3_cat_name) != 0 and ama_level_3_cat_name[0]:
                    condition_ama_3_cat_name = Q(ama_level_3_cat_name__icontains=ama_level_3_cat_name)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return WowCategory.objects.select_related().filter(
                condition_p_cat_id &
                condition_p_cat_name &
                condition_level_1_cat_name &
                condition_level_2_cat_name &
                condition_level_3_cat_name &
                condition_level_4_cat_name &
                condition_ama_1_cat_id &
                condition_ama_2_cat_id &
                condition_ama_3_cat_id &
                condition_ama_1_cat_name &
                condition_ama_2_cat_name &
                condition_ama_3_cat_name &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            #return WowCategory.objects.none()
            return WowCategory.objects.select_related().order_by("-update_date")[:10000]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product_cat_id = 0
        product_cat_name = ''
        level_1_cat_name = ''
        level_2_cat_name = ''
        level_3_cat_name = ''
        level_4_cat_name = ''
        ama_level_1_cat_id = 0
        ama_level_2_cat_id = 0
        ama_level_3_cat_id = 0
        ama_level_1_cat_name = ''
        ama_level_2_cat_name = ''
        ama_level_3_cat_name = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_wowma_cat_list' in self.request.session:
            form_value_wowma_cat_list = self.request.session['form_value_wowma_cat_list']
            product_cat_id = form_value_wowma_cat_list[0]
            product_cat_name = form_value_wowma_cat_list[1]
            level_1_cat_name = form_value_wowma_cat_list[2]
            level_2_cat_name = form_value_wowma_cat_list[3]
            level_3_cat_name = form_value_wowma_cat_list[4]
            level_4_cat_name = form_value_wowma_cat_list[5]
            ama_level_1_cat_id = form_value_wowma_cat_list[6]
            ama_level_2_cat_id = form_value_wowma_cat_list[7]
            ama_level_3_cat_id = form_value_wowma_cat_list[8]
            ama_level_1_cat_name = form_value_wowma_cat_list[9]
            ama_level_2_cat_name = form_value_wowma_cat_list[10]
            ama_level_3_cat_name = form_value_wowma_cat_list[11]
            create_date_from = form_value_wowma_cat_list[12]
            create_date_to = form_value_wowma_cat_list[13]
        default_data = {
                    'product_cat_id': product_cat_id, # product_cat_id
                    'product_cat_name': product_cat_name, # p_cat_name
                    'level_1_cat_name': level_1_cat_name, # level_1_cat_name
                    'level_2_cat_name': level_2_cat_name, # level_2_cat_name
                    'level_3_cat_name': level_3_cat_name, # level_3_cat_name
                    'level_4_cat_name': level_4_cat_name, # level_4_cat_name
                    'ama_level_1_cat_id': ama_level_1_cat_id, # ama_level_1_cat_id
                    'ama_level_2_cat_id': ama_level_2_cat_id, # ama_level_2_cat_id
                    'ama_level_3_cat_id': ama_level_3_cat_id, # ama_level_3_cat_id
                    'ama_level_1_cat_name': ama_level_1_cat_name, # ama_level_1_cat_name
                    'ama_level_2_cat_name': ama_level_2_cat_name, # ama_level_2_cat_name
                    'ama_level_3_cat_name': ama_level_3_cat_name, # ama_level_3_cat_name
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = WowCategoryForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx

class WowmaCatDetail(generic.DetailView):
    """
    WowmaCatListテーブルのレコード詳細
    """
    template_name = 'yaget/wowma_cat_detail.html'
    model = WowCategory

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'wowmaカテゴリの詳細です'
        return self.render_to_response(context)

class WowmaCatUpdate(generic.UpdateView):
    template_name = 'yaget/wowma_cat_update.html'
    model = WowCategory
    fields = [
        'product_cat_id',
        'product_cat_name',
        'level_1_cat_name',
        'level_2_cat_name',
        'level_3_cat_name',
        'level_4_cat_name',
        'ama_level_1_cat_id',
        'ama_level_2_cat_id',
        'ama_level_3_cat_id',
        'ama_level_1_cat_name',
        'ama_level_2_cat_name',
        'ama_level_3_cat_name',
        'create_date',
    ]

    def get_success_url(self):
        return reverse('yaget:wowma_cat_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(WowmaCatUpdate, self).get_form()
        form.fields['product_cat_id'].label = 'product_cat_id'
        form.fields['product_cat_name'].label = 'product_cat_name'
        form.fields['level_1_cat_name'].label = 'level_1_cat_name'
        form.fields['level_2_cat_name'].label = 'level_2_cat_name'
        form.fields['level_3_cat_name'].label = 'level_3_cat_name'
        form.fields['level_4_cat_name'].label = 'level_4_cat_name'
        form.fields['ama_level_1_cat_id'].label = 'ama_level_1_cat_id'
        form.fields['ama_level_2_cat_id'].label = 'ama_level_2_cat_id'
        form.fields['ama_level_3_cat_id'].label = 'ama_level_3_cat_id'
        form.fields['ama_level_1_cat_name'].label = 'ama_level_1_cat_name'
        form.fields['ama_level_2_cat_name'].label = 'ama_level_2_cat_name'
        form.fields['ama_level_3_cat_name'].label = 'ama_level_3_cat_name'
        form.fields['create_date'].label = '登録日'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowmaカテゴリ情報 更新ページです'
        context['message'] = 'Wowmaカテゴリ情報 更新ページ メッセージです'
        return context


class WowmaCatModelList(generic.ListView):
    """
    WowCategoryテーブルの一覧表作成
    ここ参考に。
    https://blog.narito.ninja/detail/30/
    クラスビューを使うならこっちか
    https://k2ss.info/archives/2653/
    """
    model = WowCategory
    template_name = 'yaget/wowma_cat_model_list.html'
    paginate_by = 50
    form_class = WowCategoryModelForm

    def get_formset(self, *args, **kwargs):
        """ 自身に設定されたモデルとフォームからフォームセットを作成する """
        formset = modelformset_factory(self.model, form=self.form_class, extra=0)
        return formset(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # ListView が context を作れるように
        self.object_list = self.get_queryset()
        base_ctx = super().get_context_data()
        page_qs = base_ctx['page_obj'].object_list if base_ctx.get('page_obj') else base_ctx['object_list']

        FormSet = modelformset_factory(self.model, form=self.form_class, extra=0)
        formset = FormSet(request.POST, queryset=page_qs)

        # 画面上の検索条件をセッションへ（今の実装を維持）
        form_value_wowma_cat_list = [
            request.POST.get('product_cat_id'),
            request.POST.get('product_cat_name'),
            request.POST.get('level_1_cat_name'),
            request.POST.get('level_2_cat_name'),
            request.POST.get('level_3_cat_name'),
            request.POST.get('level_4_cat_name'),
            request.POST.get('ama_level_1_cat_id'),
            request.POST.get('ama_level_2_cat_id'),
            request.POST.get('ama_level_3_cat_id'),
            request.POST.get('ama_level_1_cat_name'),
            request.POST.get('ama_level_2_cat_name'),
            request.POST.get('ama_level_3_cat_name'),
            request.POST.get('create_date_from'),
            request.POST.get('create_date_to'),
        ]
        request.session['form_value_wowma_cat_list'] = form_value_wowma_cat_list

        if formset.is_valid():
            formset.save()
            # クエリ文字列を維持してリロード
            qs = ('?' + request.META.get('QUERY_STRING')) if request.META.get('QUERY_STRING') else ''
            return redirect(request.path + qs)

        # invalid のときはエラーを含めて再描画
        ctx = self.get_context_data(formset=formset)
        return self.render_to_response(ctx)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return WowmaCatList.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_wowma_cat_list' in self.request.session:
            form_value_wowma_cat_list = self.request.session['form_value_wowma_cat_list']
            product_cat_id = form_value_wowma_cat_list[0]
            product_cat_name = form_value_wowma_cat_list[1]
            level_1_cat_name = form_value_wowma_cat_list[2]
            level_2_cat_name = form_value_wowma_cat_list[3]
            level_3_cat_name = form_value_wowma_cat_list[4]
            level_4_cat_name = form_value_wowma_cat_list[5]
            ama_level_1_cat_id = form_value_wowma_cat_list[6]
            ama_level_2_cat_id = form_value_wowma_cat_list[7]
            ama_level_3_cat_id = form_value_wowma_cat_list[8]
            ama_level_1_cat_name = form_value_wowma_cat_list[9]
            ama_level_2_cat_name = form_value_wowma_cat_list[10]
            ama_level_3_cat_name = form_value_wowma_cat_list[11]
            create_date_from = form_value_wowma_cat_list[12]
            create_date_to = form_value_wowma_cat_list[13]
            # 検索条件
            condition_p_cat_id = Q()
            condition_p_cat_name = Q()
            condition_level_1_cat_name = Q()
            condition_level_2_cat_name = Q()
            condition_level_3_cat_name = Q()
            condition_level_4_cat_name = Q()
            condition_ama_1_cat_id = Q()
            condition_ama_2_cat_id = Q()
            condition_ama_3_cat_id = Q()
            condition_ama_1_cat_name = Q()
            condition_ama_2_cat_name = Q()
            condition_ama_3_cat_name = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if product_cat_id is not None:
                if len(product_cat_id) != 0 and product_cat_id[0]:
                    condition_p_cat_id = Q(product_cat_id__icontains=product_cat_id)
            if product_cat_name is not None:
                if len(product_cat_name) != 0 and product_cat_name[0]:
                    condition_p_cat_name = Q(product_cat_name__icontains=product_cat_name)
            if level_1_cat_name is not None:
                if len(level_1_cat_name) != 0 and level_1_cat_name[0]:
                    condition_level_1_cat_name = Q(level_1_cat_name__icontains=level_1_cat_name)
            if level_2_cat_name is not None:
                if len(level_2_cat_name) != 0 and level_2_cat_name[0]:
                    condition_level_2_cat_name = Q(level_2_cat_name__icontains=level_2_cat_name)
            if level_3_cat_name is not None:
                if len(level_3_cat_name) != 0 and level_3_cat_name[0]:
                    condition_level_3_cat_name = Q(level_3_cat_name__icontains=level_3_cat_name)
            if level_4_cat_name is not None:
                if len(level_4_cat_name) != 0 and level_4_cat_name[0]:
                    condition_level_4_cat_name = Q(level_4_cat_name__icontains=level_4_cat_name)
            if ama_level_1_cat_id is not None:
                if len(ama_level_1_cat_id) != 0 and ama_level_1_cat_id[0]:
                    condition_ama_1_cat_id = Q(ama_level_1_cat_id__icontains=ama_level_1_cat_id)
            if ama_level_2_cat_id is not None:
                if len(ama_level_2_cat_id) != 0 and ama_level_2_cat_id[0]:
                    condition_ama_2_cat_id = Q(ama_level_2_cat_id__icontains=ama_level_2_cat_id)
            if ama_level_3_cat_id is not None:
                if len(ama_level_3_cat_id) != 0 and ama_level_3_cat_id[0]:
                    condition_ama_3_cat_id = Q(ama_level_3_cat_id__icontains=ama_level_3_cat_id)
            if ama_level_1_cat_name is not None:
                if len(ama_level_1_cat_name) != 0 and ama_level_1_cat_name[0]:
                    condition_ama_1_cat_name = Q(ama_level_1_cat_name__icontains=ama_level_1_cat_name)
            if ama_level_2_cat_name is not None:
                if len(ama_level_2_cat_name) != 0 and ama_level_2_cat_name[0]:
                    condition_ama_2_cat_name = Q(ama_level_2_cat_name__icontains=ama_level_2_cat_name)
            if ama_level_3_cat_name is not None:
                if len(ama_level_3_cat_name) != 0 and ama_level_3_cat_name[0]:
                    condition_ama_3_cat_name = Q(ama_level_3_cat_name__icontains=ama_level_3_cat_name)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return WowCategory.objects.select_related().filter(
                condition_p_cat_id &
                condition_p_cat_name &
                condition_level_1_cat_name &
                condition_level_2_cat_name &
                condition_level_3_cat_name &
                condition_level_4_cat_name &
                condition_ama_1_cat_id &
                condition_ama_2_cat_id &
                condition_ama_3_cat_id &
                condition_ama_1_cat_name &
                condition_ama_2_cat_name &
                condition_ama_3_cat_name &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            #return WowCategory.objects.none()
            return WowCategory.objects.select_related().order_by("-update_date")[:200]

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # ページに表示している分だけ formset を作る
        page_qs = ctx['page_obj'].object_list if ctx.get('page_obj') else ctx['object_list']
        FormSet = modelformset_factory(self.model, form=self.form_class, extra=0)

        if 'formset' in kwargs and kwargs['formset'] is not None:
            ctx['formset'] = kwargs['formset']
        else:
            ctx['formset'] = FormSet(queryset=page_qs)
        
        product_cat_id = 0
        product_cat_name = ''
        level_1_cat_name = ''
        level_2_cat_name = ''
        level_3_cat_name = ''
        level_4_cat_name = ''
        ama_level_1_cat_id = 0
        ama_level_2_cat_id = 0
        ama_level_3_cat_id = 0
        ama_level_1_cat_name = ''
        ama_level_2_cat_name = ''
        ama_level_3_cat_name = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_wowma_cat_list' in self.request.session:
            form_value_wowma_cat_list = self.request.session['form_value_wowma_cat_list']
            product_cat_id = form_value_wowma_cat_list[0]
            product_cat_name = form_value_wowma_cat_list[1]
            level_1_cat_name = form_value_wowma_cat_list[2]
            level_2_cat_name = form_value_wowma_cat_list[3]
            level_3_cat_name = form_value_wowma_cat_list[4]
            level_4_cat_name = form_value_wowma_cat_list[5]
            ama_level_1_cat_id = form_value_wowma_cat_list[6]
            ama_level_2_cat_id = form_value_wowma_cat_list[7]
            ama_level_3_cat_id = form_value_wowma_cat_list[8]
            ama_level_1_cat_name = form_value_wowma_cat_list[9]
            ama_level_2_cat_name = form_value_wowma_cat_list[10]
            ama_level_3_cat_name = form_value_wowma_cat_list[11]
            create_date_from = form_value_wowma_cat_list[12]
            create_date_to = form_value_wowma_cat_list[13]
        default_data = {
                    'product_cat_id': product_cat_id, # product_cat_id
                    'product_cat_name': product_cat_name, # p_cat_name
                    'level_1_cat_name': level_1_cat_name, # level_1_cat_name
                    'level_2_cat_name': level_2_cat_name, # level_2_cat_name
                    'level_3_cat_name': level_3_cat_name, # level_3_cat_name
                    'level_4_cat_name': level_4_cat_name, # level_4_cat_name
                    'ama_level_1_cat_id': ama_level_1_cat_id, # ama_level_1_cat_id
                    'ama_level_2_cat_id': ama_level_2_cat_id, # ama_level_2_cat_id
                    'ama_level_3_cat_id': ama_level_3_cat_id, # ama_level_3_cat_id
                    'ama_level_1_cat_name': ama_level_1_cat_name, # ama_level_1_cat_name
                    'ama_level_2_cat_name': ama_level_2_cat_name, # ama_level_2_cat_name
                    'ama_level_3_cat_name': ama_level_3_cat_name, # ama_level_3_cat_name
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = WowCategoryForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class QooShopInfoList(generic.ListView):
    """
    QooShopInfoテーブルの一覧表作成
    """
    model = QooShopInfo
    template_name = 'yaget/qoo_shop_info_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_qoo_shop_info_list = [
            self.request.POST.get('my_shop_num', None),
            self.request.POST.get('shop_name', None),
            self.request.POST.get('user_id', None),
            self.request.POST.get('shop_status', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_qoo_shop_info_list'] = form_qoo_shop_info_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_qoo_shop_info_list' in self.request.session:
            form_qoo_shop_info_list = self.request.session['form_qoo_shop_info_list']
            my_shop_num = form_qoo_shop_info_list[0]
            shop_name = form_qoo_shop_info_list[1]
            user_id = form_qoo_shop_info_list[2]
            shop_status = form_qoo_shop_info_list[3]
            create_date_from = form_qoo_shop_info_list[4]
            create_date_to = form_qoo_shop_info_list[5]
            # 検索条件
            condition_my_shop_num = Q()
            condition_shop_name = Q()
            condition_user_id = Q()
            condition_shop_status = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(my_shop_num) != 0 and my_shop_num[0]:
                condition_my_shop_num = Q(my_shop_num__icontains=my_shop_num)
            if len(shop_name) != 0 and shop_name[0]:
                condition_shop_name = Q(shop_name__icontains=shop_name)
            if len(user_id) != 0 and user_id[0]:
                condition_user_id = Q(user_id__icontains=user_id)
            if len(shop_status) != 0 and shop_status[0]:
                condition_shop_status = Q(shop_status__icontains=shop_status)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return QooShopInfo.objects.select_related().filter(
                condition_my_shop_num &
                condition_shop_name &
                condition_user_id &
                condition_shop_status &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return QooShopInfo.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        my_shop_num = ''
        shop_name = ''
        user_id = ''
        shop_status = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_qoo_shop_info_list' in self.request.session:
            form_qoo_shop_info_list = self.request.session['form_qoo_shop_info_list']
            my_shop_num = form_qoo_shop_info_list[0]
            shop_name = form_qoo_shop_info_list[1]
            user_id = form_qoo_shop_info_list[2]
            shop_status = form_qoo_shop_info_list[3]
            create_date_from = form_qoo_shop_info_list[4]
            create_date_to = form_qoo_shop_info_list[5]
        default_data = {
                    'my_shop_num': my_shop_num, # my_shop_num
                    'shop_name': shop_name, # shop_name
                    'user_id': user_id, # user_id
                    'shop_status': shop_status, # shop_status
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = QooShopInfoForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'QooShopInfoテーブルの一覧'
        return ctx


class QooShopInfoDetail(generic.DetailView):
    """
    QooShopInfoテーブルのレコード詳細
    """
    template_name = 'yaget/qoo_shop_info_detail.html'
    model = QooShopInfo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'Qooショップ情報の詳細です'
        context['message'] = 'QooShopInfoテーブルの詳細'
        return self.render_to_response(context)


class QooShopInfoDelete(generic.DeleteView):
    """
    QooShopInfoのレコード削除
    """
    template_name = 'yaget/qoo_shop_info_delete.html'
    model = QooShopInfo
    success_url = reverse_lazy('yaget:qoo_shop_info_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class QooShopInfoCreate(generic.CreateView):
    template_name = 'yaget/qoo_shop_info_create.html'
    model = QooShopInfo
    fields = [
        'my_shop_num',
        'shop_name',
        'auth_key',
        'user_id',
        'pwd',
        'target_url',
        'from_name',
        'from_postcode',
        'from_state',
        'from_address_1',
        'from_address_2',
        'from_phone',
        'shop_status',
    ]

    def get_success_url(self):
        return reverse('yaget:qoo_shop_info_list')
        #return reverse('yaget:qoo_shop_info_list', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(QooShopInfoCreate, self).get_form()
        form.fields['my_shop_num'].label = 'qoo10のショップ登録情報 id'
        form.fields['my_shop_num'].required = True
        return form


class QooShopInfoUpdate(generic.UpdateView):
    template_name = 'yaget/qoo_shop_info_update.html'
    model = QooShopInfo
    fields = [
        'my_shop_num',
        'shop_name',
        'auth_key',
        'user_id',
        'pwd',
        'target_url',
        'from_name',
        'from_postcode',
        'from_state',
        'from_address_1',
        'from_address_2',
        'from_phone',
        'shop_status',
        'create_date',
    ]

    def get_success_url(self):
        return reverse('yaget:qoo_shop_info_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(QooShopInfoUpdate, self).get_form()
        form.fields['my_shop_num'].label = 'ショップ番号'
        form.fields['shop_name'].label = 'ショップ名'
        form.fields['auth_key'].label = 'auth_key'
        form.fields['user_id'].label = 'ユーザID'
        form.fields['pwd'].label = 'パスワード'
        form.fields['target_url'].label = '販売URL'
        form.fields['from_name'].label = '発送元　送り主名'
        form.fields['from_postcode'].label = '発送元　郵便番号'
        form.fields['from_state'].label = '発送元　都道府県'
        form.fields['from_address_1'].label = '発送元　住所１'
        form.fields['from_address_2'].label = '発送元　住所２'
        form.fields['from_phone'].label = '発送元　電話番号'
        form.fields['shop_status'].label = 'ステータス'
        form.fields['create_date'].label = '登録日'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Qoo10ショップ情報 更新ページです'
        context['message'] = 'Qoo10ショップ情報 更新ページ メッセージです'
        return context


class WowShopInfoList(generic.ListView):
    """
    WowmaShopInfoテーブルの一覧表作成
    """
    model = WowmaShopInfo
    template_name = 'yaget/wow_shop_info_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_wow_shop_info_list = [
            self.request.POST.get('my_shop_num', None),
            self.request.POST.get('shop_name', None),
            self.request.POST.get('shop_id', None),
            self.request.POST.get('shop_status', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_wow_shop_info_list'] = form_wow_shop_info_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_wow_shop_info_list' in self.request.session:
            form_wow_shop_info_list = self.request.session['form_wow_shop_info_list']
            my_shop_num = form_wow_shop_info_list[0]
            shop_name = form_wow_shop_info_list[1]
            shop_id = form_wow_shop_info_list[2]
            shop_status = form_wow_shop_info_list[3]
            create_date_from = form_wow_shop_info_list[4]
            create_date_to = form_wow_shop_info_list[5]
            # 検索条件
            condition_my_shop_num = Q()
            condition_shop_name = Q()
            condition_shop_id = Q()
            condition_shop_status = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(my_shop_num) != 0 and my_shop_num[0]:
                condition_my_shop_num = Q(my_shop_num__icontains=my_shop_num)
            if len(shop_name) != 0 and shop_name[0]:
                condition_shop_name = Q(shop_name__icontains=shop_name)
            if len(shop_id) != 0 and shop_id[0]:
                condition_shop_id = Q(shop_id__icontains=shop_id)
            if len(shop_status) != 0 and shop_status[0]:
                condition_shop_status = Q(shop_status__icontains=shop_status)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return WowmaShopInfo.objects.select_related().filter(
                condition_my_shop_num &
                condition_shop_name &
                condition_shop_id &
                condition_shop_status &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return WowmaShopInfo.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        my_shop_num = ''
        shop_name = ''
        shop_id = ''
        shop_status = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_wow_shop_info_list' in self.request.session:
            form_wow_shop_info_list = self.request.session['form_wow_shop_info_list']
            my_shop_num = form_wow_shop_info_list[0]
            shop_name = form_wow_shop_info_list[1]
            shop_id = form_wow_shop_info_list[2]
            shop_status = form_wow_shop_info_list[3]
            create_date_from = form_wow_shop_info_list[4]
            create_date_to = form_wow_shop_info_list[5]
        default_data = {
                    'my_shop_num': my_shop_num, # my_shop_num
                    'shop_name': shop_name, # shop_name
                    'shop_id': shop_id, # shop_id
                    'shop_status': shop_status, # shop_status
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = WowShopInfoForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'WowShopInfoテーブルの一覧'
        return ctx


class WowShopInfoDetail(generic.DetailView):
    """
    WowmaShopInfoテーブルのレコード詳細
    """
    template_name = 'yaget/wow_shop_info_detail.html'
    model = WowmaShopInfo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'Wowmaショップ情報の詳細です'
        context['message'] = 'WowShopInfoテーブルの一覧'
        return self.render_to_response(context)


class WowShopInfoDelete(generic.DeleteView):
    """
    WowmaShopInfoのレコード削除
    """
    template_name = 'yaget/wow_shop_info_delete.html'
    model = WowmaShopInfo
    success_url = reverse_lazy('yaget:wow_shop_info_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class WowShopInfoCreate(generic.CreateView):
    template_name = 'yaget/wow_shop_info_create.html'
    model = WowmaShopInfo
    fields = [
        'my_shop_num',
        'shop_id',
        'shop_name',
        'api_key',
        'target_url',
        'from_name',
        'from_postcode',
        'from_state',
        'from_address_1',
        'from_address_2',
        'from_phone',
        'shop_status',
    ]

    def get_success_url(self):
        return reverse('yaget:wow_shop_info_list')
        #return reverse('yaget:wow_shop_info_list', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(WowShopInfoCreate, self).get_form()
        form.fields['my_shop_num'].label = 'wowmaのショップ登録情報 id'
        form.fields['my_shop_num'].required = True
        return form


class WowShopInfoUpdate(generic.UpdateView):
    template_name = 'yaget/wow_shop_info_update.html'
    model = WowmaShopInfo
    fields = [
        'my_shop_num',
        'shop_id',
        'shop_name',
        'api_key',
        'target_url',
        'from_name',
        'from_postcode',
        'from_state',
        'from_address_1',
        'from_address_2',
        'from_phone',
        'shop_status',
        'create_date',
    ]

    def get_success_url(self):
        return reverse('yaget:wow_shop_info_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(WowShopInfoUpdate, self).get_form()
        form.fields['my_shop_num'].label = 'ショップ番号'
        form.fields['shop_id'].label = 'ショップID'
        form.fields['shop_name'].label = 'ショップ名'
        form.fields['api_key'].label = 'api_key'
        form.fields['target_url'].label = '販売URL'
        form.fields['from_name'].label = '発送元　送り主名'
        form.fields['from_postcode'].label = '発送元　郵便番号'
        form.fields['from_state'].label = '発送元　都道府県'
        form.fields['from_address_1'].label = '発送元　住所１'
        form.fields['from_address_2'].label = '発送元　住所２'
        form.fields['from_phone'].label = '発送元　電話番号'
        form.fields['shop_status'].label = 'ステータス'
        form.fields['create_date'].label = '登録日'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowmaショップ情報 更新ページです'
        context['message'] = 'Wowmaショップ情報 更新ページ メッセージです'
        return context


class ErrorGoodsLogList(generic.ListView):
    """
    ErrorGoodsLogテーブルの一覧表作成
    """
    model = ErrorGoodsLog
    template_name = 'yaget/error_goods_log_list.html'
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        form_value_error_goods_log_list = [
            self.request.POST.get('id', None),
            self.request.POST.get('batch_name', None),
            self.request.POST.get('gid', None),
            self.request.POST.get('status', None),
            self.request.POST.get('code', None),
            self.request.POST.get('message', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_error_goods_log_list'] = form_value_error_goods_log_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。
        #if 'form_value_error_goods_log_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_error_goods_log_list' in self.request.session:
            form_value_error_goods_log_list = self.request.session['form_value_error_goods_log_list']
            id = form_value_error_goods_log_list[0]
            batch_name = form_value_error_goods_log_list[1]
            gid = form_value_error_goods_log_list[2]
            status = form_value_error_goods_log_list[3]
            code = form_value_error_goods_log_list[4]
            message = form_value_error_goods_log_list[5]
            create_date_from = form_value_error_goods_log_list[6]
            create_date_to = form_value_error_goods_log_list[7]
            # 検索条件
            condition_id = Q()
            condition_batch_name = Q()
            condition_gid = Q()
            condition_status = Q()
            condition_code = Q()
            condition_message = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(id) != 0 and id[0]:
                condition_id = Q(id__icontains=id)
            if len(batch_name) != 0 and batch_name[0]:
                condition_batch_name = Q(batch_name__icontains=batch_name)
            if len(gid) != 0 and gid[0]:
                condition_gid = Q(gid__icontains=gid)
            if len(status) != 0 and status[0]:
                condition_status = Q(status__icontains=status)
            if len(code) != 0 and code[0]:
                condition_code = Q(code__icontains=code)
            if len(message) != 0 and message[0]:
                condition_message = Q(message__icontains=message)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return ErrorGoodsLog.objects.select_related().filter(
                condition_id &
                condition_batch_name &
                condition_gid &
                condition_status &
                condition_code &
                condition_message &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return ErrorGoodsLog.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        id = ''
        batch_name = ''
        gid = ''
        status = ''
        code = ''
        message = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_error_goods_log_list' in self.request.session:
            form_value_error_goods_log_list = self.request.session['form_value_error_goods_log_list']
            id = form_value_error_goods_log_list[0]
            batch_name = form_value_error_goods_log_list[1]
            gid = form_value_error_goods_log_list[2]
            status = form_value_error_goods_log_list[3]
            code = form_value_error_goods_log_list[4]
            message = form_value_error_goods_log_list[5]
            create_date_from = form_value_error_goods_log_list[6]
            create_date_to = form_value_error_goods_log_list[7]
        default_data = {
                    'id': id, # id
                    'batch_name': batch_name, # batch_name
                    'gid': gid, # gid
                    'status': status, # status
                    'code': code,
                    'message': message, # message
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = ErrorGoodsLogSearchForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class ErrorGoodsLogDetail(generic.DetailView):
    """
    ErrorGoodsLogテーブルのレコード詳細
    """
    template_name = 'yaget/error_goods_log_detail.html'
    model = ErrorGoodsLog

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'エラーになった商品更新の詳細です'
        context['message'] = 'エラーになった商品更新の詳細メッセージです'
        return self.render_to_response(context)


class ErrorGoodsLogDelete(generic.DeleteView):
    """
    ErrorGoodsLogのレコード削除
    """
    template_name = 'yaget/error_goods_log_delete.html'
    model = ErrorGoodsLog
    success_url = reverse_lazy('yaget:error_goods_log_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class AllOrderList(generic.ListView):
    """
    AllOrderInfoテーブルの一覧表作成
    """
    model = AllOrderInfo
    template_name = 'yaget/all_order_list.html'
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        form_all_order_list = [
            self.request.POST.get('qoo_id', None),
            self.request.POST.get('wow_id', None),
            self.request.POST.get('buyer', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_all_order_list'] = form_all_order_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。

        if 'form_all_order_list' in self.request.session:
            form_all_order_list = self.request.session['form_all_order_list']
            qoo_id = form_all_order_list[0]
            wow_id = form_all_order_list[1]
            buyer = form_all_order_list[2]
            create_date_from = form_all_order_list[3]
            create_date_to = form_all_order_list[4]
            # 検索条件
            condition_qoo_id = Q()
            condition_wow_id = Q()
            condition_buyer = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(qoo_id) != 0 and qoo_id[0]:
                condition_qoo_id = Q(qoo_id__icontains=qoo_id)
            if len(wow_id) != 0 and wow_id[0]:
                wow_id = Q(wow_id__icontains=wow_id)
            if len(buyer) != 0 and buyer[0]:
                condition_buyer = Q(buyer__icontains=buyer)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return AllOrderInfo.objects.select_related().filter(
                condition_qoo_id &
                condition_wow_id &
                condition_buyer &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return AllOrderInfo.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qoo_id = ''
        wow_id = ''
        buyer = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_all_order_list' in self.request.session:
            form_all_order_list = self.request.session['form_all_order_list']
            qoo_id = form_all_order_list[0]
            wow_id = form_all_order_list[1]
            buyer = form_all_order_list[2]
            create_date_from = form_all_order_list[3]
            create_date_to = form_all_order_list[4]
        default_data = {
                    'qoo_id': qoo_id,  # qoo_id
                    'wow_id': wow_id,  # wow_id
                    'buyer': buyer,  # buyer
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = AllOrderInfoForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'all_order_list'
        return ctx


class QooOrderList(generic.ListView):
    """
    QooOrderInfoテーブルの一覧表作成
    """
    model = QooOrderInfo
    template_name = 'yaget/qoo_order_list.html'
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        form_qoo_order_list = [
            self.request.POST.get('seller_id', None),
            self.request.POST.get('order_no', None),
            self.request.POST.get('shipping_status', None),
            self.request.POST.get('buyer', None),
            self.request.POST.get('order_date', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_qoo_order_list'] = form_qoo_order_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。

        if 'form_qoo_order_list' in self.request.session:
            form_qoo_order_list = self.request.session['form_qoo_order_list']
            seller_id = form_qoo_order_list[0]
            order_no = form_qoo_order_list[1]
            shipping_status = form_qoo_order_list[2]
            buyer = form_qoo_order_list[3]
            order_date = form_qoo_order_list[4]
            create_date_from = form_qoo_order_list[5]
            create_date_to = form_qoo_order_list[6]
            # 検索条件
            condition_seller_id = Q()
            condition_order_no = Q()
            condition_shipping_status = Q()
            condition_buyer = Q()
            condition_order_date = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(seller_id) != 0 and seller_id[0]:
                condition_seller_id = Q(seller_id__icontains=seller_id)
            if len(order_no) != 0 and order_no[0]:
                condition_order_no = Q(order_no__icontains=order_no)
            if len(shipping_status) != 0 and shipping_status[0]:
                condition_shipping_status = Q(shipping_status__icontains=shipping_status)
            if len(buyer) != 0 and buyer[0]:
                condition_buyer = Q(buyer__icontains=buyer)
            if len(order_date) != 0 and order_date[0]:
                condition_order_date = Q(order_date__icontains=order_date)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return QooOrderInfo.objects.select_related().filter(
                condition_seller_id &
                condition_order_no &
                condition_shipping_status &
                condition_buyer &
                condition_order_date &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return QooOrderInfo.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        seller_id = ''
        order_no = ''
        shipping_status = ''
        buyer = ''
        order_date = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_qoo_order_list' in self.request.session:
            form_qoo_order_list = self.request.session['form_qoo_order_list']
            seller_id = form_qoo_order_list[0]
            order_no = form_qoo_order_list[1]
            shipping_status = form_qoo_order_list[2]
            buyer = form_qoo_order_list[3]
            order_date = form_qoo_order_list[4]
            create_date_from = form_qoo_order_list[5]
            create_date_to = form_qoo_order_list[6]
        default_data = {
                    'seller_id': seller_id,  # seller_id
                    'order_no': order_no,  # order_no
                    'shipping_status': shipping_status,  # shipping_status
                    'buyer': buyer,  # buyer
                    'order_date': order_date,  # order_date
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = QooOrderInfoForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'qoo_order_list'
        return ctx


class QooOrderDetail(generic.DetailView):
    """
    QooOrderInfoテーブルのレコード詳細
    """
    template_name = 'yaget/qoo_order_detail.html'
    model = QooOrderInfo

    def get(self, request, *args, **kwargs):
        logger.debug("--- QooOrderDetail gin")
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        logger.debug("--- QooOrderDetail order_no:{}".format(self.object.order_no))
        return self.render_to_response(context)

    def get_context_data(self, object, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        qoo_buyers_order_detail_list = QooBuyersOrderDetail.objects.filter(
            order_detail=object
        ).all
        context['buyers_order_list'] = qoo_buyers_order_detail_list

        buyers_goods_detail = YaBuyersItemDetail.objects.filter(
            qoo_seller_code=object.seller_item_code
        ).first
        context['buyers_goods_detail'] = buyers_goods_detail

        context['message'] = 'qoo_order_detail'

        return context


class QooOrderUpdate(generic.UpdateView):
    template_name = 'yaget/qoo_order_update.html'
    model = QooOrderInfo
    fields = [
        'order_no',
        'shipping_status',
        'seller_id',
        'pack_no',
        'order_date',
        'payment_date',
        'est_shipping_date',
        'shipping_date',
        'delivered_date',
        'buyer',
        'buyer_gata',
        'buyer_tel',
        'buyer_mobile',
        'buyer_email',
        'item_code',
        'seller_item_code',
        'item_title',
        'option',
        'option_code',
        'order_price',
        'order_qty',
        'discount',
        'total',
        'receiver',
        'receiver_gata',
        'shipping_country',
        'zipcode',
        'shipping_addr',
        'addr1',
        'addr2',
        'receiver_tel',
        'receiver_mobile',
        'hope_date',
        'sender_name',
        'sender_tel',
        'sender_nation',
        'sender_zipcode',
        'sender_addr',
        'shipping_way',
        'shipping_msg',
        'payment_method',
        'seller_discount',
        'currency',
        'shipping_rate',
        'related_order',
        'shipping_rate_type',
        'delivery_company',
        'voucher_code',
        'packing_no',
        'seller_delivery_no',
        'payment_nation',
        'gift',
        'cod_price',
        'cart_discount_seller',
        'cart_discount_qoo10',
        'settle_price',
        'branch_name',
        'tracking_no',
        'oversea_consignment',
        'oversea_consignment_receiver',
        'oversea_consignment_country',
        'oversea_consignment_zipcode',
        'oversea_consignment_addr1',
        'oversea_consignment_addr2',
        'delay_type',
        'delay_memo',
    ]

    def get_success_url(self):
        return reverse('yaget:qoo_order_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(QooOrderUpdate, self).get_form()
        form.fields['order_no'].label = 'id 注文番号'
        form.fields['shipping_status'].label = '配送状態'
        form.fields['seller_id'].label = '販売者ID'
        form.fields['pack_no'].label = 'id カート番号'
        form.fields['order_date'].label = '注文日'
        form.fields['payment_date'].label = '決済日'
        form.fields['est_shipping_date'].label = '発送予定日'
        form.fields['shipping_date'].label = '発送日'
        form.fields['delivered_date'].label = '配送完了日'
        form.fields['buyer'].label = '購入者名'
        form.fields['buyer_gata'].label = '購入者名（カタカナ）'
        form.fields['buyer_tel'].label = '購入者の電話番号'
        form.fields['buyer_mobile'].label = '購入者の携帯電話番号'
        form.fields['buyer_email'].label = '購入者の携帯電話番号'
        form.fields['item_code'].label = 'Qoo10商品番号'
        form.fields['seller_item_code'].label = '販売商品コード'
        form.fields['item_title'].label = '商品名'
        form.fields['option'].label = 'オプション'
        form.fields['option_code'].label = 'オプションコード'
        form.fields['order_price'].label = '商品価格'
        form.fields['order_qty'].label = '注文数量'
        form.fields['discount'].label = '商品割引金額'
        form.fields['total'].label = '注文数量（商品価格 + オプション価格 - 割引額）'
        form.fields['receiver'].label = '受取人名'
        form.fields['receiver_gata'].label = '受取人名（カタカナ）'
        form.fields['shipping_country'].label = 'お届け先の国家'
        form.fields['zipcode'].label = '郵便番号'
        form.fields['shipping_addr'].label = 'お届け先住所'
        form.fields['addr1'].label = '住所(都道府県/市区町村)'
        form.fields['addr2'].label = '住所(市区町村以降)'
        form.fields['receiver_tel'].label = '受取人の電話番号'
        form.fields['receiver_mobile'].label = '受取人の携帯電話番号'
        form.fields['hope_date'].label = '配送希望日'
        form.fields['sender_name'].label = '送信者'
        form.fields['sender_tel'].label = '送り主の電話番号'
        form.fields['sender_nation'].label = '送り主の国家'
        form.fields['sender_zipcode'].label = '送り主の郵便番号'
        form.fields['sender_addr'].label = '送り主の住所'
        form.fields['shipping_way'].label = '配送方法'
        form.fields['shipping_msg'].label = '配送メッセージ'
        form.fields['payment_method'].label = '決済手段'
        form.fields['seller_discount'].label = '販売者負担割引額'
        form.fields['currency'].label = '注文金額通貨'
        form.fields['shipping_rate'].label = '送料'
        form.fields['related_order'].label = '関連注文番号：（、）区切り文字で注文番号区分する。例）12345432、12343212、12323232'
        form.fields['shipping_rate_type'].label = '送料グループの種類：Free / Charge / Free on condition / Charge on delivery'
        form.fields['delivery_company'].label = '配送会社'
        form.fields['voucher_code'].label = '訪問受領認証番号'
        form.fields['packing_no'].label = '発注時に生成されるパッキング番号（例：JPP22894429）'
        form.fields['seller_delivery_no'].label = '発注時に生成されるパッキング番号と1：1でマッチングされる販売者単位のシリアル番号（例：130705-0003）'
        form.fields['payment_nation'].label = '注文サイト国：JP'
        form.fields['gift'].label = '贈答品（ギフト、プレゼント、おまけ）'
        form.fields['cod_price'].label = '着払い決済金額'
        form.fields['cart_discount_seller'].label = '販売者負担カート割引'
        form.fields['cart_discount_qoo10'].label = 'Qoo10負担カート割引'
        form.fields['settle_price'].label = '総供給原価'
        form.fields['branch_name'].label = '支店名'
        form.fields['tracking_no'].label = '送り状番号'
        form.fields['oversea_consignment'].label = '海外委託 (Y/N)'
        form.fields['oversea_consignment_receiver'].label = '海外委託受取人'
        form.fields['oversea_consignment_country'].label = '海外委託国家'
        form.fields['oversea_consignment_zipcode'].label = '海外委託 郵便番号'
        form.fields['oversea_consignment_addr1'].label = '海外委託 住所(都道府県/市区町村)'
        form.fields['oversea_consignment_addr2'].label = '海外委託 住所(市区町村以降)'
        form.fields['delay_type'].label = '遅延の理由。（1：商品準備中、2：注文製作（オーダーメイド）、3：顧客の要求、4：その他）'
        form.fields['delay_memo'].label = '販売者メモ'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Qoo10注文情報 更新ページです'
        context['message'] = 'Qoo10注文情報 更新ページ メッセージです'
        return context

class QooOrderDelete(generic.DeleteView):
    """
    QooOrderInfoテーブルのレコード削除
    """
    template_name = 'yaget/qoo_order_delete.html'
    model = QooOrderInfo
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:all_order_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- QooOrderDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10のステータスを削除に更新
            # Qoo10にアクセス
            # が必要だがまだできてない！
            """
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)
            """

            #goods_object = self.get_object()
            """
            self.object.qoo_upd_status = 3  # 取引廃止


            # 続けてwowmaから削除
            # まず商品ステータスを変えてから
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 削除更新 ok')
                else:
                    messages.error(
                        self.request, 'wowmaから削除に失敗しました。[{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma で対象商品が見つからないのでスルー。DBから消す")
            """

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '「{}」を削除しました'.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '削除に失敗しました。[{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- QooOrderDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- QooOrderDelete out")
        return result


class WowOrderList(generic.ListView):
    """
    WowmaOrderInfoテーブルの一覧表作成
    """
    model = WowmaOrderInfo
    template_name = 'yaget/wow_order_list.html'
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        form_wow_order_list = [
            self.request.POST.get('orderid', None),
            self.request.POST.get('shop_id', None),
            self.request.POST.get('order_status', None),
            self.request.POST.get('ship_status', None),
            self.request.POST.get('order_name', None),
            self.request.POST.get('user_comment', None),
            self.request.POST.get('order_date', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_wow_order_list'] = form_wow_order_list
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # sessionに値がある場合、その値でクエリ発行する。

        if 'form_wow_order_list' in self.request.session:
            form_wow_order_list = self.request.session['form_wow_order_list']
            orderid = form_wow_order_list[0]
            shop_id = form_wow_order_list[1]
            order_status = form_wow_order_list[2]
            ship_status = form_wow_order_list[3]
            order_name = form_wow_order_list[4]
            user_comment = form_wow_order_list[5]
            order_date = form_wow_order_list[6]
            create_date_from = form_wow_order_list[7]
            create_date_to = form_wow_order_list[8]
            # 検索条件
            condition_orderid = Q()
            condition_shop_id = Q()
            condition_order_status = Q()
            condition_ship_status = Q()
            condition_order_name = Q()
            condition_user_comment = Q()
            condition_order_date = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(orderid) != 0 and orderid[0]:
                condition_orderid = Q(orderid__icontains=orderid)
            if len(shop_id) != 0 and shop_id[0]:
                condition_shop_id = Q(shop_id__icontains=shop_id)
            if len(order_status) != 0 and order_status[0]:
                condition_order_status = Q(order_status__icontains=order_status)
            if len(ship_status) != 0 and ship_status[0]:
                condition_ship_status = Q(ship_status__icontains=ship_status)
            if len(order_name) != 0 and order_name[0]:
                condition_order_name = Q(order_name__icontains=order_name)
            if len(user_comment) != 0 and user_comment[0]:
                condition_user_comment = Q(user_comment__icontains=user_comment)
            if len(order_date) != 0 and order_date[0]:
                condition_order_date = Q(order_date__icontains=order_date)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return WowmaOrderInfo.objects.select_related().filter(
                condition_orderid &
                condition_shop_id &
                condition_order_status &
                condition_ship_status &
                condition_order_name &
                condition_user_comment &
                condition_order_date &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return WowmaOrderInfo.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        orderid = ''
        shop_id = ''
        order_status = ''
        ship_status = ''
        order_name = ''
        user_comment = ''
        order_date = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_wow_order_list' in self.request.session:
            form_wow_order_list = self.request.session['form_wow_order_list']
            orderid = form_wow_order_list[0]
            shop_id = form_wow_order_list[1]
            order_status = form_wow_order_list[2]
            ship_status = form_wow_order_list[3]
            order_name = form_wow_order_list[4]
            user_comment = form_wow_order_list[5]
            order_date = form_wow_order_list[6]
            create_date_from = form_wow_order_list[7]
            create_date_to = form_wow_order_list[8]
        default_data = {
                    'orderid': orderid,  # orderid
                    'shop_id': shop_id,  # shop_id
                    'order_status': order_status,  # order_status
                    'ship_status': ship_status,  # ship_status
                    'order_name': order_name,  # order_name
                    'user_comment': user_comment,  # user_comment
                    'order_date': order_date,  # order_date
                    'create_date_from': create_date_from,
                    'create_date_to': create_date_to,
                    }
        test_form = WowOrderInfoForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'wow_order_list'
        return ctx


class WowOrderDetail(generic.DetailView):
    """
    WowOrderInfoテーブルのレコード詳細
    """
    template_name = 'yaget/wow_order_detail.html'
    model = WowmaOrderInfo

    def get(self, request, *args, **kwargs):
        logger.debug("--- WowOrderDetail gin")
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        logger.debug("--- WowOrderDetail orderid:{}".format(self.object.orderid))
        return self.render_to_response(context)

    #def get_context_data(self, *args, **kwargs):
    def get_context_data(self, object, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        wowma_order_detail_list = WowmaOrderDetail.objects.filter(
            orderinfo=object
        ).all
        context['order_detail_list'] = wowma_order_detail_list

        wowma_buyers_order_detail_list = WowmaBuyersOrderDetail.objects.filter(
            order_detail__orderinfo=object
        ).all

        context['buyers_order_list'] = wowma_buyers_order_detail_list

        context['message'] = 'wow_order_detail'

        return context


class WowOrderUpdate(generic.UpdateView):
    template_name = 'yaget/wow_order_update.html'
    model = WowmaOrderInfo
    fields = [
        'orderid',
        'site_and_device',
        'mail_address',
        'order_name',
        'order_kana',
        'order_zipcode',
        'order_address',
        'order_phone_number_1',
        'order_phone_number_2',
        'nickname',
        'sender_name',
        'sender_kana',
        'sender_zipcode',
        'sender_address',
        'sender_phone_number_1',
        'sender_phone_number_2',
        'order_option',
        'settlement_name',
        'user_comment',
        'memo',
        'order_status',
        'contact_status',
        'authorization_status',
        'payment_status',
        'ship_status',
        'print_status',
        'cancel_status',
        'cancel_reason',
        'cancel_comment',
        'total_sale_price',
        'total_sale_unit',
        'postage_price',
        'charge_price',
        'total_price',
        'coupon_total_price',
        'use_point',
        'use_point_cancel',
        'use_au_point_price',
        'use_au_point',
        'use_au_point_cancel',
        'point_fixed_status',
        'settle_status',
        'pg_result',
        'pg_orderid',
        'pg_request_price',
        'coupon_type',
        'coupon_key',
        'card_jagdement',
        'delivery_name',
        'delivery_method_id',
        'delivery_request_time',
        'shipping_carrier',
        'shipping_number',
        'order_date',
        'contact_date',
        'authorization_date',
        'payment_date',
        'ship_date',
        'print_date',
        'cancel_date',
        'point_fixed_date',
        'delivery_request_day',
        'shipping_date',
    ]

    def get_success_url(self):
        return reverse('yaget:qoo_order_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(WowOrderUpdate, self).get_form()
        form.fields['orderid'].label = 'orderid'
        form.fields['site_and_device'].label = 'site and device'
        form.fields['mail_address'].label = 'mailaddress'
        form.fields['order_name'].label = '注文者氏名'
        form.fields['order_kana'].label = 'order_kana'
        form.fields['order_zipcode'].label = 'order_zipcode'
        form.fields['order_address'].label = 'order_address'
        form.fields['order_phone_number_1'].label = 'order_phone_number_1'
        form.fields['order_phone_number_2'].label = 'order_zipcode'
        form.fields['nickname'].label = 'nickname'
        form.fields['sender_name'].label = '送付先氏名'
        form.fields['sender_kana'].label = '送付先かな'
        form.fields['sender_zipcode'].label = '送付先zipcode'
        form.fields['sender_address'].label = '送付先住所'
        form.fields['sender_phone_number_1'].label = '送付先_電話番号_1'
        form.fields['sender_phone_number_2'].label = '送付先_電話番号_2'
        form.fields['order_option'].label = '注文オプション'
        form.fields['settlement_name'].label = '決済方法'
        form.fields['user_comment'].label = 'ユーザコメント'
        form.fields['memo'].label = 'メモ'
        form.fields['order_status'].label = 'order_ステータス'
        form.fields['contact_status'].label = 'コンタクト_ステータス'
        form.fields['authorization_status'].label = '承認_ステータス'
        form.fields['payment_status'].label = '支払い_ステータス'
        form.fields['ship_status'].label = '発送_ステータス'
        form.fields['print_status'].label = '印刷_ステータス'
        form.fields['cancel_status'].label = 'キャンセル_ステータス'
        form.fields['cancel_reason'].label = 'キャンセル理由'
        form.fields['cancel_comment'].label = 'キャンセルコメント'
        form.fields['total_sale_price'].label = '売上金額合計'
        form.fields['total_sale_unit'].label = '売上個数合計'
        form.fields['postage_price'].label = '送料'
        form.fields['charge_price'].label = '請求金額'
        form.fields['total_price'].label = '総合計金額'
        form.fields['coupon_total_price'].label = 'クーポン利用合計金額'
        form.fields['use_point'].label = '利用ポイント'
        form.fields['use_point_cancel'].label = '利用ポイント キャンセル分'
        form.fields['use_au_point_price'].label = 'au利用ポイント金額'
        form.fields['use_au_point'].label = 'au利用ポイント'
        form.fields['use_au_point_cancel'].label = 'au利用ポイント キャンセル分'
        form.fields['point_fixed_status'].label = 'ポイント fixステータス'
        form.fields['settle_status'].label = '承認ステータス'
        form.fields['pg_result'].label = 'pg結果'
        form.fields['pg_orderid'].label = 'pg_orderid'
        form.fields['pg_request_price'].label = 'pg_請求金額'
        form.fields['coupon_type'].label = 'クーポンタイプ'
        form.fields['coupon_key'].label = 'クーポンキー'
        form.fields['card_jagdement'].label = 'カード判定'
        form.fields['delivery_name'].label = '配送名'
        form.fields['delivery_method_id'].label = '配送方法id'
        form.fields['delivery_request_time'].label = 'お届希望時間帯'
        form.fields['shipping_carrier'].label = '配送業者'
        form.fields['shipping_number'].label = '追跡番号'
        form.fields['order_date'].label = '受注日'
        form.fields['contact_date'].label = 'コンタクトした日'
        form.fields['authorization_date'].label = '承認日'
        form.fields['payment_date'].label = '支払い日'
        form.fields['ship_date'].label = '発送日'
        form.fields['print_date'].label = '印刷日'
        form.fields['cancel_date'].label = 'キャンセル日'
        form.fields['point_fixed_date'].label = 'ポイント確定日'
        form.fields['delivery_request_day'].label = '配送希望日'
        form.fields['shipping_date'].label = '配送日'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowma注文情報 更新ページです'
        context['message'] = 'Wowma注文情報 更新ページ メッセージです'
        return context


class WowOrderDelete(generic.DeleteView):
    """
    WowmaOrderInfoテーブルのレコード削除
    """
    template_name = 'yaget/qoo_order_delete.html'
    model = WowmaOrderInfo
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:all_order_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- WowOrderDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10のステータスを削除に更新
            # Qoo10にアクセス
            # が必要だがまだできてない！
            """
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)
            """

            #goods_object = self.get_object()
            """
            self.object.qoo_upd_status = 3  # 取引廃止


            # 続けてwowmaから削除
            # まず商品ステータスを変えてから
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 削除更新 ok')
                else:
                    messages.error(
                        self.request, 'wowmaから削除に失敗しました。[{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma で対象商品が見つからないのでスルー。DBから消す")
            """

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '「{}」を削除しました'.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '削除に失敗しました。[{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- WowOrderDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- WowOrderDelete out")
        return result


def cut_zenkaku(chk_text):
    return chk_text.replace('\u3000', ' ')


# qoo10 最新の注文情報を取得
def qoo_get_order_info_ajax_res(request):
    model = QooOrderInfo
    logger.debug("--- qoo_get_order_info_ajax_res in")

    d = {
        'msg': '',
        'ret_code': '',
    }

    try:
        # 配送状態。（1：出荷待ち、2：出荷済み、3：発注確認、4：配送中、5：配送完了）
        shipping_stat = request.POST.get('shipping_stat')
        search_sdate = request.POST.get('search_sdate')  # 照会開始日 例）20190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_edate = request.POST.get('search_edate')  # 照会終了日 例）20190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_sdate = search_sdate.replace('-', '')
        search_edate = search_edate.replace('-', '')
        search_condition = request.POST.get('search_condition')  # 日付の種類。（1：注文日、2：決済完了日、3：配送日、4：配送完了日）

        # Qoo10にアクセス
        qoo10obj = Qoo10Access(logger)
        msg = 'start[' + YagetConfig.verbose_name + ']'
        qoo10obj.qoo10_create_cert_key()

        logger.debug("--- qoo_get_order_info_ajax_res 1")

        # Qoo10の商品情報を検索
        # Qoo10に登録済みであれば　goods.qoo_gdno　に値が入っている
        #res_code, res_msg, res_obj = qoo10obj.qoo10_shipping_basic_get_shipping_info(
        res_obj_list = qoo10obj.qoo10_shipping_basic_get_shipping_info(
            shipping_stat,
            search_sdate,
            search_edate,
            search_condition,
            )
        logger.debug("--- qoo_get_order_info_ajax_res 2")

        for res_obj in res_obj_list:
            if int(res_obj["res_code"]) < 0:
                logger.debug("--- qoo_get_order_info_ajax_res 1 res_code[{}]".format(res_obj["res_code"]))
                # エラー
                d = {
                    'msg': res_obj["res_msg"],
                    'ret_code': res_obj["res_code"],
                }
            else:
                # 成功
                # QooOrderInfo　に新規レコードとして追加する
                logger.debug("--- qoo_get_order_info_ajax_res 2 res_code[{}]".format(res_obj["res_code"]))
                logger.debug("--- qoo_get_order_info_ajax_res 2_1 res_obj[{}]".format(res_obj["res_obj"]))
                for order in res_obj["res_obj"]:
                    logger.debug("--- qoo_get_order_info_ajax_res 3")
                    logger.debug("--- qoo_get_order_info_ajax_res 3 order[{}]".format(order))
                    logger.debug('order: orderNo[{}]:itemCode[{}]'.format(
                        str(order['orderNo']),
                        str(order['itemCode']),
                    ))
                    msg += 'orderNo:' + str(order['orderNo']) + ' '

                    # 注文詳細をそれぞれ取り込む
                    new_obj = QooOrderInfo.objects.filter(
                        order_no=order['orderNo'],
                        seller_id=order['sellerID'],
                    ).first()
                    if not new_obj:
                        obj, created = QooOrderInfo.objects.update_or_create(
                            order_no=order['orderNo'],
                            shipping_status=order['shippingStatus'],
                            seller_id=order['sellerID'],
                            pack_no=order['packNo'],
                            order_date=order['orderDate'],
                            payment_date=order['PaymentDate'],
                            est_shipping_date=order['EstShippingDate'],
                            shipping_date=order['ShippingDate'],
                            delivered_date=order['DeliveredDate'],
                            buyer=cut_zenkaku(order['buyer']),
                            buyer_gata=cut_zenkaku(order['buyer_gata']),
                            buyer_tel=order['buyerTel'],
                            buyer_mobile=order['buyerMobile'],
                            buyer_email=order['buyerEmail'],
                            item_code=order['itemCode'],
                            seller_item_code=order['sellerItemCode'],
                            item_title=order['itemTitle'],
                            option=order['option'],
                            option_code=order['optionCode'],
                            order_price=order['orderPrice'],
                            order_qty=order['orderQty'],
                            discount=order['discount'],
                            total=order['total'],
                            receiver=cut_zenkaku(order['receiver']),
                            receiver_gata=cut_zenkaku(order['receiver_gata']),
                            shipping_country=order['shippingCountry'],
                            zipcode=order['zipCode'],
                            shipping_addr=cut_zenkaku(order['shippingAddr']),
                            addr1=cut_zenkaku(order['Addr1']),
                            addr2=cut_zenkaku(order['Addr2']),
                            receiver_tel=order['receiverTel'],
                            receiver_mobile=order['receiverMobile'],
                            hope_date=order['hopeDate'],
                            sender_name=order['senderName'],
                            sender_tel=order['senderTel'],
                            sender_nation=order['senderNation'],
                            sender_zipcode=order['senderZipCode'],
                            sender_addr=order['senderAddr'],
                            shipping_way=order['ShippingWay'],
                            shipping_msg=order['ShippingMsg'],
                            payment_method=order['PaymentMethod'],
                            seller_discount=order['SellerDiscount'],
                            currency=order['Currency'],
                            shipping_rate=order['ShippingRate'],
                            related_order=order['RelatedOrder'],
                            shipping_rate_type=order['shippingRateType'],
                            delivery_company=order['DeliveryCompany'],
                            voucher_code=order['VoucherCode'],
                            packing_no=order['PackingNo'],
                            seller_delivery_no=order['SellerDeliveryNo'],
                            payment_nation=order['PaymentNation'],
                            gift=order['Gift'],
                            cod_price=order['cod_price'],
                            cart_discount_seller=order['Cart_Discount_Seller'],
                            cart_discount_qoo10=order['Cart_Discount_Qoo10'],
                            settle_price=order['SettlePrice'],
                            branch_name=order['BranchName'],
                            tracking_no=order['TrackingNo'],
                            oversea_consignment=order['OverseaConsignment'],
                            oversea_consignment_receiver=order['OverseaConsignment_receiver'],
                            oversea_consignment_country=order['OverseaConsignment_Country'],
                            oversea_consignment_zipcode=order['OverseaConsignment_zipCode'],
                            oversea_consignment_addr1=order['OverseaConsignment_Addr1'],
                            oversea_consignment_addr2=order['OverseaConsignment_Addr2'],
                            delay_type='',
                            delay_memo='',
                        )
                        obj.save()
                    else:
                        new_obj.order_no = order['orderNo']
                        new_obj.shipping_status = order['shippingStatus']
                        new_obj.seller_id = order['sellerID']
                        new_obj.pack_no = order['packNo']
                        new_obj.order_date = order['orderDate']
                        new_obj.payment_date = order['PaymentDate']
                        new_obj.est_shipping_date = order['EstShippingDate']
                        new_obj.shipping_date = order['ShippingDate']
                        new_obj.delivered_date = order['DeliveredDate']
                        new_obj.buyer = cut_zenkaku(order['buyer'])
                        new_obj.buyer_gata = cut_zenkaku(order['buyer_gata'])
                        new_obj.buyer_tel = order['buyerTel']
                        new_obj.buyer_mobile = order['buyerMobile']
                        new_obj.buyer_email = order['buyerEmail']
                        new_obj.item_code = order['itemCode']
                        new_obj.seller_item_code = order['sellerItemCode']
                        new_obj.item_title = order['itemTitle']
                        new_obj.option = order['option']
                        new_obj.option_code = order['optionCode']
                        new_obj.order_price = order['orderPrice']
                        new_obj.order_qty = order['orderQty']
                        new_obj.discount = order['discount']
                        new_obj.total = order['total']
                        new_obj.receiver = cut_zenkaku(order['receiver'])
                        new_obj.receiver_gata = cut_zenkaku(order['receiver_gata'])
                        new_obj.shipping_country = order['shippingCountry']
                        new_obj.zipcode = order['zipCode']
                        new_obj.shipping_addr = cut_zenkaku(order['shippingAddr'])
                        new_obj.addr1 = cut_zenkaku(order['Addr1'])
                        new_obj.addr2 = cut_zenkaku(order['Addr2'])
                        new_obj.receiver_tel = order['receiverTel']
                        new_obj.receiver_mobile = order['receiverMobile']
                        new_obj.hope_date = order['hopeDate']
                        new_obj.sender_name = order['senderName']
                        new_obj.sender_tel = order['senderTel']
                        new_obj.sender_nation = order['senderNation']
                        new_obj.sender_zipcode = order['senderZipCode']
                        new_obj.sender_addr = order['senderAddr']
                        new_obj.shipping_way = order['ShippingWay']
                        new_obj.shipping_msg = order['ShippingMsg']
                        new_obj.payment_method = order['PaymentMethod']
                        new_obj.seller_discount = order['SellerDiscount']
                        new_obj.currency = order['Currency']
                        new_obj.shipping_rate = order['ShippingRate']
                        new_obj.related_order = order['RelatedOrder']
                        new_obj.shipping_rate_type = order['shippingRateType']
                        new_obj.delivery_company = order['DeliveryCompany']
                        new_obj.voucher_code = order['VoucherCode']
                        new_obj.packing_no = order['PackingNo']
                        new_obj.seller_delivery_no = order['SellerDeliveryNo']
                        new_obj.payment_nation = order['PaymentNation']
                        new_obj.gift = order['Gift']
                        new_obj.cod_price = order['cod_price']
                        new_obj.cart_discount_seller = order['Cart_Discount_Seller']
                        new_obj.cart_discount_qoo10 = order['Cart_Discount_Qoo10']
                        new_obj.settle_price = order['SettlePrice']
                        new_obj.branch_name = order['BranchName']
                        new_obj.tracking_no = order['TrackingNo']
                        new_obj.oversea_consignment = order['OverseaConsignment']
                        new_obj.oversea_consignment_receiver = order['OverseaConsignment_receiver']
                        new_obj.oversea_consignment_country = order['OverseaConsignment_Country']
                        new_obj.oversea_consignment_zipcode = order['OverseaConsignment_zipCode']
                        new_obj.oversea_consignment_addr1 = order['OverseaConsignment_Addr1']
                        new_obj.oversea_consignment_addr2 = order['OverseaConsignment_Addr2']
                        new_obj.save()

                logger.debug("--- qoo_get_order_info_ajax_res 3")
                d = {
                    'msg': msg,
                    'ret_code': res_obj["res_code"],
                }
    except Exception as e:
        logger.debug("--- qoo_get_order_info_ajax_res error occurred.[{}]".format(traceback.format_exc()))
        d = {
            'msg': traceback.format_exc(),
            'ret_code': -1,
        }
        return JsonResponse()

    logger.debug("--- qoo_get_order_info_ajax_res out")
    return JsonResponse(d)


# qoo10 注文情報　発送予定日や遅延理由を送信
def qoo_order_seller_chk_ajax_res(request):
    model = QooOrderInfo
    logger.debug("--- qoo_order_seller_chk_ajax_res in")
    pk = request.POST.get('pk')
    if pk:
        order = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)
    est_shipping_date = request.POST.get('est_shipping_date')  # 発送予定日 例）20190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
    est_shipping_date = est_shipping_date.replace('-', '')
    delay_type = request.POST.get('delay_type')  # 遅延の理由。（1：商品準備中、2：注文製作（オーダーメイド）、3：顧客の要求、4：その他）
    delay_memo = request.POST.get('delay_memo')  # 販売者メモ

    # Qoo10にアクセス
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10の商品情報を検索
    # Qoo10に登録済みであれば　goods.qoo_gdno　に値が入っている
    res_list = qoo10obj.qoo10_shipping_basic_set_seller_check_yn(
        order.order_no,
        est_shipping_date,
        delay_type,
        delay_memo,
        )
    my_ret_code = 0
    my_ret_msg = ''
    for res_item in res_list:
        my_ret_code = res_item['res_code']
        my_ret_msg = res_item['res_msg']
        msg += my_ret_msg
        if my_ret_code == 0:
            # 更新に成功している。次の処理は行わない
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)


# qoo10 注文情報　発送日や追跡番号を送信
def qoo_order_sending_info_ajax(request):
    model = QooOrderInfo
    logger.debug("--- qoo_order_sending_info_ajax in")
    pk = request.POST.get('pk')
    if pk:
        order = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)
    delivery_company = request.POST.get('delivery_company')  # 配送会社
    tracking_no = request.POST.get('tracking_no')  # 送り状番号

    # Qoo10にアクセス
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10の商品情報を検索
    res_list = qoo10obj.qoo10_shipping_basic_set_sending_info(
        order.order_no,
        delivery_company,
        tracking_no,
    )
    my_ret_code = 0
    my_ret_msg = ''
    for res_item in res_list:
        my_ret_code = res_item['res_code']
        my_ret_msg = res_item['res_msg']
        msg += my_ret_msg + ' '
        if my_ret_code == 0:
            # 更新に成功している。次の処理は行わない
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)

# wowma 最新の注文情報を取得
def wow_get_order_info_ajax_res(request):
    model = WowmaOrderInfo
    logger.debug("--- wow_get_order_info_ajax_res in")

    # order_status は配送状態。
    """
    新規受付
    発送前入金待ち
    発送後入金待ち
    与信待ち
    発送待ち
    完了
    保留
    キャンセル
    各種カスタムステータス（取引管理で貴店舗が登録したステータス名）
    新規予約
    予約中
    不正取引審査中
    審査保留
    審査NG
    キャンセル受付中
    """
    try:
        search_sdate = request.POST.get('search_sdate')  # 照会開始日 例）20190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_edate = request.POST.get('search_edate')  # 照会終了日 例）20190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_sdate = search_sdate.replace('-', '')
        search_edate = search_edate.replace('-', '')
        date_type = request.POST.get('date_type')  # 日付の種類。0:注文日　1:発送日　2:入金日　3:発売(入荷)予定日　4:発送期限日　（デフォルト0）
        order_status_1 = request.POST.get('order_status_1')
        order_status_2 = request.POST.get('order_status_2')

        # wowmaにアクセス

        wowma_access = WowmaAccess(logger)

        #msg = 'start[' + YagetConfig.verbose_name + ']'
        msg = ''
        ret_code = 0

        document_list = wowma_access.wowma_get_order_all_list(
            search_sdate,
            search_edate,
            date_type,
            order_status_1,
            order_status_2,
            )

        #logger.debug("--- wow_get_order_info_ajax_res doc_list len[{}]".format(len(document_list)))
        # document は、[shop_obj, res_obj]　の配列で返している
        for document in document_list:
            if document:
                #logger.debug("--- wow_get_order_info_ajax_res doc_list doc[{}]".format(document.toprettyxml(indent="  ")))

                #logger.debug(document.toprettyxml(indent="  "))  # パースされたXML情報をインデント付きで文字列に変換して表示
                myrtn = document[1].getElementsByTagName("status")[0].firstChild.nodeValue  # 0なら成功、1　失敗
                if myrtn == 1:
                    my_code = str(document[1].getElementsByTagName("code")[0].firstChild.nodeValue)
                    my_message = str(document[1].getElementsByTagName("message")[0].firstChild.nodeValue)
                    msg = 'エラー発生：[{}][{}]'.format(my_code, my_message)
                    logger.info('wow_get_order_info_ajax_res code:[{}] msg:[{}]'.format(my_code, my_message))
                else:
                    # 正常にデータ取得できた。DB登録
                    my_total_cnt = str(document[1].getElementsByTagName("resultCount")[0].firstChild.nodeValue)
                    msg = '取得OK：件数[{}]'.format(my_total_cnt)
                    logger.debug('wow_get_order_info_ajax_res ok total_cnt:[{}]'.format(my_total_cnt))

                    # 注文詳細をそれぞれ取り込む
                    msg += 'orderId:\n'
                    for order_id_elm in document[1].getElementsByTagName("orderInfo"):
                        order_id = str(order_id_elm.getElementsByTagName("orderId")[0].firstChild.nodeValue)
                        logger.info('wow_get_order_info_ajax_res order_id:[{}]'.format(order_id))
                        msg += order_id + ' '

                        # 注文詳細をそれぞれ取り込む
                        new_obj = WowmaOrderInfo.objects.filter(
                            orderid=order_id,
                        ).first()

                        # レスポンスに存在しない項目はチェックしないと
                        releaseDate = ''
                        if order_id_elm.getElementsByTagName("releaseDate"):
                            if order_id_elm.getElementsByTagName("releaseDate")[0].firstChild:
                                releaseDate = str(order_id_elm.getElementsByTagName("releaseDate")[0].firstChild.nodeValue)
                        raw_mail_address = ''
                        if order_id_elm.getElementsByTagName("rawMailAddress"):
                            if order_id_elm.getElementsByTagName("rawMailAddress")[0].firstChild:
                                raw_mail_address = str(order_id_elm.getElementsByTagName("rawMailAddress")[0].firstChild.nodeValue)
                        contact_date = ''
                        if order_id_elm.getElementsByTagName("contactDate"):
                            if order_id_elm.getElementsByTagName("contactDate")[0].firstChild:
                                contact_date = str(order_id_elm.getElementsByTagName("contactDate")[0].firstChild.nodeValue)
                        ship_date = ''
                        if order_id_elm.getElementsByTagName("shipDate"):
                            if order_id_elm.getElementsByTagName("shipDate")[0].firstChild:
                                ship_date = str(order_id_elm.getElementsByTagName("shipDate")[0].firstChild.nodeValue)
                        print_date = ''
                        if order_id_elm.getElementsByTagName("printDate"):
                            if order_id_elm.getElementsByTagName("printDate")[0].firstChild:
                                print_date = str(order_id_elm.getElementsByTagName("printDate")[0].firstChild.nodeValue)
                        sender_shop_cd = ''
                        if order_id_elm.getElementsByTagName("senderShopCd"):
                            if order_id_elm.getElementsByTagName("senderShopCd")[0].firstChild:
                                sender_shop_cd = str(order_id_elm.getElementsByTagName("senderShopCd")[0].firstChild.nodeValue)
                        cancel_reason = ''
                        if order_id_elm.getElementsByTagName("cancelReason"):
                            if order_id_elm.getElementsByTagName("cancelReason")[0].firstChild:
                                cancel_reason = str(order_id_elm.getElementsByTagName("cancelReason")[0].firstChild.nodeValue)
                        cancel_comment = ''
                        if order_id_elm.getElementsByTagName("cancelComment"):
                            if order_id_elm.getElementsByTagName("cancelComment")[0].firstChild:
                                cancel_comment = str(order_id_elm.getElementsByTagName("cancelComment")[0].firstChild.nodeValue)
                        cancel_date = ''
                        if order_id_elm.getElementsByTagName("cancelDate"):
                            if order_id_elm.getElementsByTagName("cancelDate")[0].firstChild:
                                cancel_date = str(order_id_elm.getElementsByTagName("cancelDate")[0].firstChild.nodeValue)
                        gift_wrapping_type = ''
                        if order_id_elm.getElementsByTagName("giftWrappingType"):
                            if order_id_elm.getElementsByTagName("giftWrappingType")[0].firstChild:
                                gift_wrapping_type = str(order_id_elm.getElementsByTagName("giftWrappingType")[0].firstChild.nodeValue)
                        item_cancel_date = ''
                        if order_id_elm.getElementsByTagName("itemCancelDate"):
                            if order_id_elm.getElementsByTagName("itemCancelDate")[0].firstChild:
                                item_cancel_date = str(order_id_elm.getElementsByTagName("itemCancelDate")[0].firstChild.nodeValue)
                        settle_status = ''
                        if order_id_elm.getElementsByTagName("settleStatus"):
                            if order_id_elm.getElementsByTagName("settleStatus")[0].firstChild:
                                settle_status = str(order_id_elm.getElementsByTagName("settleStatus")[0].firstChild.nodeValue)
                        authori_timelimit_date = ''
                        if order_id_elm.getElementsByTagName("authoriTimelimitDate"):
                            if order_id_elm.getElementsByTagName("authoriTimelimitDate")[0].firstChild:
                                authori_timelimit_date = str(order_id_elm.getElementsByTagName("authoriTimelimitDate")[0].firstChild.nodeValue)
                        pg_result = ''
                        if order_id_elm.getElementsByTagName("pgResult"):
                            if order_id_elm.getElementsByTagName("pgResult")[0].firstChild:
                                pg_result = str(order_id_elm.getElementsByTagName("pgResult")[0].firstChild.nodeValue)
                        pg_response_code = ''
                        if order_id_elm.getElementsByTagName("pgResponseCode"):
                            if order_id_elm.getElementsByTagName("pgResponseCode")[0].firstChild:
                                pg_response_code = str(order_id_elm.getElementsByTagName("pgResponseCode")[0].firstChild.nodeValue)
                        pg_response_detail = ''
                        if order_id_elm.getElementsByTagName("pgResponseDetail"):
                            if order_id_elm.getElementsByTagName("pgResponseDetail")[0].firstChild:
                                pg_response_detail = str(order_id_elm.getElementsByTagName("pgResponseDetail")[0].firstChild.nodeValue)
                        pg_orderid = ''
                        if order_id_elm.getElementsByTagName("pgOrderId"):
                            if order_id_elm.getElementsByTagName("pgOrderId")[0].firstChild:
                                pg_orderid = str(order_id_elm.getElementsByTagName("pgOrderId")[0].firstChild.nodeValue)
                        pg_request_price = 0
                        if order_id_elm.getElementsByTagName("pgRequestPrice"):
                            if order_id_elm.getElementsByTagName("pgRequestPrice")[0].firstChild:
                                pg_request_price = int(order_id_elm.getElementsByTagName("pgRequestPrice")[0].firstChild.nodeValue)
                        pg_request_price_normal_tax = 0
                        if order_id_elm.getElementsByTagName("pgRequestPriceNormalTax"):
                            if order_id_elm.getElementsByTagName("pgRequestPriceNormalTax")[0].firstChild:
                                pg_request_price_normal_tax = int(order_id_elm.getElementsByTagName("pgRequestPriceNormalTax")[0].firstChild.nodeValue)
                        pg_request_price_reduced_tax = 0
                        if order_id_elm.getElementsByTagName("pgRequestPriceReducedTax"):
                            if order_id_elm.getElementsByTagName("pgRequestPriceReducedTax")[0].firstChild:
                                pg_request_price_reduced_tax = int(order_id_elm.getElementsByTagName("pgRequestPriceReducedTax")[0].firstChild.nodeValue)
                        pg_request_price_no_tax = 0
                        if order_id_elm.getElementsByTagName("pgRequestPriceNoTax"):
                            if order_id_elm.getElementsByTagName("pgRequestPriceNoTax")[0].firstChild:
                                pg_request_price_no_tax = int(order_id_elm.getElementsByTagName("pgRequestPriceNoTax")[0].firstChild.nodeValue)
                        coupon_type = ''
                        if order_id_elm.getElementsByTagName("couponType"):
                            if order_id_elm.getElementsByTagName("couponType")[0].firstChild:
                                coupon_type = str(order_id_elm.getElementsByTagName("couponType")[0].firstChild.nodeValue)
                        coupon_key = ''
                        if order_id_elm.getElementsByTagName("couponKey"):
                            if order_id_elm.getElementsByTagName("couponKey")[0].firstChild:
                                coupon_key = str(order_id_elm.getElementsByTagName("couponKey")[0].firstChild.nodeValue)
                        card_jagdement = 0
                        if order_id_elm.getElementsByTagName("cardJadgement"):
                            if order_id_elm.getElementsByTagName("cardJadgement")[0].firstChild:
                                card_jagdement = int(order_id_elm.getElementsByTagName("cardJadgement")[0].firstChild.nodeValue)
                        delivery_name = ''
                        if order_id_elm.getElementsByTagName("deliveryName"):
                            if order_id_elm.getElementsByTagName("deliveryName")[0].firstChild:
                                delivery_name = str(order_id_elm.getElementsByTagName("deliveryName")[0].firstChild.nodeValue)
                        delivery_method_id = ''
                        if order_id_elm.getElementsByTagName("deliveryMethodId"):
                            if order_id_elm.getElementsByTagName("deliveryMethodId")[0].firstChild:
                                delivery_method_id = str(order_id_elm.getElementsByTagName("deliveryMethodId")[0].firstChild.nodeValue)
                        delivery_id = ''
                        if order_id_elm.getElementsByTagName("deliveryId"):
                            if order_id_elm.getElementsByTagName("deliveryId")[0].firstChild:
                                delivery_id = str(order_id_elm.getElementsByTagName("deliveryId")[0].firstChild.nodeValue)
                        elec_receipt_issue_status = ''
                        if order_id_elm.getElementsByTagName("elecReceiptIssueStatus"):
                            if order_id_elm.getElementsByTagName("elecReceiptIssueStatus")[0].firstChild:
                                elec_receipt_issue_status = str(order_id_elm.getElementsByTagName("elecReceiptIssueStatus")[0].firstChild.nodeValue)
                        elec_receipt_issue_times = ''
                        if order_id_elm.getElementsByTagName("elecReceiptIssueTimes"):
                            if order_id_elm.getElementsByTagName("elecReceiptIssueTimes")[0].firstChild:
                                elec_receipt_issue_times = str(order_id_elm.getElementsByTagName("elecReceiptIssueTimes")[0].firstChild.nodeValue)
                        delivery_request_day = ''
                        if order_id_elm.getElementsByTagName("deliveryRequestDay"):
                            if order_id_elm.getElementsByTagName("deliveryRequestDay")[0].firstChild:
                                delivery_request_day = str(order_id_elm.getElementsByTagName("deliveryRequestDay")[0].firstChild.nodeValue)
                        delivery_request_time = ''
                        if order_id_elm.getElementsByTagName("deliveryRequestTime"):
                            if order_id_elm.getElementsByTagName("deliveryRequestTime")[0].firstChild:
                                delivery_request_time = str(order_id_elm.getElementsByTagName("deliveryRequestTime")[0].firstChild.nodeValue)
                        shipping_date = ''
                        if order_id_elm.getElementsByTagName("shippingDate"):
                            if order_id_elm.getElementsByTagName("shippingDate")[0].firstChild:
                                shipping_date = str(order_id_elm.getElementsByTagName("shippingDate")[0].firstChild.nodeValue)
                        shipping_carrier = ''
                        if order_id_elm.getElementsByTagName("shippingCarrier"):
                            if order_id_elm.getElementsByTagName("shippingCarrier")[0].firstChild:
                                shipping_carrier = str(order_id_elm.getElementsByTagName("shippingCarrier")[0].firstChild.nodeValue)
                        shipping_number = ''
                        if order_id_elm.getElementsByTagName("shippingNumber"):
                            if order_id_elm.getElementsByTagName("shippingNumber")[0].firstChild:
                                shipping_number = str(order_id_elm.getElementsByTagName("shippingNumber")[0].firstChild.nodeValue)
                        yamato_lnk_mgt_no = ''
                        if order_id_elm.getElementsByTagName("yamatoLnkMgtNo"):
                            if order_id_elm.getElementsByTagName("yamatoLnkMgtNo")[0].firstChild:
                                yamato_lnk_mgt_no = str(order_id_elm.getElementsByTagName("yamatoLnkMgtNo")[0].firstChild.nodeValue)
                        cross_border_ec_trade_kbn = ''
                        if len(order_id_elm.getElementsByTagName("crossBorderEcTradeKbn")) > 0:
                            if order_id_elm.getElementsByTagName("crossBorderEcTradeKbn")[0].firstChild:
                                cross_border_ec_trade_kbn = str(order_id_elm.getElementsByTagName("crossBorderEcTradeKbn")[0].firstChild.nodeValue)
                        sender_phone_number_2 = ''
                        if len(order_id_elm.getElementsByTagName("senderPhoneNumber2")) > 0:
                            if order_id_elm.getElementsByTagName("senderPhoneNumber2")[0].firstChild:
                                sender_phone_number_2 = str(order_id_elm.getElementsByTagName("senderPhoneNumber2")[0].firstChild.nodeValue)
                        order_option = ''
                        if len(order_id_elm.getElementsByTagName("orderOption")) > 0:
                            if order_id_elm.getElementsByTagName("orderOption")[0].firstChild:
                                order_option = str(order_id_elm.getElementsByTagName("orderOption")[0].firstChild.nodeValue)
                        user_comment = ''
                        if len(order_id_elm.getElementsByTagName("userComment")) > 0:
                            if order_id_elm.getElementsByTagName("userComment")[0].firstChild:
                                user_comment = str(order_id_elm.getElementsByTagName("userComment")[0].firstChild.nodeValue)
                        memo = ''
                        if len(order_id_elm.getElementsByTagName("memo")) > 0:
                            if order_id_elm.getElementsByTagName("memo")[0].firstChild:
                                memo = str(order_id_elm.getElementsByTagName("memo")[0].firstChild.nodeValue)
                        item_management_id = ''
                        if len(order_id_elm.getElementsByTagName("itemManagementId")) > 0:
                            if order_id_elm.getElementsByTagName("itemManagementId")[0].firstChild:
                                item_management_id = str(order_id_elm.getElementsByTagName("itemManagementId")[0].firstChild.nodeValue)
                        order_phone_number_2 = ''
                        if len(order_id_elm.getElementsByTagName("ordererPhoneNumber2")) > 0:
                            if order_id_elm.getElementsByTagName("ordererPhoneNumber2")[0].firstChild:
                                order_phone_number_2 = str(order_id_elm.getElementsByTagName("ordererPhoneNumber2")[0].firstChild.nodeValue)
                        secure_segment = ''
                        if len(order_id_elm.getElementsByTagName("secureSegment")) > 0:
                            if order_id_elm.getElementsByTagName("secureSegment")[0].firstChild:
                                secure_segment = str(order_id_elm.getElementsByTagName("secureSegment")[0].firstChild.nodeValue)
                        use_point_cancel = ''
                        if len(order_id_elm.getElementsByTagName("usePointCancel")) > 0:
                            if order_id_elm.getElementsByTagName("usePointCancel")[0].firstChild:
                                use_point_cancel = str(order_id_elm.getElementsByTagName("usePointCancel")[0].firstChild.nodeValue)
                        use_point = 0
                        if len(order_id_elm.getElementsByTagName("usePoint")) > 0:
                            if order_id_elm.getElementsByTagName("usePoint")[0].firstChild:
                                use_point = int(order_id_elm.getElementsByTagName("usePoint")[0].firstChild.nodeValue)

                        use_au_point_cancel = ''
                        if len(order_id_elm.getElementsByTagName("useAuPointCancel")) > 0:
                            if order_id_elm.getElementsByTagName("useAuPointCancel")[0].firstChild:
                                use_au_point_cancel = str(order_id_elm.getElementsByTagName("useAuPointCancel")[0].firstChild.nodeValue)

                        payment_date = ''
                        if len(order_id_elm.getElementsByTagName("paymentDate")) > 0:
                            if order_id_elm.getElementsByTagName("paymentDate")[0].firstChild:
                                payment_date = str(order_id_elm.getElementsByTagName("paymentDate")[0].firstChild.nodeValue)

                        point_fixed_date = ''
                        if len(order_id_elm.getElementsByTagName("pointFixedDate")) > 0:
                            if order_id_elm.getElementsByTagName("pointFixedDate")[0].firstChild:
                                point_fixed_date = str(order_id_elm.getElementsByTagName("pointFixedDate")[0].firstChild.nodeValue.replace('/','-'))

                        point_fixed_status = ''
                        if len(order_id_elm.getElementsByTagName("pointFixedStatus")) > 0:
                            if order_id_elm.getElementsByTagName("pointFixedStatus")[0].firstChild:
                                point_fixed_status = str(order_id_elm.getElementsByTagName("pointFixedStatus")[0].firstChild.nodeValue)

                        authorization_date = ''
                        if len(order_id_elm.getElementsByTagName("authorizationDate")) > 0:
                            if order_id_elm.getElementsByTagName("authorizationDate")[0].firstChild:
                                authorization_date = str(order_id_elm.getElementsByTagName("authorizationDate")[0].firstChild.nodeValue.replace('/','-'))

                        nickname = ''
                        if len(order_id_elm.getElementsByTagName("nickname")) > 0:
                            if order_id_elm.getElementsByTagName("nickname")[0].firstChild:
                                nickname = str(order_id_elm.getElementsByTagName("nickname")[0].firstChild.nodeValue)

                        logger.info('wow_get_order_info_ajax_res point-1')

                        if not new_obj:
                            obj, created = WowmaOrderInfo.objects.update_or_create(
                                orderid=order_id,
                                shop_id=document[0].shop_id,
                                order_date=str(order_id_elm.getElementsByTagName("orderDate")[0].firstChild.nodeValue).replace('/','-'),
                                sell_method_segment=str(order_id_elm.getElementsByTagName("sellMethodSegment")[0].firstChild.nodeValue),
                                release_date=releaseDate.replace('/','-'),
                                site_and_device=str(order_id_elm.getElementsByTagName("siteAndDevice")[0].firstChild.nodeValue),
                                cross_border_ec_trade_kbn=cross_border_ec_trade_kbn,
                                mail_address=str(order_id_elm.getElementsByTagName("mailAddress")[0].firstChild.nodeValue),
                                raw_mail_address=raw_mail_address,
                                order_name=str(order_id_elm.getElementsByTagName("ordererName")[0].firstChild.nodeValue),
                                order_kana=str(order_id_elm.getElementsByTagName("ordererKana")[0].firstChild.nodeValue),
                                order_zipcode=str(order_id_elm.getElementsByTagName("ordererZipCode")[0].firstChild.nodeValue),
                                order_address=str(order_id_elm.getElementsByTagName("ordererAddress")[0].firstChild.nodeValue),
                                order_phone_number_1=str(order_id_elm.getElementsByTagName("ordererPhoneNumber1")[0].firstChild.nodeValue),
                                order_phone_number_2=order_phone_number_2,
                                nickname=nickname,
                                sender_name=str(order_id_elm.getElementsByTagName("senderName")[0].firstChild.nodeValue),
                                sender_kana=str(order_id_elm.getElementsByTagName("senderKana")[0].firstChild.nodeValue),
                                sender_zipcode=str(order_id_elm.getElementsByTagName("senderZipCode")[0].firstChild.nodeValue),
                                sender_address=str(order_id_elm.getElementsByTagName("senderAddress")[0].firstChild.nodeValue),
                                sender_phone_number_1=str(order_id_elm.getElementsByTagName("senderPhoneNumber1")[0].firstChild.nodeValue),
                                sender_phone_number_2=sender_phone_number_2,
                                sender_shop_cd=sender_shop_cd,
                                order_option=order_option,
                                settlement_name=str(order_id_elm.getElementsByTagName("settlementName")[0].firstChild.nodeValue),
                                secure_segment=secure_segment,
                                user_comment=user_comment,
                                trade_remarks=str(order_id_elm.getElementsByTagName("tradeRemarks")[0].firstChild.nodeValue),
                                memo=memo,
                                order_status=str(order_id_elm.getElementsByTagName("orderStatus")[0].firstChild.nodeValue),
                                contact_status=str(order_id_elm.getElementsByTagName("contactStatus")[0].firstChild.nodeValue),
                                contact_date=contact_date.replace('/','-'),
                                authorization_status=str(order_id_elm.getElementsByTagName("authorizationStatus")[0].firstChild.nodeValue),
                                authorization_date=authorization_date,
                                payment_status=str(order_id_elm.getElementsByTagName("paymentStatus")[0].firstChild.nodeValue),
                                payment_date=payment_date.replace('/','-'),
                                ship_status=str(order_id_elm.getElementsByTagName("shipStatus")[0].firstChild.nodeValue),
                                ship_date=ship_date.replace('/','-'),
                                print_status=str(order_id_elm.getElementsByTagName("printStatus")[0].firstChild.nodeValue),
                                print_date=print_date.replace('/','-'),
                                cancel_status=str(order_id_elm.getElementsByTagName("cancelStatus")[0].firstChild.nodeValue),
                                cancel_reason=cancel_reason,
                                cancel_comment=cancel_comment,
                                cancel_date=cancel_date.replace('/','-'),
                                total_sale_price=int(order_id_elm.getElementsByTagName("totalSalePrice")[0].firstChild.nodeValue),
                                total_sale_price_normal_tax=int(order_id_elm.getElementsByTagName("totalSalePriceNormalTax")[0].firstChild.nodeValue),
                                total_sale_price_reduced_tax=int(order_id_elm.getElementsByTagName("totalSalePriceReducedTax")[0].firstChild.nodeValue),
                                total_sale_price_no_tax=int(order_id_elm.getElementsByTagName("totalSalePriceNoTax")[0].firstChild.nodeValue),
                                total_sale_unit=int(order_id_elm.getElementsByTagName("totalSaleUnit")[0].firstChild.nodeValue),
                                postage_price=int(order_id_elm.getElementsByTagName("postagePrice")[0].firstChild.nodeValue),
                                postage_price_tax_rate=float(order_id_elm.getElementsByTagName("postagePriceTaxRate")[0].firstChild.nodeValue),
                                charge_price=int(order_id_elm.getElementsByTagName("chargePrice")[0].firstChild.nodeValue),
                                charge_price_tax_rate=float(order_id_elm.getElementsByTagName("chargePriceTaxRate")[0].firstChild.nodeValue),
                                total_item_option_price=int(order_id_elm.getElementsByTagName("totalItemOptionPrice")[0].firstChild.nodeValue),
                                total_item_option_price_tax_rate=float(order_id_elm.getElementsByTagName("totalItemOptionPriceTaxRate")[0].firstChild.nodeValue),
                                total_gift_wrapping_price=int(order_id_elm.getElementsByTagName("totalGiftWrappingPrice")[0].firstChild.nodeValue),
                                total_gift_wrapping_price_tax_rate=float(order_id_elm.getElementsByTagName("totalGiftWrappingPriceTaxRate")[0].firstChild.nodeValue),
                                total_price=int(order_id_elm.getElementsByTagName("totalPrice")[0].firstChild.nodeValue),
                                total_price_normal_tax=int(order_id_elm.getElementsByTagName("totalPriceNormalTax")[0].firstChild.nodeValue),
                                total_price_reduced_tax=int(order_id_elm.getElementsByTagName("totalPriceReducedTax")[0].firstChild.nodeValue),
                                total_price_no_tax=int(order_id_elm.getElementsByTagName("totalPriceNoTax")[0].firstChild.nodeValue),
                                premium_type= str(order_id_elm.getElementsByTagName("premiumType")[0].firstChild.nodeValue),
                                premium_issue_price= int(order_id_elm.getElementsByTagName("premiumIssuePrice")[0].firstChild.nodeValue),
                                premium_mall_price= int(order_id_elm.getElementsByTagName("premiumMallPrice")[0].firstChild.nodeValue),
                                premium_shop_price= int(order_id_elm.getElementsByTagName("premiumShopPrice")[0].firstChild.nodeValue),
                                coupon_total_price= int(order_id_elm.getElementsByTagName("couponTotalPrice")[0].firstChild.nodeValue),
                                coupon_total_price_normal_tax= int(order_id_elm.getElementsByTagName("couponTotalPriceNormalTax")[0].firstChild.nodeValue),
                                coupon_total_price_reduced_tax= int(order_id_elm.getElementsByTagName("couponTotalPriceReducedTax")[0].firstChild.nodeValue),
                                coupon_total_price_no_tax= int(order_id_elm.getElementsByTagName("couponTotalPriceNoTax")[0].firstChild.nodeValue),
                                use_point= use_point,
                                use_point_normal_tax= int(order_id_elm.getElementsByTagName("usePointNormalTax")[0].firstChild.nodeValue),
                                use_point_reduced_tax= int(order_id_elm.getElementsByTagName("usePointReducedTax")[0].firstChild.nodeValue),
                                use_point_no_tax= int(order_id_elm.getElementsByTagName("usePointNoTax")[0].firstChild.nodeValue),
                                use_point_cancel= use_point_cancel,
                                use_au_point_price= int(order_id_elm.getElementsByTagName("useAuPointPrice")[0].firstChild.nodeValue),
                                use_au_point_price_normal_tax= int(order_id_elm.getElementsByTagName("useAuPointPriceNormalTax")[0].firstChild.nodeValue),
                                use_au_point_price_reduced_tax= int(order_id_elm.getElementsByTagName("useAuPointPriceReducedTax")[0].firstChild.nodeValue),
                                use_au_point_price_no_tax= int(order_id_elm.getElementsByTagName("useAuPointPriceNoTax")[0].firstChild.nodeValue),
                                use_au_point= int(order_id_elm.getElementsByTagName("useAuPoint")[0].firstChild.nodeValue),
                                use_au_point_cancel= use_au_point_cancel,
                                request_price= int(order_id_elm.getElementsByTagName("requestPrice")[0].firstChild.nodeValue),
                                request_price_normal_tax= int(order_id_elm.getElementsByTagName("requestPriceNormalTax")[0].firstChild.nodeValue),
                                request_price_reduced_tax= int(order_id_elm.getElementsByTagName("requestPriceReducedTax")[0].firstChild.nodeValue),
                                request_price_no_tax= int(order_id_elm.getElementsByTagName("requestPriceNoTax")[0].firstChild.nodeValue),
                                point_fixed_date=point_fixed_date,
                                point_fixed_status=point_fixed_status,
                                settle_status=settle_status,
                                authori_timelimit_date=authori_timelimit_date.replace('/','-'),
                                pg_result=pg_result,
                                pg_response_detail=pg_response_detail,
                                pg_orderid=pg_orderid,
                                pg_request_price= pg_request_price,
                                pg_request_price_normal_tax= pg_request_price_normal_tax,
                                pg_request_price_reduced_tax= pg_request_price_reduced_tax,
                                pg_request_price_no_tax= pg_request_price_no_tax,
                                coupon_type= coupon_type,
                                coupon_key= coupon_key,
                                card_jagdement= card_jagdement,
                                delivery_name= delivery_name,
                                delivery_method_id= delivery_method_id,
                                delivery_id= delivery_id,
                                elec_receipt_issue_status= elec_receipt_issue_status,
                                elec_receipt_issue_times= elec_receipt_issue_times,
                                delivery_request_day= delivery_request_day.replace('/','-'),
                                delivery_request_time= delivery_request_time,
                                shipping_date= shipping_date.replace('/','-'),
                                shipping_carrier= shipping_carrier,
                                shipping_number=shipping_number,
                                yamato_lnk_mgt_no= yamato_lnk_mgt_no,
                            )
                            obj.save()
                            logger.debug('wow_get_order_info_ajax_res new_obj saved.')
                            # 続いて受注明細を登録
                            for detail in order_id_elm.getElementsByTagName("detail"):

                                total_item_charge_price = 0
                                if len(detail.getElementsByTagName("totalItemChargePrice")) > 0:
                                    if detail.getElementsByTagName("totalItemChargePrice")[0].firstChild:
                                        total_item_charge_price = int(
                                            detail.getElementsByTagName("totalItemChargePrice")[0].firstChild.nodeValue)
                                item_option = ''
                                if len(order_id_elm.getElementsByTagName("itemOption")) > 0:
                                    if order_id_elm.getElementsByTagName("itemOption")[0].firstChild:
                                        item_option = str(
                                            order_id_elm.getElementsByTagName("itemOption")[0].firstChild.nodeValue)
                                gift_message = ''
                                if len(order_id_elm.getElementsByTagName("giftMessage")) > 0:
                                    if order_id_elm.getElementsByTagName("giftMessage")[0].firstChild:
                                        gift_message = str(
                                            order_id_elm.getElementsByTagName("giftMessage")[0].firstChild.nodeValue)
                                noshi_type = ''
                                if len(order_id_elm.getElementsByTagName("noshiType")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiType")[0].firstChild:
                                        noshi_type = str(order_id_elm.getElementsByTagName("noshiType")[0].firstChild.nodeValue)
                                noshi_presenter_name1 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName1")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName1")[0].firstChild:
                                        noshi_presenter_name1 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName1")[0].firstChild.nodeValue)
                                noshi_presenter_name2 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName2")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName2")[0].firstChild:
                                        noshi_presenter_name2 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName2")[0].firstChild.nodeValue)
                                noshi_presenter_name3 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName3")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName3")[0].firstChild:
                                        noshi_presenter_name3 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName3")[0].firstChild.nodeValue)

                                # item_name は取り直して格納
                                my_item_code = str(detail.getElementsByTagName("itemCode")[0].firstChild.nodeValue)
                                item = YaBuyersItemDetail.objects.filter(
                                    gid=my_item_code,
                                ).first()
                                my_item_name = item.wow_gname

                                obj_detail, created_message = WowmaOrderDetail.objects.update_or_create(
                                    orderinfo=obj,
                                    order_detail_id=str(detail.getElementsByTagName("orderDetailId")[0].firstChild.nodeValue),
                                    item_management_id=item_management_id,
                                    item_code=str(detail.getElementsByTagName("itemCode")[0].firstChild.nodeValue),
                                    lot_number=str(detail.getElementsByTagName("lotnumber")[0].firstChild.nodeValue),
                                    #item_name=str(detail.getElementsByTagName("itemName")[0].firstChild.nodeValue),
                                    item_name=my_item_name,
                                    item_option=item_option,
                                    item_option_price=str(detail.getElementsByTagName("itemOptionPrice")[0].firstChild.nodeValue),
                                    gift_wrapping_type=gift_wrapping_type,
                                    gift_wrapping_price=int(detail.getElementsByTagName("giftWrappingPrice")[0].firstChild.nodeValue),
                                    gift_message=gift_message,
                                    noshi_type=noshi_type,
                                    noshi_presenter_name1=noshi_presenter_name1,
                                    noshi_presenter_name2=noshi_presenter_name2,
                                    noshi_presenter_name3=noshi_presenter_name3,
                                    item_cancel_status=str(detail.getElementsByTagName("itemCancelStatus")[0].firstChild.nodeValue),
                                    item_cancel_date=item_cancel_date.replace('/','-'),
                                    before_discount=int(detail.getElementsByTagName("beforeDiscount")[0].firstChild.nodeValue),
                                    discount=int(detail.getElementsByTagName("discount")[0].firstChild.nodeValue),
                                    item_price=int(detail.getElementsByTagName("itemPrice")[0].firstChild.nodeValue),
                                    unit=int(detail.getElementsByTagName("unit")[0].firstChild.nodeValue),
                                    total_item_price=int(detail.getElementsByTagName("totalItemPrice")[0].firstChild.nodeValue),
                                    total_item_charge_price=total_item_charge_price,
                                    tax_type=str(detail.getElementsByTagName("taxType")[0].firstChild.nodeValue),
                                    reduced_tax=str(detail.getElementsByTagName("reducedTax")[0].firstChild.nodeValue),
                                    tax_rate=str(detail.getElementsByTagName("taxRate")[0].firstChild.nodeValue),
                                    gift_point=int(detail.getElementsByTagName("giftPoint")[0].firstChild.nodeValue),
                                    shipping_day_disp_text=str(detail.getElementsByTagName("shippingDayDispText")[0].firstChild.nodeValue),
                                    shipping_time_limit_date=str(detail.getElementsByTagName("shippingTimelimitDate")[0].firstChild.nodeValue),
                                )
                                obj_detail.save()
                                logger.debug('wow_get_order_info_ajax_res new_obj_detail saved.')

                        else:
                            new_obj.orderid = order_id
                            new_obj.shop_id = document[0].shop_id
                            new_obj.order_date = str(order_id_elm.getElementsByTagName("orderDate")[0].firstChild.nodeValue).replace('/', '-')
                            new_obj.sell_method_segment = str(order_id_elm.getElementsByTagName("sellMethodSegment")[0].firstChild.nodeValue)
                            new_obj.release_date = releaseDate.replace('/','-')
                            new_obj.site_and_device = str(order_id_elm.getElementsByTagName("siteAndDevice")[0].firstChild.nodeValue)
                            new_obj.cross_border_ec_trade_kbn = cross_border_ec_trade_kbn
                            new_obj.mail_address = str(order_id_elm.getElementsByTagName("mailAddress")[0].firstChild.nodeValue)
                            new_obj.raw_mail_address = raw_mail_address
                            new_obj.order_name = str(order_id_elm.getElementsByTagName("ordererName")[0].firstChild.nodeValue)
                            new_obj.order_kana = str(order_id_elm.getElementsByTagName("ordererKana")[0].firstChild.nodeValue)
                            new_obj.order_zipcode = str(order_id_elm.getElementsByTagName("ordererZipCode")[0].firstChild.nodeValue)
                            new_obj.order_address = str(order_id_elm.getElementsByTagName("ordererAddress")[0].firstChild.nodeValue)
                            new_obj.order_phone_number_1 = str(order_id_elm.getElementsByTagName("ordererPhoneNumber1")[0].firstChild.nodeValue)
                            new_obj.order_phone_number_2 = order_phone_number_2
                            new_obj.nickname = nickname
                            new_obj.sender_name = str(order_id_elm.getElementsByTagName("senderName")[0].firstChild.nodeValue)
                            new_obj.sender_kana = str(order_id_elm.getElementsByTagName("senderKana")[0].firstChild.nodeValue)
                            new_obj.sender_zipcode = str(order_id_elm.getElementsByTagName("senderZipCode")[0].firstChild.nodeValue)
                            new_obj.sender_address = str(order_id_elm.getElementsByTagName("senderAddress")[0].firstChild.nodeValue)
                            new_obj.sender_phone_number_1 = str(order_id_elm.getElementsByTagName("senderPhoneNumber1")[0].firstChild.nodeValue)
                            new_obj.sender_phone_number_2 = sender_phone_number_2
                            new_obj.sender_shop_cd = sender_shop_cd
                            new_obj.order_option = order_option
                            new_obj.settlement_name = str(order_id_elm.getElementsByTagName("settlementName")[0].firstChild.nodeValue)
                            new_obj.secure_segment = secure_segment
                            new_obj.user_comment = user_comment
                            new_obj.trade_remarks = str(order_id_elm.getElementsByTagName("tradeRemarks")[0].firstChild.nodeValue)
                            new_obj.memo = memo
                            new_obj.order_status = str(order_id_elm.getElementsByTagName("orderStatus")[0].firstChild.nodeValue)
                            new_obj.contact_status = str(order_id_elm.getElementsByTagName("contactStatus")[0].firstChild.nodeValue)
                            new_obj.contact_date = contact_date.replace('/','-')
                            new_obj.authorization_status = str(order_id_elm.getElementsByTagName("authorizationStatus")[0].firstChild.nodeValue)
                            new_obj.authorization_date = authorization_date
                            new_obj.payment_status = str(order_id_elm.getElementsByTagName("paymentStatus")[0].firstChild.nodeValue)
                            new_obj.payment_date = payment_date.replace('/','-')
                            new_obj.ship_status = str(order_id_elm.getElementsByTagName("shipStatus")[0].firstChild.nodeValue)
                            new_obj.ship_date = ship_date.replace('/','-')
                            new_obj.print_status = str(order_id_elm.getElementsByTagName("printStatus")[0].firstChild.nodeValue)
                            new_obj.print_date = print_date.replace('/','-')
                            new_obj.cancel_status = str(order_id_elm.getElementsByTagName("cancelStatus")[0].firstChild.nodeValue)
                            new_obj.cancel_reason = cancel_reason
                            new_obj.cancel_comment = cancel_comment
                            new_obj.cancel_date = cancel_date.replace('/','-')
                            new_obj.total_sale_price = int(order_id_elm.getElementsByTagName("totalSalePrice")[0].firstChild.nodeValue)
                            new_obj.total_sale_price_normal_tax = int(
                                order_id_elm.getElementsByTagName("totalSalePriceNormalTax")[0].firstChild.nodeValue)
                            new_obj.total_sale_price_reduced_tax = int(
                                order_id_elm.getElementsByTagName("totalSalePriceReducedTax")[0].firstChild.nodeValue)
                            new_obj.total_sale_price_no_tax = int(order_id_elm.getElementsByTagName("totalSalePriceNoTax")[0].firstChild.nodeValue)
                            new_obj.total_sale_unit = int(order_id_elm.getElementsByTagName("totalSaleUnit")[0].firstChild.nodeValue)
                            new_obj.postage_price = int(order_id_elm.getElementsByTagName("postagePrice")[0].firstChild.nodeValue)
                            new_obj.postage_price_tax_rate = float(order_id_elm.getElementsByTagName("postagePriceTaxRate")[0].firstChild.nodeValue)
                            new_obj.charge_price = int(order_id_elm.getElementsByTagName("chargePrice")[0].firstChild.nodeValue)
                            new_obj.charge_price_tax_rate = float(order_id_elm.getElementsByTagName("chargePriceTaxRate")[0].firstChild.nodeValue)
                            new_obj.total_item_option_price = int(order_id_elm.getElementsByTagName("totalItemOptionPrice")[0].firstChild.nodeValue)
                            new_obj.total_item_option_price_tax_rate = float(
                                order_id_elm.getElementsByTagName("totalItemOptionPriceTaxRate")[0].firstChild.nodeValue)
                            new_obj.total_gift_wrapping_price = int(
                                order_id_elm.getElementsByTagName("totalGiftWrappingPrice")[0].firstChild.nodeValue)
                            new_obj.total_gift_wrapping_price_tax_rate = float(
                                order_id_elm.getElementsByTagName("totalGiftWrappingPriceTaxRate")[0].firstChild.nodeValue)
                            new_obj.total_price = int(order_id_elm.getElementsByTagName("totalPrice")[0].firstChild.nodeValue)
                            new_obj.total_price_normal_tax = int(order_id_elm.getElementsByTagName("totalPriceNormalTax")[0].firstChild.nodeValue)
                            new_obj.total_price_reduced_tax = int(order_id_elm.getElementsByTagName("totalPriceReducedTax")[0].firstChild.nodeValue)
                            new_obj.total_price_no_tax = int(order_id_elm.getElementsByTagName("totalPriceNoTax")[0].firstChild.nodeValue)
                            new_obj.premium_type = str(order_id_elm.getElementsByTagName("premiumType")[0].firstChild.nodeValue)
                            new_obj.premium_issue_price = int(order_id_elm.getElementsByTagName("premiumIssuePrice")[0].firstChild.nodeValue)
                            new_obj.premium_mall_price = int(order_id_elm.getElementsByTagName("premiumMallPrice")[0].firstChild.nodeValue)
                            new_obj.premium_shop_price = int(order_id_elm.getElementsByTagName("premiumShopPrice")[0].firstChild.nodeValue)
                            new_obj.coupon_total_price = int(order_id_elm.getElementsByTagName("couponTotalPrice")[0].firstChild.nodeValue)
                            new_obj.coupon_total_price_normal_tax = int(
                                order_id_elm.getElementsByTagName("couponTotalPriceNormalTax")[0].firstChild.nodeValue)
                            new_obj.coupon_total_price_reduced_tax = int(
                                order_id_elm.getElementsByTagName("couponTotalPriceReducedTax")[0].firstChild.nodeValue)
                            new_obj.coupon_total_price_no_tax = int(
                                order_id_elm.getElementsByTagName("couponTotalPriceNoTax")[0].firstChild.nodeValue)
                            new_obj.use_point = use_point
                            new_obj.use_point_normal_tax = int(order_id_elm.getElementsByTagName("usePointNormalTax")[0].firstChild.nodeValue)
                            new_obj.use_point_reduced_tax = int(order_id_elm.getElementsByTagName("usePointReducedTax")[0].firstChild.nodeValue)
                            new_obj.use_point_no_tax = int(order_id_elm.getElementsByTagName("usePointNoTax")[0].firstChild.nodeValue)
                            new_obj.use_point_cancel = use_point_cancel
                            new_obj.use_au_point_price = int(order_id_elm.getElementsByTagName("useAuPointPrice")[0].firstChild.nodeValue)
                            new_obj.use_au_point_price_normal_tax = int(
                                order_id_elm.getElementsByTagName("useAuPointPriceNormalTax")[0].firstChild.nodeValue)
                            new_obj.use_au_point_price_reduced_tax = int(
                                order_id_elm.getElementsByTagName("useAuPointPriceReducedTax")[0].firstChild.nodeValue)
                            new_obj.use_au_point_price_no_tax = int(
                                order_id_elm.getElementsByTagName("useAuPointPriceNoTax")[0].firstChild.nodeValue)
                            new_obj.use_au_point = int(order_id_elm.getElementsByTagName("useAuPoint")[0].firstChild.nodeValue)
                            new_obj.use_au_point_cancel = use_au_point_cancel
                            new_obj.request_price = int(order_id_elm.getElementsByTagName("requestPrice")[0].firstChild.nodeValue)
                            new_obj.request_price_normal_tax = int(
                                order_id_elm.getElementsByTagName("requestPriceNormalTax")[0].firstChild.nodeValue)
                            new_obj.request_price_reduced_tax = int(
                                order_id_elm.getElementsByTagName("requestPriceReducedTax")[0].firstChild.nodeValue)
                            new_obj.request_price_no_tax = int(order_id_elm.getElementsByTagName("requestPriceNoTax")[0].firstChild.nodeValue)
                            new_obj.point_fixed_date = point_fixed_date
                            new_obj.point_fixed_status = point_fixed_status
                            new_obj.settle_status = settle_status
                            new_obj.authori_timelimit_date = authori_timelimit_date
                            new_obj.pg_result = pg_result
                            new_obj.pg_response_code = pg_response_code
                            new_obj.pg_response_detail = pg_response_detail
                            new_obj.pg_orderid = pg_orderid
                            new_obj.pg_request_price = pg_request_price
                            new_obj.pg_request_price_normal_tax = pg_request_price_normal_tax
                            new_obj.pg_request_price_reduced_tax = pg_request_price_reduced_tax
                            new_obj.pg_request_price_no_tax = pg_request_price_no_tax
                            new_obj.coupon_type = coupon_type
                            new_obj.coupon_key = coupon_key
                            new_obj.card_jagdement = card_jagdement
                            new_obj.delivery_name = delivery_name
                            new_obj.delivery_method_id = delivery_method_id
                            new_obj.delivery_id = delivery_id
                            new_obj.elec_receipt_issue_status = elec_receipt_issue_status
                            new_obj.elec_receipt_issue_times = elec_receipt_issue_times
                            new_obj.delivery_request_day = delivery_request_day.replace('/','-')
                            new_obj.delivery_request_time = delivery_request_time
                            new_obj.shipping_date = shipping_date.replace('/','-')
                            new_obj.shipping_carrier = shipping_carrier
                            new_obj.shipping_number = shipping_number
                            new_obj.yamato_lnk_mgt_no = yamato_lnk_mgt_no
                            new_obj.save()
                            logger.debug('wow_get_order_info_ajax_res new_obj already exists saved.')

                            # 続いて受注明細を登録

                            for detail in order_id_elm.getElementsByTagName("detail"):

                                total_item_charge_price = 0
                                if len(detail.getElementsByTagName("totalItemChargePrice")) > 0:
                                    if detail.getElementsByTagName("totalItemChargePrice")[0].firstChild:
                                        total_item_charge_price = int(
                                            detail.getElementsByTagName("totalItemChargePrice")[0].firstChild.nodeValue)
                                item_option = ''
                                if len(order_id_elm.getElementsByTagName("itemOption")) > 0:
                                    if order_id_elm.getElementsByTagName("itemOption")[0].firstChild:
                                        item_option = str(
                                            order_id_elm.getElementsByTagName("itemOption")[0].firstChild.nodeValue)
                                gift_message = ''
                                if len(order_id_elm.getElementsByTagName("giftMessage")) > 0:
                                    if order_id_elm.getElementsByTagName("giftMessage")[0].firstChild:
                                        gift_message = str(
                                            order_id_elm.getElementsByTagName("giftMessage")[0].firstChild.nodeValue)
                                noshi_type = ''
                                if len(order_id_elm.getElementsByTagName("noshiType")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiType")[0].firstChild:
                                        noshi_type = str(order_id_elm.getElementsByTagName("noshiType")[0].firstChild.nodeValue)
                                noshi_presenter_name1 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName1")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName1")[0].firstChild:
                                        noshi_presenter_name1 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName1")[0].firstChild.nodeValue)
                                noshi_presenter_name2 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName2")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName2")[0].firstChild:
                                        noshi_presenter_name2 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName2")[0].firstChild.nodeValue)
                                noshi_presenter_name3 = ''
                                if len(order_id_elm.getElementsByTagName("noshiPresenterName3")) > 0:
                                    if order_id_elm.getElementsByTagName("noshiPresenterName3")[0].firstChild:
                                        noshi_presenter_name3 = str(
                                            order_id_elm.getElementsByTagName("noshiPresenterName3")[0].firstChild.nodeValue)

                                new_obj_detail_list = WowmaOrderDetail.objects.filter(
                                    order_detail_id=str(detail.getElementsByTagName("orderDetailId")[0].firstChild.nodeValue)
                                ).all()

                                # item_name は取り直して格納
                                my_item_code = str(detail.getElementsByTagName("itemCode")[0].firstChild.nodeValue)

                                item = YaBuyersItemDetail.objects.filter(
                                    gid=my_item_code,
                                ).first()
                                my_item_name = item.wow_gname

                                if new_obj_detail_list:
                                    for new_obj_detail in new_obj_detail_list:
                                        new_obj_detail.item_management_id=item_management_id
                                        new_obj_detail.item_code=str(detail.getElementsByTagName("itemCode")[0].firstChild.nodeValue)
                                        new_obj_detail.lot_number=str(detail.getElementsByTagName("lotnumber")[0].firstChild.nodeValue)
                                        #new_obj_detail.item_name=str(detail.getElementsByTagName("itemName")[0].firstChild.nodeValue)
                                        new_obj_detail.item_name=my_item_name
                                        new_obj_detail.item_option=item_option
                                        new_obj_detail.item_option_price=str(detail.getElementsByTagName("itemOptionPrice")[0].firstChild.nodeValue)
                                        new_obj_detail.gift_wrapping_type=gift_wrapping_type
                                        new_obj_detail.gift_wrapping_price=int(detail.getElementsByTagName("giftWrappingPrice")[0].firstChild.nodeValue)
                                        new_obj_detail.gift_message=gift_message
                                        new_obj_detail.noshi_type=noshi_type
                                        new_obj_detail.noshi_presenter_name1=noshi_presenter_name1
                                        new_obj_detail.noshi_presenter_name2=noshi_presenter_name2
                                        new_obj_detail.noshi_presenter_name3=noshi_presenter_name3
                                        new_obj_detail.item_cancel_status=str(detail.getElementsByTagName("itemCancelStatus")[0].firstChild.nodeValue)
                                        new_obj_detail.item_cancel_date=item_cancel_date.replace('/','-')
                                        new_obj_detail.before_discount=int(detail.getElementsByTagName("beforeDiscount")[0].firstChild.nodeValue)
                                        new_obj_detail.discount=int(detail.getElementsByTagName("discount")[0].firstChild.nodeValue)
                                        new_obj_detail.item_price=int(detail.getElementsByTagName("itemPrice")[0].firstChild.nodeValue)
                                        new_obj_detail.unit=int(detail.getElementsByTagName("unit")[0].firstChild.nodeValue)
                                        new_obj_detail.total_item_price=int(detail.getElementsByTagName("totalItemPrice")[0].firstChild.nodeValue)
                                        new_obj_detail.total_item_charge_price=total_item_charge_price
                                        new_obj_detail.tax_type=str(detail.getElementsByTagName("taxType")[0].firstChild.nodeValue)
                                        new_obj_detail.reduced_tax=str(detail.getElementsByTagName("reducedTax")[0].firstChild.nodeValue)
                                        new_obj_detail.tax_rate=str(detail.getElementsByTagName("taxRate")[0].firstChild.nodeValue)
                                        new_obj_detail.gift_point=int(detail.getElementsByTagName("giftPoint")[0].firstChild.nodeValue)
                                        new_obj_detail.shipping_day_disp_text=str(detail.getElementsByTagName("shippingDayDispText")[0].firstChild.nodeValue)
                                        new_obj_detail.shipping_time_limit_date=str(detail.getElementsByTagName("shippingTimelimitDate")[0].firstChild.nodeValue)
                                        new_obj_detail.save()
                                        logger.debug('wow_get_order_info_ajax_res new_obj_detail already exists saved.')
                                else:
                                    logger.debug('wow_get_order_info_ajax_res new_obj_detail could not found? ')

                # if
                msg = msg + msg
                ret_code = document[1].getElementsByTagName("status")[0].firstChild.nodeValue
                """
                d = {
                    'msg': msg + msg,
                    'ret_code': document.getElementsByTagName("status")[0].firstChild.nodeValue,
                }
                """
                #return JsonResponse(d)
            else:
                msg = msg + 'no_document'
                ret_code = 1

    except:
        # 更新時にエラー？
        logger.info(
            '--> error(info). wow_get_order_info_ajax_res msg[{}] '.format(traceback.format_exc()))
        logger.debug(
            '--> error. wow_get_order_info_ajax_res msg[{}] '.format(traceback.format_exc()))
        msg += traceback.format_exc()
        ret_code = -1

    # for
    d = {
        'msg': msg,
        'ret_code': ret_code,
    }
    return JsonResponse(d)


# wowma 注文ステータスを送信
def wow_order_seller_chk_ajax_res(request):
    model = WowmaOrderInfo
    logger.debug("--- wow_order_seller_chk_ajax_res in")
    pk = request.POST.get('pk')
    my_ret_code = 0
    if pk:
        order = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)
    order_status = request.POST.get('order_status')  # 注文ステータス

    # wowmaにアクセス
    wowma_access = WowmaAccess(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'

    res_list = wowma_access.wowma_update_trade_sts_proc(
        order.orderid,
        order_status,
        )

    for res_item in res_list:
        my_ret_code = res_item['res_code']
        my_ret_msg = res_item['res_msg']
        msg += my_ret_msg
        if my_ret_code == 0:
            # 更新に成功している。次の処理は行わない
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }
    return JsonResponse(d)


# wowma 注文情報　発送日や追跡番号を送信
def wow_order_sending_info_ajax(request):
    model = WowmaOrderInfo
    logger.debug("--- wow_order_sending_info_ajax in")
    my_ret_code = 0
    pk = request.POST.get('pk')
    if pk:
        order = model.objects.get(pk=pk)
    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)
    shipping_date = request.POST.get('shipping_date')  # 配送会社
    shipping_carrier = request.POST.get('shipping_carrier')  # 配送会社
    shipping_number = request.POST.get('shipping_number')  # 送り状番号
    logger.debug("--- wow_order_sending_info_ajax shipping_carrier[{}]".format(shipping_carrier))

    # wowmaにアクセス
    wowma_access = WowmaAccess(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'

    # wowmaの商品情報を検索
    res_list = wowma_access.wowma_update_trade_info_proc(
        order.orderid,
        shipping_date,
        shipping_carrier,
        shipping_number,
    )

    for res_item in res_list:
        my_ret_code = res_item['res_code']
        my_ret_msg = res_item['res_msg']
        msg += my_ret_msg
        if my_ret_code == 0:
            # 更新に成功している。次の処理は行わない
            # DBを更新しておく
            order.shipping_date = shipping_date
            order.shipping_number = shipping_number
            order.shipping_carrier = shipping_carrier
            """
            if int(shipping_carrier) == 1:
                order.shipping_carrier = 'クロネコヤマト'
            elif int(shipping_carrier) == 2:
                order.shipping_carrier = '佐川急便'
            elif int(shipping_carrier) == 3:
                order.shipping_carrier = 'JPエクスプレス（旧 日本通運）'
            elif int(shipping_carrier) == 4:
                order.shipping_carrier = '福山通運'
            elif int(shipping_carrier) == 5:
                order.shipping_carrier = '西濃運輸'
            elif int(shipping_carrier) == 6:
                order.shipping_carrier = '日本郵便'
            else:
                order.shipping_carrier = 'その他配送会社'
            """

            # ステータスは完了にしておく
            order.order_status = '完了'
            order.ship_status = 'Y'
            order.save()
            logger.debug("--- wow_order_sending_info_ajax saved 配送業者[{}] 配送日[{}] 配送番号[{}]".format(
                order.shipping_carrier, order.shipping_date, order.shipping_number
            ))
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)


# qoo10 バイヤーズに発注をかける
def qoo_do_order_buyers_ajax(request):
    model = QooOrderInfo
    msg = ''
    res_code = ''
    logger.debug("--- qoo_do_order_buyers_ajax in")
    pk = request.POST.get('pk')
    payment_method = request.POST.get('payment_method')
    if pk:
        # ここでサププロセスをキック
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py qoo_do_buyers_order --pk "
        cmd += pk + " --payment_method " + payment_method
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)

        # pkが得られたらコマンドをキック

    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # 以下、受注した商品コードからバイヤーズにアクセスして購入のフローを。
    msg = 'start:'

    res_msg = 'qoo_do_order_buyers_ajax: start'
    msg += res_msg
    d = {
        'msg': msg,
        'ret_code': res_code,
    }
    logger.debug("--- qoo_do_order_buyers_ajax end.msg:[{}]".format(msg))

    return JsonResponse(d)


# wowma バイヤーズに発注をかける
def wow_do_order_buyers_ajax(request):
    model = WowmaOrderInfo
    msg = ''
    res_code = ''
    logger.debug("--- wow_do_order_buyers_ajax in")
    pk = request.POST.get('pk')
    payment_method = request.POST.get('payment_method')
    if pk:
        #order = model.objects.get(pk=pk)
        # ここでサププロセスをキック
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_do_buyers_order --pk "
        cmd += pk + " --payment_method " + payment_method
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        #msg += ' maybe ok.' + p.stdout.readline()
        msg += ' maybe ok.' + str(p.pid)

        # pkが得られたらコマンドをキック

    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # 以下、受注した商品コードからバイヤーズにアクセスして購入のフローを。
    msg = 'start:'
    #buinfo_obj = BuyersInfo(logger)
    # バイヤーズにログインしておく
    #buinfo_obj.login_buyers()

    # wowmaの商品情報を検索
    """
    res_code, res_msg = wowma_access.wowma_update_trade_info_proc(
        order.orderid,
        shipping_date,
        shipping_carrier,
        shipping_number,
    )
    """

    res_msg = 'wow_do_order_buyers_ajax: start'
    msg += res_msg
    d = {
        'msg': msg,
        'ret_code': res_code,
    }
    logger.debug("--- wow_do_order_buyers_ajax end.msg:[{}]".format(msg))

    return JsonResponse(d)


# wowma 指定されたメール種別（type）でgmailを送信
def wow_send_gmail_ajax(request):
    model = WowmaOrderInfo
    msg = ''
    res_code = ''
    logger.info("--- wow_send_gmail_ajax in(info)")
    logger.debug("--- wow_send_gmail_ajax in")
    pk = request.POST.get('pk')
    mail_type = request.POST.get('mail_type')
    other_message = request.POST.get('other_message')
    #payment_method = request.POST.get('payment_method')
    if pk:
        logger.info("--- wow_send_gmail_ajax pk:[{}]".format(pk))
        #order = model.objects.get(pk=pk)
        # ここでサププロセスをキック
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_send_gmail --pk "
        cmd += pk + " --mail_type " + mail_type + " --other_message " + other_message
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)

        # pkが得られたらコマンドをキック

    else:
        logger.info("--- wow_send_gmail_ajax cant get pt")
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    msg = 'start:'

    res_msg = 'wow_send_gmail_ajax: start'
    msg += res_msg
    d = {
        'msg': msg,
        'ret_code': res_code,
    }
    logger.debug("--- wow_send_gmail_ajax end.msg:[{}]".format(msg))

    return JsonResponse(d)

def get_qoo_asin_detail_upd_csv(request):
    """
    20220807 追加。指定したASINのリストCSVをアップロードして
    SP-API呼び出しでUS or JPからデータを引っ張る。
    Qoo10販売用として対象は絞るイメージ
    なんならついでにKeepa APIも呼び出して詳細を保存したいが・・

    ★取り込むcsvのフォーマット
    | asin | wholesale_price | wholesale_name |
    asin:asinコードそのまま
    wholesale_price: 卸業者の下代
    wholesale_name: 卸業者の名称

    """

    logger.debug("get_qoo_asin_detail_upd_csv in")

    msg = "get_qoo_asin_detail_upd_csv start."
    # まず、フォームから渡されるCSVをとりこみましょ
    if request.method == 'POST':
        try:
            form = QooAsinUpdCsvForm(request.POST, request.FILES)
            if form.is_valid():
                form_data = TextIOWrapper(request.FILES['file'].file, encoding='utf-8')
                csv_file = csv.reader(form_data, delimiter="\t")

                # QooAsinDetail の csv_no に、取り込んだcsv単位で管理用連番をふる。 + 1
                db_entries = QooAsinDetail.objects.all().order_by("-csv_no")[0:1]
                if not db_entries:
                    new_csv_no = 1
                else:
                    old_csv_no = db_entries[0].csv_no
                    new_csv_no = old_csv_no + 1

                for i, line in enumerate(csv_file):
                    if i == 0:
                        continue
                    if len(line) < 4:
                        # form is_validがNG
                        params = {
                            'title': 'csvの取り込み失敗',
                            'message': 'csvの形式が正しくありません(行の数が足らない:[' + str(len(line)) + '])',
                        }
                        return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)

                    msg += '<br> QooAsinDetail save start.'
                    #msg += '<br>0[{}]1[{}]2[{}]3[{}]4[{}]5[{}]6[{}]'.format(line[0],line[1],line[2],line[3],line[4],line[5],line[6])
                    asin_obj, created = QooAsinDetail.objects.get_or_create(
                        asin=line[0],
                        defaults={
                            'csv_no': new_csv_no,
                            'wholesale_price': line[1],
                            'wholesale_name': line[2],
                        },
                    )
                    if not created:
                        asin_obj.csv_no = new_csv_no
                        asin_obj.asin = line[0]
                        asin_obj.wholesale_price = line[1]
                        asin_obj.wholesale_name = line[2]
                        asin_obj.save()
                    msg += '<br> QooAsinDetail save done.'

                msg += "<br> csv-> all db set ok."
                # サブプロセスでyagetのコマンドをキックする
                msg += '<br>--------------------'
                msg += '<br> be on kick csvno. [' + str(new_csv_no) + ']'
                # ここでサププロセスをキック
                cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --csv_no "
                #cmd = "python3.6 /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback "
                cmd += str(new_csv_no)
                msg += ' cmd[' + cmd + ']'

                # 2019/7/6 以下は普通の呼び出しだったが標準出力を取りたい
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()
                msg += ' <br>pid:[' + str(p.pid) + ']'

                msg += '<br>--------------------'
                msg += "<br> end of get_qoo_asin_detail_upd_csv"
                params = {
                    'title': 'CSV UPLOAD完了。ASIN情報の更新を開始します',
                    'message': msg,
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_upd_csv called [exec_get_qoo_asin_detail_upd_csv]")
                return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)
            else:
                # form is_validがNG
                params = {
                    'title': 'csvの取り込み失敗',
                    'message': 'csvの形式が正しくありません',
                }
                logger.debug("get_qoo_asin_detail_upd_csv invalid csv format.")
                return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)
        except Exception as e:
            msg += str(traceback.format_tb(e.__traceback__))
            params = {
                'title': 'CSV UPLOAD 失敗・・',
                'message': msg,
                'form': form,
            }
            logger.debug("get_qoo_asin_detail_upd_csv invalid exception occured[{}]".format(traceback.format_tb(e.__traceback__)))
            return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)

    else:
        csvform = QooAsinUpdCsvForm()
        params = {
            'title': '(Qoo10用) ASINリストCSVによるASIN詳細情報取得 UPLOAD FORM',
            'message': 'CSVを指定してアップロードしてください',
            'form': csvform,
        }

        logger.debug("get_qoo_asin_detail_upd_csv no csv entered.")
        return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)

    return

def get_qoo_asin_detail_single(request):
    """
    20220820 追加。指定したASIN単体について
    SP-API呼び出しでUS or JPからデータを引っ張る。
    Qoo10販売用として対象は絞るイメージ
    なんならついでにKeepa APIも呼び出して詳細を保存したいが・・

    POST引数はasinだけ。

    """

    logger.debug("get_qoo_asin_detail_single in")

    msg = "get_qoo_asin_detail_single start."
    # まず、フォームから渡されるCSVをとりこみましょ
    if request.method == 'POST':
        try:
            form = QooAsinUpdAsinForm(request.POST)
            wholesale_price = 0
            if request.POST['wholesale_price']:
                wholesale_price = int(request.POST['wholesale_price'])

            if form.is_valid():
                msg += '<br> QooAsinDetail save start(single).'
                asin_obj, created = QooAsinDetail.objects.get_or_create(
                    asin=request.POST['asin'],
                    defaults={
                        'csv_no': int(0),
                        'wholesale_price': wholesale_price,
                        'wholesale_name': request.POST['wholesale_name'],
                    },
                )
                if not created:
                    asin_obj.csv_no = 0
                    asin_obj.asin = request.POST['asin']
                    asin_obj.wholesale_price = wholesale_price
                    asin_obj.wholesale_name = request.POST['wholesale_name']
                    asin_obj.save()
                msg += '<br> QooAsinDetail save done.'

                msg += "<br> csv-> all db set ok."
                # サブプロセスでyagetのコマンドをキックする
                msg += '<br>--------------------'
                # ここでサププロセスをキック
                cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --asin "
                #cmd = "python3.6 /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --asin "
                cmd += str(request.POST['asin'])
                cmd += ' --csv_no ' + str(0) # csv_no は空でいい
                msg += ' cmd[' + cmd + ']'

                # 2019/7/6 以下は普通の呼び出しだったが標準出力を取りたい
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()
                msg += ' <br>pid:[' + str(p.pid) + ']'

                msg += '<br>--------------------'
                msg += "<br> end of get_qoo_asin_detail_single"
                params = {
                    'title': 'ASIN情報の更新を開始します・・・',
                    'message': msg,
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_single called [exec_get_qoo_asin_detail_upd_csv]")
                return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)
            else:
                # form is_validがNG
                params = {
                    'title': 'asin取り込み失敗',
                    'message': 'asinの形式が正しくありません',
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_single invalid csv format.")
                return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)
        except Exception as e:
            msg += str(traceback.format_tb(e.__traceback__))
            params = {
                'title': 'ASIN UPLOAD 失敗・・',
                'message': msg,
                'form': form,
            }
            logger.debug("get_qoo_asin_detail_single invalid exception occured[{}]".format(traceback.format_tb(e.__traceback__)))
            return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)

    else:
        asinform = QooAsinUpdAsinForm() # FormはASINを個別入力するフォームに
        params = {
            'title': '(Qoo10用) ASIN詳細情報取得 UPLOAD FORM',
            'message': 'ASINを指定してください',
            'form': asinform,
        }

        logger.debug("get_qoo_asin_detail_single no asin entered.")
        return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)

    return


class QooAsinDetailList(generic.ListView):
    """
    QooAsinDetailテーブルの一覧表作成
    """
    model = QooAsinDetail
    template_name = 'yaget/qoo_asin_detail_list.html'
    paginate_by = 25

    def post(self, request, *args, **kwargs):
        form_value_imp_asin = [
            self.request.POST.get('csv_no', None),
            self.request.POST.get('asin', None),
            self.request.POST.get('shopid', None),
            self.request.POST.get('y_cat_1', None),
            self.request.POST.get('myshop_cat_1', None),
            self.request.POST.get('myshop_cat_2', None),
            self.request.POST.get('create_date_from', None),
            self.request.POST.get('create_date_to', None),
        ]
        request.session['form_value_imp_asin'] = form_value_imp_asin
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 抽出件数を絞る
    def get_queryset(self, queryset=None):
        #return YaShopImportAmaGoodsDetail.objects.all()[:10]

        if 'form_value_qoo_asin' in self.request.session:
            form_value_qoo_asin = self.request.session['form_value_qoo_asin']
            csv_no = form_value_qoo_asin[0]
            asin = form_value_qoo_asin[1]
            shopid = form_value_qoo_asin[2]
            y_cat_1 = form_value_qoo_asin[3]
            myshop_cat_1 = form_value_qoo_asin[4]
            myshop_cat_2 = form_value_qoo_asin[5]
            create_date_from = form_value_qoo_asin[6]
            create_date_to = form_value_qoo_asin[7]
            # 検索条件
            condition_csv_no = Q()
            condition_asin = Q()
            condition_shopid = Q()
            condition_y_cat_1 = Q()
            condition_myshop_cat_1 = Q()
            condition_myshop_cat_2 = Q()
            condition_create_date_from = Q()
            condition_create_date_to = Q()
            if len(csv_no) != 0 and csv_no[0]:
                condition_csv_no = Q(csv_no__icontains=csv_no)
            if len(asin) != 0 and asin[0]:
                condition_asin = Q(asin__contains=asin)
            if len(shopid) != 0 and shopid[0]:
                condition_shopid = Q(shopid__contains=shopid)
            if len(y_cat_1) != 0 and y_cat_1[0]:
                condition_y_cat_1 = Q(y_cat_1__contains=y_cat_1)
            if len(myshop_cat_1) != 0 and myshop_cat_1[0]:
                condition_myshop_cat_1 = Q(myshop_cat_1__contains=myshop_cat_1)
            if len(myshop_cat_2) != 0 and myshop_cat_2[0]:
                condition_myshop_cat_2 = Q(myshop_cat_2__contains=myshop_cat_2)
            if len(create_date_from) != 0 and create_date_from[0]:
                condition_create_date_from = Q(create_date__gte=create_date_from)
            if len(create_date_to) != 0 and create_date_to[0]:
                condition_create_date_to = Q(create_date__lte=create_date_to)
            return QooAsinDetail.objects.select_related().filter(
                condition_csv_no &
                condition_asin &
                condition_shopid &
                condition_y_cat_1 &
                condition_myshop_cat_1 &
                condition_myshop_cat_2 &
                condition_create_date_from &
                condition_create_date_to
            ).order_by("-update_date")[:10000]
        else:
            # 何も返さない
            return QooAsinDetail.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        csv_no = ''
        asin = ''
        shopid = ''
        y_cat_1 = ''
        myshop_cat_1 = ''
        myshop_cat_2 = ''
        create_date_from = ''
        create_date_to = ''
        if 'form_value_qoo_asin' in self.request.session:
            form_value_qoo_asin = self.request.session['form_value_qoo_asin']
            csv_no = form_value_qoo_asin[0]
            asin = form_value_qoo_asin[1]
            shopid = form_value_qoo_asin[2]
            y_cat_1 = form_value_qoo_asin[3]
            myshop_cat_1 = form_value_qoo_asin[4]
            myshop_cat_2 = form_value_qoo_asin[5]
            create_date_from = form_value_qoo_asin[6]
            create_date_to = form_value_qoo_asin[7]
        default_data = {'csv_no': csv_no,  # csv_no
                        'asin': asin,  # asin
                        'shopid': shopid,  # shopid
                        'y_cat_1': y_cat_1,  # y_cat_1
                        'myshop_cat_1': myshop_cat_1,  # myshop_cat_1
                        'myshop_cat_2': myshop_cat_2,  # myshop_cat_2
                        'create_date_from': create_date_from,
                        'create_date_to': create_date_to,
                        }
        test_form = QooAsinDetailSearchForm(initial=default_data) # 検索フォーム
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['obj_all_cnt'] = QooAsinDetail.objects.all().count()
        return ctx

class QooAsinDetailDetail(generic.DetailView):
    """
    QooAsinDetailテーブルのレコード詳細
    """
    template_name = 'yaget/qoo_asin_detail_detail.html'
    model = QooAsinDetail

class QooAsinDetailDelete(generic.DeleteView):
    """
    QooAsinDetailテーブルのレコード削除
    """
    template_name = 'yaget/qoo_asin_detail_delete.html'
    model = QooAsinDetail
    success_url = reverse_lazy('yaget:qoo_asin_detail_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '「{}」を削除しました'.format(self.object))
        return result


class QooAsinDetailCreate(generic.CreateView):
    """
    QooAsinDetailテーブルのレコード作成
    """
    template_name = 'yaget/qoo_asin_detail_create.html'
    model = QooAsinDetail
    fields = [
        'asin',
        'title',
        'url',
        'amount',
        'binding',
        'brand',
        'color',
        'department',
        'is_adlt',
        'i_height',
        'i_length',
        'i_width',
        'i_weight',
        'p_height',
        'p_length',
        'p_width',
        'p_weight',
        'rank_cat_1',
        'rank_1',
        'rank_cat_2',
        'rank_2',
        'rank_cat_3',
        'rank_3',
        'shopid',
        'gid',
        'csv_no',
        'y_cat_1',
        'y_cat_2',
        'myshop_cat_all',
        'myshop_cat_1',
        'myshop_cat_2'
    ]

    def get_success_url(self):
        return reverse('yaget:qoo_asin_detail_detail', kwargs={'pk': self.object.pk})


class QooAsinDetailUpdate(generic.UpdateView):
    template_name = 'yaget/qoo_asin_detail_update.html'
    model = QooAsinDetail
    fields = [
        'asin',
        'title',
        'url',
        'amount',
        'binding',
        'brand',
        'color',
        'department',
        'is_adlt',
        'i_height',
        'i_length',
        'i_width',
        'i_weight',
        'p_height',
        'p_length',
        'p_width',
        'p_weight',
        'rank_cat_1',
        'rank_1',
        'rank_cat_2',
        'rank_2',
        'rank_cat_3',
        'rank_3',
        'shopid',
        'gid',
        'csv_no',
        'y_cat_1',
        'y_cat_2',
        'myshop_cat_all',
        'myshop_cat_1',
        'myshop_cat_2'
        ]

    def get_success_url(self):
        return reverse('yaget:qoo_asin_detail_detail', kwargs={'pk': self.object.pk})

    def get_form(self):
        form = super(QooAsinDetailUpdate, self).get_form()
        form.fields['asin'].label = 'asin'
        form.fields['title'].label = 'title'
        form.fields['url'].label = 'url'
        form.fields['amount'].label = 'amount'
        form.fields['binding'].label = 'binding'
        form.fields['brand'].label = 'brand'
        form.fields['color'].label = 'color'
        form.fields['department'].label = 'department'
        form.fields['is_adlt'].label = 'is_adlt'
        form.fields['i_height'].label = 'i_height'
        form.fields['i_length'].label = 'i_length'
        form.fields['i_width'].label = 'i_width'
        form.fields['i_weight'].label = 'i_weight'
        form.fields['p_height'].label = 'p_height'
        form.fields['p_length'].label = 'p_length'
        form.fields['p_width'].label = 'p_width'
        form.fields['p_weight'].label = 'p_weight'
        form.fields['rank_cat_1'].label = 'rank_cat_1'
        form.fields['rank_1'].label = 'rank_1'
        form.fields['rank_cat_2'].label = 'rank_cat_2'
        form.fields['rank_2'].label = 'rank_2'
        form.fields['rank_cat_3'].label = 'rank_cat_3'
        form.fields['rank_3'].label = 'rank_3'
        form.fields['shopid'].label = 'shopid'
        form.fields['gid'].label = 'gid'
        form.fields['csv_no'].label = 'csv_no'
        form.fields['y_cat_1'].label = 'y_cat_1'
        form.fields['y_cat_2'].label = 'y_cat_2'
        form.fields['myshop_cat_all'].label = 'myshop_cat_all'
        form.fields['myshop_cat_1'].label = 'myshop_cat_1'
        form.fields['myshop_cat_2'].label = 'myshop_cat_2'
        return form


class QooAsinCsvImport(generic.FormView):
    """
    QooAsinDetailを全件検索して、CSVファイルを取り込みDBに格納します。
    """
    template_name = 'yaget/qoo_asin_csv_import.html'
    success_url = reverse_lazy('yaget:qoo_asin_detail_list')
    form_class = QooAsinUpdCsvForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'QooAsinCsvImportです'
        return ctx

    def form_valid(self, form):
        """postされたTSVファイルを読み込み、YaShopImportCat テーブルに登録します"""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile, delimiter="\t")
        for row in reader:
            """
            YaShopImportCat テーブルをmyshop_cat_all (primary key)で検索します
            """
            qoo_asin, created = QooAsinDetail.objects.get_or_create(asin=row[0])
            qoo_asin.asin = row[0]
            qoo_asin.wholesale_price = row[1]
            qoo_asin.wholesale_name = row[2]
            qoo_asin.update_date = dt.now()
            qoo_asin.save()
        return super().form_valid(form)

def QooAsinCsvExport(request):
    """
    QooAsinDetailのレコードから、CSVファイルを作成してresponseに出力します。
    """
    response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
    tdatetime = dt.now()
    tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
    csvfilename = ''

    if 'form_value_qoo_asin' in request.session:
        form_value_qoo_asin = request.session['form_value_qoo_asin']
        csv_no = form_value_qoo_asin[0]
        asin = form_value_qoo_asin[1]
        shopid = form_value_qoo_asin[2]
        y_cat_1 = form_value_qoo_asin[3]
        myshop_cat_1 = form_value_qoo_asin[4]
        myshop_cat_2 = form_value_qoo_asin[5]
        create_date_from = form_value_qoo_asin[6]
        create_date_to = form_value_qoo_asin[7]

        # 検索条件
        condition_csv_no = Q()
        condition_asin = Q()
        condition_shopid = Q()
        condition_y_cat_1 = Q()
        condition_myshop_cat_1 = Q()
        condition_myshop_cat_2 = Q()
        condition_create_date_from = Q()
        condition_create_date_to = Q()
        if len(csv_no) != 0 and csv_no[0]:
            condition_csv_no = Q(csv_no__contains=csv_no)
        if len(asin) != 0 and asin[0]:
            condition_asin = Q(asin__icontains=asin)
        if len(shopid) != 0 and shopid[0]:
            condition_shopid = Q(shopid__contains=shopid)
        if len(y_cat_1) != 0 and y_cat_1[0]:
            condition_y_cat_1 = Q(y_cat_1__contains=y_cat_1)
        if len(myshop_cat_1) != 0 and myshop_cat_1[0]:
            condition_myshop_cat_1 = Q(myshop_cat_1__contains=myshop_cat_1)
        if len(myshop_cat_2) != 0 and myshop_cat_2[0]:
            condition_myshop_cat_2 = Q(myshop_cat_2__contains=myshop_cat_2)
        if len(create_date_from) != 0 and create_date_from[0]:
            condition_create_date_from = Q(create_date__gte=create_date_from)
        if len(create_date_to) != 0 and create_date_to[0]:
            condition_create_date_to = Q(create_date__lte=create_date_to)

        for retobj_tmp in QooAsinDetail.objects.select_related().filter(
                condition_csv_no &
                condition_asin &
                condition_shopid &
                condition_y_cat_1 &
                condition_myshop_cat_1 &
                condition_myshop_cat_2 &
                condition_create_date_from &
                condition_create_date_to
        ).order_by("-update_date")[:1]:
            csvfilename = tstr + '_asin_' + retobj_tmp.y_cat_1 + '_' + retobj_tmp.myshop_cat_1 + '_' + retobj_tmp.myshop_cat_2 + '.csv'
            csvfilename = csvfilename.replace(' ','').replace('>','_').replace('、','-')

        writer = get_csv_writer(response, csvfilename)

        for retobj in QooAsinDetail.objects.select_related().filter(
                condition_csv_no &
                condition_asin &
                condition_shopid &
                condition_y_cat_1 &
                condition_myshop_cat_1 &
                condition_myshop_cat_2 &
                condition_create_date_from &
                condition_create_date_to
        ).order_by("-update_date")[:10000]:
            writer.writerow([
                retobj.asin,
            ])
    else:
        csvfilename = tstr + '_asin_all.csv'
        writer = get_csv_writer(response, csvfilename)
        for retobj in QooAsinDetail.objects.all():
            writer.writerow([
                retobj.asin,
            ])
    return response
