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
from .models import LwaCredential

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
# Load .env strictly via django-environ
env = environ.Env()
try:
    env.read_env(os.path.join(settings.BASE_DIR, '.env'))
except Exception:
    env.read_env('.env')
from django.http import JsonResponse

import logging
import logging.config
import traceback

# 郢晢ｽｭ郢ｧ・ｰ髫ｪ・ｭ陞ｳ繝ｻ
# 遯ｶ・ｻ郢晁・繝｣郢昶・・定惱・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蟶吮・邵ｺ繝ｻ・ｰ・ｴ陷ｷ蛹ｻ竊醍ｸｺ・ｩ邵ｺ・ｯ邵ｲ竏夲ｼ・ｸｺ・｡郢ｧ蟲ｨ・丹N邵ｺ・ｫ邵ｺ蜷ｶ・狗ｸｲ繧・ｼ邵ｺ荵晢ｼ邵ｺ阮吮蔓郢ｧ蟲ｨ窶ｲON邵ｺ・ｮ邵ｺ・ｾ邵ｺ・ｾ邵ｺ・ｰ邵ｺ・ｨ邵ｲ竏壹Σ郢昴・繝｡邵ｺ・ｮstdout邵ｺ・ｨ邵ｺ荵昴・邵ｺ・｣邵ｺ・ｦ郢ｧ荵昴・邵ｺ繝ｻ
# 郢晢ｽｭ郢ｧ・ｰ邵ｺ蠕鯉ｼ・ｸｺ・｣邵ｺ・｡邵ｺ・ｫ邵ｺ蜉ｱﾂｰ邵ｺ・ｯ邵ｺ讎翫・邵ｺ霈費ｽ檎ｸｺ・ｪ邵ｺ荳岩・郢ｧ荵昴・邵ｺ・ｧ邵ｲ竏ｫ謠ｴ隴・ｽｹ邵ｺ・ｰ邵ｺ莉｣竊鍋ｸｺ蜉ｱ・育ｸｺ繝ｻﾂ繝ｻ
# logging
#logging.basicConfig(filename='/home/django/sample/yaget/management/commands/log/yashop_amamws.log', level=logging.DEBUG)
#logging.config.fileConfig(fname="/home/django/sample/yaget/log/yaget_logging.config", disable_existing_loggers=False)

#logger = logging.getLogger(__name__)

# --- logger 髫ｪ・ｭ陞ｳ繝ｻ-----------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logger.setLevel(20)

# 郢晢ｽｭ郢ｧ・ｰ郢晢ｽｭ郢晢ｽｼ郢昴・・ｨ・ｭ陞ｳ繝ｻ

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
# --- logger 髫ｪ・ｭ陞ｳ繝ｻ-----------------------------------------





# 郢ｧ・｢郢昴・繝ｻ郢晢ｽｭ郢晢ｽｼ郢晏ｳｨ・邵ｺ貅倥Ψ郢ｧ・｡郢ｧ・､郢晢ｽｫ郢ｧ蜑・ｽｿ譎擾ｽｭ蛟･笘・ｹｧ荵昴Ι郢ｧ・｣郢晢ｽｬ郢ｧ・ｯ郢晏現ﾎ・
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
    client_id = env('LWA_CLIENT_ID', default=None)
    if not client_id:
        logger.error('LWA client id not configured (LWA_APP_ID/LWA_CLIENT_ID)')
        return HttpResponse('LWA client id not configured', status=500)

    try:
        callback_url = request.build_absolute_uri(reverse('yaget:spapi_oauth_callback'))
    except Exception:
        callback_url = request.build_absolute_uri('/spapi/oauth/callback/')

    scope = env('SP_API_LWA_SCOPE', default='sellingpartnerapi::migration')
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

    client_id = env('LWA_CLIENT_ID', default=None)
    client_secret = env('LWA_CLIENT_SECRET', default=None)
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

        # Persist to DB\r\n    try:\r\n        LwaCredential.objects.update_or_create(name='default', defaults={'refresh_token': refresh_token})\r\n    except Exception:\r\n        logger.exception('Failed to persist refresh_token to DB')\r\nmessages.success(request, 'SP-API 邵ｺ・ｮ髫ｱ讎雁ｺ・ｸｺ謔滂ｽｮ蠕｡・ｺ繝ｻ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ・ｳefresh_token 邵ｺ・ｯ郢ｧ・ｻ郢昴・縺咏ｹ晢ｽｧ郢晢ｽｳ邵ｺ・ｫ闖ｫ譎擾ｽｭ蛟･・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繧茨ｿ｡闕ｵ繝ｻ・ｿ譎擾ｽｭ蛟･繝ｻ陋ｻ・･鬨ｾ豕鯉ｽｮ貅ｯ・｣繝ｻ・邵ｺ・ｦ邵ｺ荳岩味邵ｺ霈費ｼ樒ｸｲ繝ｻ)
    return HttpResponse('OK: SP-API OAuth completed. refresh_token stored in session.', status=200)


# Ajax郢昴・縺帷ｹ昴・
def ajax_test(request):
    # ajax test
    title = request.POST.get('title')
    msg = 'ajax_test'
    params = {
        'title': 'ajax test start',
        'message': msg,
    }
    return render(request, 'yaget/ajax_test.html', params)

# Ajax郢昴・縺帷ｹ昴・
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

    # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
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


# qoo10 邵ｺ荵晢ｽ芽擒繝ｻ蛻隲繝ｻ・ｰ・ｱ邵ｺ・ｮ陷ｿ髢・ｾ繝ｻ
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

    # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    qoo10obj = Qoo10Access(logger)
    msg = 'qoo陜繝ｻ蛻隲繝ｻ・ｰ・ｱ繝ｻ繝ｻ
    qoo10obj.qoo10_create_cert_key()

    # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
    # Qoo10邵ｺ・ｫ騾具ｽｻ鬪ｭ・ｲ雋ょ現竏ｩ邵ｺ・ｧ邵ｺ繧・ｽ檎ｸｺ・ｰ邵ｲﾂgoods.qoo_gdno邵ｲﾂ邵ｺ・ｫ陋滂ｽ､邵ｺ謔溘・邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ・・郢ｧ繧・ｼ邵ｺ荳翫・qoo_seller_code邵ｺ・ｰ邵ｺ莉｣繝ｻ陜｣・ｴ陷ｷ蛹ｻ・・
    if goods.qoo_gdno or goods.qoo_seller_code:
        # 隴厄ｽｴ隴・ｽｰ
        ret_obj_list = qoo10obj.qoo10_items_lookup_get_item_detail_info(goods)
        chk_flg = 0
        for ret_obj in ret_obj_list:
            if ret_obj['res_code'] != "0":
                logger.debug("--- qoo_goods_detail_info_ajax qoo10 陜繝ｻ蛻隲繝ｻ・ｰ・ｱ邵ｺ・ｮ陷ｿ髢・ｾ蜉ｱ縲堤ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ [{}][{}]".format(ret_obj['res_code'],
                                                                                          ret_obj['res_msg']))
                chk_flg = 1  # 邵ｺ・ｪ邵ｺ・ｫ邵ｺ荵昴♀郢晢ｽｩ郢晢ｽｼ邵ｺ・ｫ邵ｺ・ｪ邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ
                break
        if chk_flg == 0:
            # 陷ｿ髢・ｾ邇ｲ繝ｻ陷峨・
            msg += '[ok][{}][{}]'.format(ret_obj['res_msg'],ret_obj['res_obj'])
            logger.debug("--- qoo_goods_detail_info_ajax qoo10 陜繝ｻ蛻隲繝ｻ・ｰ・ｱ邵ｺ・ｮ陷ｿ髢・ｾ辭婆 [{}][{}]".format(ret_obj['res_code'],
                                                                                            ret_obj['res_msg']))
        else:
            # 陷ｿ髢・ｾ諤懶ｽ､・ｱ隰ｨ繝ｻ
            msg += '[ng]['
            msg += str(ret_obj['res_msg']) + ']'

    else:
        # 陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ諤懶ｽ､・ｱ隰ｨ繝ｻ
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


# qoo10 陜繝ｻ蛻騾具ｽｻ鬪ｭ・ｲ郢晢ｽｻ隴厄ｽｴ隴・ｽｰ
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

    # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    #qoo10obj = Qoo10Access(logger)
    #msg = 'start[' + YagetConfig.verbose_name + ']'
    #qoo10obj.qoo10_create_cert_key()

    msg = ''
    status = False
    qoo10obj = ExecQoo10(logger)

    try:
        # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
        # Qoo10邵ｺ・ｫ騾具ｽｻ鬪ｭ・ｲ雋ょ現竏ｩ邵ｺ・ｧ邵ｺ繧・ｽ檎ｸｺ・ｰ邵ｲﾂgoods.qoo_gdno邵ｲﾂ邵ｺ・ｫ陋滂ｽ､邵ｺ謔溘・邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ・・
        status, msg = qoo10obj.exec_qoo10_goods_update(goods)
        """
        if goods.qoo_gdno:
            # 隴厄ｽｴ隴・ｽｰ
            qoo10obj.qoo10_items_basic_update_goods(goods)
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧会ｽｶ螢ｹ・邵ｺ・ｦ隴厄ｽｴ隴・ｽｰ隴弱ｅ繝ｻ邵ｺ・ｿ邵ｲ竏晁・陷ｩ竏ｬ・ｩ・ｳ驍擾ｽｰ郢ｧ蜻亥ｳｩ隴・ｽｰ
            qoo10obj.qoo10_items_contents_edit_goods_contents(goods)
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧会ｽｶ螢ｹ・邵ｺ・ｦ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ蜻亥ｳｩ隴・ｽｰ
            qoo10obj.qoo10_items_basic_edit_goods_status(goods)
            # 隴厄ｽｴ隴・ｽｰ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧会ｽｶ螢ｹ・邵ｺ・ｦ郢晄ｧｭﾎ晉ｹ昶悪蛻､陷剃ｸ奇ｽ定ｭ厄ｽｴ隴・ｽｰ
            qoo10obj.qoo10_items_contents_edit_goods_multi_image(goods)
            # 隴崢陟募ｾ娯・陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ郢ｧ蜻亥ｳｩ隴・ｽｰ
            qoo10obj.qoo10_items_order_set_goods_price_qty(goods)
        else:
            # 隴・ｽｰ髫募・蛹ｳ鬪ｭ・ｲ
            qoo10obj.qoo10_items_basic_set_new_goods(goods)
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧会ｽｶ螢ｹ・邵ｺ・ｦ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ蜻亥ｳｩ隴・ｽｰ
            qoo10obj.qoo10_items_basic_edit_goods_status(goods)
            # 隴厄ｽｴ隴・ｽｰ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧会ｽｶ螢ｹ・邵ｺ・ｦ郢晄ｧｭﾎ晉ｹ昶悪蛻､陷剃ｸ奇ｽ定ｭ厄ｽｴ隴・ｽｰ
            qoo10obj.qoo10_items_contents_edit_goods_multi_image(goods)
            # 隴崢陟募ｾ娯・陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ郢ｧ蜻亥ｳｩ隴・ｽｰ
            qoo10obj.qoo10_items_order_set_goods_price_qty(goods)
        """
    except:
        # 隴厄ｽｴ隴・ｽｰ隴弱ｅ竊鍋ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ繝ｻ繝ｻ
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

# wowma 陜繝ｻ蛻騾具ｽｻ鬪ｭ・ｲ郢晢ｽｻ隴厄ｽｴ隴・ｽｰ
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
        # wowma邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
        status, msg = wowma_obj.exec_wowma_goods_update(goods, taglist_upd_flg)
    except:
        # 隴厄ｽｴ隴・ｽｰ隴弱ｅ竊鍋ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ繝ｻ繝ｻ
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


# Qoo10 隰暦ｽ･驍ｯ螢ｹ繝ｦ郢ｧ・ｹ郢昴・
def qoo10_cert_test(request):
    # Qoo10邵ｺ・ｮ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｵ郢ｧ雋槭・隴帶ｺｷ蝟ｧ邵ｺ蜉ｱ窶ｻ陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ窶ｻ邵ｺ・ｿ郢ｧ繝ｻ
    qoo10obj = Qoo10Access(logger)
    #msg = ' call qoo10_cert_test start..'
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()
    params = {
        'title': 'qoo10 certification test',
        'message': msg,
    }

    return render(request, 'yaget/qoo10_cert_test.html', params)


# 陜ｨ・ｨ陟趣ｽｫ郢昶・縺臥ｹ昴・縺・
def stock_chk(request):
    # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧyaget邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
    if (request.method == 'POST'):
        msg = ' start stock check.. <br>'
        # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_stock_chk 123"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)
    else:
        msg = ' call stock_chk ..'
    params = {
        'title': '陜ｨ・ｨ陟趣ｽｫ郢昶・縺臥ｹ昴・縺鷹ｫ｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ繝ｻ,
        'message': msg,
    }

    return render(request, 'yaget/stock_chk.html', params)


def top(request):
    return render(request, 'yaget/top.html')

"""
--- google spread sheet ---
陷ｿ繧環繝ｻ・ｼ蝟㏄tps://a-zumi.net/python-google-spreadsheet-api/
闖ｴ・ｿ邵ｺ繝ｻ蟀ｿ
if __name__ == '__main__':
  worksheet = WorkSheet("spreadsheetId")

  # A陋ｻ蜉ｱﾂｰ郢ｧ髻ｻ陋ｻ蜉ｱ竏ｪ邵ｺ・ｧ邵ｺ・ｮ陋滂ｽ､郢ｧ雋槫徐陟輔・
  print(worksheet.get_values('A:C'))

  # E1邵ｺ・ｨG1邵ｺ・ｫ陋滂ｽ､郢ｧ蜻郁ｫｺ陷茨ｽ･
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
        # 郢ｧ・ｷ郢晢ｽｼ郢晏現・弛pen邵ｺ蜉ｱ窶ｻ髴第ｳ悟陪邵ｺ蜷ｶ・狗ｸｲ繧・・郢ｧ鄙ｫ竕邵ｺ蛹ｻ笘・ｹｧ・ｷ郢晢ｽｼ郢晏現繝ｻ sheet1 邵ｺ・ｧ陜暦ｽｺ陞ｳ繝ｻ
        if gsheetname is None:
            return None
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.keyfilename, self.scope)
        gc = gspread.authorize(credentials)
        wks = gc.open(gsheetname).sheet1
        return wks


# --- 闔会ｽ･闕ｳ荵昴・sample邵ｺ荵晢ｽ芽ｬ壽㏍・ｲ繝ｻ
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
            'title': '郢昴・縺帷ｹ晏現ﾎ鍋ｹ晢ｽｼ郢晢ｽｫ邵ｲﾂ鬩溷ｺ・ｿ・｡邵ｺ・ｧ邵ｺ髦ｪ・狗ｸｺ繝ｻ,
            'message':'郢昴・縺帷ｹ晏現ﾎ鍋ｹ晢ｽｼ郢晢ｽｫ邵ｲﾂ鬩溷ｺ・ｿ・｡邵ｺ・ｧ邵ｺ髦ｪ・狗ｸｺ荵昶・',
            'data': page.get_page(num),
        }
    return render(request, 'yaget/test_mail.html', params)


# send_mail
def send_my_mail(request, num=1):
    data = YaItemList.objects.all()
    page = Paginator(data, 3)
    params = {
        'title': '郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ鬨ｾ竏夲ｽ顔ｸｺ・ｾ邵ｺ蜉ｱ笳・,
        'message': '郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ鬨ｾ竏夲ｽ顔ｸｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ繝ｻ,
        'data': page.get_page(num),
    }
    if (request.method == 'POST'):
        if 'button_1' in request.POST:
            params = {
                'title': '郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ鬨ｾ竏夲ｽ顔ｸｺ・ｾ邵ｺ蜉ｱ笳・,
                'message': '邵ｺ鄙ｫ・･郢ｧ鄙ｫ竏ｪ邵ｺ繝ｻ + request.POST['button_1'],
                'data': page.get_page(num),
            }
            return render(request, 'yaget/test_mail.html', params)
    else:
        params = {
            'title': '郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ鬨ｾ竏夲ｽ顔ｸｺ・ｾ邵ｺ繝ｻ,
            'message': '郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ鬨ｾ竏夲ｽ顔ｸｺ・ｾ邵ｺ蜷ｶ・・,
            'data': page.get_page(num),
        }
        return render(request, 'yaget/test_mail.html', params)


def showdetail(request, num=1):
    """ 髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｮ騾具ｽｻ鬪ｭ・ｲ雋ょ現竏ｩ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晏ｳｨ・定叉ﾂ髫包ｽｧ邵ｺ・ｧ髴第鱒笘・"""
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
    # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧyaget邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
    if (request.method == 'POST'):
        yaurl = request.POST['YaUrl']
        form = KickYagetForm(request.POST)
        msg = ' be on kick [' + yaurl + ']'
        # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
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


# 郢ｧ・｢郢昴・繝ｻ郢晢ｽｭ郢晢ｽｼ郢晏ｳｨ・・ｹｧ蠕娯螺郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ邵ｺ・ｮ郢昜ｸ莞ｦ郢晏ｳｨﾎ・
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
        # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧbyers邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
        if (request.method == 'POST'):

            yaurl = request.POST['YaUrl']
            #form = UpdByersCtListForm(request.POST, request.FILES)
            form = UpdByersCtListForm(request.POST)
            if form.is_valid():
                msg = ' be on kick upd_byers_ct_list'
                #handle_uploaded_file(request.FILES['file'])
                # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
                #cmd = "cd /home/django/sample/yaget/management/commands; source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py get_ya_buyers_list "
                cmd = "cd /home/django/sample/yaget/management/commands; source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py get_wowma_buyers_list "

                # 闔臥ｿｫ繝ｻ陟大｢鍋・郢ｧ螳夲ｽｦ荵昶ｻ邵ｺ・ｪ邵ｺ繝ｻ繝ｻ郢晢ｽｻ邵ｺ蠕｡・ｻ・ｮ邵ｺ・ｫ騾具ｽｻ鬪ｭ・ｲ邵ｺ蜉ｱ窶ｻ邵ｺ鄙ｫ・･
                cmd += "12345"
                msg += ' cmd[' + cmd + ']'
                # cmd = "pwd"
                ##p = subprocess.Popen(cmd)
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()

                # 郢晢ｽｪ郢ｧ・｢郢晢ｽｫ郢ｧ・ｿ郢ｧ・､郢晢｣ｰ邵ｺ・ｫ陷ｿ髢・ｾ蜉ｱﾂﾂ郢昴・繝ｰ郢昴・縺堤ｸｺ蜉ｱ笳・ｸｺ繝ｻ竊堤ｸｺ髦ｪ竊徹N邵ｺ・ｫ邵ｺ蜷ｶ・檎ｸｺ・ｰ騾包ｽｻ鬮ｱ・｢邵ｺ・ｮmsg邵ｺ・ｫ隶灘綜・ｺ髢繝ｻ陷牙ｸ呻ｽ定怎・ｺ邵ｺ蟶呻ｽ・

                #p = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
                """
                while p.poll() is None:
                    #print('status:', p.poll(), p.stdout.readline().decode().strip())
                    #msg += 'status:' + str(p.poll()) + p.stdout.readline().decode().strip() + '<br />'
                    msg += p.stdout.readline().decode().strip() + '<br />'
                """

                msg += ' maybe ok.' + str(p.pid)
                # 郢ｧ・｢郢昴・繝ｻ郢晢ｽｭ郢晢ｽｼ郢晉甥・ｮ蠕｡・ｺ繝ｻ蛻､鬮ｱ・｢邵ｺ・ｫ郢晢ｽｪ郢敖郢ｧ・､郢晢ｽｬ郢ｧ・ｯ郢昴・
                params = {
                    'title': '郢昴・繝ｻ郢ｧ・ｿ隴厄ｽｴ隴・ｽｰ鬮｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・,
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

# 髯ｦ譴ｧ辟・
print(wks.row_count)

# 髯ｦ蠕鯉ｽ定怦・ｨ邵ｺ・ｦ陷ｿ髢・ｾ繝ｻ
print(wks.row_values(2))

# 驕ｽ繝ｻ蟲・ｹｧ雋槭・邵ｺ・ｦ陷ｿ髢・ｾ繝ｻ
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


# list 邵ｺ・ｮ郢昴・繝ｻ郢ｧ・ｿ郢ｧ逞ｴpreadsheet邵ｺ・ｫ陞ｻ證ｮ蟷慕ｸｺ蜷ｶ・・
def set_list_to_sheet(request):
    return HttpResponse("Hello yaget getdetail!")
    """
    if (request.method == 'POST'):
        sheetnum = request.POST['sheetnum']
        form = YaSetListToSheet(request.POST)
        # 邵ｺ・ｨ郢ｧ鄙ｫ竕邵ｺ蛹ｻ笘・怦・ｨ闔会ｽｶ
        data = YaItemList.objects.all()
        msg = 'after post..'

        # 郢ｧ・ｷ郢晢ｽｼ郢晏現竊鍋ｹｧ・ｻ郢昴・繝ｨ邵ｺ蜷ｶ・・
        worksheet = WorkSheet(sheetnum)

        # E1邵ｺ・ｨG1邵ｺ・ｫ陋滂ｽ､郢ｧ蜻郁ｫｺ陷茨ｽ･
        worksheet.update('E1:G1', {'values': [1, 2]})

    else:
        msg = 'sheeet num...'
        form = YaSetListToSheet()
        # 邵ｺ・ｨ郢ｧ鄙ｫ竕邵ｺ蛹ｻ笘・怦・ｨ闔会ｽｶ
        data = YaItemList.objects.all()


    params = {
        'title': 'Hello set list to sheet.',
        'message': msg,
        'form':form,
        'data':data,
    }

    # 邵ｺ・ｨ郢ｧ鄙ｫ竕邵ｺ蛹ｻ笘・怦・ｨ闔会ｽｶ
    data = YaItemList.objects.all()

    # 郢ｧ・ｷ郢晢ｽｼ郢晏現竊鍋ｹｧ・ｻ郢昴・繝ｨ邵ｺ蜷ｶ・・
    worksheet = WorkSheet(sheetnum)

    # E1邵ｺ・ｨG1邵ｺ・ｫ陋滂ｽ､郢ｧ蜻郁ｫｺ陷茨ｽ･
    worksheet.update('E1:G1', {'values': [1, 2]})

    # 闕ｳ鄙ｫ窶ｲ鬨ｾ螢ｹ笆ｲ邵ｺ貅假ｽ臥ｹ晢ｽｻ郢晢ｽｻ data 邵ｺ・ｮ陷繝ｻ・ｮ・ｹ郢ｧ雋橸ｽｱ證ｮ蟷慕ｸｺ蜉ｱ窶ｻ邵ｺ・ｿ邵ｺ貅假ｼ・
    # data邵ｺ・ｯ邵ｲ繝ｻ闔会ｽｶ邵ｺ・ｰ邵ｺ謇假ｽｼ繝ｻll 邵ｺ蛟･・・ｸｺ・ｪ邵ｺ蜿琶rst繝ｻ蟲ｨ竊醍ｹｧ蟲ｨ・樒ｸｺ莉｣・狗ｸｺ繝ｻ
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
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = YaBuyersItemDetailSearchForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ陜繝ｻ蛻郢晢ｽｪ郢ｧ・ｹ郢晏現縲堤ｸｺ繝ｻ
        ctx['title'] = '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ陜繝ｻ蛻郢晢ｽｪ郢ｧ・ｹ郢昴・郢ｧ・ｿ郢ｧ・､郢晏現ﾎ・
        ctx['obj_all_cnt'] = YaBuyersItemDetail.objects.all().count()
        return ctx


def BuyersGoodsDetailExport(request):
    """
    YaBuyersItemDetail邵ｲ・郡V郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ蜑・ｽｽ諛医・邵ｺ蜉ｱ窶ｻresponse邵ｺ・ｫ陷・ｽｺ陷牙ｸ呻ｼ邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
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

        # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
        csvfilename = csvfilename.replace(' ','').replace('>','_').replace('邵ｲ繝ｻ,'-')
        writer = get_csv_writer(response, csvfilename)

        # 郢晏･繝｣郢敖髯ｦ蠕後◎郢昴・繝ｨ
        writer.writerow([
            '陜繝ｻ蛻ID',
            '陜繝ｻ蛻郢晢ｽｪ郢晢ｽｳ郢ｧ・ｯ',
            '陜繝ｻ蛻陷ｷ繝ｻ,
            '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            '鬨ｾ螢ｼ・ｸ・ｸ關難ｽ｡隴ｬ・ｼ',
            '陞滂ｽｧ鬩･蜀怜験雎包ｽｨ關難ｽ｡隴ｬ・ｼ',
            '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・,
            '陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ',
            'wow隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'wow郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'wow陜繝ｻ蛻陷ｷ繝ｻ,
            'wow陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'wow雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'wow關難ｽ｡隴ｬ・ｼ',
            'wow陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ',
            'wow鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'wow陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ',
            'wow鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'wow郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID',
            'qoo隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'qoo郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'qoo髮具ｽｩ陞｢・ｲ髢繝ｻ縺慕ｹ晢ｽｼ郢昴・,
            'qoo陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・,
            'qoo陜繝ｻ蛻陷ｷ繝ｻ,
            'qoo陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'qoo雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'qoo關難ｽ｡隴ｬ・ｼ',
            'qoo陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ',
            'qoo鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'qoo陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ',
            'qoo鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'qoo郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID',
            '闖ｴ諛医・隴鯉ｽ･',
            '隴厄ｽｴ隴・ｽｰ隴鯉ｽ･',
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
            # 陞溽判驪､邵ｺ蜷ｶ・玖ｭ√・・ｭ蜉ｱﾂ・ｴhift-jis陞溽判驪､邵ｺ・ｧ郢ｧ・ｳ郢ｧ・ｱ邵ｺ貊捺椢陝・干繝ｻ邵ｺ阮呻ｼ・ｸｺ・ｫ騾具ｽｻ鬪ｭ・ｲ
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

        # 郢晏･繝｣郢敖髯ｦ蠕後◎郢昴・繝ｨ
        writer.writerow([
            '陜繝ｻ蛻ID',
            '陜繝ｻ蛻郢晢ｽｪ郢晢ｽｳ郢ｧ・ｯ',
            '陜繝ｻ蛻陷ｷ繝ｻ,
            '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            '鬨ｾ螢ｼ・ｸ・ｸ關難ｽ｡隴ｬ・ｼ',
            '陞滂ｽｧ鬩･蜀怜験雎包ｽｨ關難ｽ｡隴ｬ・ｼ',
            '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・,
            '陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ',
            'wow隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'wow郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'wow陜繝ｻ蛻陷ｷ繝ｻ,
            'wow陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'wow雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'wow關難ｽ｡隴ｬ・ｼ',
            'wow陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ',
            'wow鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'wow陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ',
            'wow鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'wow郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID',
            'qoo隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'qoo郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'qoo髮具ｽｩ陞｢・ｲ髢繝ｻ縺慕ｹ晢ｽｼ郢昴・,
            'qoo陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・,
            'qoo陜繝ｻ蛻陷ｷ繝ｻ,
            'qoo陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'qoo雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'qoo關難ｽ｡隴ｬ・ｼ',
            'qoo陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ',
            'qoo鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'qoo陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ',
            'qoo鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ,
            'qoo郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID',
            '闖ｴ諛医・隴鯉ｽ･',
            '隴厄ｽｴ隴・ｽｰ隴鯉ｽ･',
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
    YaBuyersItemDetail邵ｲ竏晁・陷ｩ竏ｬ・ｪ・ｬ隴丞ｼｱ竊醍ｸｺ・ｩ邵ｺ・ｫ鬯・・蟯ｼ郢ｧ蝣､・ｵ讒ｭ・企恷・ｼ郢ｧ阮吮味CSV郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ蜑・ｽｽ諛医・邵ｺ蜉ｱ窶ｻresponse邵ｺ・ｫ陷・ｽｺ陷牙ｸ呻ｼ邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
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

        # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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

        # 驍ｵ・ｮ陝・・豐ｿ邵ｺ・ｯ s 陝倶ｹ昶穐郢ｧ鄙ｫ繝ｻ郢晢ｽｫ郢晢ｽｼ郢晢ｽｫ邵ｺ・ｫ邵ｺ蜷ｶ・・
        csvfilename = 's_' + tstr + '_buyers_item_detail.csv'
        csvfilename = csvfilename.replace(' ','').replace('>','_').replace('邵ｲ繝ｻ,'-')
        writer = get_csv_writer(response, csvfilename)

        # 郢晏･繝｣郢敖髯ｦ蠕後◎郢昴・繝ｨ
        writer.writerow([
            '陜繝ｻ蛻ID',
            '陜繝ｻ蛻陷ｷ繝ｻ,
            '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            '鬨ｾ螢ｼ・ｸ・ｸ關難ｽ｡隴ｬ・ｼ',
            '陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ',
            'wow隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'wow郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'wow陜繝ｻ蛻陷ｷ繝ｻ,
            'wow陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'wow雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'qoo隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'qoo郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'qoo陜繝ｻ蛻陷ｷ繝ｻ,
            'qoo陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'qoo雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            '闖ｴ諛医・隴鯉ｽ･',
            '隴厄ｽｴ隴・ｽｰ隴鯉ｽ･',
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
            # 陞溽判驪､邵ｺ蜷ｶ・玖ｭ√・・ｭ蜉ｱﾂ・ｴhift-jis陞溽判驪､邵ｺ・ｧ郢ｧ・ｳ郢ｧ・ｱ邵ｺ貊捺椢陝・干繝ｻ邵ｺ阮呻ｼ・ｸｺ・ｫ騾具ｽｻ鬪ｭ・ｲ
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

        # 郢晏･繝｣郢敖髯ｦ蠕後◎郢昴・繝ｨ
        writer.writerow([
            '陜繝ｻ蛻ID',
            '陜繝ｻ蛻陷ｷ繝ｻ,
            '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            '鬨ｾ螢ｼ・ｸ・ｸ關難ｽ｡隴ｬ・ｼ',
            '陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ',
            'wow隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'wow郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'wow陜繝ｻ蛻陷ｷ繝ｻ,
            'wow陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'wow雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            'qoo隰暦ｽｲ髴郁・諞ｾ雎輔・,
            'qoo郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ',
            'qoo陜繝ｻ蛻陷ｷ繝ｻ,
            'qoo陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ',
            'qoo雎包ｽｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・,
            '闖ｴ諛医・隴鯉ｽ･',
            '隴厄ｽｴ隴・ｽｰ隴鯉ｽ･',
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
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｹｧ雋槭・闔会ｽｶ隶諛・ｽｴ・｢邵ｺ蜉ｱ窶ｻ邵ｲ・郡V郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ雋槫徐郢ｧ鬘假ｽｾ・ｼ邵ｺ・ｿDB邵ｺ・ｫ隴ｬ・ｼ驍城亂・邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
    """
    template_name = 'yaget/buyers_goods_detail_import.html'
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    form_class = BuyersGoodsDetailImportForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'BuyersGoodsDetailImport邵ｲﾂ邵ｺ・ｧ邵ｺ繝ｻ
        return ctx

    def form_valid(self, form):
        """post邵ｺ霈費ｽ檎ｸｺ鬯ｱSV郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ螳夲ｽｪ・ｭ邵ｺ・ｿ髴趣ｽｼ邵ｺ・ｿ邵ｲ縲・BuyersItemDetail 郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｫ騾具ｽｻ鬪ｭ・ｲ邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        #csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 隰悶・・ｮ螢ｹ繝ｧ郢ｧ・｣郢晢ｽｬ郢ｧ・ｯ郢晏現ﾎ懃ｸｺ・ｫcsv邵ｺ・ｧ郢ｧ・ｫ郢ｧ・ｭ郢ｧ・ｳ
        self.write_csv(reader)

        # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
        mymsg = 'goods info update start. '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py upload_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        mymsg += ' maybe ok.' + str(p.pid)

        """
        #reader = csv.reader(csvfile, delimiter="\t")
        for i, row in enumerate(reader):
            if i == 0:
                continue # 郢晏･繝｣郢敖髯ｦ蠕後・鬯溷ｸ吶・邵ｺ繝ｻ

            #YaBuyersItemDetail 郢昴・繝ｻ郢晄じﾎ晉ｹｧ證吠d (primary key)邵ｺ・ｧ隶諛・ｽｴ・｢邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ
            try:
                #ya_b_item_detail, created = YaBuyersItemDetail.objects.get_or_create(gid=row[0])
                ya_b_item_detail = YaBuyersItemDetail.objects.get(gid=row[0])
            except Exception as e:
                # 髫ｧ・ｲ陟冶侭ﾎ樒ｹｧ・ｳ郢晢ｽｼ郢晏ｳｨ窶ｲ邵ｺ・ｪ邵ｺ莉｣・檎ｸｺ・ｰ郢昜ｻ｣縺・
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

    # csv邵ｺ・ｫ郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ陷・ｽｺ陷峨・
    def write_csv(self, reader):
        logger.debug('write_csv in .')
        # csv邵ｺ・ｯ邵ｺ阮呻ｼ・ｸｺ・ｧ騾包ｽｨ隲｢荳岩・郢ｧ荵敖ｰ
        csvname = myupdcsv_dir + 'updcsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'

        # 闔会ｽ･闕ｳ荵昴・郢晏･繝｣郢敖髯ｦ蠕後・邵ｺ・ｿ
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
        # 郢昴・繝ｻ郢ｧ・ｿ髯ｦ蠕後・髴托ｽｽ髫ｪ繝ｻ
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
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｹｧ雋槭・闔会ｽｶ隶諛・ｽｴ・｢邵ｺ蜉ｱ窶ｻ邵ｲ・郡V郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ雋槫徐郢ｧ鬘假ｽｾ・ｼ邵ｺ・ｿDB邵ｺ・ｫ隴ｬ・ｼ驍城亂・邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
    驍ｨ讒ｭ・企恷・ｼ邵ｺ・ｿ鬯・・蟯ｼ霑壹・
    """
    template_name = 'yaget/buyers_goods_detail_small_import.html'
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    form_class = BuyersGoodsDetailSmallImportForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'BuyersGoodsDetailSmallImport邵ｲﾂ邵ｺ・ｧ邵ｺ繝ｻ
        return ctx

    def form_valid(self, form):
        logger.debug("--- BuyersGoodsDetailSmallImport in")

        """post邵ｺ霈費ｽ檎ｸｺ鬯ｱSV郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ螳夲ｽｪ・ｭ邵ｺ・ｿ髴趣ｽｼ邵ｺ・ｿ邵ｲ縲・BuyersItemDetail 郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｫ騾具ｽｻ鬪ｭ・ｲ邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        #csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 隰悶・・ｮ螢ｹ繝ｧ郢ｧ・｣郢晢ｽｬ郢ｧ・ｯ郢晏現ﾎ懃ｸｺ・ｫcsv邵ｺ・ｧ郢ｧ・ｫ郢ｧ・ｭ郢ｧ・ｳ
        self.write_csv(reader)

        # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
        mymsg = 'goods info update start. '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py upload_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        mymsg += ' maybe ok.' + str(p.pid)

        """
        #reader = csv.reader(csvfile, delimiter="\t")
        for i, row in enumerate(reader):
            if i == 0:
                logger.debug("--- BuyersGoodsDetailSmallImport i=0 continue")

                continue # 郢晏･繝｣郢敖髯ｦ蠕後・鬯溷ｸ吶・邵ｺ繝ｻ

            #YaBuyersItemDetail 郢昴・繝ｻ郢晄じﾎ晉ｹｧ遏･yshop_cat_all (primary key)邵ｺ・ｧ隶諛・ｽｴ・｢邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ

            try:
                #ya_b_item_detail, created = YaBuyersItemDetail.objects.get_or_create(gid=row[0])
                logger.debug("--- BuyersGoodsDetailSmallImport gid:[{}]".format(row[0]))
                ya_b_item_detail = YaBuyersItemDetail.objects.get(gid=row[0])
            except Exception as e:
                # 髫ｧ・ｲ陟冶侭ﾎ樒ｹｧ・ｳ郢晢ｽｼ郢晏ｳｨ窶ｲ邵ｺ・ｪ邵ｺ莉｣・檎ｸｺ・ｰ郢昜ｻ｣縺・
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

    # csv邵ｺ・ｫ郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ陷・ｽｺ陷峨・驍・ｽ｡隴城豪豐ｿ)
    def write_csv(self, reader):
        logger.debug('write_csv in .')
        # csv邵ｺ・ｯ邵ｺ阮呻ｼ・ｸｺ・ｧ騾包ｽｨ隲｢荳岩・郢ｧ荵敖ｰ
        csvname = myupdcsv_dir + 's_updcsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'

        # 闔会ｽ･闕ｳ荵昴・郢晏･繝｣郢敖髯ｦ蠕後・邵ｺ・ｿ
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
        # 郢昴・繝ｻ郢ｧ・ｿ髯ｦ蠕後・髴托ｽｽ髫ｪ繝ｻ
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
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ荵晢ｽ芽ｬ悶・・ｮ螢ｹ・・ｹｧ蠕娯螺gid邵ｺ・ｮ陜繝ｻ蛻郢ｧ雋樒ｎ鬮ｯ・､邵ｲ縲姉wma邵ｺ・ｨqoo10邵ｺ荵晢ｽ臥ｹｧ繧・ｎ鬮ｯ・､邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ
    """
    template_name = 'yaget/buyers_goods_delete.html'
    success_url = reverse_lazy('yaget:buyers_goods_delete_confirm')
    form_class = BuyersGoodsDeleteForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = '闕ｳﾂ隲｡・ｬ陷台ｼ∝求邵ｺ・ｮ騾包ｽｻ鬮ｱ・｢邵ｺ・ｧ邵ｺ繝ｻ
        return ctx

    def form_valid(self, form):
        logger.debug("--- BuyersGoodsDelete in")
        #ctx = {'form': form }
        #ctx['form_name'] = 'yaget'
        ctx = self.get_context_data()
        # 驕抵ｽｺ髫ｱ蜥ｲ蛻､鬮ｱ・｢邵ｺ・ｧ邵ｺ・ｮ陷・ｽｦ騾・・
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
        # csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile)

        # 隰悶・・ｮ螢ｹ繝ｧ郢ｧ・｣郢晢ｽｬ郢ｧ・ｯ郢晏現ﾎ懃ｸｺ・ｫcsv邵ｺ・ｧ郢ｧ・ｫ郢ｧ・ｭ郢ｧ・ｳ
        ctx['item_list'] = self._write_csv(reader)
        ctx['message'] = '陷台ｼ∝求郢ｧ雋橸ｽｮ貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ・・

        logger.debug("--- BuyersGoodsDelete confirm out")
        return render(self.request, 'yaget/buyers_goods_delete_confirm.html', ctx)
        #return super().form_valid(form)

        """
        if self.request.POST.get('next', '') == 'confirm':
            # 驕抵ｽｺ髫ｱ蜥ｲ蛻､鬮ｱ・｢邵ｺ・ｧ邵ｺ・ｮ陷・ｽｦ騾・・
            csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='shift-JIS')
            # csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
            reader = csv.reader(csvfile)

            # 隰悶・・ｮ螢ｹ繝ｧ郢ｧ・｣郢晢ｽｬ郢ｧ・ｯ郢晏現ﾎ懃ｸｺ・ｫcsv邵ｺ・ｧ郢ｧ・ｫ郢ｧ・ｭ郢ｧ・ｳ
            ctx['item_list'] = self._write_csv(reader)
            ctx['message'] = '陷台ｼ∝求郢ｧ雋橸ｽｮ貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ・・

            logger.debug("--- BuyersGoodsDelete confirm out")
            return render(self.request, 'yaget/buyers_goods_delete_confirm.html', ctx)

        if self.request.POST.get('next', '') == 'back':
            # 陷医・竊楢ｬ鯉ｽｻ郢ｧ荵昶味邵ｺ繝ｻ
            logger.debug("--- BuyersGoodsDelete back out")
            ctx['message'] = '郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ蟶昶・隰壽ｧｭ・騾ｶ・ｴ邵ｺ蜉ｱ窶ｻ邵ｺ荳岩味邵ｺ霈費ｼ・
            return render(self.request, 'yaget/buyers_goods_delete.html', ctx)

        if self.request.POST.get('next', '') == 'delete':
            # 驕抵ｽｺ髫ｱ蠑婁邵ｺ・ｪ邵ｺ・ｮ邵ｺ・ｧ陷台ｼ∝求郢晁・繝｣郢昶・・堤ｸｺ貅倪螺邵ｺ繝ｻ
            # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
            mymsg = '陷台ｼ∝求郢晁・繝｣郢昶・・定楜貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ繝ｻ郢晢ｽｻ '
            cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
            p = subprocess.Popen(cmd, shell=True)
            mymsg += ' 鬮｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ' + str(p.pid)

            logger.debug("--- BuyersGoodsDelete delete out")
            #return super().form_valid(form)
            ctx['message'] = mymsg
            return render(self.request, 'yaget/buyers_goods_delete.html', ctx)
        else:
            # 雎・ｽ｣陝ｶ・ｸ陷咲ｩゑｽｽ諛翫堤ｸｺ・ｯ邵ｺ阮呻ｼ・ｸｺ・ｯ鬨ｾ螢ｹ・臥ｸｺ・ｪ邵ｺ繝ｻﾂ繧・♀郢晢ｽｩ郢晢ｽｼ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｸ邵ｺ・ｮ鬩包ｽｷ驕假ｽｻ邵ｺ・ｧ郢ｧ繧頑・邵ｺ繝ｻ
            logger.debug("--- BuyersGoodsDelete error occurred?")
            return redirect(reverse_lazy('yaget:buyers_goods_delete'))
        """


    # csv邵ｺ・ｫ郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ陷・ｽｺ陷牙ｸ卍繧・・陷ｩ・・邵ｺ・ｨ陜繝ｻ蛻陷ｷ髦ｪ・帝恷讓雁ｶ檎ｸｺ・ｫ邵ｺ蜉ｱ窶ｻ隰鯉ｽｻ邵ｺ繝ｻ
    def _write_csv(self, reader):
        logger.debug('write_csv in .')
        # csv邵ｺ・ｯ邵ｺ阮呻ｼ・ｸｺ・ｧ騾包ｽｨ隲｢荳岩・郢ｧ荵敖ｰ
        csvname = mydeletecsv_dir + 'deletecsv_' + "{0:%Y%m%d_%H%M%S}".format(datetime.datetime.now()) + '.csv'
        item_list = {}
        # 郢昴・繝ｻ郢ｧ・ｿ髯ｦ蠕後・髴托ｽｽ髫ｪ繝ｻ
        with open(csvname, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for item in reader:
                writer.writerow([
                    item[0],  # 陜繝ｻ蛻id
                    item[1],  # 陜繝ｻ蛻陷ｷ繝ｻ
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
        # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
        msg = '陷台ｼ∝求郢晁・繝｣郢昶・・定楜貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ繝ｻ郢晢ｽｻ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 鬮｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ' + str(p.pid)
        """

        logger.debug("--- BuyersGoodsDelete delete out")
        # return super().form_valid(form)
        context['title'] = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜷ｶ・育ｹｧ・ｿ郢ｧ・､郢晏現ﾎ・
        context['message'] = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜷ｶ・育ｹ晢ｽｼ'
        return render(self.request, 'yaget/buyers_goods_delete_done.html', context)

        """
        params = {
            'title': '陜ｨ・ｨ陟趣ｽｫ郢昶・縺臥ｹ昴・縺鷹ｫ｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ繝ｻ,
            'message': msg,
        }
        return render(self.request, 'yaget/buyers_goods_delete_done.html', params)
        """


def buyers_goods_delete_done(request):
    # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧyaget邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
    if (request.method == 'POST'):
        # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
        msg = '陷台ｼ∝求郢晁・繝｣郢昶・・定楜貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ繝ｻ郢晢ｽｻ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 鬮｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ' + str(p.pid)

        logger.debug("--- BuyersGoodsDeleteDone delete out")
        # return super().form_valid(form)
        title = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ・ｿ郢ｧ・､郢晏現ﾎ・
        msg = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ繝ｻ
    else:
        title = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ・ｿ郢ｧ・､郢晏現ﾎ・get'
        msg = ' buyers_goods_delete_done Get陷ｻ・ｼ邵ｺ・ｰ郢ｧ蠕娯穐邵ｺ蜉ｱ笳・ｸｲ繝ｻ'

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

        # 隴厄ｽｸ邵ｺ蟠趣ｽｾ・ｼ郢ｧ阮吮味郢ｧ蟲ｨ繝ｰ郢昴・繝｡郢ｧ蛛ｵ縺冗ｹ昴・縺・
        msg = '陷台ｼ∝求郢晁・繝｣郢昶・・定楜貅ｯ・｡蠕鯉ｼ邵ｺ・ｾ邵ｺ蜷ｶ繝ｻ郢晢ｽｻ '
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py delete_goods_info"
        p = subprocess.Popen(cmd, shell=True)
        msg += ' 鬮｢蜿･・ｧ荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ' + str(p.pid)

        logger.debug("--- BuyersGoodsDeleteDone delete out")
        # return super().form_valid(form)
        context['title'] = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ・ｿ郢ｧ・､郢晏現ﾎ・
        context['message'] = '陜繝ｻ蛻陷台ｼ∝求郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜉ｱ笳・ｹｧ繝ｻ
        return context
"""


class BuyersGoodsDetailDetail(generic.DetailView):
    """
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
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
        context['title'] = '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context


class BuyersGoodsDetailAjaxRes(generic.DetailView):
    """
    detail邵ｺ荵晢ｽ衛oo10隴厄ｽｴ隴・ｽｰ騾包ｽｨ邵ｺ・ｫ陷ｻ・ｼ邵ｺ・ｰ郢ｧ蠕鯉ｽ・
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
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/buyers_goods_detail_delete.html'
    model = YaBuyersItemDetail
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:buyers_goods_detail_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- BuyersGoodsDetailDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10邵ｺ・ｮ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋樒ｎ鬮ｯ・､邵ｺ・ｫ隴厄ｽｴ隴・ｽｰ
            # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)

            #goods_object = self.get_object()

            self.object.qoo_upd_status = 3  # 陷ｿ髢・ｼ蜍滂ｽｻ繝ｻ・ｭ・｢

            # qoo10邵ｺ荵晢ｽ芽恆莨∝求
            # 邵ｺ・ｾ邵ｺ螟ょ元鬪ｭ・ｲ邵ｺ蠕娯旺郢ｧ荵敖ｰ邵ｺ・ｩ邵ｺ繝ｻﾂｰ邵ｲ繧・・邵ｺ荵昶夢邵ｺ貅假ｽ芽怎・ｦ騾・・・邵ｺ・ｪ邵ｺ繝ｻ
            ret_obj_list = qoo10obj.qoo10_items_lookup_get_item_detail_info(self.object)
            chk_flg = 0
            for ret_obj in ret_obj_list:
                if ret_obj['res_code'] != "0":
                    logger.debug("--- BuyersGoodsDetailDelete qoo10 陜繝ｻ蛻隶諛・ｽｴ・｢邵ｺ・ｧ郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ [{}][{}]".format(ret_obj['res_code'],ret_obj['res_msg'] ))
                    chk_flg = 1  # 邵ｺ・ｪ邵ｺ・ｫ邵ｺ荵昴♀郢晢ｽｩ郢晢ｽｼ邵ｺ・ｫ邵ｺ・ｪ邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ
            if chk_flg == 0:
                # 陜繝ｻ蛻邵ｺ迹夲ｽｦ荵昶命邵ｺ荵昶夢邵ｺ貅倪・邵ｺ髦ｪ笆｡邵ｺ蛟頴o10邵ｺ荵晢ｽ芽恆莨∝求
                qoo10obj.qoo10_items_basic_edit_goods_status(self.object)
                logger.debug("--- BuyersGoodsDetailDelete qoo10 陷台ｼ∝求隴厄ｽｴ隴・ｽｰ ok")
            else:
                logger.debug("--- BuyersGoodsDetailDelete qoo10 邵ｺ・ｧ陝・ｽｾ髮趣ｽ｡陜繝ｻ蛻邵ｺ迹夲ｽｦ荵昶命邵ｺ荵晢ｽ臥ｸｺ・ｪ邵ｺ繝ｻ繝ｻ邵ｺ・ｧ郢ｧ・ｹ郢晢ｽｫ郢晢ｽｼ邵ｲ・ｸowma邵ｺ・ｮ陷・ｽｦ騾・・竊馴け螢ｹ・･")

            # 驍ｯ螢ｹ・邵ｺ・ｦwowma邵ｺ荵晢ｽ芽恆莨∝求
            # 邵ｺ・ｾ邵ｺ螢ｼ閹夊惓竏壹○郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋橸ｽ､蟲ｨ竏ｴ邵ｺ・ｦ邵ｺ荵晢ｽ・
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 陷台ｼ∝求隴厄ｽｴ隴・ｽｰ ok')
                else:
                    messages.error(
                        self.request, 'wowma邵ｺ荵晢ｽ芽恆莨∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma 邵ｺ・ｧ陝・ｽｾ髮趣ｽ｡陜繝ｻ蛻邵ｺ迹夲ｽｦ荵昶命邵ｺ荵晢ｽ臥ｸｺ・ｪ邵ｺ繝ｻ繝ｻ邵ｺ・ｧ郢ｧ・ｹ郢晢ｽｫ郢晢ｽｼ邵ｲ繝ｻB邵ｺ荵晢ｽ芽ｱｸ蛹ｻ笘・)

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '陷台ｼ∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- BuyersGoodsDetailDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- BuyersGoodsDetailDelete out")
        return result
        #     return render(request, 'hello/delete.html', params)


class BuyersGoodsDetailCreate(generic.CreateView):
    """
    YaBuyersItemDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晄・・ｽ諛医・
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
        context['title'] = '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context

    def get_form(self):
        form = super(BuyersGoodsDetailUpdate, self).get_form()
        form.fields['gid'].label = '陜繝ｻ蛻ID'
        form.fields['glink'].label = '陜繝ｻ蛻郢晢ｽｪ郢晢ｽｳ郢ｧ・ｯ'
        form.fields['ss_url'].label = '郢晢ｽｪ郢晢ｽｳ郢ｧ・ｯ陷医・ﾎ懃ｹｧ・ｹ郢晏現繝ｻ郢晢ｽｼ郢ｧ・ｸURL'
        form.fields['bu_ctid'].label = '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID'
        form.fields['gsrc'].label = '郢ｧ・ｵ郢晢｣ｰ郢晞亂縺・ｹ晢ｽｫ騾包ｽｻ陷帝・RL'
        form.fields['gname'].label = '陜繝ｻ蛻陷ｷ繝ｻ
        form.fields['gdetail'].label = '陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ'
        form.fields['wow_lotnum'].label = 'wowma郢晢ｽｭ郢昴・繝ｨ騾｡・ｪ陷ｿ・ｷ'
        form.fields['gnormalprice'].label = '鬨ｾ螢ｼ・ｸ・ｸ關難ｽ｡隴ｬ・ｼ'
        form.fields['gspprice'].label = '陞滂ｽｧ鬩･蜀怜験雎包ｽｨ關難ｽ｡隴ｬ・ｼ'
        form.fields['gcode'].label = '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・
        form.fields['stock'].label = '陜ｨ・ｨ陟趣ｽｫ隰ｨ・ｰ'
        form.fields['wow_upd_status'].label = 'wow隰暦ｽｲ髴郁・諞ｾ雎輔・
        form.fields['wow_on_flg'].label = 'wowma邵ｺ・ｮ陷・ｽｺ陷ｩ竏壹○郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['wow_gname'].label = 'wow陜繝ｻ蛻陷ｷ繝ｻ
        form.fields['wow_gdetail'].label = 'wow陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ'
        form.fields['wow_worn_key'].label = 'wow髫補扱・ｳ・ｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・
        form.fields['wow_price'].label = 'wow關難ｽ｡隴ｬ・ｼ'
        form.fields['wow_fixed_price'].label = 'wow陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ'
        form.fields['wow_postage_segment'].label = 'wow鬨ｾ竏ｵ萓ｭ髫ｪ・ｭ陞ｳ螢ｼ邇・崕繝ｻ
        form.fields['wow_postage'].label = 'wow陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ'
        form.fields['wow_delivery_method_id'].label = 'wow鬩溷涵ﾂ竏ｵ蟀ｿ雎戊ｘD'
        form.fields['wow_ctid'].label = 'wow郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID'
        form.fields['qoo_upd_status'].label = 'qoo隰暦ｽｲ髴郁・諞ｾ雎輔・
        form.fields['qoo_on_flg'].label = 'qoo邵ｺ・ｮ陷・ｽｺ陷ｩ竏壹○郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['qoo_gname'].label = 'qoo陜繝ｻ蛻陷ｷ繝ｻ
        form.fields['qoo_gdetail'].label = 'qoo陜繝ｻ蛻髫ｧ・ｳ驍擾ｽｰ'
        form.fields['qoo_worn_key'].label = 'qoo髫補扱・ｳ・ｨ隲｢荳翫￥郢晢ｽｼ郢晢ｽｯ郢晢ｽｼ郢昴・
        form.fields['qoo_price'].label = 'qoo關難ｽ｡隴ｬ・ｼ'
        form.fields['qoo_fixed_price'].label = 'qoo陜暦ｽｺ陞ｳ螢ｻ・ｾ・｡隴ｬ・ｼ'
        form.fields['qoo_shipping_no'].label = 'qoo鬨ｾ竏ｵ萓ｭ郢ｧ・ｳ郢晢ｽｼ郢昴・
        form.fields['qoo_postage'].label = 'qoo陋溷唱謖ｨ鬨ｾ竏ｵ萓ｭ'
        form.fields['qoo_delivery_method_id'].label = 'qoo鬩溷涵ﾂ竏ｵ蟀ｿ雎戊ｘD'
        form.fields['qoo_ctid'].label = 'qoo郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪID'
        form.fields['qoo_item_qty'].label = 'qoo陜繝ｻ蛻隰ｨ・ｰ鬩･繝ｻ
        form.fields['qoo_standard_img'].label = 'qoo陜繝ｻ蛻闔会ｽ｣髯ｦ・ｨ騾包ｽｻ陷帝・RL'
        form.fields['g_img_src_1'].label = '騾包ｽｻ陷帝・RL_1'
        form.fields['g_img_src_2'].label = '騾包ｽｻ陷帝・RL_2'
        form.fields['g_img_src_3'].label = '騾包ｽｻ陷帝・RL_3'
        form.fields['g_img_src_4'].label = '騾包ｽｻ陷帝・RL_4'
        form.fields['g_img_src_5'].label = '騾包ｽｻ陷帝・RL_5'
        form.fields['g_img_src_6'].label = '騾包ｽｻ陷帝・RL_6'
        form.fields['g_img_src_7'].label = '騾包ｽｻ陷帝・RL_7'
        form.fields['g_img_src_8'].label = '騾包ｽｻ陷帝・RL_8'
        form.fields['g_img_src_9'].label = '騾包ｽｻ陷帝・RL_9'
        form.fields['g_img_src_10'].label = '騾包ｽｻ陷帝・RL_10'
        form.fields['g_img_src_11'].label = '騾包ｽｻ陷帝・RL_11'
        form.fields['g_img_src_12'].label = '騾包ｽｻ陷帝・RL_12'
        form.fields['g_img_src_13'].label = '騾包ｽｻ陷帝・RL_13'
        form.fields['g_img_src_14'].label = '騾包ｽｻ陷帝・RL_14'
        form.fields['g_img_src_15'].label = '騾包ｽｻ陷帝・RL_15'
        form.fields['g_img_src_16'].label = '騾包ｽｻ陷帝・RL_16'
        form.fields['g_img_src_17'].label = '騾包ｽｻ陷帝・RL_17'
        form.fields['g_img_src_18'].label = '騾包ｽｻ陷帝・RL_18'
        form.fields['g_img_src_19'].label = '騾包ｽｻ陷帝・RL_19'
        form.fields['g_img_src_20'].label = '騾包ｽｻ陷帝・RL_20'
        return form


class BatchStatusList(generic.ListView):
    """
    BatchStatus郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = BatchStatusSearchForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class BatchStatusDetail(generic.DetailView):
    """
    BatchStatus郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/batch_status_detail.html'
    model = BatchStatus

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = '郢晁・繝｣郢昶・・ｮ貅ｯ・｡讙取・雎補・繝ｻ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = '郢晁・繝｣郢昶・・ｮ貅ｯ・｡讙取・雎補・繝ｻ髫ｧ・ｳ驍擾ｽｰ(郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ)邵ｺ・ｧ邵ｺ繝ｻ
        return self.render_to_response(context)


class BatchStatusDelete(generic.DeleteView):
    """
    BatchStatus邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/batch_status_delete.html'
    model = BatchStatus
    success_url = reverse_lazy('yaget:batch_status_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        return result


class BlackListList(generic.ListView):
    """
    YaBuyersItemBlackList郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
        #if 'form_value_batch_status_list' in self.request.session:
        #    self.request.session.clear()

        if 'form_value_black_list_list' in self.request.session:
            form_value_black_list_list = self.request.session['form_value_black_list_list']
            gid = form_value_black_list_list[0]
            create_date_from = form_value_black_list_list[1]
            create_date_to = form_value_black_list_list[2]
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = BlackListForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class BlackListDetail(generic.DetailView):
    """
    YaBuyersItemBlackList郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/black_list_detail.html'
    model = YaBuyersItemBlackList

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = '郢晁・繝｣郢昶・・ｮ貅ｯ・｡讙取・雎補・繝ｻ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        return self.render_to_response(context)


class BlackListDelete(generic.DeleteView):
    """
    YaBuyersItemBlackList邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/black_list_delete.html'
    model = YaBuyersItemBlackList
    success_url = reverse_lazy('yaget:black_list_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        return result


class BlackListCreate(generic.CreateView):
    template_name = 'yaget/black_list_create.html'
    model = YaBuyersItemBlackList
    fields = ['gid']

    def get_success_url(self):
        return reverse('yaget:black_list_list')

    def get_form(self):
        form = super(BlackListCreate, self).get_form()
        form.fields['gid'].label = '郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｮ陜繝ｻ蛻id'
        form.fields['gid'].required = True
        return form


class WowmaCatList(generic.ListView):
    """
    WowCategory郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return WowmaCatList.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = WowCategoryForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx

class WowmaCatDetail(generic.DetailView):
    """
    WowmaCatList郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/wowma_cat_detail.html'
    model = WowCategory

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'wowma郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪ邵ｺ・ｮ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
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
        form.fields['create_date'].label = '騾具ｽｻ鬪ｭ・ｲ隴鯉ｽ･'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowma郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'Wowma郢ｧ・ｫ郢昴・縺也ｹ晢ｽｪ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context


class WowmaCatModelList(generic.ListView):
    """
    WowCategory郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
    邵ｺ阮呻ｼ・愾繧環繝ｻ竊鍋ｸｲ繝ｻ
    https://blog.narito.ninja/detail/30/
    郢ｧ・ｯ郢晢ｽｩ郢ｧ・ｹ郢晁侭ﾎ礼ｹ晢ｽｼ郢ｧ蜑・ｽｽ・ｿ邵ｺ繝ｻ竊醍ｹｧ蟲ｨ・・ｸｺ・｣邵ｺ・｡邵ｺ繝ｻ
    https://k2ss.info/archives/2653/
    """
    model = WowCategory
    template_name = 'yaget/wowma_cat_model_list.html'
    paginate_by = 50
    form_class = WowCategoryModelForm

    def get_formset(self, *args, **kwargs):
        """ 髢ｾ・ｪ髴・ｽｫ邵ｺ・ｫ髫ｪ・ｭ陞ｳ螢ｹ・・ｹｧ蠕娯螺郢晢ｽ｢郢昴・ﾎ晉ｸｺ・ｨ郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ邵ｺ荵晢ｽ臥ｹ晁ｼ斐°郢晢ｽｼ郢晢｣ｰ郢ｧ・ｻ郢昴・繝ｨ郢ｧ蜑・ｽｽ諛医・邵ｺ蜷ｶ・・"""
        formset = modelformset_factory(self.model, form=self.form_class, extra=0)
        return formset(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # ListView 邵ｺ繝ｻcontext 郢ｧ蜑・ｽｽ諛奇ｽ檎ｹｧ荵晢ｽ育ｸｺ繝ｻ竊・
        self.object_list = self.get_queryset()
        base_ctx = super().get_context_data()
        page_qs = base_ctx['page_obj'].object_list if base_ctx.get('page_obj') else base_ctx['object_list']

        FormSet = modelformset_factory(self.model, form=self.form_class, extra=0)
        formset = FormSet(request.POST, queryset=page_qs)

        # 騾包ｽｻ鬮ｱ・｢闕ｳ鄙ｫ繝ｻ隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ郢ｧ蛛ｵ縺晉ｹ昴・縺咏ｹ晢ｽｧ郢晢ｽｳ邵ｺ・ｸ繝ｻ莠包ｽｻ鄙ｫ繝ｻ陞ｳ貅ｯ・｣繝ｻ・帝け・ｭ隰悶・・ｼ繝ｻ
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
            # 郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ隴√・・ｭ諤懊・郢ｧ蝣､・ｶ・ｭ隰問・・邵ｺ・ｦ郢晢ｽｪ郢晢ｽｭ郢晢ｽｼ郢昴・
            qs = ('?' + request.META.get('QUERY_STRING')) if request.META.get('QUERY_STRING') else ''
            return redirect(request.path + qs)

        # invalid 邵ｺ・ｮ邵ｺ・ｨ邵ｺ髦ｪ繝ｻ郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ雋樊ｧ郢ｧ竏壺ｻ陷閧ｴ邱帝包ｽｻ
        ctx = self.get_context_data(formset=formset)
        return self.render_to_response(ctx)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return WowmaCatList.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
            #return WowCategory.objects.none()
            return WowCategory.objects.select_related().order_by("-update_date")[:200]

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        # 郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｫ髯ｦ・ｨ驕会ｽｺ邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・玖崕繝ｻ笆｡邵ｺ繝ｻformset 郢ｧ蜑・ｽｽ諛奇ｽ・
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
        test_form = WowCategoryForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class QooShopInfoList(generic.ListView):
    """
    QooShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = QooShopInfoForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'QooShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ'
        return ctx


class QooShopInfoDetail(generic.DetailView):
    """
    QooShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/qoo_shop_info_detail.html'
    model = QooShopInfo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'Qoo郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ邵ｺ・ｮ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'QooShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ髫ｧ・ｳ驍擾ｽｰ'
        return self.render_to_response(context)


class QooShopInfoDelete(generic.DeleteView):
    """
    QooShopInfo邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/qoo_shop_info_delete.html'
    model = QooShopInfo
    success_url = reverse_lazy('yaget:qoo_shop_info_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
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
        form.fields['my_shop_num'].label = 'qoo10邵ｺ・ｮ郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ騾具ｽｻ鬪ｭ・ｲ隲繝ｻ・ｰ・ｱ id'
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
        form.fields['my_shop_num'].label = '郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ騾｡・ｪ陷ｿ・ｷ'
        form.fields['shop_name'].label = '郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ陷ｷ繝ｻ
        form.fields['auth_key'].label = 'auth_key'
        form.fields['user_id'].label = '郢晢ｽｦ郢晢ｽｼ郢ｧ・ｶID'
        form.fields['pwd'].label = '郢昜ｻ｣縺帷ｹ晢ｽｯ郢晢ｽｼ郢昴・
        form.fields['target_url'].label = '髮具ｽｩ陞｢・ｲURL'
        form.fields['from_name'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬨ｾ竏夲ｽ願叉・ｻ陷ｷ繝ｻ
        form.fields['from_postcode'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬩幢ｽｵ關難ｽｿ騾｡・ｪ陷ｿ・ｷ'
        form.fields['from_state'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬩幢ｽｽ鬩慕§・ｺ諛・＝'
        form.fields['from_address_1'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ闖ｴ荵怜恍繝ｻ繝ｻ
        form.fields['from_address_2'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ闖ｴ荵怜恍繝ｻ繝ｻ
        form.fields['from_phone'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['shop_status'].label = '郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['create_date'].label = '騾具ｽｻ鬪ｭ・ｲ隴鯉ｽ･'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Qoo10郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'Qoo10郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context


class WowShopInfoList(generic.ListView):
    """
    WowmaShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = WowShopInfoForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'WowShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ'
        return ctx


class WowShopInfoDetail(generic.DetailView):
    """
    WowmaShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/wow_shop_info_detail.html'
    model = WowmaShopInfo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = 'Wowma郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ邵ｺ・ｮ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'WowShopInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ'
        return self.render_to_response(context)


class WowShopInfoDelete(generic.DeleteView):
    """
    WowmaShopInfo邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/wow_shop_info_delete.html'
    model = WowmaShopInfo
    success_url = reverse_lazy('yaget:wow_shop_info_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
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
        form.fields['my_shop_num'].label = 'wowma邵ｺ・ｮ郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ騾具ｽｻ鬪ｭ・ｲ隲繝ｻ・ｰ・ｱ id'
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
        form.fields['my_shop_num'].label = '郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ騾｡・ｪ陷ｿ・ｷ'
        form.fields['shop_id'].label = '郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻID'
        form.fields['shop_name'].label = '郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ陷ｷ繝ｻ
        form.fields['api_key'].label = 'api_key'
        form.fields['target_url'].label = '髮具ｽｩ陞｢・ｲURL'
        form.fields['from_name'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬨ｾ竏夲ｽ願叉・ｻ陷ｷ繝ｻ
        form.fields['from_postcode'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬩幢ｽｵ關難ｽｿ騾｡・ｪ陷ｿ・ｷ'
        form.fields['from_state'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬩幢ｽｽ鬩慕§・ｺ諛・＝'
        form.fields['from_address_1'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ闖ｴ荵怜恍繝ｻ繝ｻ
        form.fields['from_address_2'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ闖ｴ荵怜恍繝ｻ繝ｻ
        form.fields['from_phone'].label = '騾具ｽｺ鬨ｾ竏昴・邵ｲﾂ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['shop_status'].label = '郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['create_date'].label = '騾具ｽｻ鬪ｭ・ｲ隴鯉ｽ･'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowma郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'Wowma郢ｧ・ｷ郢晢ｽｧ郢昴・繝ｻ隲繝ｻ・ｰ・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context


class ErrorGoodsLogList(generic.ListView):
    """
    ErrorGoodsLog郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = ErrorGoodsLogSearchForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        return ctx


class ErrorGoodsLogDetail(generic.DetailView):
    """
    ErrorGoodsLog郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/error_goods_log_detail.html'
    model = ErrorGoodsLog

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['title'] = '郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ邵ｺ・ｫ邵ｺ・ｪ邵ｺ・｣邵ｺ貅ｷ閹夊惓竏ｵ蟲ｩ隴・ｽｰ邵ｺ・ｮ髫ｧ・ｳ驍擾ｽｰ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = '郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ邵ｺ・ｫ邵ｺ・ｪ邵ｺ・｣邵ｺ貅ｷ閹夊惓竏ｵ蟲ｩ隴・ｽｰ邵ｺ・ｮ髫ｧ・ｳ驍擾ｽｰ郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return self.render_to_response(context)


class ErrorGoodsLogDelete(generic.DeleteView):
    """
    ErrorGoodsLog邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/error_goods_log_delete.html'
    model = ErrorGoodsLog
    success_url = reverse_lazy('yaget:error_goods_log_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        return result


class AllOrderList(generic.ListView):
    """
    AllOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ

        if 'form_all_order_list' in self.request.session:
            form_all_order_list = self.request.session['form_all_order_list']
            qoo_id = form_all_order_list[0]
            wow_id = form_all_order_list[1]
            buyer = form_all_order_list[2]
            create_date_from = form_all_order_list[3]
            create_date_to = form_all_order_list[4]
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = AllOrderInfoForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'all_order_list'
        return ctx


class QooOrderList(generic.ListView):
    """
    QooOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ

        if 'form_qoo_order_list' in self.request.session:
            form_qoo_order_list = self.request.session['form_qoo_order_list']
            seller_id = form_qoo_order_list[0]
            order_no = form_qoo_order_list[1]
            shipping_status = form_qoo_order_list[2]
            buyer = form_qoo_order_list[3]
            order_date = form_qoo_order_list[4]
            create_date_from = form_qoo_order_list[5]
            create_date_to = form_qoo_order_list[6]
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = QooOrderInfoForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'qoo_order_list'
        return ctx


class QooOrderDetail(generic.DetailView):
    """
    QooOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
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
        form.fields['order_no'].label = 'id 雎包ｽｨ隴√・蛻・愾・ｷ'
        form.fields['shipping_status'].label = '鬩溷涵ﾂ竏ｫ諞ｾ隲ｷ繝ｻ
        form.fields['seller_id'].label = '髮具ｽｩ陞｢・ｲ髢繝ｻD'
        form.fields['pack_no'].label = 'id 郢ｧ・ｫ郢晢ｽｼ郢晁ご蛻・愾・ｷ'
        form.fields['order_date'].label = '雎包ｽｨ隴√・蠕・
        form.fields['payment_date'].label = '雎趣ｽｺ雋ょ沺蠕・
        form.fields['est_shipping_date'].label = '騾具ｽｺ鬨ｾ竏ｽ・ｺ莠･・ｮ螢ｽ蠕・
        form.fields['shipping_date'].label = '騾具ｽｺ鬨ｾ竏ｵ蠕・
        form.fields['delivered_date'].label = '鬩溷涵ﾂ竏晢ｽｮ蠕｡・ｺ繝ｻ蠕・
        form.fields['buyer'].label = '髮会ｽｼ陷茨ｽ･髢繝ｻ骭・
        form.fields['buyer_gata'].label = '髮会ｽｼ陷茨ｽ･髢繝ｻ骭舌・蛹ｻ縺咲ｹｧ・ｿ郢ｧ・ｫ郢晏･・ｽｼ繝ｻ
        form.fields['buyer_tel'].label = '髮会ｽｼ陷茨ｽ･髢繝ｻ繝ｻ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['buyer_mobile'].label = '髮会ｽｼ陷茨ｽ･髢繝ｻ繝ｻ隰ｳ・ｺ陝ｶ・ｯ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['buyer_email'].label = '髮会ｽｼ陷茨ｽ･髢繝ｻ繝ｻ隰ｳ・ｺ陝ｶ・ｯ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['item_code'].label = 'Qoo10陜繝ｻ蛻騾｡・ｪ陷ｿ・ｷ'
        form.fields['seller_item_code'].label = '髮具ｽｩ陞｢・ｲ陜繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢昴・
        form.fields['item_title'].label = '陜繝ｻ蛻陷ｷ繝ｻ
        form.fields['option'].label = '郢ｧ・ｪ郢晏干縺咏ｹ晢ｽｧ郢晢ｽｳ'
        form.fields['option_code'].label = '郢ｧ・ｪ郢晏干縺咏ｹ晢ｽｧ郢晢ｽｳ郢ｧ・ｳ郢晢ｽｼ郢昴・
        form.fields['order_price'].label = '陜繝ｻ蛻關難ｽ｡隴ｬ・ｼ'
        form.fields['order_qty'].label = '雎包ｽｨ隴√・辟夐ｩ･繝ｻ
        form.fields['discount'].label = '陜繝ｻ蛻陷托ｽｲ陟第坩竕｡鬯倥・
        form.fields['total'].label = '雎包ｽｨ隴√・辟夐ｩ･謫ｾ・ｼ莠･閹夊惓竏ｽ・ｾ・｡隴ｬ・ｼ + 郢ｧ・ｪ郢晏干縺咏ｹ晢ｽｧ郢晢ｽｳ關難ｽ｡隴ｬ・ｼ - 陷托ｽｲ陟第坩・｡謳ｾ・ｼ繝ｻ
        form.fields['receiver'].label = '陷ｿ諤懷徐闔・ｺ陷ｷ繝ｻ
        form.fields['receiver_gata'].label = '陷ｿ諤懷徐闔・ｺ陷ｷ謳ｾ・ｼ蛹ｻ縺咲ｹｧ・ｿ郢ｧ・ｫ郢晏･・ｽｼ繝ｻ
        form.fields['shipping_country'].label = '邵ｺ髮・ｽｱ鄙ｫ・陷亥現繝ｻ陜暦ｽｽ陞ｳ・ｶ'
        form.fields['zipcode'].label = '鬩幢ｽｵ關難ｽｿ騾｡・ｪ陷ｿ・ｷ'
        form.fields['shipping_addr'].label = '邵ｺ髮・ｽｱ鄙ｫ・陷井ｺ包ｽｽ荵怜恍'
        form.fields['addr1'].label = '闖ｴ荵怜恍(鬩幢ｽｽ鬩慕§・ｺ諛・＝/陝ｶ繧・私騾包ｽｺ隴壹・'
        form.fields['addr2'].label = '闖ｴ荵怜恍(陝ｶ繧・私騾包ｽｺ隴壼床・ｻ・･鬮ｯ繝ｻ'
        form.fields['receiver_tel'].label = '陷ｿ諤懷徐闔・ｺ邵ｺ・ｮ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['receiver_mobile'].label = '陷ｿ諤懷徐闔・ｺ邵ｺ・ｮ隰ｳ・ｺ陝ｶ・ｯ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['hope_date'].label = '鬩溷涵ﾂ竏晢ｽｸ譴ｧ謔崎ｭ鯉ｽ･'
        form.fields['sender_name'].label = '鬨ｾ竏ｽ・ｿ・｡髢繝ｻ
        form.fields['sender_tel'].label = '鬨ｾ竏夲ｽ願叉・ｻ邵ｺ・ｮ鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ'
        form.fields['sender_nation'].label = '鬨ｾ竏夲ｽ願叉・ｻ邵ｺ・ｮ陜暦ｽｽ陞ｳ・ｶ'
        form.fields['sender_zipcode'].label = '鬨ｾ竏夲ｽ願叉・ｻ邵ｺ・ｮ鬩幢ｽｵ關難ｽｿ騾｡・ｪ陷ｿ・ｷ'
        form.fields['sender_addr'].label = '鬨ｾ竏夲ｽ願叉・ｻ邵ｺ・ｮ闖ｴ荵怜恍'
        form.fields['shipping_way'].label = '鬩溷涵ﾂ竏ｵ蟀ｿ雎輔・
        form.fields['shipping_msg'].label = '鬩溷涵ﾂ竏墅鍋ｹ昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ'
        form.fields['payment_method'].label = '雎趣ｽｺ雋ょ沺辟碑ｰｿ・ｵ'
        form.fields['seller_discount'].label = '髮具ｽｩ陞｢・ｲ髢繝ｻ・ｲ・ｰ隲｡繝ｻ迚｡陟第坩・｡繝ｻ
        form.fields['currency'].label = '雎包ｽｨ隴√・竕｡鬯伜涵ﾂ螟奇ｽｲ・ｨ'
        form.fields['shipping_rate'].label = '鬨ｾ竏ｵ萓ｭ'
        form.fields['related_order'].label = '鬮｢・｢鬨ｾ・｣雎包ｽｨ隴√・蛻・愾・ｷ繝ｻ螟ｲ・ｼ蛹ｻﾂ繝ｻ・ｼ迚咏私陋ｻ繝ｻ・願ｭ√・・ｭ蜉ｱ縲定ｱ包ｽｨ隴√・蛻・愾・ｷ陋ｹ・ｺ陋ｻ繝ｻ笘・ｹｧ荵敖繧・ｽｾ蜈ｷ・ｼ繝ｻ2345432邵ｲ繝ｻ2343212邵ｲ繝ｻ2323232'
        form.fields['shipping_rate_type'].label = '鬨ｾ竏ｵ萓ｭ郢ｧ・ｰ郢晢ｽｫ郢晢ｽｼ郢晏干繝ｻ驕橸ｽｮ鬯俶ｩｸ・ｼ蜩･ree / Charge / Free on condition / Charge on delivery'
        form.fields['delivery_company'].label = '鬩溷涵ﾂ竏ｽ・ｼ螟ゑｽ､・ｾ'
        form.fields['voucher_code'].label = '髫ｪ・ｪ陜荳槫･ｳ鬯・ｩ・ｪ蟠趣ｽｨ・ｼ騾｡・ｪ陷ｿ・ｷ'
        form.fields['packing_no'].label = '騾具ｽｺ雎包ｽｨ隴弱ｅ竊馴墓ｻ薙・邵ｺ霈費ｽ檎ｹｧ荵昴Τ郢昴・縺冗ｹ晢ｽｳ郢ｧ・ｰ騾｡・ｪ陷ｿ・ｷ繝ｻ莠包ｽｾ蜈ｷ・ｼ蜩ｽPP22894429繝ｻ繝ｻ
        form.fields['seller_delivery_no'].label = '騾具ｽｺ雎包ｽｨ隴弱ｅ竊馴墓ｻ薙・邵ｺ霈費ｽ檎ｹｧ荵昴Τ郢昴・縺冗ｹ晢ｽｳ郢ｧ・ｰ騾｡・ｪ陷ｿ・ｷ邵ｺ・ｨ1繝ｻ繝ｻ邵ｺ・ｧ郢晄ｧｭ繝｣郢昶・ﾎｦ郢ｧ・ｰ邵ｺ霈費ｽ檎ｹｧ邇厄ｽｲ・ｩ陞｢・ｲ髢繝ｻ閻ｰ闖ｴ髦ｪ繝ｻ郢ｧ・ｷ郢晢ｽｪ郢ｧ・｢郢晢ｽｫ騾｡・ｪ陷ｿ・ｷ繝ｻ莠包ｽｾ蜈ｷ・ｼ繝ｻ30705-0003繝ｻ繝ｻ
        form.fields['payment_nation'].label = '雎包ｽｨ隴√・縺礼ｹｧ・､郢昜ｺ･蠏懊・蜩ｽP'
        form.fields['gift'].label = '髮崎ご・ｭ豕悟・繝ｻ蛹ｻ縺千ｹ晁ｼ斐Κ邵ｲ竏壹・郢晢ｽｬ郢ｧ・ｼ郢晢ｽｳ郢晏現ﾂ竏壺凰邵ｺ・ｾ邵ｺ謇假ｽｼ繝ｻ
        form.fields['cod_price'].label = '騾ｹﾂ隰・ｼ費ｼ櫁ｱ趣ｽｺ雋ら｣ｯ竕｡鬯倥・
        form.fields['cart_discount_seller'].label = '髮具ｽｩ陞｢・ｲ髢繝ｻ・ｲ・ｰ隲｡繝ｻ縺咲ｹ晢ｽｼ郢昜ｺ･迚｡陟代・
        form.fields['cart_discount_qoo10'].label = 'Qoo10髮具｣ｰ隲｡繝ｻ縺咲ｹ晢ｽｼ郢昜ｺ･迚｡陟代・
        form.fields['settle_price'].label = '驍ｱ荳茨ｽｾ蟶ｷ・ｵ・ｦ陷ｴ貊会ｽｾ・｡'
        form.fields['branch_name'].label = '隰ｾ・ｯ陟取憺倹'
        form.fields['tracking_no'].label = '鬨ｾ竏夲ｽ願ｿ･・ｶ騾｡・ｪ陷ｿ・ｷ'
        form.fields['oversea_consignment'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ繝ｻ(Y/N)'
        form.fields['oversea_consignment_receiver'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ諤懷･ｳ陷ｿ邏具ｽｺ・ｺ'
        form.fields['oversea_consignment_country'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ諤懷ｵ懆楜・ｶ'
        form.fields['oversea_consignment_zipcode'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ繝ｻ鬩幢ｽｵ關難ｽｿ騾｡・ｪ陷ｿ・ｷ'
        form.fields['oversea_consignment_addr1'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ繝ｻ闖ｴ荵怜恍(鬩幢ｽｽ鬩慕§・ｺ諛・＝/陝ｶ繧・私騾包ｽｺ隴壹・'
        form.fields['oversea_consignment_addr2'].label = '雎ｬ・ｷ陞滄摩・ｧ遒托ｽｨ繝ｻ闖ｴ荵怜恍(陝ｶ繧・私騾包ｽｺ隴壼床・ｻ・･鬮ｯ繝ｻ'
        form.fields['delay_type'].label = '鬩輔・・ｻ・ｶ邵ｺ・ｮ騾・・鄂ｰ邵ｲ繧托ｽｼ繝ｻ繝ｻ螢ｼ閹夊惓竏ｵ・ｺ髢・呵叉・ｭ邵ｲ繝ｻ繝ｻ螢ｽ・ｳ・ｨ隴√・・｣・ｽ闖ｴ諛ｶ・ｼ蛹ｻ縺檎ｹ晢ｽｼ郢敖郢晢ｽｼ郢晢ｽ｡郢ｧ・､郢昜ｼ夲ｽｼ蟲ｨﾂ繝ｻ繝ｻ螟撰ｽ｡・ｧ陞ｳ・｢邵ｺ・ｮ髫補扱・ｱ繧・繝ｻ繝ｻ螢ｹ笳守ｸｺ・ｮ闔牙私・ｼ繝ｻ
        form.fields['delay_memo'].label = '髮具ｽｩ陞｢・ｲ髢繝ｻﾎ鍋ｹ晢ｽ｢'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Qoo10雎包ｽｨ隴√・繝･陜｣・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'Qoo10雎包ｽｨ隴√・繝･陜｣・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context

class QooOrderDelete(generic.DeleteView):
    """
    QooOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/qoo_order_delete.html'
    model = QooOrderInfo
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:all_order_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- QooOrderDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10邵ｺ・ｮ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋樒ｎ鬮ｯ・､邵ｺ・ｫ隴厄ｽｴ隴・ｽｰ
            # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
            # 邵ｺ謔滂ｽｿ繝ｻ・ｦ竏壺味邵ｺ蠕娯穐邵ｺ・ｰ邵ｺ・ｧ邵ｺ髦ｪ窶ｻ邵ｺ・ｪ邵ｺ繝ｻ・ｼ繝ｻ
            """
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)
            """

            #goods_object = self.get_object()
            """
            self.object.qoo_upd_status = 3  # 陷ｿ髢・ｼ蜍滂ｽｻ繝ｻ・ｭ・｢


            # 驍ｯ螢ｹ・邵ｺ・ｦwowma邵ｺ荵晢ｽ芽恆莨∝求
            # 邵ｺ・ｾ邵ｺ螢ｼ閹夊惓竏壹○郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋橸ｽ､蟲ｨ竏ｴ邵ｺ・ｦ邵ｺ荵晢ｽ・
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 陷台ｼ∝求隴厄ｽｴ隴・ｽｰ ok')
                else:
                    messages.error(
                        self.request, 'wowma邵ｺ荵晢ｽ芽恆莨∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma 邵ｺ・ｧ陝・ｽｾ髮趣ｽ｡陜繝ｻ蛻邵ｺ迹夲ｽｦ荵昶命邵ｺ荵晢ｽ臥ｸｺ・ｪ邵ｺ繝ｻ繝ｻ邵ｺ・ｧ郢ｧ・ｹ郢晢ｽｫ郢晢ｽｼ邵ｲ繝ｻB邵ｺ荵晢ｽ芽ｱｸ蛹ｻ笘・)
            """

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '陷台ｼ∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- QooOrderDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- QooOrderDelete out")
        return result


class WowOrderList(generic.ListView):
    """
    WowmaOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
    def get_queryset(self, queryset=None):
        #return YaBuyersItemDetail.objects.all()[:10]
        # session邵ｺ・ｫ陋滂ｽ､邵ｺ蠕娯旺郢ｧ蜿･・ｰ・ｴ陷ｷ蛹ｻﾂ竏壺落邵ｺ・ｮ陋滂ｽ､邵ｺ・ｧ郢ｧ・ｯ郢ｧ・ｨ郢晢ｽｪ騾具ｽｺ髯ｦ蠕娯・郢ｧ荵敖繝ｻ

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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = WowOrderInfoForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'wow_order_list'
        return ctx


class WowOrderDetail(generic.DetailView):
    """
    WowOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
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
        form.fields['order_name'].label = '雎包ｽｨ隴√・ﾂ繝ｻ・ｰ荳樣倹'
        form.fields['order_kana'].label = 'order_kana'
        form.fields['order_zipcode'].label = 'order_zipcode'
        form.fields['order_address'].label = 'order_address'
        form.fields['order_phone_number_1'].label = 'order_phone_number_1'
        form.fields['order_phone_number_2'].label = 'order_zipcode'
        form.fields['nickname'].label = 'nickname'
        form.fields['sender_name'].label = '鬨ｾ竏ｽ・ｻ莨懊・雎御ｸ樣倹'
        form.fields['sender_kana'].label = '鬨ｾ竏ｽ・ｻ莨懊・邵ｺ荵昶・'
        form.fields['sender_zipcode'].label = '鬨ｾ竏ｽ・ｻ莨懊・zipcode'
        form.fields['sender_address'].label = '鬨ｾ竏ｽ・ｻ莨懊・闖ｴ荵怜恍'
        form.fields['sender_phone_number_1'].label = '鬨ｾ竏ｽ・ｻ莨懊・_鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ_1'
        form.fields['sender_phone_number_2'].label = '鬨ｾ竏ｽ・ｻ莨懊・_鬮ｮ・ｻ髫ｧ・ｱ騾｡・ｪ陷ｿ・ｷ_2'
        form.fields['order_option'].label = '雎包ｽｨ隴√・縺檎ｹ晏干縺咏ｹ晢ｽｧ郢晢ｽｳ'
        form.fields['settlement_name'].label = '雎趣ｽｺ雋ょ沺蟀ｿ雎輔・
        form.fields['user_comment'].label = '郢晢ｽｦ郢晢ｽｼ郢ｧ・ｶ郢ｧ・ｳ郢晢ｽ｡郢晢ｽｳ郢昴・
        form.fields['memo'].label = '郢晢ｽ｡郢晢ｽ｢'
        form.fields['order_status'].label = 'order_郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['contact_status'].label = '郢ｧ・ｳ郢晢ｽｳ郢ｧ・ｿ郢ｧ・ｯ郢昴・郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['authorization_status'].label = '隰・ｽｿ髫ｱ豬ｩ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['payment_status'].label = '隰ｾ・ｯ隰・ｼ費ｼ枩郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['ship_status'].label = '騾具ｽｺ鬨ｾ・ｼ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['print_status'].label = '陷奇ｽｰ陋ｻ・ｷ_郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['cancel_status'].label = '郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ_郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['cancel_reason'].label = '郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ騾・・鄂ｰ'
        form.fields['cancel_comment'].label = '郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ郢ｧ・ｳ郢晢ｽ｡郢晢ｽｳ郢昴・
        form.fields['total_sale_price'].label = '陞｢・ｲ闕ｳ莨≫横鬯俶ｦ顔ｲ矩坎繝ｻ
        form.fields['total_sale_unit'].label = '陞｢・ｲ闕ｳ髮・蛹ｺ辟夊惺驛・ｽｨ繝ｻ
        form.fields['postage_price'].label = '鬨ｾ竏ｵ萓ｭ'
        form.fields['charge_price'].label = '髫ｲ蛹ｺ・ｱ繧銀横鬯倥・
        form.fields['total_price'].label = '驍ｱ荳樒ｲ矩坎逎ｯ竕｡鬯倥・
        form.fields['coupon_total_price'].label = '郢ｧ・ｯ郢晢ｽｼ郢晄亢ﾎｦ陋ｻ・ｩ騾包ｽｨ陷ｷ驛・ｽｨ逎ｯ竕｡鬯倥・
        form.fields['use_point'].label = '陋ｻ・ｩ騾包ｽｨ郢晄亢縺・ｹ晢ｽｳ郢昴・
        form.fields['use_point_cancel'].label = '陋ｻ・ｩ騾包ｽｨ郢晄亢縺・ｹ晢ｽｳ郢昴・郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ陋ｻ繝ｻ
        form.fields['use_au_point_price'].label = 'au陋ｻ・ｩ騾包ｽｨ郢晄亢縺・ｹ晢ｽｳ郢晉｣ｯ竕｡鬯倥・
        form.fields['use_au_point'].label = 'au陋ｻ・ｩ騾包ｽｨ郢晄亢縺・ｹ晢ｽｳ郢昴・
        form.fields['use_au_point_cancel'].label = 'au陋ｻ・ｩ騾包ｽｨ郢晄亢縺・ｹ晢ｽｳ郢昴・郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ陋ｻ繝ｻ
        form.fields['point_fixed_status'].label = '郢晄亢縺・ｹ晢ｽｳ郢昴・fix郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['settle_status'].label = '隰・ｽｿ髫ｱ髦ｪ縺帷ｹ昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ'
        form.fields['pg_result'].label = 'pg驍ｨ蜈域｣｡'
        form.fields['pg_orderid'].label = 'pg_orderid'
        form.fields['pg_request_price'].label = 'pg_髫ｲ蛹ｺ・ｱ繧銀横鬯倥・
        form.fields['coupon_type'].label = '郢ｧ・ｯ郢晢ｽｼ郢晄亢ﾎｦ郢ｧ・ｿ郢ｧ・､郢昴・
        form.fields['coupon_key'].label = '郢ｧ・ｯ郢晢ｽｼ郢晄亢ﾎｦ郢ｧ・ｭ郢晢ｽｼ'
        form.fields['card_jagdement'].label = '郢ｧ・ｫ郢晢ｽｼ郢晉甥諢幄楜繝ｻ
        form.fields['delivery_name'].label = '鬩溷涵ﾂ竏晞倹'
        form.fields['delivery_method_id'].label = '鬩溷涵ﾂ竏ｵ蟀ｿ雎募刀d'
        form.fields['delivery_request_time'].label = '邵ｺ髮・ｽｱ髮・ｽｸ譴ｧ謔崎ｭ弱ｋ菫｣陝ｶ・ｯ'
        form.fields['shipping_carrier'].label = '鬩溷涵ﾂ竏ｵ・･・ｭ髢繝ｻ
        form.fields['shipping_number'].label = '髴托ｽｽ髴搾ｽ｡騾｡・ｪ陷ｿ・ｷ'
        form.fields['order_date'].label = '陷ｿ邇ｲ・ｳ・ｨ隴鯉ｽ･'
        form.fields['contact_date'].label = '郢ｧ・ｳ郢晢ｽｳ郢ｧ・ｿ郢ｧ・ｯ郢晏現・邵ｺ貊灘ｾ・
        form.fields['authorization_date'].label = '隰・ｽｿ髫ｱ閧ｴ蠕・
        form.fields['payment_date'].label = '隰ｾ・ｯ隰・ｼ費ｼ櫁ｭ鯉ｽ･'
        form.fields['ship_date'].label = '騾具ｽｺ鬨ｾ竏ｵ蠕・
        form.fields['print_date'].label = '陷奇ｽｰ陋ｻ・ｷ隴鯉ｽ･'
        form.fields['cancel_date'].label = '郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ隴鯉ｽ･'
        form.fields['point_fixed_date'].label = '郢晄亢縺・ｹ晢ｽｳ郢晁ご・｢・ｺ陞ｳ螢ｽ蠕・
        form.fields['delivery_request_day'].label = '鬩溷涵ﾂ竏晢ｽｸ譴ｧ謔崎ｭ鯉ｽ･'
        form.fields['shipping_date'].label = '鬩溷涵ﾂ竏ｵ蠕・
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wowma雎包ｽｨ隴√・繝･陜｣・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        context['message'] = 'Wowma雎包ｽｨ隴√・繝･陜｣・ｱ 隴厄ｽｴ隴・ｽｰ郢晏｣ｹ繝ｻ郢ｧ・ｸ 郢晢ｽ｡郢昴・縺晉ｹ晢ｽｼ郢ｧ・ｸ邵ｺ・ｧ邵ｺ繝ｻ
        return context


class WowOrderDelete(generic.DeleteView):
    """
    WowmaOrderInfo郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/qoo_order_delete.html'
    model = WowmaOrderInfo
    #success_url = reverse_lazy('yaget:buyers_goods_detail_list')
    success_url = reverse_lazy('yaget:all_order_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        logger.debug("--- WowOrderDelete in.gid:[{}]".format(self.object.gid))
        try:
            # qoo10邵ｺ・ｮ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋樒ｎ鬮ｯ・､邵ｺ・ｫ隴厄ｽｴ隴・ｽｰ
            # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
            # 邵ｺ謔滂ｽｿ繝ｻ・ｦ竏壺味邵ｺ蠕娯穐邵ｺ・ｰ邵ｺ・ｧ邵ｺ髦ｪ窶ｻ邵ｺ・ｪ邵ｺ繝ｻ・ｼ繝ｻ
            """
            qoo10obj = Qoo10Access(logger)
            qoo10obj.qoo10_create_cert_key()
            wowma_access = WowmaAccess(logger)
            """

            #goods_object = self.get_object()
            """
            self.object.qoo_upd_status = 3  # 陷ｿ髢・ｼ蜍滂ｽｻ繝ｻ・ｭ・｢


            # 驍ｯ螢ｹ・邵ｺ・ｦwowma邵ｺ荵晢ｽ芽恆莨∝求
            # 邵ｺ・ｾ邵ｺ螢ｼ閹夊惓竏壹○郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ雋橸ｽ､蟲ｨ竏ｴ邵ｺ・ｦ邵ｺ荵晢ｽ・
            if wowma_access.wowma_update_stock(self.object.gid, 0, '2') == 0:
                logger.debug('--- BuyersGoodsDetailDelete wow_delete wowma_update_stock ok.')
                ret_code, ret_msg = wowma_access.wowma_delete_item_infos(self.object.gid)
                if ret_code == 0:
                    logger.info('--- BuyersGoodsDetailDelete wow 陷台ｼ∝求隴厄ｽｴ隴・ｽｰ ok')
                else:
                    messages.error(
                        self.request, 'wowma邵ｺ荵晢ｽ芽恆莨∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}][{}]'.format(ret_code, ret_msg))
                    context = self.get_context_data(object=self.object)
                    logger.debug('--- BuyersGoodsDetailDelete wow_delete error occurred.[{}][{}]'.format(ret_code, ret_msg))
                    return self.render_to_response(context)
            else:
                logger.debug("--- BuyersGoodsDetailDelete wowma 邵ｺ・ｧ陝・ｽｾ髮趣ｽ｡陜繝ｻ蛻邵ｺ迹夲ｽｦ荵昶命邵ｺ荵晢ｽ臥ｸｺ・ｪ邵ｺ繝ｻ繝ｻ邵ｺ・ｧ郢ｧ・ｹ郢晢ｽｫ郢晢ｽｼ邵ｲ繝ｻB邵ｺ荵晢ｽ芽ｱｸ蛹ｻ笘・)
            """

            result = super().delete(request, *args, **kwargs)
            messages.success(
                self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        except Exception as e:
            messages.error(
                self.request, '陷台ｼ∝求邵ｺ・ｫ陞滂ｽｱ隰ｨ蜉ｱ・邵ｺ・ｾ邵ｺ蜉ｱ笳・ｸｲ繝ｻ{}]'.format(traceback.format_exc()))
            context = self.get_context_data(object=self.object)
            logger.debug("--- WowOrderDelete error occurred.[{}]".format(traceback.format_exc()))
            return self.render_to_response(context)

        logger.debug("--- WowOrderDelete out")
        return result


def cut_zenkaku(chk_text):
    return chk_text.replace('\u3000', ' ')


# qoo10 隴崢隴・ｽｰ邵ｺ・ｮ雎包ｽｨ隴√・繝･陜｣・ｱ郢ｧ雋槫徐陟輔・
def qoo_get_order_info_ajax_res(request):
    model = QooOrderInfo
    logger.debug("--- qoo_get_order_info_ajax_res in")

    d = {
        'msg': '',
        'ret_code': '',
    }

    try:
        # 鬩溷涵ﾂ竏ｫ諞ｾ隲ｷ荵敖繧托ｽｼ繝ｻ繝ｻ螢ｼ繝ｻ髣包ｽｷ陟輔・笆邵ｲ繝ｻ繝ｻ螢ｼ繝ｻ髣包ｽｷ雋ょ現竏ｩ邵ｲ繝ｻ繝ｻ螟ょ験雎包ｽｨ驕抵ｽｺ髫ｱ髦ｪﾂ繝ｻ繝ｻ螟舌・鬨ｾ竏ｽ・ｸ・ｭ邵ｲ繝ｻ繝ｻ螟舌・鬨ｾ竏晢ｽｮ蠕｡・ｺ繝ｻ・ｼ繝ｻ
        shipping_stat = request.POST.get('shipping_stat')
        search_sdate = request.POST.get('search_sdate')  # 霎｣・ｧ闔ｨ螟仙ｹ戊沂蛹ｺ蠕・關灘・・ｼ繝ｻ0190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_edate = request.POST.get('search_edate')  # 霎｣・ｧ闔ｨ螟ゑｽｵ繧・ｽｺ繝ｻ蠕・關灘・・ｼ繝ｻ0190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_sdate = search_sdate.replace('-', '')
        search_edate = search_edate.replace('-', '')
        search_condition = request.POST.get('search_condition')  # 隴鯉ｽ･闔牙･繝ｻ驕橸ｽｮ鬯俶ｧｭﾂ繧托ｽｼ繝ｻ繝ｻ螢ｽ・ｳ・ｨ隴√・蠕狗ｸｲ繝ｻ繝ｻ螢ｽ・ｱ・ｺ雋ゆｺ･・ｮ蠕｡・ｺ繝ｻ蠕狗ｸｲ繝ｻ繝ｻ螟舌・鬨ｾ竏ｵ蠕狗ｸｲ繝ｻ繝ｻ螟舌・鬨ｾ竏晢ｽｮ蠕｡・ｺ繝ｻ蠕九・繝ｻ

        # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
        qoo10obj = Qoo10Access(logger)
        msg = 'start[' + YagetConfig.verbose_name + ']'
        qoo10obj.qoo10_create_cert_key()

        logger.debug("--- qoo_get_order_info_ajax_res 1")

        # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
        # Qoo10邵ｺ・ｫ騾具ｽｻ鬪ｭ・ｲ雋ょ現竏ｩ邵ｺ・ｧ邵ｺ繧・ｽ檎ｸｺ・ｰ邵ｲﾂgoods.qoo_gdno邵ｲﾂ邵ｺ・ｫ陋滂ｽ､邵ｺ謔溘・邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ・・
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
                # 郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ
                d = {
                    'msg': res_obj["res_msg"],
                    'ret_code': res_obj["res_code"],
                }
            else:
                # 隰御ｻ咏ｲ･
                # QooOrderInfo邵ｲﾂ邵ｺ・ｫ隴・ｽｰ髫穂ｸ莞樒ｹｧ・ｳ郢晢ｽｼ郢晏ｳｨ竊堤ｸｺ蜉ｱ窶ｻ髴托ｽｽ陷会｣ｰ邵ｺ蜷ｶ・・
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

                    # 雎包ｽｨ隴√・・ｩ・ｳ驍擾ｽｰ郢ｧ蛛ｵ笳守ｹｧ蠕娯裸郢ｧ謔溷徐郢ｧ鬘假ｽｾ・ｼ郢ｧﾂ
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


# qoo10 雎包ｽｨ隴√・繝･陜｣・ｱ邵ｲﾂ騾具ｽｺ鬨ｾ竏ｽ・ｺ莠･・ｮ螢ｽ蠕狗ｹｧ繝ｻ竕ｦ陝抵ｽｶ騾・・鄂ｰ郢ｧ蟶敖竏ｽ・ｿ・｡
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
    est_shipping_date = request.POST.get('est_shipping_date')  # 騾具ｽｺ鬨ｾ竏ｽ・ｺ莠･・ｮ螢ｽ蠕・關灘・・ｼ繝ｻ0190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
    est_shipping_date = est_shipping_date.replace('-', '')
    delay_type = request.POST.get('delay_type')  # 鬩輔・・ｻ・ｶ邵ｺ・ｮ騾・・鄂ｰ邵ｲ繧托ｽｼ繝ｻ繝ｻ螢ｼ閹夊惓竏ｵ・ｺ髢・呵叉・ｭ邵ｲ繝ｻ繝ｻ螢ｽ・ｳ・ｨ隴√・・｣・ｽ闖ｴ諛ｶ・ｼ蛹ｻ縺檎ｹ晢ｽｼ郢敖郢晢ｽｼ郢晢ｽ｡郢ｧ・､郢昜ｼ夲ｽｼ蟲ｨﾂ繝ｻ繝ｻ螟撰ｽ｡・ｧ陞ｳ・｢邵ｺ・ｮ髫補扱・ｱ繧・繝ｻ繝ｻ螢ｹ笳守ｸｺ・ｮ闔牙私・ｼ繝ｻ
    delay_memo = request.POST.get('delay_memo')  # 髮具ｽｩ陞｢・ｲ髢繝ｻﾎ鍋ｹ晢ｽ｢

    # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
    # Qoo10邵ｺ・ｫ騾具ｽｻ鬪ｭ・ｲ雋ょ現竏ｩ邵ｺ・ｧ邵ｺ繧・ｽ檎ｸｺ・ｰ邵ｲﾂgoods.qoo_gdno邵ｲﾂ邵ｺ・ｫ陋滂ｽ､邵ｺ謔溘・邵ｺ・｣邵ｺ・ｦ邵ｺ繝ｻ・・
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
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧茨ｽｬ・｡邵ｺ・ｮ陷・ｽｦ騾・・繝ｻ髯ｦ蠕鯉ｽ冗ｸｺ・ｪ邵ｺ繝ｻ
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)


# qoo10 雎包ｽｨ隴√・繝･陜｣・ｱ邵ｲﾂ騾具ｽｺ鬨ｾ竏ｵ蠕狗ｹｧ繝ｻ・ｿ・ｽ髴搾ｽ｡騾｡・ｪ陷ｿ・ｷ郢ｧ蟶敖竏ｽ・ｿ・｡
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
    delivery_company = request.POST.get('delivery_company')  # 鬩溷涵ﾂ竏ｽ・ｼ螟ゑｽ､・ｾ
    tracking_no = request.POST.get('tracking_no')  # 鬨ｾ竏夲ｽ願ｿ･・ｶ騾｡・ｪ陷ｿ・ｷ

    # Qoo10邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    qoo10obj = Qoo10Access(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'
    qoo10obj.qoo10_create_cert_key()

    # Qoo10邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
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
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧茨ｽｬ・｡邵ｺ・ｮ陷・ｽｦ騾・・繝ｻ髯ｦ蠕鯉ｽ冗ｸｺ・ｪ邵ｺ繝ｻ
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)

# wowma 隴崢隴・ｽｰ邵ｺ・ｮ雎包ｽｨ隴√・繝･陜｣・ｱ郢ｧ雋槫徐陟輔・
def wow_get_order_info_ajax_res(request):
    model = WowmaOrderInfo
    logger.debug("--- wow_get_order_info_ajax_res in")

    # order_status 邵ｺ・ｯ鬩溷涵ﾂ竏ｫ諞ｾ隲ｷ荵敖繝ｻ
    """
    隴・ｽｰ髫穂ｸ槫･ｳ闔峨・
    騾具ｽｺ鬨ｾ竏晉√陷茨ｽ･鬩･螟ｧ・ｾ繝ｻ笆
    騾具ｽｺ鬨ｾ竏晢ｽｾ謔溘・鬩･螟ｧ・ｾ繝ｻ笆
    闕ｳ諠ｹ・ｿ・｡陟輔・笆
    騾具ｽｺ鬨ｾ竏晢ｽｾ繝ｻ笆
    陞ｳ蠕｡・ｺ繝ｻ
    闖ｫ譎芽風
    郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ
    陷ｷ繝ｻ・ｨ・ｮ郢ｧ・ｫ郢ｧ・ｹ郢ｧ・ｿ郢晢｣ｰ郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ繝ｻ莠･蜿呵第・・ｮ・｡騾・・縲帝寞・ｴ陟手挙繝ｻ邵ｺ讙主元鬪ｭ・ｲ邵ｺ蜉ｱ笳・ｹｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ陷ｷ謳ｾ・ｼ繝ｻ
    隴・ｽｰ髫穂ｸ茨ｽｺ閧ｲ・ｴ繝ｻ
    闔閧ｲ・ｴ繝ｻ・ｸ・ｭ
    闕ｳ閧ｴ・ｭ・｣陷ｿ髢・ｼ蜍滂ｽｯ・ｩ隴滂ｽｻ闕ｳ・ｭ
    陝・ｽｩ隴滂ｽｻ闖ｫ譎芽風
    陝・ｽｩ隴滂ｽｻNG
    郢ｧ・ｭ郢晢ｽ｣郢晢ｽｳ郢ｧ・ｻ郢晢ｽｫ陷ｿ蠍ｺ・ｻ蛟・ｽｸ・ｭ
    """
    try:
        search_sdate = request.POST.get('search_sdate')  # 霎｣・ｧ闔ｨ螟仙ｹ戊沂蛹ｺ蠕・關灘・・ｼ繝ｻ0190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_edate = request.POST.get('search_edate')  # 霎｣・ｧ闔ｨ螟ゑｽｵ繧・ｽｺ繝ｻ蠕・關灘・・ｼ繝ｻ0190101 (yyyyMMdd), 20190101153000 (yyyyMMddHHmmss)
        search_sdate = search_sdate.replace('-', '')
        search_edate = search_edate.replace('-', '')
        date_type = request.POST.get('date_type')  # 隴鯉ｽ･闔牙･繝ｻ驕橸ｽｮ鬯俶ｧｭﾂ繝ｻ:雎包ｽｨ隴√・蠕狗ｸｲﾂ1:騾具ｽｺ鬨ｾ竏ｵ蠕狗ｸｲﾂ2:陷茨ｽ･鬩･隨ｬ蠕狗ｸｲﾂ3:騾具ｽｺ陞｢・ｲ(陷茨ｽ･髣包ｽｷ)闔莠･・ｮ螢ｽ蠕狗ｸｲﾂ4:騾具ｽｺ鬨ｾ竏ｵ謔・ｫｯ蜈亥ｾ狗ｸｲﾂ繝ｻ蛹ｻ繝ｧ郢晁ｼ斐°郢晢ｽｫ郢昴・繝ｻ繝ｻ
        order_status_1 = request.POST.get('order_status_1')
        order_status_2 = request.POST.get('order_status_2')

        # wowma邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ

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
        # document 邵ｺ・ｯ邵ｲ繝ｼshop_obj, res_obj]邵ｲﾂ邵ｺ・ｮ鬩滓ｦ翫・邵ｺ・ｧ髴第鱒・邵ｺ・ｦ邵ｺ繝ｻ・・
        for document in document_list:
            if document:
                #logger.debug("--- wow_get_order_info_ajax_res doc_list doc[{}]".format(document.toprettyxml(indent="  ")))

                #logger.debug(document.toprettyxml(indent="  "))  # 郢昜ｻ｣繝ｻ郢ｧ・ｹ邵ｺ霈費ｽ檎ｸｺ逶廴L隲繝ｻ・ｰ・ｱ郢ｧ蛛ｵ縺・ｹ晢ｽｳ郢昴・ﾎｦ郢昜ｺ包ｽｻ蛟･窶ｳ邵ｺ・ｧ隴√・・ｭ諤懊・邵ｺ・ｫ陞溽判驪､邵ｺ蜉ｱ窶ｻ髯ｦ・ｨ驕会ｽｺ
                myrtn = document[1].getElementsByTagName("status")[0].firstChild.nodeValue  # 0邵ｺ・ｪ郢ｧ逕ｻ繝ｻ陷画ｺ伉繝ｻ邵ｲﾂ陞滂ｽｱ隰ｨ繝ｻ
                if myrtn == 1:
                    my_code = str(document[1].getElementsByTagName("code")[0].firstChild.nodeValue)
                    my_message = str(document[1].getElementsByTagName("message")[0].firstChild.nodeValue)
                    msg = '郢ｧ・ｨ郢晢ｽｩ郢晢ｽｼ騾具ｽｺ騾墓ｻゑｽｼ蝟几}][{}]'.format(my_code, my_message)
                    logger.info('wow_get_order_info_ajax_res code:[{}] msg:[{}]'.format(my_code, my_message))
                else:
                    # 雎・ｽ｣陝ｶ・ｸ邵ｺ・ｫ郢昴・繝ｻ郢ｧ・ｿ陷ｿ髢・ｾ蜉ｱ縲堤ｸｺ髦ｪ笳・ｸｲ繝ｻB騾具ｽｻ鬪ｭ・ｲ
                    my_total_cnt = str(document[1].getElementsByTagName("resultCount")[0].firstChild.nodeValue)
                    msg = '陷ｿ髢・ｾ豸桑繝ｻ螢ｻ・ｻ・ｶ隰ｨ・ｰ[{}]'.format(my_total_cnt)
                    logger.debug('wow_get_order_info_ajax_res ok total_cnt:[{}]'.format(my_total_cnt))

                    # 雎包ｽｨ隴√・・ｩ・ｳ驍擾ｽｰ郢ｧ蛛ｵ笳守ｹｧ蠕娯裸郢ｧ謔溷徐郢ｧ鬘假ｽｾ・ｼ郢ｧﾂ
                    msg += 'orderId:\n'
                    for order_id_elm in document[1].getElementsByTagName("orderInfo"):
                        order_id = str(order_id_elm.getElementsByTagName("orderId")[0].firstChild.nodeValue)
                        logger.info('wow_get_order_info_ajax_res order_id:[{}]'.format(order_id))
                        msg += order_id + ' '

                        # 雎包ｽｨ隴√・・ｩ・ｳ驍擾ｽｰ郢ｧ蛛ｵ笳守ｹｧ蠕娯裸郢ｧ謔溷徐郢ｧ鬘假ｽｾ・ｼ郢ｧﾂ
                        new_obj = WowmaOrderInfo.objects.filter(
                            orderid=order_id,
                        ).first()

                        # 郢晢ｽｬ郢ｧ・ｹ郢晄亢ﾎｦ郢ｧ・ｹ邵ｺ・ｫ陝・ｼ懈Β邵ｺ蜉ｱ竊醍ｸｺ繝ｻ・ｰ繝ｻ蟯ｼ邵ｺ・ｯ郢昶・縺臥ｹ昴・縺醍ｸｺ蜉ｱ竊醍ｸｺ繝ｻ竊・
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
                            # 驍ｯ螢ｹ・樒ｸｺ・ｦ陷ｿ邇ｲ・ｳ・ｨ隴丞ｮ茨ｽｴ・ｰ郢ｧ蝣､蛹ｳ鬪ｭ・ｲ
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

                                # item_name 邵ｺ・ｯ陷ｿ謔ｶ・企ｶ・ｴ邵ｺ蜉ｱ窶ｻ隴ｬ・ｼ驍上・
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

                            # 驍ｯ螢ｹ・樒ｸｺ・ｦ陷ｿ邇ｲ・ｳ・ｨ隴丞ｮ茨ｽｴ・ｰ郢ｧ蝣､蛹ｳ鬪ｭ・ｲ

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

                                # item_name 邵ｺ・ｯ陷ｿ謔ｶ・企ｶ・ｴ邵ｺ蜉ｱ窶ｻ隴ｬ・ｼ驍上・
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
        # 隴厄ｽｴ隴・ｽｰ隴弱ｅ竊鍋ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ繝ｻ繝ｻ
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


# wowma 雎包ｽｨ隴√・縺帷ｹ昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ郢ｧ蟶敖竏ｽ・ｿ・｡
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
    order_status = request.POST.get('order_status')  # 雎包ｽｨ隴√・縺帷ｹ昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ

    # wowma邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
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
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧茨ｽｬ・｡邵ｺ・ｮ陷・ｽｦ騾・・繝ｻ髯ｦ蠕鯉ｽ冗ｸｺ・ｪ邵ｺ繝ｻ
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }
    return JsonResponse(d)


# wowma 雎包ｽｨ隴√・繝･陜｣・ｱ邵ｲﾂ騾具ｽｺ鬨ｾ竏ｵ蠕狗ｹｧ繝ｻ・ｿ・ｽ髴搾ｽ｡騾｡・ｪ陷ｿ・ｷ郢ｧ蟶敖竏ｽ・ｿ・｡
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
    shipping_date = request.POST.get('shipping_date')  # 鬩溷涵ﾂ竏ｽ・ｼ螟ゑｽ､・ｾ
    shipping_carrier = request.POST.get('shipping_carrier')  # 鬩溷涵ﾂ竏ｽ・ｼ螟ゑｽ､・ｾ
    shipping_number = request.POST.get('shipping_number')  # 鬨ｾ竏夲ｽ願ｿ･・ｶ騾｡・ｪ陷ｿ・ｷ
    logger.debug("--- wow_order_sending_info_ajax shipping_carrier[{}]".format(shipping_carrier))

    # wowma邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ
    wowma_access = WowmaAccess(logger)
    msg = 'start[' + YagetConfig.verbose_name + ']'

    # wowma邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
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
            # 隴厄ｽｴ隴・ｽｰ邵ｺ・ｫ隰御ｻ咏ｲ･邵ｺ蜉ｱ窶ｻ邵ｺ繝ｻ・狗ｸｲ繧茨ｽｬ・｡邵ｺ・ｮ陷・ｽｦ騾・・繝ｻ髯ｦ蠕鯉ｽ冗ｸｺ・ｪ邵ｺ繝ｻ
            # DB郢ｧ蜻亥ｳｩ隴・ｽｰ邵ｺ蜉ｱ窶ｻ邵ｺ鄙ｫ・･
            order.shipping_date = shipping_date
            order.shipping_number = shipping_number
            order.shipping_carrier = shipping_carrier
            """
            if int(shipping_carrier) == 1:
                order.shipping_carrier = '郢ｧ・ｯ郢晢ｽｭ郢晞亂縺慕ｹ晢ｽ､郢晄ｧｭ繝ｨ'
            elif int(shipping_carrier) == 2:
                order.shipping_carrier = '闖ｴ莉呻ｽｷ譎・・･關難ｽｿ'
            elif int(shipping_carrier) == 3:
                order.shipping_carrier = 'JP郢ｧ・ｨ郢ｧ・ｯ郢ｧ・ｹ郢晏干ﾎ樒ｹｧ・ｹ繝ｻ蝓溽ｫ・隴鯉ｽ･隴幢ｽｬ鬨ｾ螟青ｰ繝ｻ繝ｻ
            elif int(shipping_carrier) == 4:
                order.shipping_carrier = '驕紋ｸ橸ｽｱ・ｱ鬨ｾ螟青ｰ'
            elif int(shipping_carrier) == 5:
                order.shipping_carrier = '髫假ｽｿ雎ｼ繝ｻﾂｰ髴茨ｽｸ'
            elif int(shipping_carrier) == 6:
                order.shipping_carrier = '隴鯉ｽ･隴幢ｽｬ鬩幢ｽｵ關難ｽｿ'
            else:
                order.shipping_carrier = '邵ｺ譏ｴ繝ｻ闔牙､懊・鬨ｾ竏ｽ・ｼ螟ゑｽ､・ｾ'
            """

            # 郢ｧ・ｹ郢昴・繝ｻ郢ｧ・ｿ郢ｧ・ｹ邵ｺ・ｯ陞ｳ蠕｡・ｺ繝ｻ竊鍋ｸｺ蜉ｱ窶ｻ邵ｺ鄙ｫ・･
            order.order_status = '陞ｳ蠕｡・ｺ繝ｻ
            order.ship_status = 'Y'
            order.save()
            logger.debug("--- wow_order_sending_info_ajax saved 鬩溷涵ﾂ竏ｵ・･・ｭ髢繝ｻ{}] 鬩溷涵ﾂ竏ｵ蠕擬{}] 鬩溷涵ﾂ竏ｫ蛻・愾・ｷ[{}]".format(
                order.shipping_carrier, order.shipping_date, order.shipping_number
            ))
            break

    d = {
        'msg': msg,
        'ret_code': my_ret_code,
    }

    return JsonResponse(d)


# qoo10 郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｫ騾具ｽｺ雎包ｽｨ郢ｧ蛛ｵﾂｰ邵ｺ莉｣・・
def qoo_do_order_buyers_ajax(request):
    model = QooOrderInfo
    msg = ''
    res_code = ''
    logger.debug("--- qoo_do_order_buyers_ajax in")
    pk = request.POST.get('pk')
    payment_method = request.POST.get('payment_method')
    if pk:
        # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py qoo_do_buyers_order --pk "
        cmd += pk + " --payment_method " + payment_method
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)

        # pk邵ｺ謔滂ｽｾ蜉ｱ・臥ｹｧ蠕娯螺郢ｧ蟲ｨ縺慕ｹ晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺・

    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # 闔会ｽ･闕ｳ荵敖竏晏･ｳ雎包ｽｨ邵ｺ蜉ｱ笳・擒繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢晏ｳｨﾂｰ郢ｧ蟲ｨ繝ｰ郢ｧ・､郢晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ邵ｺ蜉ｱ窶ｻ髮会ｽｼ陷茨ｽ･邵ｺ・ｮ郢晁ｼ釆溽ｹ晢ｽｼ郢ｧ蛛ｵﾂ繝ｻ
    msg = 'start:'

    res_msg = 'qoo_do_order_buyers_ajax: start'
    msg += res_msg
    d = {
        'msg': msg,
        'ret_code': res_code,
    }
    logger.debug("--- qoo_do_order_buyers_ajax end.msg:[{}]".format(msg))

    return JsonResponse(d)


# wowma 郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｫ騾具ｽｺ雎包ｽｨ郢ｧ蛛ｵﾂｰ邵ｺ莉｣・・
def wow_do_order_buyers_ajax(request):
    model = WowmaOrderInfo
    msg = ''
    res_code = ''
    logger.debug("--- wow_do_order_buyers_ajax in")
    pk = request.POST.get('pk')
    payment_method = request.POST.get('payment_method')
    if pk:
        #order = model.objects.get(pk=pk)
        # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_do_buyers_order --pk "
        cmd += pk + " --payment_method " + payment_method
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        #msg += ' maybe ok.' + p.stdout.readline()
        msg += ' maybe ok.' + str(p.pid)

        # pk邵ｺ謔滂ｽｾ蜉ｱ・臥ｹｧ蠕娯螺郢ｧ蟲ｨ縺慕ｹ晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺・

    else:
        d = {
            'ret_code': None,
        }
        return JsonResponse(d)

    # 闔会ｽ･闕ｳ荵敖竏晏･ｳ雎包ｽｨ邵ｺ蜉ｱ笳・擒繝ｻ蛻郢ｧ・ｳ郢晢ｽｼ郢晏ｳｨﾂｰ郢ｧ蟲ｨ繝ｰ郢ｧ・､郢晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｫ郢ｧ・｢郢ｧ・ｯ郢ｧ・ｻ郢ｧ・ｹ邵ｺ蜉ｱ窶ｻ髮会ｽｼ陷茨ｽ･邵ｺ・ｮ郢晁ｼ釆溽ｹ晢ｽｼ郢ｧ蛛ｵﾂ繝ｻ
    msg = 'start:'
    #buinfo_obj = BuyersInfo(logger)
    # 郢晁・縺・ｹ晢ｽ､郢晢ｽｼ郢ｧ・ｺ邵ｺ・ｫ郢晢ｽｭ郢ｧ・ｰ郢ｧ・､郢晢ｽｳ邵ｺ蜉ｱ窶ｻ邵ｺ鄙ｫ・･
    #buinfo_obj.login_buyers()

    # wowma邵ｺ・ｮ陜繝ｻ蛻隲繝ｻ・ｰ・ｱ郢ｧ蜻茨ｽ､諛・ｽｴ・｢
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


# wowma 隰悶・・ｮ螢ｹ・・ｹｧ蠕娯螺郢晢ｽ｡郢晢ｽｼ郢晢ｽｫ驕橸ｽｮ陋ｻ・･繝ｻ繝ｻype繝ｻ蟲ｨ縲暖mail郢ｧ蟶敖竏ｽ・ｿ・｡
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
        # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
        cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py wowma_send_gmail --pk "
        cmd += pk + " --mail_type " + mail_type + " --other_message " + other_message
        msg += ' cmd[' + cmd + ']'
        p = subprocess.Popen(cmd, shell=True)
        msg += ' maybe ok.' + str(p.pid)

        # pk邵ｺ謔滂ｽｾ蜉ｱ・臥ｹｧ蠕娯螺郢ｧ蟲ｨ縺慕ｹ晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺・

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
    20220807 髴托ｽｽ陷会｣ｰ邵ｲ繧域ｬ陞ｳ螢ｹ・邵ｺ陂祐IN邵ｺ・ｮ郢晢ｽｪ郢ｧ・ｹ郢昴・SV郢ｧ蛛ｵ縺・ｹ昴・繝ｻ郢晢ｽｭ郢晢ｽｼ郢晏ｳｨ・邵ｺ・ｦ
    SP-API陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ縲旦S or JP邵ｺ荵晢ｽ臥ｹ昴・繝ｻ郢ｧ・ｿ郢ｧ雋橸ｽｼ霈披夢陟托ｽｵ郢ｧ荵敖繝ｻ
    Qoo10髮具ｽｩ陞｢・ｲ騾包ｽｨ邵ｺ・ｨ邵ｺ蜉ｱ窶ｻ陝・ｽｾ髮趣ｽ｡邵ｺ・ｯ驍ｨ讒ｭ・狗ｹｧ・､郢晢ｽ｡郢晢ｽｼ郢ｧ・ｸ
    邵ｺ・ｪ郢ｧ阮吮・郢ｧ蟲ｨ笆ｽ邵ｺ繝ｻ縲堤ｸｺ・ｫKeepa API郢ｧ繧・ｻ也ｸｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ窶ｻ髫ｧ・ｳ驍擾ｽｰ郢ｧ蜑・ｽｿ譎擾ｽｭ蛟･・邵ｺ貅假ｼ樒ｸｺ蠕後・郢晢ｽｻ

    隨倥・蜿咏ｹｧ鬘假ｽｾ・ｼ郢ｧﾂcsv邵ｺ・ｮ郢晁ｼ斐°郢晢ｽｼ郢晄ｧｭ繝｣郢昴・
    | asin | wholesale_price | wholesale_name |
    asin:asin郢ｧ・ｳ郢晢ｽｼ郢晏ｳｨ笳守ｸｺ・ｮ邵ｺ・ｾ邵ｺ・ｾ
    wholesale_price: 陷奇ｽｸ隶鯉ｽｭ髢繝ｻ繝ｻ闕ｳ蛟ｶ・ｻ・｣
    wholesale_name: 陷奇ｽｸ隶鯉ｽｭ髢繝ｻ繝ｻ陷ｷ蜥ｲ・ｧ・ｰ

    """

    logger.debug("get_qoo_asin_detail_upd_csv in")

    msg = "get_qoo_asin_detail_upd_csv start."
    # 邵ｺ・ｾ邵ｺ螢ｹﾂ竏壹Ψ郢ｧ・ｩ郢晢ｽｼ郢晢｣ｰ邵ｺ荵晢ｽ芽ｲゑｽ｡邵ｺ霈費ｽ檎ｹｧ豌祐V郢ｧ蛛ｵ竊堤ｹｧ鄙ｫ・・ｸｺ・ｿ邵ｺ・ｾ邵ｺ蜉ｱ・・
    if request.method == 'POST':
        try:
            form = QooAsinUpdCsvForm(request.POST, request.FILES)
            if form.is_valid():
                form_data = TextIOWrapper(request.FILES['file'].file, encoding='utf-8')
                csv_file = csv.reader(form_data, delimiter="\t")

                # QooAsinDetail 邵ｺ・ｮ csv_no 邵ｺ・ｫ邵ｲ竏晏徐郢ｧ鬘假ｽｾ・ｼ郢ｧ阮吮味csv陷雁・ｽｽ髦ｪ縲帝ｂ・｡騾・・逡鷹ｨｾ・｣騾｡・ｪ郢ｧ蛛ｵ繝ｻ郢ｧ荵敖繝ｻ+ 1
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
                        # form is_valid邵ｺ蜷姆
                        params = {
                            'title': 'csv邵ｺ・ｮ陷ｿ謔ｶ・企恷・ｼ邵ｺ・ｿ陞滂ｽｱ隰ｨ繝ｻ,
                            'message': 'csv邵ｺ・ｮ陟厄ｽ｢陟台ｸ岩ｲ雎・ｽ｣邵ｺ蜉ｱ・･邵ｺ繧・ｽ顔ｸｺ・ｾ邵ｺ蟶呻ｽ・髯ｦ蠕後・隰ｨ・ｰ邵ｺ迹夲ｽｶ・ｳ郢ｧ蟲ｨ竊醍ｸｺ繝ｻ[' + str(len(line)) + '])',
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
                # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧyaget邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
                msg += '<br>--------------------'
                msg += '<br> be on kick csvno. [' + str(new_csv_no) + ']'
                # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
                cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --csv_no "
                #cmd = "python3.6 /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback "
                cmd += str(new_csv_no)
                msg += ' cmd[' + cmd + ']'

                # 2019/7/6 闔会ｽ･闕ｳ荵昴・隴趣ｽｮ鬨ｾ螢ｹ繝ｻ陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ笆｡邵ｺ・｣邵ｺ貅倪ｲ隶灘綜・ｺ髢繝ｻ陷牙ｸ呻ｽ定愾謔ｶ・顔ｸｺ貅假ｼ・
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()
                msg += ' <br>pid:[' + str(p.pid) + ']'

                msg += '<br>--------------------'
                msg += "<br> end of get_qoo_asin_detail_upd_csv"
                params = {
                    'title': 'CSV UPLOAD陞ｳ蠕｡・ｺ繝ｻﾂ繝ｻSIN隲繝ｻ・ｰ・ｱ邵ｺ・ｮ隴厄ｽｴ隴・ｽｰ郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ繝ｻ,
                    'message': msg,
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_upd_csv called [exec_get_qoo_asin_detail_upd_csv]")
                return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)
            else:
                # form is_valid邵ｺ蜷姆
                params = {
                    'title': 'csv邵ｺ・ｮ陷ｿ謔ｶ・企恷・ｼ邵ｺ・ｿ陞滂ｽｱ隰ｨ繝ｻ,
                    'message': 'csv邵ｺ・ｮ陟厄ｽ｢陟台ｸ岩ｲ雎・ｽ｣邵ｺ蜉ｱ・･邵ｺ繧・ｽ顔ｸｺ・ｾ邵ｺ蟶呻ｽ・,
                }
                logger.debug("get_qoo_asin_detail_upd_csv invalid csv format.")
                return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)
        except Exception as e:
            msg += str(traceback.format_tb(e.__traceback__))
            params = {
                'title': 'CSV UPLOAD 陞滂ｽｱ隰ｨ蜉ｱ繝ｻ郢晢ｽｻ',
                'message': msg,
                'form': form,
            }
            logger.debug("get_qoo_asin_detail_upd_csv invalid exception occured[{}]".format(traceback.format_tb(e.__traceback__)))
            return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)

    else:
        csvform = QooAsinUpdCsvForm()
        params = {
            'title': '(Qoo10騾包ｽｨ) ASIN郢晢ｽｪ郢ｧ・ｹ郢昴・SV邵ｺ・ｫ郢ｧ蛹ｻ・帰SIN髫ｧ・ｳ驍擾ｽｰ隲繝ｻ・ｰ・ｱ陷ｿ髢・ｾ繝ｻUPLOAD FORM',
            'message': 'CSV郢ｧ蜻域ｬ陞ｳ螢ｹ・邵ｺ・ｦ郢ｧ・｢郢昴・繝ｻ郢晢ｽｭ郢晢ｽｼ郢晏ｳｨ・邵ｺ・ｦ邵ｺ荳岩味邵ｺ霈費ｼ・,
            'form': csvform,
        }

        logger.debug("get_qoo_asin_detail_upd_csv no csv entered.")
        return render(request, 'yaget/get_qoo_asin_detail_upd_csv.html', params)

    return

def get_qoo_asin_detail_single(request):
    """
    20220820 髴托ｽｽ陷会｣ｰ邵ｲ繧域ｬ陞ｳ螢ｹ・邵ｺ陂祐IN陷雁・ｽｽ阮吮・邵ｺ・､邵ｺ繝ｻ窶ｻ
    SP-API陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ縲旦S or JP邵ｺ荵晢ｽ臥ｹ昴・繝ｻ郢ｧ・ｿ郢ｧ雋橸ｽｼ霈披夢陟托ｽｵ郢ｧ荵敖繝ｻ
    Qoo10髮具ｽｩ陞｢・ｲ騾包ｽｨ邵ｺ・ｨ邵ｺ蜉ｱ窶ｻ陝・ｽｾ髮趣ｽ｡邵ｺ・ｯ驍ｨ讒ｭ・狗ｹｧ・､郢晢ｽ｡郢晢ｽｼ郢ｧ・ｸ
    邵ｺ・ｪ郢ｧ阮吮・郢ｧ蟲ｨ笆ｽ邵ｺ繝ｻ縲堤ｸｺ・ｫKeepa API郢ｧ繧・ｻ也ｸｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ窶ｻ髫ｧ・ｳ驍擾ｽｰ郢ｧ蜑・ｽｿ譎擾ｽｭ蛟･・邵ｺ貅假ｼ樒ｸｺ蠕後・郢晢ｽｻ

    POST陟大｢鍋・邵ｺ・ｯasin邵ｺ・ｰ邵ｺ莉｣ﾂ繝ｻ

    """

    logger.debug("get_qoo_asin_detail_single in")

    msg = "get_qoo_asin_detail_single start."
    # 邵ｺ・ｾ邵ｺ螢ｹﾂ竏壹Ψ郢ｧ・ｩ郢晢ｽｼ郢晢｣ｰ邵ｺ荵晢ｽ芽ｲゑｽ｡邵ｺ霈費ｽ檎ｹｧ豌祐V郢ｧ蛛ｵ竊堤ｹｧ鄙ｫ・・ｸｺ・ｿ邵ｺ・ｾ邵ｺ蜉ｱ・・
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
                # 郢ｧ・ｵ郢晄じ繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ邵ｺ・ｧyaget邵ｺ・ｮ郢ｧ・ｳ郢晄ｧｭﾎｦ郢晏ｳｨ・堤ｹｧ・ｭ郢昴・縺醍ｸｺ蜷ｶ・・
                msg += '<br>--------------------'
                # 邵ｺ阮呻ｼ・ｸｺ・ｧ郢ｧ・ｵ郢晏干繝ｻ郢晢ｽｭ郢ｧ・ｻ郢ｧ・ｹ郢ｧ蛛ｵ縺冗ｹ昴・縺・
                cmd = "source /home/django/djangoenv/bin/activate;python /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --asin "
                #cmd = "python3.6 /home/django/sample/manage.py exec_get_qoo_asin_detail_upd_csv --traceback --asin "
                cmd += str(request.POST['asin'])
                cmd += ' --csv_no ' + str(0) # csv_no 邵ｺ・ｯ驕ｨ・ｺ邵ｺ・ｧ邵ｺ繝ｻ・・
                msg += ' cmd[' + cmd + ']'

                # 2019/7/6 闔会ｽ･闕ｳ荵昴・隴趣ｽｮ鬨ｾ螢ｹ繝ｻ陷ｻ・ｼ邵ｺ・ｳ陷・ｽｺ邵ｺ蜉ｱ笆｡邵ｺ・｣邵ｺ貅倪ｲ隶灘綜・ｺ髢繝ｻ陷牙ｸ呻ｽ定愾謔ｶ・顔ｸｺ貅假ｼ・
                p = subprocess.Popen(cmd, shell=True)

                #msg += ' maybe ok.' + p.stdout.readline()
                msg += ' <br>pid:[' + str(p.pid) + ']'

                msg += '<br>--------------------'
                msg += "<br> end of get_qoo_asin_detail_single"
                params = {
                    'title': 'ASIN隲繝ｻ・ｰ・ｱ邵ｺ・ｮ隴厄ｽｴ隴・ｽｰ郢ｧ蟶晏ｹ戊沂荵晢ｼ邵ｺ・ｾ邵ｺ蜷ｶ繝ｻ郢晢ｽｻ郢晢ｽｻ',
                    'message': msg,
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_single called [exec_get_qoo_asin_detail_upd_csv]")
                return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)
            else:
                # form is_valid邵ｺ蜷姆
                params = {
                    'title': 'asin陷ｿ謔ｶ・企恷・ｼ邵ｺ・ｿ陞滂ｽｱ隰ｨ繝ｻ,
                    'message': 'asin邵ｺ・ｮ陟厄ｽ｢陟台ｸ岩ｲ雎・ｽ｣邵ｺ蜉ｱ・･邵ｺ繧・ｽ顔ｸｺ・ｾ邵ｺ蟶呻ｽ・,
                    'form': form,
                }
                logger.debug("get_qoo_asin_detail_single invalid csv format.")
                return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)
        except Exception as e:
            msg += str(traceback.format_tb(e.__traceback__))
            params = {
                'title': 'ASIN UPLOAD 陞滂ｽｱ隰ｨ蜉ｱ繝ｻ郢晢ｽｻ',
                'message': msg,
                'form': form,
            }
            logger.debug("get_qoo_asin_detail_single invalid exception occured[{}]".format(traceback.format_tb(e.__traceback__)))
            return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)

    else:
        asinform = QooAsinUpdAsinForm() # Form邵ｺ・ｯASIN郢ｧ雋楪蜿･謖ｨ陷茨ｽ･陷牙ｸ吮・郢ｧ荵昴Ψ郢ｧ・ｩ郢晢ｽｼ郢晢｣ｰ邵ｺ・ｫ
        params = {
            'title': '(Qoo10騾包ｽｨ) ASIN髫ｧ・ｳ驍擾ｽｰ隲繝ｻ・ｰ・ｱ陷ｿ髢・ｾ繝ｻUPLOAD FORM',
            'message': 'ASIN郢ｧ蜻域ｬ陞ｳ螢ｹ・邵ｺ・ｦ邵ｺ荳岩味邵ｺ霈費ｼ・,
            'form': asinform,
        }

        logger.debug("get_qoo_asin_detail_single no asin entered.")
        return render(request, 'yaget/get_qoo_asin_detail_upd_asin.html', params)

    return


class QooAsinDetailList(generic.ListView):
    """
    QooAsinDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ闕ｳﾂ髫包ｽｧ髯ｦ・ｨ闖ｴ諛医・
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
        # 隶諛・ｽｴ・｢隴弱ｅ竊鍋ｹ晏｣ｹ繝ｻ郢ｧ・ｸ郢晞亂繝ｻ郢ｧ・ｷ郢晢ｽｧ郢晢ｽｳ邵ｺ・ｫ鬮｢・｢鬨ｾ・｣邵ｺ蜉ｱ笳・ｹｧ・ｨ郢晢ｽｩ郢晢ｽｼ郢ｧ蟶昜ｺ溽ｸｺ繝ｻ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    # 隰夲ｽｽ陷・ｽｺ闔会ｽｶ隰ｨ・ｰ郢ｧ蝣､・ｵ讒ｭ・・
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
            # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            # 闖ｴ霈費ｽる恆譁撰ｼ・ｸｺ・ｪ邵ｺ繝ｻ
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
        test_form = QooAsinDetailSearchForm(initial=default_data) # 隶諛・ｽｴ・｢郢晁ｼ斐°郢晢ｽｼ郢晢｣ｰ
        ctx['test_form'] = test_form
        ctx['form_name'] = 'yaget'
        ctx['obj_all_cnt'] = QooAsinDetail.objects.all().count()
        return ctx

class QooAsinDetailDetail(generic.DetailView):
    """
    QooAsinDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晁歓・ｩ・ｳ驍擾ｽｰ
    """
    template_name = 'yaget/qoo_asin_detail_detail.html'
    model = QooAsinDetail

class QooAsinDetailDelete(generic.DeleteView):
    """
    QooAsinDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晉甥轤朱ｫｯ・､
    """
    template_name = 'yaget/qoo_asin_detail_delete.html'
    model = QooAsinDetail
    success_url = reverse_lazy('yaget:qoo_asin_detail_list')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, '邵ｲ鮓殉邵ｲ髦ｪ・定恆莨∝求邵ｺ蜉ｱ竏ｪ邵ｺ蜉ｱ笳・.format(self.object))
        return result


class QooAsinDetailCreate(generic.CreateView):
    """
    QooAsinDetail郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晄・・ｽ諛医・
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
    QooAsinDetail郢ｧ雋槭・闔会ｽｶ隶諛・ｽｴ・｢邵ｺ蜉ｱ窶ｻ邵ｲ・郡V郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ雋槫徐郢ｧ鬘假ｽｾ・ｼ邵ｺ・ｿDB邵ｺ・ｫ隴ｬ・ｼ驍城亂・邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
    """
    template_name = 'yaget/qoo_asin_csv_import.html'
    success_url = reverse_lazy('yaget:qoo_asin_detail_list')
    form_class = QooAsinUpdCsvForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_name'] = 'yaget'
        ctx['message'] = 'QooAsinCsvImport邵ｺ・ｧ邵ｺ繝ｻ
        return ctx

    def form_valid(self, form):
        """post邵ｺ霈費ｽ檎ｸｺ鬯ｱSV郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ螳夲ｽｪ・ｭ邵ｺ・ｿ髴趣ｽｼ邵ｺ・ｿ邵ｲ縲・ShopImportCat 郢昴・繝ｻ郢晄じﾎ晉ｸｺ・ｫ騾具ｽｻ鬪ｭ・ｲ邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ""
        csvfile = TextIOWrapper(form.cleaned_data['file'], encoding='utf-8')
        reader = csv.reader(csvfile, delimiter="\t")
        for row in reader:
            """
            YaShopImportCat 郢昴・繝ｻ郢晄じﾎ晉ｹｧ遏･yshop_cat_all (primary key)邵ｺ・ｧ隶諛・ｽｴ・｢邵ｺ蜉ｱ竏ｪ邵ｺ繝ｻ
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
    QooAsinDetail邵ｺ・ｮ郢晢ｽｬ郢ｧ・ｳ郢晢ｽｼ郢晏ｳｨﾂｰ郢ｧ蟲ｨﾂ・郡V郢晁ｼ斐＜郢ｧ・､郢晢ｽｫ郢ｧ蜑・ｽｽ諛医・邵ｺ蜉ｱ窶ｻresponse邵ｺ・ｫ陷・ｽｺ陷牙ｸ呻ｼ邵ｺ・ｾ邵ｺ蜷ｶﾂ繝ｻ
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

        # 隶諛・ｽｴ・｢隴夲ｽ｡闔会ｽｶ
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
            csvfilename = csvfilename.replace(' ','').replace('>','_').replace('邵ｲ繝ｻ,'-')

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