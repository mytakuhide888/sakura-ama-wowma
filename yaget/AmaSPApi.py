# coding: utf-8
import base64
from django.shortcuts import render
from django.http import HttpResponse
import sys, io, six
import datetime
import sqlite3
from contextlib import closing
import re
import json
from time import sleep

import hashlib
from hashlib import sha256
from base64 import b64encode

from oauth2client.service_account import ServiceAccountCredentials
import time
import hmac
import logging
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
import requests
import sys
import linecache
import traceback

from chrome_driver import CommonChromeDriver

from sp_api.api import Feeds
from sp_api.api import Sellers, Catalog, Products, CatalogItems
from sp_api.base.marketplaces import Marketplaces

# こちらは python-amazon-sp-api を組み込んでみる版

"""
参考にしたサイト
★SP-API　API一覧
https://github.com/jlevers/selling-partner-api/tree/main/docs/Api

★これ組み込むほうが早いかも
pip install python-amazon-sp-api
https://sp-api-docs.saleweaver.com/endpoints/catalog/

こんな感じで使えそう
https://www.shinkainoblog.com/programing/amazon-selling-partner-api%E3%81%AE%E3%83%A1%E3%83%A2/#toc6




SP-APIのドキュメント（公式）
https://developer.amazonservices.jp/

日本語のgit hub　ドキュメント
https://github.com/amzn/selling-partner-api-docs/tree/main/guides/ja-JP

★デベロッパー向け
https://github.com/amzn/selling-partner-api-docs/blob/main/guides/ja-JP/developer-guide/SellingPartnerApiDeveloperGuide(%E6%97%A5%E6%9C%AC%E8%AA%9E).md

SP-APIの準備
https://zats-firm.com/2021/09/07/amazon-mws-%e3%81%8b%e3%82%89-sp-api-%e3%81%b8%e3%81%ae%e7%a7%bb%e8%a1%8c-%e6%ba%96%e5%82%99%e7%b7%a8/#AWS_IAM

PYTHONでたたく
https://zats-firm.com/2021/09/09/amazon-mws-%e3%81%8b%e3%82%89-sp-api-%e3%81%b8%e3%81%ae%e7%a7%bb%e8%a1%8c-python%e3%81%a7sp-api%e3%82%92%e3%81%9f%e3%81%9f%e3%81%8f%e7%b7%a8/


"""

# mojule よみこみ
sys.path.append('/home/django/sample')
sys.path.append('/home/django/sample/yaget')
sys.path.append('/home/django/sample/sample')

from yaget.models import (
    YaAmaGoodsDetail,
    YaShopAmaGoodsDetail,
    YaShopImportAmaGoodsDetail,
    YaItemList,
    YaShopImportSpApiAmaGoodsDetail,
    AsinDetail,
    QooAsinDetail,
    AsinBlacklistAsin,
    AsinBlacklistKeyword,
    AsinBlacklistBrand,
)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# reload(sys)
# sys.setdefaultencoding('utf-8')
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# listmatchingproductsについてこちら
# https://lets-hack.tech/programming/languages/python/mws/

# 共通設定
dbname = '/home/django/sample/amget/amget.sqlite3'
# スクレイピング時のchromeデータ保持領域
USER_DATA_DIR = '/home/django/sample/yaget/userdata/'


AMAZON_CREDENTIAL = {
  'SELLER_ID': os.getenv('AWS_SELLER_ID', ''),
  'ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', ''),
  'ACCESS_SECRET': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
}

MARKETPLACES = {
  "CA": ("https://mws.amazonservices.ca", "A2EUQ1WTGCTBG2"),
  "US": ("https://mws.amazonservices.com", "ATVPDKIKX0DER"),
  "DE": ("https://mws-eu.amazonservices.com", "A1PA6795UKMFR9"),
  "ES": ("https://mws-eu.amazonservices.com", "A1RKKUPIHCS9HS"),
  "FR": ("https://mws-eu.amazonservices.com", "A13V1IB3VIYZZH"),
  "IN": ("https://mws.amazonservices.in", "A21TJRUUN4KGV"),
  "IT": ("https://mws-eu.amazonservices.com", "APJ6JRA9NG5V4"),
  "UK": ("https://mws-eu.amazonservices.com", "A1F83G8C2ARO7P"),
  "JP": ("https://mws.amazonservices.jp", "A1VC38T7YXB528"),
  "CN": ("https://mws.amazonservices.com.cn", "AAHKV2X7AFYLW"),
  "MX": ("https://mws.amazonservices.com.mx", "A1AM78C64UM0Y8")
}

DOMAIN = 'mws.amazonservices.jp'
ORDERENDPOINT = '/Orders/2013-09-01'

ENDPOINT = '/Products/2011-10-01'


PRODUCTSENDPOINT = '/Products/2011-10-01'

ORDERSNS = {
  "2013-09-01": "https://mws.amazonservices.com/Orders/2013-09-01"
}

PRODUCTSNS = {
  "2011-10-01":"https://mws.amazonservices.com/schema/Products/2011-10-01"
}

class MWSError(Exception):
  pass

def failure(e):
    exc_type, exc_obj, tb=sys.exc_info()
    lineno=tb.tb_lineno
    return str(lineno) + ":" + str(type(e))

def datetime_encode(dt):
  return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def find_orders_by_obj(myobj, element):
  return myobj.find(".//2013-09-01:%s" % element, ORDERSNS)


def set_order(myc, myorder):
  myAmazonOrderId = find_orders_by_obj(myorder, 'AmazonOrderId')
  myAmazonOrderIdval = ' '
  if (myAmazonOrderId is not None):
      myAmazonOrderIdval = myAmazonOrderId.text
  myPurchaseDate = find_orders_by_obj(myorder, 'PurchaseDate')
  myPurchaseDateval = None
  if (myPurchaseDate is not None):
      myPurchaseDateval = myPurchaseDate.text
  myLastUpdateDate = find_orders_by_obj(myorder, 'LastUpdateDate')
  myLastUpdateDateval = None
  if (myLastUpdateDate is not None):
      myLastUpdateDateval = myLastUpdateDate.text
  myFulfillmentChannel = find_orders_by_obj(myorder, 'FulfillmentChannel')
  myFulfillmentChannelval = None
  if (myFulfillmentChannel is not None):
      myFulfillmentChannelval = myFulfillmentChannel.text

  myShippingAddress = find_orders_by_obj(myorder, 'ShippingAddress')
  if (myShippingAddress is not None):
      myShippingAddressName = find_orders_by_obj(myShippingAddress, 'Name')
      myShippingAddressNameval = None
      if (myShippingAddressName is not None):
          myShippingAddressNameval = myShippingAddressName.text
      myShippingAddressAddressLine1 = find_orders_by_obj(myShippingAddress, 'AddressLine1')
      myShippingAddressAddressLine1val = None
      if (myShippingAddressAddressLine1 is not None):
          myShippingAddressAddressLine1val = myShippingAddressAddressLine1.text
      myShippingAddressAddressLine2 = find_orders_by_obj(myShippingAddress, 'AddressLine2')
      myShippingAddressAddressLine2val = None
      if (myShippingAddressAddressLine2 is not None):
          myShippingAddressAddressLine2val = myShippingAddressAddressLine2.text
      myShippingAddressAddressLine3 = find_orders_by_obj(myShippingAddress, 'AddressLine3')
      myShippingAddressAddressLine3val = None
      if (myShippingAddressAddressLine3 is not None):
          myShippingAddressAddressLine3val = myShippingAddressAddressLine3.text
      myShippingAddressCity = find_orders_by_obj(myShippingAddress, 'City')
      myShippingAddressCityval = None
      if (myShippingAddressCity is not None):
          myShippingAddressCityval = myShippingAddressCity.text
      myShippingAddressCounty = find_orders_by_obj(myShippingAddress, 'County')
      myShippingAddressCountyval = None
      if (myShippingAddressCounty is not None):
          myShippingAddressCountyval = myShippingAddressCounty.text
      myShippingAddressDistrict = find_orders_by_obj(myShippingAddress, 'District')
      myShippingAddressDistrictval = None
      if (myShippingAddressDistrict is not None):
          myShippingAddressDistrictval = myShippingAddressDistrict.text
      myShippingAddressStateOrRegion = find_orders_by_obj(myShippingAddress, 'StateOrRegion')
      myShippingAddressStateOrRegionval = None
      if (myShippingAddressStateOrRegion is not None):
          myShippingAddressStateOrRegionval = myShippingAddressStateOrRegion.text
      myShippingAddressPostalCode = find_orders_by_obj(myShippingAddress, 'PostalCode')
      myShippingAddressPostalCodeval = None
      if (myShippingAddressPostalCode is not None):
          myShippingAddressPostalCodeval = myShippingAddressPostalCode.text
      myShippingAddressCountryCode = find_orders_by_obj(myShippingAddress, 'CountryCode')
      myShippingAddressCountryCodeval = None
      if (myShippingAddressCountryCode is not None):
          myShippingAddressCountryCodeval = myShippingAddressCountryCode.text
      myShippingAddressPhone = find_orders_by_obj(myShippingAddress, 'Phone')
      myShippingAddressPhoneval = None
      if (myShippingAddressPhone is not None):
          myShippingAddressPhoneval = myShippingAddressPhone.text
      myShippingAddressAddressType = find_orders_by_obj(myShippingAddress, 'AddressType')
      myShippingAddressAddressTypeval = None
      if (myShippingAddressAddressType is not None):
          myShippingAddressAddressTypeval = myShippingAddressAddressType.text

  mySalesChannel = find_orders_by_obj(myorder, 'SalesChannel')
  mySalesChannelval = None
  if (mySalesChannel is not None):
      mySalesChannelval = mySalesChannel.text
  myShipServiceLevel = find_orders_by_obj(myorder, 'ShipServiceLevel')
  myShipServiceLevelval = None
  if (myShipServiceLevel is not None):
      myShipServiceLevelval = myShipServiceLevel.text
  myPofileFieldsval = None

  myOrderTotal = find_orders_by_obj(myorder, 'OrderTotal')
  if (myOrderTotal is not None):
      myOrderCurrencycode = find_orders_by_obj(myOrderTotal, 'CurrencyCode')
      myOrderCurrencycodeval = None
      if (myOrderCurrencycode is not None):
          myOrderCurrencycodeval = myOrderCurrencycode.text
      myOrderAmount = find_orders_by_obj(myOrderTotal, 'Amount')
      myOrderAmountval = None
      if (myOrderAmount is not None):
          myOrderAmountval = myOrderAmount.text

  myNumberOfItemsShipped = find_orders_by_obj(myorder, 'NumberOfItemsShipped')
  myNumberOfItemsShippedval = None
  if (myNumberOfItemsShipped is not None):
      myNumberOfItemsShippedval = myNumberOfItemsShipped.text
  myNumberOfItemsUnshipped = find_orders_by_obj(myorder, 'NumberOfItemsUnshipped')
  myNumberOfItemsUnshippedval = None
  if (myNumberOfItemsUnshipped is not None):
      myNumberOfItemsUnshippedval = myNumberOfItemsUnshipped.text
  myPaymentExecutionDetail = find_orders_by_obj(myorder, 'PaymentExecutionDetail')
  myPaymentExecutionDetailval = None
  if (myPaymentExecutionDetail is not None):
      myPaymentExecutionDetailval = myPaymentExecutionDetail.text
  myPaymentMethod = find_orders_by_obj(myorder, 'PaymentMethod')
  myPaymentMethodval = None
  if (myPaymentMethod is not None):
      myPaymentMethodval = myPaymentMethod.text
  myPaymentMethodDetails = find_orders_by_obj(myorder, 'PaymentMethodDetails')
  myPaymentMethodDetailsval = None
  if (myPaymentMethodDetails is not None):
      myPaymentMethodDetailsval = myPaymentMethodDetails.text
  myIsReplacementOrder = find_orders_by_obj(myorder, 'IsReplacementOrder')
  myIsReplacementOrderval = None
  if (myIsReplacementOrder is not None):
      myIsReplacementOrderval = myIsReplacementOrder.text
  myMarketplaceId = find_orders_by_obj(myorder, 'MarketplaceId')
  myMarketplaceIdval = None
  if (myMarketplaceId is not None):
      myMarketplaceIdval = myMarketplaceId.text
  myBuyerEmail = find_orders_by_obj(myorder, 'BuyerEmail')
  myBuyerEmailval = None
  if (myBuyerEmail is not None):
      myBuyerEmailval = myBuyerEmail.text
  myBuyerName = find_orders_by_obj(myorder, 'BuyerName')
  myBuyerNameval = None
  if (myBuyerName is not None):
      myBuyerNameval = myBuyerName.text
  myBuyerCountry = find_orders_by_obj(myorder, 'BuyerCountry')
  myBuyerCountryval = None
  if (myBuyerCountry is not None):
      myBuyerCountryval = myBuyerCountry.text
  myBuyerTaxInfo = find_orders_by_obj(myorder, 'BuyerTaxInfo')
  myBuyerTaxInfoval = None
  if (myBuyerTaxInfo is not None):
      myBuyerTaxInfoval = myBuyerTaxInfo.text
  myShipmentServiceLevelCategory = find_orders_by_obj(myorder, 'ShipmentServiceLevelCategory')
  myShipmentServiceLevelCategoryval = None
  if (myShipmentServiceLevelCategory is not None):
      myShipmentServiceLevelCategoryval = myShipmentServiceLevelCategory.text
  myOrderType = find_orders_by_obj(myorder, 'OrderType')
  myOrderTypeval = None
  if (myOrderType is not None):
      myOrderTypeval = myOrderType.text
  myEarliestShipDate = find_orders_by_obj(myorder, 'EarliestShipDate')
  myEarliestShipDateval = None
  if (myEarliestShipDate is not None):
      myEarliestShipDateval = myEarliestShipDate.text
  myLatestShipDate = find_orders_by_obj(myorder, 'LatestShipDate')
  myLatestShipDateval = None
  if (myLatestShipDate is not None):
      myLatestShipDateval = myLatestShipDate.text
  myEarliestDeliveryDate = find_orders_by_obj(myorder, 'EarliestDeliveryDate')
  myEarliestDeliveryDateval = None
  if (myEarliestDeliveryDate is not None):
      myEarliestDeliveryDateval = myEarliestDeliveryDate.text
  myLatestDeliveryDate = find_orders_by_obj(myorder, 'LatestDeliveryDate')
  myLatestDeliveryDateval = None
  if (myLatestDeliveryDate is not None):
      myLatestDeliveryDateval = myLatestDeliveryDate.text
  myIsBusinessOrder = find_orders_by_obj(myorder, 'IsBusinessOrder')
  myIsBusinessOrderval = None
  if (myIsBusinessOrder is not None):
      myIsBusinessOrderval = myIsBusinessOrder.text
  myIsPrime = find_orders_by_obj(myorder, 'IsPrime')
  myIsPrimeval = None
  if (myIsPrime is not None):
      myIsPrimeval = myIsPrime.text
  myPromiseResponseDueDate = find_orders_by_obj(myorder, 'PromiseResponseDueDate')
  myPromiseResponseDueDateval = None
  if (myPromiseResponseDueDate is not None):
      myPromiseResponseDueDateval = myPromiseResponseDueDate.text
  myOrderStatus = find_orders_by_obj(myorder, 'OrderStatus')
  myOrderStatusval = None
  if (myOrderStatus is not None):
      myOrderStatusval = myOrderStatus.text

  sql = 'insert into orders (amazon_order_id,purchase_date,last_update_date,fulfillment_channel,shipping_add_name,shipping_add_line_1,shipping_add_line_2,shipping_add_line_3,shipping_add_city,shipping_add_country,shipping_add_distinct,shipping_add_state,shipping_add_poscode,shipping_add_countrycode,shipping_add_phone,shipping_add_addtype,sales_channel,ship_service_level,profile_fields,order_currencycode,order_amount,number_of_items_shipped,number_of_items_unshipped,payment_execution_detail,payment_method,payment_method_details,is_replacement_order,marketplace_id,buyer_email,buyer_name,buyer_county,buyer_tax_info,shipment_service_level_category,order_type,earliest_ship_date,latest_ship_date,earliest_delivery_date,latest_delivery_date,is_business_order,is_prime,promise_response_due_date,order_status) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
  mydata = (
  myAmazonOrderIdval, myPurchaseDateval, myLastUpdateDateval, myFulfillmentChannelval, myShippingAddressNameval,
  myShippingAddressAddressLine1val, myShippingAddressAddressLine2val, myShippingAddressAddressLine3val,
  myShippingAddressCityval, myShippingAddressCountyval, myShippingAddressDistrictval,
  myShippingAddressStateOrRegionval, myShippingAddressPostalCodeval, myShippingAddressCountryCodeval,
  myShippingAddressPhoneval, myShippingAddressAddressTypeval, mySalesChannelval, myShipServiceLevelval,
  myPofileFieldsval, myOrderCurrencycodeval, myOrderAmountval, myNumberOfItemsShippedval, myNumberOfItemsUnshippedval,
  myPaymentExecutionDetailval, myPaymentMethodval, myPaymentMethodDetailsval, myIsReplacementOrderval,
  myMarketplaceIdval, myBuyerEmailval, myBuyerNameval, myBuyerCountryval, myBuyerTaxInfoval,
  myShipmentServiceLevelCategoryval, myOrderTypeval, myEarliestShipDateval, myLatestShipDateval,
  myEarliestDeliveryDateval, myLatestDeliveryDateval, myIsBusinessOrderval, myIsPrimeval, myPromiseResponseDueDateval,
  myOrderStatusval)
  myc.execute(sql, mydata)
  return


class MWSError(Exception):
  pass


# MWS
#
class BaseObject(object):
    _response = None

    _orders_namespace = {
        "ns": "http://mws.amazonaws.com/doc/2009-01-01/"
    }

    _orders_namespace = {
        "2013-09-01": "https://mws.amazonservices.com/Orders/2013-09-01"
    }

    _products_namespace = {
        "2011-10-01": "http://mws.amazonservices.com/schema/Products/2011-10-01",
        "ns2": "http://mws.amazonservices.com/schema/Products/2011-10-01/default.xsd"
    }

    # VERSION = "2009-01-01"
    #VERSION = "2013-09-01"
    VERSION = "2011-10-01"

    AMAZON_CREDENTIAL = {
        'SELLER_ID': os.getenv('AWS_SELLER_ID', ''),
        'ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID', ''),
        'ACCESS_SECRET': os.getenv('AWS_SECRET_ACCESS_KEY', ''),
    }

    DOMAIN = 'mws.amazonservices.jp'
    ENDPOINT = '/Products/2011-10-01'
    VERSION = "2011-10-01"

    def datetime_encode(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def __init__(self, logger, AWSAccessKeyId=None, AWSSecretAccessKey=None,
               SellerId=None, Region='JP', Version="", MWSAuthToken=""):

        # logging
        #logging.basicConfig(filename='/home/django/sample/yaget/log/amamws.log', level=logging.DEBUG)
        #logger = logging.getLogger(__name__)
        #logger.setLevel(10)
        self.logger = logger
        self.logger.info('AmaMws request init in')
        self.logger.debug('AmaMws request debug init in')

        # self.AWSAccessKeyId = AWSAccessKeyId
        # self.AWSSecretAccessKey = AWSSecretAccessKey
        # self.SellerId = SellerId
        self.AWSAccessKeyId = AMAZON_CREDENTIAL['ACCESS_KEY_ID']
        self.AWSSecretAccessKey = AMAZON_CREDENTIAL['ACCESS_SECRET']
        self.SellerId = AMAZON_CREDENTIAL['SELLER_ID']
        self.Region = Region
        self.Version = Version or self.VERSION

        if Region in MARKETPLACES:
            self.service_domain = MARKETPLACES[self.Region][0]
        else:
            raise MWSError("Incorrrect region supplied {region}".format(**{"region": region}))

    # API
    def request(self, endpoint, method="POST", **kwargs):
        params = {
            'AWSAccessKeyId': self.AWSAccessKeyId,
            'SellerId': self.SellerId,
            'SignatureVersion': '2',
            'Timestamp': self.timestamp,
            'Version': self.Version,
            'SignatureMethod': 'HmacSHA256'
        }

        params.update(kwargs)

        #        signature, query_string = self.signature(method, endpoint, params)

        query_string = '&'.join('{}={}'.format(
            n, urllib.parse.quote(v, safe='')) for n, v in sorted(params.items()))

        canonical = "{}\n{}\n{}\n{}".format(
            'POST', DOMAIN, endpoint, query_string
        )

        h = hmac.new(
            six.b(AMAZON_CREDENTIAL['ACCESS_SECRET']),
            six.b(canonical), hashlib.sha256)

        signature = urllib.parse.quote(base64.b64encode(h.digest()), safe='')

        url = 'https://{}{}?{}&Signature={}'.format(
            DOMAIN, endpoint, query_string, signature)

      #        url = self.build_url(endpoint, query_string, signature)

        print("m_url:[%s]", url)
        #self.logger.info('AmaMws request m_url:' + str(url))
        #self.logger.debug('AmaMws request debug m_url:' + str(url))

        try:
            request = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(request) as page:
                self._response = page.read()
        except Exception as e:
            print("message:{0}".format(str(failure(e))))
        #request = urllib.request.Request(url, method=method)
        #with urllib.request.urlopen(request) as page:
        #    self._response = page.read()
        print("doukana response:[%s]", self._response)
        return self

    def signature(self, method, endpoint, params):
        query_string = self.quote_query(params)

        data = method + "\n" + self.service_domain.replace("https://", "") + endpoint + "\n/\n" + query_string

        if type(self.AWSSecretAccessKey) is str:
            self.AWSSecretAccessKey = self.AWSSecretAccessKey.encode('utf-8')

        if type(data) is str:
            data = data.encode('utf-8')

        digest = hmac.new(self.AWSSecretAccessKey, data, sha256).digest()
        return (urllib.parse.quote(b64encode(digest)), query_string)

    def build_url(self, endpoint, query_string, signature):
        return "%s%s/?%s&Signature=%s" % (self.service_domain, endpoint, query_string, signature)

    def enumerate_param(self, param, values):
        """
          Builds a dictionary of an enumerated parameter.
          Takes any iterable and returns a dictionary.
          ie.
          enumerate_param('MarketplaceIdList.Id', (123, 345, 4343))
          returns
          {
              MarketplaceIdList.Id.1: 123,
              MarketplaceIdList.Id.2: 345,
              MarketplaceIdList.Id.3: 4343
          }
        """
        params = {}

        if not param.endswith('.'):
            param = "%s." % param
        for num, value in enumerate(values):
            params['%s%d' % (param, (num + 1))] = value
        return params

    @staticmethod
    def quote_query(query):
        return "&".join("%s=%s" % (
            k, urllib.parse.quote(
                str(query[k]).encode('utf-8'), safe='-_.~'))
                    for k in sorted(query))

    @property
    def timestamp(self):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @property
    def raw(self):
        return self._response

    # xml
    @property
    def parse(self):
        if self._response is None:
            raise
        # print('start parse')
        # print('my res:[%s]',self._response)

        return ET.fromstring(self._response)

    def find(self, element):
        return self.parse.find(".//ns:%s" % element, self._namespace)

    def find_orders(self, element):
        return self.parse.find(".//2013-09-01:%s" % element, self._orders_namespace)

    def find_orders_all(self, element):
        return self.parse.findall(".//2013-09-01:%s" % element, self._orders_namespace)

    # element には「ASIN」などmws から返ってきたxmlのタグ名を
    def find_list_matched_product(self, element):
        #return self.parse.find("2011-10-01:%s" % element, self._products_namespace)
        return self.parse.find(".//2011-10-01:%s" % element, self._products_namespace)

    # product で取れたxmlのオブジェクト対応
    def find_list_matched_product_by_obj(self, myobj, element):
        #return self.parse.find("2011-10-01:%s" % element, self._products_namespace)
        return myobj.find(".//2011-10-01:%s" % element, self._products_namespace)

    # SalesRankは3つくらい取れそう
    def find_list_matched_product_all(self, element):
        self.logger.info('AmaMws Product find_list_matched_product_all in.')
        #self.logger.info('xml... ' + str(self._response))
        return self.parse.findall(".//2011-10-01:%s" % element, self._products_namespace)

    def find_list_matched_product_all_by_obj(self, myobj, element):
        return myobj.findall(".//2011-10-01:%s" % element, self._products_namespace)

    def find_list_matched_product_default(self, element):
        return self.parse.find(".//ns2:%s" % element, self._products_namespace)

    def find_list_matched_product_default_by_obj(self, myobj, element):
        return myobj.find(".//ns2:%s" % element, self._products_namespace)

    def find_list_matched_product_itemdimention(self, element):
        ItemDimensionsobj = self.find_list_matched_product_default('ItemDimensions')
        if ItemDimensionsobj is not None:
            return ItemDimensionsobj.find('.//ns2:%s' % element, self._products_namespace)
        else:
            return None

    def find_list_matched_product_itemdimention_by_obj(self, myobj, element):
        ItemDimensionsobj = self.find_list_matched_product_default_by_obj(myobj, 'ItemDimensions')
        if ItemDimensionsobj is not None:
            return ItemDimensionsobj.find('.//ns2:%s' % element, self._products_namespace)
        else:
            return None

    def find_list_matched_product_packagedimention(self, element):
        PackageDimensionsobj = self.find_list_matched_product_default('PackageDimensions')
        if PackageDimensionsobj is not None:
            return PackageDimensionsobj.find('.//ns2:%s' % element, self._products_namespace)
        else:
            return None

    def find_list_matched_product_packagedimention_by_obj(self, myobj, element):
        PackageDimensionsobj = self.find_list_matched_product_default_by_obj(myobj, 'PackageDimensions')
        if PackageDimensionsobj is not None:
            return PackageDimensionsobj.find('.//ns2:%s' % element, self._products_namespace)
        else:
            return None

class AmaSPApi(object):

    # Yahoo国内版は、db_entryの指定はなし
    # Yahoo 輸入版、csvでカテゴリなど渡すバージョンは、csvのレコードを db_entryに格納して渡す
    # 本版では、USのAmazon SP-API を叩いてアメリカのasinを集めてくる。
    def __init__(self, logger, bid, gid, my_query, db_entry=None):
        self.logger = logger
        #self.products = Products(logger)
        #self._response = myxml

        # 商品単位となるが一時保持用に変数を用意する
        self._bid = bid
        self._gid = gid
        self._query = my_query
        self.parsedxml_list = []
        self._db_entry = db_entry

        self.logger.info('AmaSPAPI  in. init keyword:[{}]'.format(self._query))
        self.upd_csv = []
        self.target_url = "https://api.amazon.com/auth/o2/token"
        self.grant_type = "refresh_token"
        self.refresh_token = os.getenv('LWA_REFRESH_TOKEN', '')
        self.client_id = os.getenv('LWA_CLIENT_ID', '')
        self.client_secret = os.getenv('LWA_CLIENT_SECRET', '')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        self.req_headers = None
        self.get_url = "https://sellingpartnerapi-na.amazon.com"  # 北米
        #self.get_url = "https://sellingpartnerapi-fe.amazon.com" # 日本
        self.access_token = None
        self.marketplace = "ATVPDKIKX0DER" # 北米 ATVPDKIKX0DER  カナダ　A2EUQ1WTGCTBG2 日本 A1VC38T7YXB528
        self.host = "sellingpartnerapi-na.amazon.com"  # 北米
        # self.host = "sellingpartnerapi-fe.amazon.com"  # 日本
        self.region = "us-east-1"  # 北米
        #self.region = "us-west-2"  # 日本
        self.service = "execute-api"

        self.credentials = dict(
            refresh_token=self.refresh_token,
            lwa_app_id=self.client_id,
            lwa_client_secret=self.client_secret,
            aws_secret_key=self.aws_secret_access_key,
            aws_access_key=self.aws_access_key,
            #role_arn='arn:aws:iam::000222965326:user/AWS_IAM_SPAPI_Access_User'
        )

    def spapi_get_participantion(self):

        #response = Sellers(marketplace=Marketplaces.JP, credentials=self.credentials).get_marketplace_participation()
        response = Sellers(marketplace=Marketplaces.US, credentials=self.credentials).get_marketplace_participation()
        self.logger.info('spapi_get_participantion [{}]'.format(response))
        #print(response)
        return

    def spapi_get_catalog_item(self, asin):

        asin = 'B07WXL5YPW'
        response = Catalog(marketplace=Marketplaces.US, credentials=self.credentials).get_item(asin)
        self.logger.info('spapi_get_catalog_item [{}]'.format(response))
        #print(response)
        return

    def spapi_list_item_by_keyword(self):

        keyword = 'Nintendo Switch'
        keyword = 'Watch Burgmeister BM505-122'
        #keyword = 'Watch Burgmeister Manila BM518-316'
        keyword = self._query
        response = Catalog(marketplace=Marketplaces.US, credentials=self.credentials).list_items(Query=keyword)
        #print(response)
        #response_ = ast.literal_eval(response)  # ValueError: malformed node or string:  と怒られる
        #print(response.headers)
        #print(response.payload)
        self.logger.info('spapi_list_item_by_keyword len[{}]'.format(len(response('Items'))))
        #print(len(response('Items')))  # Itemの個数はこれで取れる
        for item in response('Items'):
            MarketplaceASIN = item['Identifiers']['MarketplaceASIN']
            self.logger.info('marketplaceid:[{}] asin:[{}]'.format(
                MarketplaceASIN['MarketplaceId'], MarketplaceASIN['ASIN']))
            #print('marketplaceid:[{}] asin:[{}]'.format(MarketplaceASIN['MarketplaceId'], MarketplaceASIN['ASIN']))

            # 関連商品
            Relationships = item['Relationships']
            for relationship in Relationships:
                rel_MarketplaceASIN = relationship['Identifiers']['MarketplaceASIN']
                self.logger.info('rel_marketplaceid:[{}] asin:[{}]'.format(rel_MarketplaceASIN['MarketplaceId'],
                                                            rel_MarketplaceASIN['ASIN']))
                """
                print('rel_marketplaceid:[{}] asin:[{}]'.format(rel_MarketplaceASIN['MarketplaceId'],
                                                            rel_MarketplaceASIN['ASIN']))
                """

            # セールスランキング
            rank_cat_1 = ''
            rank_1 = ''
            SalesRankings = item['SalesRankings']
            for SalesRanking in SalesRankings:
                self.logger.info('salesrank_ProductCategoryId:[{}] Rank:[{}]'.format(SalesRanking['ProductCategoryId'],
                                                            SalesRanking['Rank']))
                rank_cat_1 = SalesRanking['ProductCategoryId']
                rank_1 = SalesRanking['Rank']
                """
                print('salesrank_ProductCategoryId:[{}] Rank:[{}]'.format(SalesRanking['ProductCategoryId'],
                                                            SalesRanking['Rank']))
                """

            # 属性
            AttributeSets = item['AttributeSets']
            for AttributeSet in AttributeSets:
                binding = ''
                if 'Binding' in AttributeSet:
                    binding = AttributeSet['Binding']
                brand = ''
                if 'Brand' in AttributeSet:
                    brand = AttributeSet['Brand']
                color = ''
                if 'Color' in AttributeSet:
                    color = AttributeSet['Color']
                self.logger.info('attr_Binding:[{}] Brand:[{}] Color:[{}]'.format(
                    binding, brand, color))
                """
                print('attr_Binding:[{}] Brand:[{}] Color:[{}]'.format(
                    binding, brand, color))
                """
                department = ''
                if 'Department' in AttributeSet:
                    department = AttributeSet['Department']


                display_size = ''
                if 'DisplaySize' in AttributeSet:
                    display_size = AttributeSet['DisplaySize']['value']
                hardware_platform = ''
                if 'HardwarePlatform' in AttributeSet:
                    hardware_platform = AttributeSet['HardwarePlatform']
                is_adult_product = ''
                if 'IsAdultProduct' in AttributeSet:
                    is_adult_product = AttributeSet['IsAdultProduct']
                self.logger.info('attr_DisplaySize:[{}] HardwarePlatform:[{}] IsAdultProduct:[{}]'.format(
                    display_size, hardware_platform, is_adult_product))
                """
                print('attr_DisplaySize:[{}] HardwarePlatform:[{}] IsAdultProduct:[{}]'.format(
                    display_size, hardware_platform, is_adult_product))
                """

                item_dim_height_val = ''
                item_dim_height_units = ''
                item_dim_length_val = ''
                item_dim_length_units = ''
                item_dim_weight_val = ''
                item_dim_weight_units = ''
                item_dim_width_val = ''
                item_dim_width_units = ''

                if 'ItemDimensions' in AttributeSet:
                    if 'Height' in AttributeSet['ItemDimensions']:
                        item_dim_height_val = AttributeSet['ItemDimensions']['Height']['value']
                        item_dim_height_units = AttributeSet['ItemDimensions']['Height']['Units']
                    if 'Length' in AttributeSet['ItemDimensions']:
                        item_dim_length_val = AttributeSet['ItemDimensions']['Length']['value']
                        item_dim_length_units = AttributeSet['ItemDimensions']['Length']['Units']
                    if 'Weight' in AttributeSet['ItemDimensions']:
                        item_dim_weight_val = AttributeSet['ItemDimensions']['Weight']['value']
                        item_dim_weight_units = AttributeSet['ItemDimensions']['Weight']['Units']
                    if 'Width' in AttributeSet['ItemDimensions']:
                        item_dim_width_val = AttributeSet['ItemDimensions']['Width']['value']
                        item_dim_width_units = AttributeSet['ItemDimensions']['Width']['Units']

                self.logger.info('attr_ItemDimensions_Height:[{}{}] Length:[{}{}] Weight:[{}{}] Width:[{}{}]'.format(
                    item_dim_height_val, item_dim_height_units,
                    item_dim_length_val, item_dim_length_units,
                    item_dim_weight_val, item_dim_weight_units,
                    item_dim_width_val, item_dim_width_units,
                ))
                """
                print('attr_ItemDimensions_Height:[{}{}] Length:[{}{}] Weight:[{}{}] Width:[{}{}]'.format(
                    item_dim_height_val, item_dim_height_units,
                    item_dim_length_val, item_dim_length_units,
                    item_dim_weight_val, item_dim_weight_units,
                    item_dim_width_val, item_dim_width_units,
                ))
                """
                label = ''
                if 'Label' in AttributeSet:
                    label = AttributeSet['Label']
                Languages = ''
                if 'Languages' in AttributeSet:
                    Languages = AttributeSet['Languages'][0]  # 複数あるが1つ目だけをとりあえず
                list_price_amount = ''
                list_price_currency_code = ''
                if 'ListPrice' in AttributeSet:
                    list_price_amount = AttributeSet['ListPrice']['Amount']
                    list_price_currency_code = AttributeSet['ListPrice']['CurrencyCode']
                self.logger.info('label:[{}] Languages:[{}] list_price:[{}({})]'.format(
                    label, Languages, list_price_amount, list_price_currency_code))
                """
                print('label:[{}] Languages:[{}] list_price:[{}({})]'.format(
                    label, Languages, list_price_amount, list_price_currency_code))
                """

                manufacturer = ''
                if 'Manufacturer' in AttributeSet:
                    manufacturer = AttributeSet['Manufacturer']
                model = ''
                if 'Model' in AttributeSet:
                    model = AttributeSet['Model']
                number_of_items = ''
                if 'NumberOfItems' in AttributeSet:
                    number_of_items = AttributeSet['NumberOfItems']
                self.logger.info('Manufacturer:[{}] Model:[{}] NumberOfItems:[{}]'.format(
                    manufacturer, model, number_of_items))
                """
                print('Manufacturer:[{}] Model:[{}] NumberOfItems:[{}]'.format(
                    manufacturer, model, number_of_items))
                """

                operating_system = ''
                if 'OperatingSystem' in AttributeSet:
                    for system_name in AttributeSet['OperatingSystem']: # ここは文字列でつなげる。必要であれば分割
                        operating_system += system_name + ' '
                self.logger.info('operating_system:[{}]'.format(operating_system))
                #print('operating_system:[{}]'.format(operating_system))

                pac_dim_height_val = ''
                pac_dim_height_units = ''
                pac_dim_length_val = ''
                pac_dim_length_units = ''
                pac_dim_weight_val = ''
                pac_dim_weight_units = ''
                pac_dim_width_val = ''
                pac_dim_width_units = ''

                if 'PackageDimensions' in AttributeSet:
                    if 'Height' in AttributeSet['PackageDimensions']:
                        pac_dim_height_val = AttributeSet['PackageDimensions']['Height']['value']
                        pac_dim_height_units = AttributeSet['PackageDimensions']['Height']['Units']
                    if 'Length' in AttributeSet['PackageDimensions']:
                        pac_dim_length_val = AttributeSet['PackageDimensions']['Length']['value']
                        pac_dim_length_units = AttributeSet['PackageDimensions']['Length']['Units']
                    if 'Weight' in AttributeSet['PackageDimensions']:
                        pac_dim_weight_val = AttributeSet['PackageDimensions']['Weight']['value']
                        pac_dim_weight_units = AttributeSet['PackageDimensions']['Weight']['Units']
                    if 'Width' in AttributeSet['PackageDimensions']:
                        pac_dim_width_val = AttributeSet['PackageDimensions']['Width']['value']
                        pac_dim_width_units = AttributeSet['PackageDimensions']['Width']['Units']

                self.logger.info('attr_PackageDimensions_Height:[{}{}] Length:[{}{}] Weight:[{}{}] Width:[{}{}]'.format(
                    pac_dim_height_val, pac_dim_height_units,
                    pac_dim_length_val, pac_dim_length_units,
                    pac_dim_weight_val, pac_dim_weight_units,
                    pac_dim_width_val, pac_dim_width_units,
                ))
                """
                print('attr_PackageDimensions_Height:[{}{}] Length:[{}{}] Weight:[{}{}] Width:[{}{}]'.format(
                    pac_dim_height_val, pac_dim_height_units,
                    pac_dim_length_val, pac_dim_length_units,
                    pac_dim_weight_val, pac_dim_weight_units,
                    pac_dim_width_val, pac_dim_width_units,
                ))
                """

                package_quantity = ''
                if 'PackageQuantity' in AttributeSet:
                    package_quantity = AttributeSet['PackageQuantity']
                part_number = ''
                if 'PartNumber' in AttributeSet:
                    part_number = AttributeSet['PartNumber']
                pegi_rating = ''
                if 'PegiRating' in AttributeSet:
                    pegi_rating = AttributeSet['PegiRating']
                self.logger.info('package_quantity:[{}] part_number:[{}] pegi_rating:[{}]'.format(
                    package_quantity, part_number, pegi_rating))
                """
                print('package_quantity:[{}] part_number:[{}] pegi_rating:[{}]'.format(
                    package_quantity, part_number, pegi_rating))
                """

                platform = ''
                if 'Platform' in AttributeSet:
                    platform = AttributeSet['Platform']
                product_group = ''
                if 'ProductGroup' in AttributeSet:
                    product_group = AttributeSet['ProductGroup']
                product_type_name = ''
                if 'ProductTypeName' in AttributeSet:
                    product_type_name = AttributeSet['ProductTypeName']
                publisher = ''
                if 'Publisher' in AttributeSet:
                    publisher = AttributeSet['Publisher']
                release_date = ''
                if 'ReleaseDate' in AttributeSet:
                    release_date = AttributeSet['ReleaseDate']
                print('platform:[{}] product_group:[{}] product_type_name:[{}] publisher[{}] release_date[{}]'.format(
                    platform, product_group, product_type_name, publisher, release_date))

                small_image_height_units = ''
                small_image_height_value = ''
                small_image_width_units = ''
                small_image_width_value = ''
                small_image_url = ''
                if 'SmallImage' in AttributeSet:
                    if 'Height' in AttributeSet['SmallImage']:
                        small_image_height_units = AttributeSet['SmallImage']['Height']['Units']
                        small_image_height_value = AttributeSet['SmallImage']['Height']['value']
                    if 'Width' in AttributeSet['SmallImage']:
                        small_image_width_units = AttributeSet['SmallImage']['Width']['Units']
                        small_image_width_value = AttributeSet['SmallImage']['Width']['value']
                    if 'URL' in AttributeSet['SmallImage']:
                        small_image_url = AttributeSet['SmallImage']['URL']

                self.logger.info('small_img height:[{} {}] width:[{} {}] URL:[{}]'.format(
                    small_image_height_units, small_image_height_value,
                    small_image_width_units, small_image_width_value,
                    small_image_url,
                ))
                """
                print('small_img height:[{} {}] width:[{} {}] URL:[{}]'.format(
                    small_image_height_units, small_image_height_value,
                    small_image_width_units, small_image_width_value,
                    small_image_url,
                ))
                """

                studio = ''
                if 'Studio' in AttributeSet:
                    studio = AttributeSet['Studio']
                title = ''
                if 'Title' in AttributeSet:
                    title = AttributeSet['Title']
                self.logger.info('studio:[{}] title:[{}]'.format(
                    studio, title))
                """
                print('studio:[{}] title:[{}]'.format(
                    studio, title))
                """

                # ここからDB登録 ====================================
                if not YaShopImportSpApiAmaGoodsDetail.objects.filter(asin=MarketplaceASIN['ASIN']).exists():
                    self.logger.debug("AmaSPApi start DB update_or_create")
                    obj, created = YaShopImportSpApiAmaGoodsDetail.objects.update_or_create(
                        asin=MarketplaceASIN['ASIN'] if MarketplaceASIN['ASIN'] else '',
                        title=title if title else '',
                        url=small_image_url if small_image_url else '',
                        amount=float(list_price_amount) if list_price_amount else 0,
                        binding=binding if binding else '',
                        brand=brand if brand else '',
                        color=color if color else '',
                        department=department if department else '',
                        is_adlt=False if is_adult_product == "false" else True,
                        i_height=float(item_dim_height_val) if item_dim_height_val else 0,
                        i_length=float(item_dim_length_val) if item_dim_length_val else 0,
                        i_width=float(item_dim_width_val) if item_dim_width_val else 0,
                        i_weight=float(item_dim_weight_val) if item_dim_weight_val else 0,
                        p_height=float(pac_dim_height_val) if pac_dim_height_val else 0,
                        p_length=float(pac_dim_length_val) if pac_dim_length_val else 0,
                        p_width=float(pac_dim_width_val) if pac_dim_width_val else 0,
                        p_weight=float(pac_dim_weight_val) if pac_dim_weight_val else 0,
                        rank_cat_1=rank_cat_1 if rank_cat_1 else '',
                        rank_1=int(rank_1) if rank_1 else 0,
                        rank_cat_2='',
                        rank_2=0,
                        rank_cat_3='',
                        rank_3=0,
                        shopid=self._bid,
                        gid=self._gid,
                        csv_no=self._db_entry.csv_no,
                        y_cat_1=self._db_entry.y_cat_1,
                        y_cat_2=self._db_entry.y_cat_2,
                        myshop_cat_1=self._db_entry.myshop_cat_1,
                        myshop_cat_2=self._db_entry.myshop_cat_2,
                    )
                    obj.save()
                self.logger.debug("AmaSPApi set DB end ")

        self.logger.info(response('Items'))
        #print(response('Items'))
        return

# ここまでがSP-APIで追加分。以下はMWSの残骸だから使わないが参考に #####################################


    def get_list_matching_products(self):
        self.products.logger.info('AmaMws get_list_matching_products in')

        try:
            tmpobj = self.products.ListMatchingProducts(urllib.parse.quote(self._query))
            #tmpobj = self.products.ListMatchingProducts(urllib.parse.quote_plus(self._query, encoding="utf-8"))
            #tmpobj = self.products.ListMatchingProducts(self._query)


            self.products.logger.info('AmaMws get_list_matching_products out')
            self.products._response = self.products.PostMWS(tmpobj)
            #self.products.logger.info('AmaMws get_list_matching_products _response:{0}'.format(str(self.products._response)))
        except Exception as e:
            self.products.logger.info('get_list_matching_products except:{0}'.format(str(failure(e))))
            print("message:{0}".format(str(failure(e))))
        if self.products._response is not None:
            return True
        else:
            return False
        #products = Products()
        #return self.products.request_list_matching_products(Query)

    # element には「ASIN」などmws から返ってきたxmlのタグ名を
    def find_list_matched_product_ns2(self, element):
        return self.products.find_list_matched_product_ns2(element)

    # element には「ASIN」などmws から返ってきたxmlのタグ名を
    def find_list_matched_product(self, element):
        return self.products.find_list_matched_product(element)

    def set_list_matched_product(self, product):

        parsedxml = {}

        key_normal_list = ["ASIN", "MarketplaceId"]
        for key_normal in key_normal_list:
            # 以下は productを引数にとらず一つだけ取ってきていた名残
            #findobj = self.find_list_matched_product(key_normal)
            findobj = self.products.find_list_matched_product_by_obj(product, key_normal)
            if findobj is None:
                return None # とれなかったらNG
            else:
                parsedxml[key_normal] = findobj.text

        # 初期値はstrのものを対象
        key_default_str_list = [
            "Title",
            "URL",
            "Amount",
            "Binding",
            "Brand",
            "Color",
            "Department",
            "IsAdultProduct",
        ]
        for key_default in key_default_str_list:
            #findobj = self.find_list_matched_product_default(key_default)
            findobj = self.products.find_list_matched_product_default_by_obj(product, key_default)
            if findobj is None:
                parsedxml[key_default] = ''
            else:
                parsedxml[key_default] = findobj.text

        # dimentionに関する値
        key_dimention_str_list = [
            "Height",
            "Length",
            "Width",
            "Weight",
        ]
        # itemdimentionに関する値
        for key_default in key_dimention_str_list:
            #findobj = self.find_list_matched_product_itemdimention(key_default)
            findobj = self.products.find_list_matched_product_itemdimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["i_" + key_default] = ''
            else:
                parsedxml["i_" + key_default] = findobj.text

        # packagedimentionに関する値
        for key_default in key_dimention_str_list: # リストはitemもpackageも同じ
            #findobj = self.find_list_matched_product_packagedimention(key_default)
            findobj = self.products.find_list_matched_product_packagedimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["p_" + key_default] = ''
            else:
                parsedxml["p_" + key_default] = findobj.text

        # SalesRankに関わるもの
        key_salesrank_list = ["ProductCategoryId", "Rank"]
        i = 0
        #findobj_list = self.find_list_matched_product_all("SalesRank")
        findobj_list = self.products.find_list_matched_product_all_by_obj(product, "SalesRank")
        #self.products.logger.info("AmaMws SalesRank findobj_list text:{0}".format(str(findobj_list)))
        if findobj_list:
            for findobj in findobj_list: # SalesRankは3つ
                i += 1
                #self.products.logger.info("AmaMws SalesRank findobj text:{0}".format(str(findobj)))

                for key_normal in key_salesrank_list:
                    finditem = findobj.find(".//2011-10-01:%s" % key_normal, self.products._products_namespace)

                    if finditem is None:
                        parsedxml[str(i) +  "_" + key_normal] = ''
                    else:
                        parsedxml[str(i) +  "_" + key_normal] = finditem.text
        if i < 3:
            parsedxml['3_Rank'] = 0
            parsedxml['3_ProductCategoryId'] = ''
        if i < 2:
            parsedxml['2_Rank'] = 0
            parsedxml['2_ProductCategoryId'] = ''
        if i < 1:
            parsedxml['1_Rank'] = 0
            parsedxml['1_ProductCategoryId'] = ''

        return parsedxml

    # Productで返ってきたリストは全部登録する
    def set_list_matched_product_all(self):
        self.products.logger.info('AmaMws set_list_matched_product_all in')

        try:
            product_list = self.products.find_list_matched_product_all("Product")
            for product in product_list:
                parsedxml = self.set_list_matched_product(product)
                if parsedxml:
                    # あったので登録
                    self.parsedxml_list.append(parsedxml)

                    # db登録してしまおう
                    self.set_db_product(parsedxml)
        except Exception as e:
            t, v, tb = sys.exc_info()
            self.products.logger.info("AmaMws set_list_matched_product_all except:{0}".format(str(failure(e))))
            #self.products.logger.info('AmaMws set_list_matched_product_all_add_except:{0}'.format(str(traceback.format_tb(e.__traceback__))))
            self.products.logger.info('AmaMws set_list_matched_product_all_add_except:{0}'.format(str(traceback.format_exception(t,v,tb))))

        self.products.logger.info('AmaMws set_list_matched_product_all out')
        return

    # Productで返ってきたリストは全部登録する
    # yahoo shopping用
    def set_shop_list_matched_product_all(self):
        self.products.logger.debug('AmaMws set_shop_list_matched_product_all in')

        try:
            product_list = self.products.find_list_matched_product_all("Product")
            for product in product_list:
                parsedxml = self.set_list_matched_product(product)
                if parsedxml:
                    # あったので登録
                    self.parsedxml_list.append(parsedxml)

                    # db登録してしまおう
                    self.set_shop_db_product(parsedxml)
        except Exception as e:
            t, v, tb = sys.exc_info()
            self.products.logger.info("AmaMws set_shop_list_matched_product_all except:{0}".format(str(failure(e))))
            #self.products.logger.info('AmaMws set_shop_list_matched_product_all:{0}'.format(str(traceback.format_tb(e.__traceback__))))
            self.products.logger.info('AmaMws set_shop_list_matched_product_all:{0}'.format(str(traceback.format_exception(t,v,tb))))

        self.products.logger.debug('AmaMws set_shop_list_matched_product_all out')
        return

    # Productで返ってきたリストは全部登録する
    # yahoo shopping 輸入用
    def set_shop_import_list_matched_product_all(self):
        self.products.logger.debug('AmaMws set_shop_import_list_matched_product_all in')

        try:
            product_list = self.products.find_list_matched_product_all("Product")
            for product in product_list:
                parsedxml = self.set_list_matched_product(product)
                if parsedxml:
                    # あったので登録
                    self.parsedxml_list.append(parsedxml)

                    # db登録してしまおう
                    self.set_shop_import_db_product(parsedxml)
        except Exception as e:
            t, v, tb = sys.exc_info()
            self.products.logger.info("AmaMws set_shop_import_list_matched_product_all except:{0}".format(str(failure(e))))
            #self.products.logger.info('AmaMws set_shop_import_list_matched_product_all:{0}'.format(str(traceback.format_tb(e.__traceback__))))
            self.products.logger.info('AmaMws set_shop_import_list_matched_product_all:{0}'.format(str(traceback.format_exception(t,v,tb))))

        self.products.logger.debug('AmaMws set_shop_import_list_matched_product_all out')
        return

    def set_db_product(self, parsedxml):
        # ASINは重複をチェックする、しかし商品ごとにぶら下がるので・・やっぱforeignkeyはいらんかも
        asin = parsedxml["ASIN"] if parsedxml["ASIN"] else ''
        #self.products.logger.info("AmaMws set_db_product  in asin:{0}".format(str(asin)))

        #self.products.logger.info("AmaMws set_db_product  in 3_Rank:{0}".format(str(parsedxml["3_Rank"])))
        #self.products.logger.info("AmaMws set_db_product  in gid:{0}".format(str(self._gid)))

        if not YaAmaGoodsDetail.objects.filter(asin=parsedxml["ASIN"]).exists():
            self.products.logger.info("AmaMws set_db_product start update_or_create")
            obj, created = YaAmaGoodsDetail.objects.update_or_create(
                asin = parsedxml["ASIN"] if parsedxml["ASIN"] else '',
                title = parsedxml["Title"] if parsedxml["Title"] else '',
                url=parsedxml["URL"] if parsedxml["URL"] else '',
                amount=float(parsedxml["Amount"]) if parsedxml["Amount"] else 0,
                binding=parsedxml["Binding"] if parsedxml["Binding"] else '',
                brand=parsedxml["Brand"] if parsedxml["Brand"] else '',
                color=parsedxml["Color"] if parsedxml["Color"] else '',
                department=parsedxml["Department"] if parsedxml["Department"] else '',
                is_adlt = False if parsedxml["IsAdultProduct"] == "false" else True,
                i_height = float(parsedxml["i_Height"]) if parsedxml["i_Height"] else 0,
                i_length = float(parsedxml["i_Length"]) if parsedxml["i_Length"] else 0,
                i_width = float(parsedxml["i_Width"]) if parsedxml["i_Width"] else 0,
                i_weight = float(parsedxml["i_Weight"]) if parsedxml["i_Weight"] else 0,
                p_height = float(parsedxml["p_Height"]) if parsedxml["p_Height"] else 0,
                p_length = float(parsedxml["p_Length"]) if parsedxml["p_Length"] else 0,
                p_width = float(parsedxml["p_Width"]) if parsedxml["p_Width"] else 0,
                p_weight = float(parsedxml["p_Weight"]) if parsedxml["p_Weight"] else 0,
                rank_cat_1 = parsedxml["1_ProductCategoryId"] if parsedxml["1_ProductCategoryId"] else '',
                rank_1 = int(parsedxml["1_Rank"]) if parsedxml["1_Rank"] else 0,
                rank_cat_2 = parsedxml["2_ProductCategoryId"] if parsedxml["2_ProductCategoryId"] else '',
                rank_2 = int(parsedxml["2_Rank"]) if parsedxml["2_Rank"] else 0,
                rank_cat_3 = parsedxml["3_ProductCategoryId"] if parsedxml["3_ProductCategoryId"] else '',
                rank_3 = int(parsedxml["3_Rank"]) if parsedxml["3_Rank"] else 0,
                bid = self._bid,
                gid = self._gid,
            )
            obj.save()
        self.products.logger.info("AmaMws set_db_product end ")
        return

    def set_shop_db_product(self, parsedxml):
        # yahoo shopping用
        # ASINは重複をチェックする、しかし商品ごとにぶら下がるので・・やっぱforeignkeyはいらんかも
        asin = parsedxml["ASIN"] if parsedxml["ASIN"] else ''
        #self.products.logger.info("AmaMws set_shop_db_product  in asin:{0}".format(str(asin)))

        #self.products.logger.info("AmaMws set_shop_db_product  in 3_Rank:{0}".format(str(parsedxml["3_Rank"])))
        #self.products.logger.info("AmaMws set_shop_db_product  in gid:{0}".format(str(self._gid)))

        if not YaShopAmaGoodsDetail.objects.filter(asin=parsedxml["ASIN"]).exists():
            self.products.logger.debug("AmaMws set_shop_db_product start update_or_create")
            obj, created = YaShopAmaGoodsDetail.objects.update_or_create(
                asin = parsedxml["ASIN"] if parsedxml["ASIN"] else '',
                title = parsedxml["Title"] if parsedxml["Title"] else '',
                url=parsedxml["URL"] if parsedxml["URL"] else '',
                amount=float(parsedxml["Amount"]) if parsedxml["Amount"] else 0,
                binding=parsedxml["Binding"] if parsedxml["Binding"] else '',
                brand=parsedxml["Brand"] if parsedxml["Brand"] else '',
                color=parsedxml["Color"] if parsedxml["Color"] else '',
                department=parsedxml["Department"] if parsedxml["Department"] else '',
                is_adlt = False if parsedxml["IsAdultProduct"] == "false" else True,
                i_height = float(parsedxml["i_Height"]) if parsedxml["i_Height"] else 0,
                i_length = float(parsedxml["i_Length"]) if parsedxml["i_Length"] else 0,
                i_width = float(parsedxml["i_Width"]) if parsedxml["i_Width"] else 0,
                i_weight = float(parsedxml["i_Weight"]) if parsedxml["i_Weight"] else 0,
                p_height = float(parsedxml["p_Height"]) if parsedxml["p_Height"] else 0,
                p_length = float(parsedxml["p_Length"]) if parsedxml["p_Length"] else 0,
                p_width = float(parsedxml["p_Width"]) if parsedxml["p_Width"] else 0,
                p_weight = float(parsedxml["p_Weight"]) if parsedxml["p_Weight"] else 0,
                rank_cat_1 = parsedxml["1_ProductCategoryId"] if parsedxml["1_ProductCategoryId"] else '',
                rank_1 = int(parsedxml["1_Rank"]) if parsedxml["1_Rank"] else 0,
                rank_cat_2 = parsedxml["2_ProductCategoryId"] if parsedxml["2_ProductCategoryId"] else '',
                rank_2 = int(parsedxml["2_Rank"]) if parsedxml["2_Rank"] else 0,
                rank_cat_3 = parsedxml["3_ProductCategoryId"] if parsedxml["3_ProductCategoryId"] else '',
                rank_3 = int(parsedxml["3_Rank"]) if parsedxml["3_Rank"] else 0,
                shopid = self._bid,
                gid = self._gid,
            )
            obj.save()
        self.products.logger.debug("AmaMws set_shop_db_product end ")
        return

    def set_shop_import_db_product(self, parsedxml):
        # yahoo shopping 輸入用
        # ASINは重複をチェックする、しかし商品ごとにぶら下がるので・・やっぱforeignkeyはいらんかも
        asin = parsedxml["ASIN"] if parsedxml["ASIN"] else ''
        #self.products.logger.info("AmaMws set_shop_import_db_product  in asin:{0}".format(str(asin)))

        #self.products.logger.info("AmaMws set_shop_import_db_product  in 3_Rank:{0}".format(str(parsedxml["3_Rank"])))
        #self.products.logger.info("AmaMws set_shop_import_db_product  in gid:{0}".format(str(self._gid)))

        if not YaShopImportAmaGoodsDetail.objects.filter(asin=parsedxml["ASIN"]).exists():
            self.products.logger.debug("AmaMws set_shop_import_db_product start update_or_create")
            obj, created = YaShopImportAmaGoodsDetail.objects.update_or_create(
                asin = parsedxml["ASIN"] if parsedxml["ASIN"] else '',
                title = parsedxml["Title"] if parsedxml["Title"] else '',
                url=parsedxml["URL"] if parsedxml["URL"] else '',
                amount=float(parsedxml["Amount"]) if parsedxml["Amount"] else 0,
                binding=parsedxml["Binding"] if parsedxml["Binding"] else '',
                brand=parsedxml["Brand"] if parsedxml["Brand"] else '',
                color=parsedxml["Color"] if parsedxml["Color"] else '',
                department=parsedxml["Department"] if parsedxml["Department"] else '',
                is_adlt = False if parsedxml["IsAdultProduct"] == "false" else True,
                i_height = float(parsedxml["i_Height"]) if parsedxml["i_Height"] else 0,
                i_length = float(parsedxml["i_Length"]) if parsedxml["i_Length"] else 0,
                i_width = float(parsedxml["i_Width"]) if parsedxml["i_Width"] else 0,
                i_weight = float(parsedxml["i_Weight"]) if parsedxml["i_Weight"] else 0,
                p_height = float(parsedxml["p_Height"]) if parsedxml["p_Height"] else 0,
                p_length = float(parsedxml["p_Length"]) if parsedxml["p_Length"] else 0,
                p_width = float(parsedxml["p_Width"]) if parsedxml["p_Width"] else 0,
                p_weight = float(parsedxml["p_Weight"]) if parsedxml["p_Weight"] else 0,
                rank_cat_1 = parsedxml["1_ProductCategoryId"] if parsedxml["1_ProductCategoryId"] else '',
                rank_1 = int(parsedxml["1_Rank"]) if parsedxml["1_Rank"] else 0,
                rank_cat_2 = parsedxml["2_ProductCategoryId"] if parsedxml["2_ProductCategoryId"] else '',
                rank_2 = int(parsedxml["2_Rank"]) if parsedxml["2_Rank"] else 0,
                rank_cat_3 = parsedxml["3_ProductCategoryId"] if parsedxml["3_ProductCategoryId"] else '',
                rank_3 = int(parsedxml["3_Rank"]) if parsedxml["3_Rank"] else 0,
                shopid = self._bid,
                gid = self._gid,
                csv_no=self._db_entry.csv_no,
                y_cat_1=self._db_entry.y_cat_1,
                y_cat_2=self._db_entry.y_cat_2,
                myshop_cat_1=self._db_entry.myshop_cat_1,
                myshop_cat_2=self._db_entry.myshop_cat_2,
            )
            obj.save()
        self.products.logger.debug("AmaMws set_shop_import_db_product end ")
        return


class AmaSPApiAsinDetail(object):

    # Yahoo 輸入版、csvでカテゴリなど渡すバージョンは、csvのレコードを db_entryに格納して渡す
    # 本版では、USのAmazon SP-API を叩いてアメリカのasinを集めてくる。
    def __init__(self, logger, db_entry=None):
        self.logger = logger

        # 商品単位となるが一時保持用に変数を用意する
        self.parsedxml_list = []
        self._db_entry = db_entry

        self.logger.info('AmaSPApiAsinDetail  in. init keyword:[{}]'.format(self._query))
        self.upd_csv = []
        self.target_url = "https://api.amazon.com/auth/o2/token"
        self.us_refresh_token = os.getenv('US_LWA_REFRESH_TOKEN', '')
        self.us_client_id = os.getenv('US_LWA_CLIENT_ID', '')
        self.us_client_secret = os.getenv('US_LWA_CLIENT_SECRET', '')
        self.us_aws_access_key = os.getenv('US_AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID', ''))
        self.us_aws_secret_access_key = os.getenv('US_AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY', ''))
        self.req_headers = None
        self.us_get_url = "https://sellingpartnerapi-na.amazon.com"  # 北米
        self.jp_get_url = "https://sellingpartnerapi-fe.amazon.com" # 日本
        self.access_token = None
        self.us_marketplace = "ATVPDKIKX0DER"  # 北米 ATVPDKIKX0DER  カナダ　A2EUQ1WTGCTBG2 日本 A1VC38T7YXB528
        self.jp_marketplace = "A1VC38T7YXB528"  # 北米 ATVPDKIKX0DER  カナダ　A2EUQ1WTGCTBG2 日本 A1VC38T7YXB528
        self.us_host = "sellingpartnerapi-na.amazon.com"  # 北米
        self.jp_host = "sellingpartnerapi-fe.amazon.com"  # 日本
        self.us_region = "us-east-1"  # 北米
        #self.region = "us-west-2"  # 日本
        self.service = "execute-api"

        self.us_credentials = dict(
            refresh_token=self.us_refresh_token,
            lwa_app_id=self.us_client_id,
            lwa_client_secret=self.us_client_secret,
            aws_secret_key=self.us_aws_secret_access_key,
            aws_access_key=self.us_aws_access_key,
            #role_arn='arn:aws:iam::000222965326:user/AWS_IAM_SPAPI_Access_User'
        )

    def spapi_get_participantion(self):

        # USから取得する
        #response = Sellers(marketplace=Marketplaces.JP, credentials=self.credentials).get_marketplace_participation()
        response = Sellers(
            marketplace=Marketplaces.US, credentials=self.us_credentials
        ).get_marketplace_participation()
        self.logger.info('spapi_get_participantion [{}]'.format(response))
        #print(response)
        return

    def spapi_get_catalog_item(self, asin):

        #asin = 'B07WXL5YPW'
        response = Catalog(marketplace=Marketplaces.US, credentials=self.us_credentials).get_item(asin)
        self.logger.info('spapi_get_catalog_item [{}]'.format(response))
        #print(response)

        res = json.loads(self.response)
        self.logger.info('spapi_get_catalog_item result_asin [{}]'.format(res["asin"]))
        """
        parsedxml = self.set_asin_data(res)
        if parsedxml:
            # db登録してしまおう
            self.set_db_product(parsedxml)
        """

        return

    def set_asin_data(self, asin_response):

        parsedxml = {}

        key_normal_list = ["ASIN", "MarketplaceId"]
        for key_normal in key_normal_list:
            # 以下は productを引数にとらず一つだけ取ってきていた名残
            #findobj = self.find_list_matched_product(key_normal)
            findobj = self.products.find_list_matched_product_by_obj(asin_response, key_normal)
            if findobj is None:
                return None  # とれなかったらNG
            else:
                parsedxml[key_normal] = findobj.text

        # 初期値はstrのものを対象
        key_default_str_list = [
            "Title",
            "URL",
            "Amount",
            "Binding",
            "Brand",
            "Color",
            "Department",
            "IsAdultProduct",
        ]
        for key_default in key_default_str_list:
            #findobj = self.find_list_matched_product_default(key_default)
            findobj = self.products.find_list_matched_product_default_by_obj(product, key_default)
            if findobj is None:
                parsedxml[key_default] = ''
            else:
                parsedxml[key_default] = findobj.text

        # dimentionに関する値
        key_dimention_str_list = [
            "Height",
            "Length",
            "Width",
            "Weight",
        ]
        # itemdimentionに関する値
        for key_default in key_dimention_str_list:
            #findobj = self.find_list_matched_product_itemdimention(key_default)
            findobj = self.products.find_list_matched_product_itemdimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["i_" + key_default] = ''
            else:
                parsedxml["i_" + key_default] = findobj.text

        # packagedimentionに関する値
        for key_default in key_dimention_str_list: # リストはitemもpackageも同じ
            #findobj = self.find_list_matched_product_packagedimention(key_default)
            findobj = self.products.find_list_matched_product_packagedimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["p_" + key_default] = ''
            else:
                parsedxml["p_" + key_default] = findobj.text

        # SalesRankに関わるもの
        key_salesrank_list = ["ProductCategoryId", "Rank"]
        i = 0
        #findobj_list = self.find_list_matched_product_all("SalesRank")
        findobj_list = self.products.find_list_matched_product_all_by_obj(product, "SalesRank")
        #self.products.logger.info("AmaMws SalesRank findobj_list text:{0}".format(str(findobj_list)))
        if findobj_list:
            for findobj in findobj_list: # SalesRankは3つ
                i += 1
                #self.products.logger.info("AmaMws SalesRank findobj text:{0}".format(str(findobj)))

                for key_normal in key_salesrank_list:
                    finditem = findobj.find(".//2011-10-01:%s" % key_normal, self.products._products_namespace)

                    if finditem is None:
                        parsedxml[str(i) +  "_" + key_normal] = ''
                    else:
                        parsedxml[str(i) +  "_" + key_normal] = finditem.text
        if i < 3:
            parsedxml['3_Rank'] = 0
            parsedxml['3_ProductCategoryId'] = ''
        if i < 2:
            parsedxml['2_Rank'] = 0
            parsedxml['2_ProductCategoryId'] = ''
        if i < 1:
            parsedxml['1_Rank'] = 0
            parsedxml['1_ProductCategoryId'] = ''

        return parsedxml

    def set_db_product(self, parsedxml):
        # ASINは重複をチェックする、しかし商品ごとにぶら下がるので・・やっぱforeignkeyはいらんかも
        asin = parsedxml["ASIN"] if parsedxml["ASIN"] else ''

        if not AsinDetail.objects.filter(asin=parsedxml["ASIN"]).exists():
            self.logger.info("AmaSPApiAsinDetail set_db_product start update_or_create")
            obj, created = AsinDetail.objects.update_or_create(
                asin=parsedxml["ASIN"] if parsedxml["ASIN"] else '',
                title=parsedxml["Title"] if parsedxml["Title"] else '',
                url=parsedxml["URL"] if parsedxml["URL"] else '',
                amount=float(parsedxml["Amount"]) if parsedxml["Amount"] else 0,
                binding=parsedxml["Binding"] if parsedxml["Binding"] else '',
                brand=parsedxml["Brand"] if parsedxml["Brand"] else '',
                color=parsedxml["Color"] if parsedxml["Color"] else '',
                department=parsedxml["Department"] if parsedxml["Department"] else '',
                is_adlt=False if parsedxml["IsAdultProduct"] == "false" else True,
                i_height=float(parsedxml["i_Height"]) if parsedxml["i_Height"] else 0,
                i_length=float(parsedxml["i_Length"]) if parsedxml["i_Length"] else 0,
                i_width=float(parsedxml["i_Width"]) if parsedxml["i_Width"] else 0,
                i_weight=float(parsedxml["i_Weight"]) if parsedxml["i_Weight"] else 0,
                p_height=float(parsedxml["p_Height"]) if parsedxml["p_Height"] else 0,
                p_length=float(parsedxml["p_Length"]) if parsedxml["p_Length"] else 0,
                p_width=float(parsedxml["p_Width"]) if parsedxml["p_Width"] else 0,
                p_weight=float(parsedxml["p_Weight"]) if parsedxml["p_Weight"] else 0,
                rank_cat_1=parsedxml["1_ProductCategoryId"] if parsedxml["1_ProductCategoryId"] else '',
                rank_1=int(parsedxml["1_Rank"]) if parsedxml["1_Rank"] else 0,
                rank_cat_2=parsedxml["2_ProductCategoryId"] if parsedxml["2_ProductCategoryId"] else '',
                rank_2=int(parsedxml["2_Rank"]) if parsedxml["2_Rank"] else 0,
                rank_cat_3=parsedxml["3_ProductCategoryId"] if parsedxml["3_ProductCategoryId"] else '',
                rank_3=int(parsedxml["3_Rank"]) if parsedxml["3_Rank"] else 0,
                bid=self._bid,
                gid=self._gid,
            )
            obj.save()
        self.logger.info("AmaSPApiAsinDetail set_db_product end ")
        return


class AmaSPApiQooAsinDetail(object):

    # Qoo10用（直送あり、メルカリshopsでも使える予定）
    # csvでカテゴリなど渡すバージョンは、
    # csvのレコードを QooAsinDetail テーブル db_entryに格納して渡す
    # 本版では、日本のAmazon SP-API を叩いてAsin詳細を取り、
    # ブラックリストのチェックや子Asinのチェックなど行う
    def __init__(self, logger, db_entry=None):
        self.logger = logger

        # 商品単位となるが一時保持用に変数を用意する
        self.parsedxml_list = []
        self._db_entry = db_entry
        self._common_chrome_driver = None

        self.logger.info('AmaSPApiAsinDetail  in. init')

        # SP-APIの登録情報等
        self.upd_csv = []
        self.target_url = "https://api.amazon.com/auth/o2/token"
        self.api_key = "56f37bab855914fd56d8f1b49215e5899d77dec93b81831052a762864a8049ed"
        self.grant_type = "refresh_token"

        self.us_refresh_token = os.getenv('US_LWA_REFRESH_TOKEN', '')
        self.us_client_id = os.getenv('US_LWA_CLIENT_ID', '')
        self.us_client_secret = os.getenv('US_LWA_CLIENT_SECRET', '')
        self.us_aws_access_key = os.getenv('US_AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY_ID', ''))
        self.us_aws_secret_access_key = os.getenv('US_AWS_SECRET_ACCESS_KEY', os.getenv('AWS_SECRET_ACCESS_KEY', ''))

        # 以下修正まだ！ JPの値を ######
        # ユーザID SPAPI-Qoo-2
        self.jp_refresh_token = os.getenv('JP_LWA_REFRESH_TOKEN', '')
        self.jp_client_id = os.getenv('JP_LWA_CLIENT_ID', '')
        self.jp_client_secret = os.getenv('JP_LWA_CLIENT_SECRET', '')
        self.jp_aws_access_key = os.getenv('JP_AWS_ACCESS_KEY_ID', '')
        self.jp_aws_secret_access_key = os.getenv('JP_AWS_SECRET_ACCESS_KEY', '')
        # 以上修正まだ！ ######
        self.req_headers = None
        self.us_get_url = "https://sellingpartnerapi-na.amazon.com"  # 北米
        self.jp_get_url = "https://sellingpartnerapi-fe.amazon.com" # 日本
        self.access_token = None
        self.us_marketplace = "ATVPDKIKX0DER"  # 北米 ATVPDKIKX0DER  カナダ　A2EUQ1WTGCTBG2 日本 A1VC38T7YXB528
        self.jp_marketplace = "A1VC38T7YXB528"  # 日本 A1VC38T7YXB528
        self.us_host = "sellingpartnerapi-na.amazon.com"  # 北米
        self.jp_host = "sellingpartnerapi-fe.amazon.com"  # 日本
        self.us_region = "us-east-1"  # 北米
        self.jp_region = "us-west-2"  # 日本
        self.service = "execute-api"

        self.jp_credentials = dict(
            refresh_token=self.jp_refresh_token,
            lwa_app_id=self.jp_client_id,
            lwa_client_secret=self.jp_client_secret,
            aws_secret_key=self.jp_aws_secret_access_key,
            aws_access_key=self.jp_aws_access_key,
            #role_arn='arn:aws:iam::000222965326:user/AWS_IAM_SPAPI_Access_User'
        )

        self.us_credentials = dict(
            refresh_token=self.us_refresh_token,
            lwa_app_id=self.us_client_id,
            lwa_client_secret=self.us_client_secret,
            aws_secret_key=self.us_aws_secret_access_key,
            aws_access_key=self.us_aws_access_key,
            #role_arn='arn:aws:iam::000222965326:user/AWS_IAM_SPAPI_Access_User'
        )

        # 保存するパラメータ関連。asin単位で覚えておくイメージ
        self._my_res = None
        self._my_res_seller = None

        self._is_seller_ok = False # 出品対象としてOKとなる出品者が存在するか。FBAかつ中国セラーなど
        self._is_black_list_ok = True # ブラックリストチェック。デフォルトはOK扱いにしておこう

        self._is_blacklist_ok_asin = True # ASINの判定結果 False:NG判定 True:OK
        self._is_blacklist_ok_img = True # 画像による判定結果 False:NG判定 True:OK
        self._is_blacklist_ok_keyword = True # キーワードによる判定結果 False:NG判定 True:OK
        self._blacklist_keyword_flg = 10000000000 # どこでブラックリストに引っかかったかフラグ立てる
        # デフォルト：0000000000　例えばタイトルとブランドがNGなら 00101 とする。
        # 末尾桁→タイトルの判定結果、NGなら１
        # 10の桁→商品説明の判定結果、NGなら１
        # 100の桁→ブランドの判定結果、NGなら１

        self._buybox_listing_price = 0 # カート価格
        self._buybox_condition = '' # カート出品状態
        self._buybox_shipping_price = 0 # カート送料
        self._shipfrom_country = '' # 出品者の所在国
        self._num_offers_amazon = 0 # NumberOfOffersのamazon出品者数
        self._num_offers_merchant = 0 # NumberOfOffersのMerchant出品者数
        self._sales_rank_1 = 0 # ランキングカテゴリ1のランク
        self._sales_rank_2 = 0 # ランキングカテゴリ2のランク
        self._sales_rank_3 = 0 # ランキングカテゴリ2のランク
        self._sales_rank_cat_1 = '' # ランキングカテゴリ1の名称
        self._sales_rank_cat_2 = '' # ランキングカテゴリ2の名称
        self._sales_rank_cat_3 = '' # ランキングカテゴリ3の名称
        self._ok_seller_feedback_rate = 0 # OKと判断されたセラーのfeedback rate
        self._ok_seller_id = '' # OKと判断されたセラーのid

        # 以下はDBにセットされるパラメータ
        self._asin = ''
        self._binding = ''
        self._color = ''
        self._is_adlt = ''
        self._brand = ''
        self._label = ''
        self._list_price_amount = 0
        self._list_price_code = ''
        self._manufacturer = ''
        self._package_quantity = 0
        self._part_number = 0
        self._platform = ''
        self._product_group = ''
        self._product_type_name = ''
        self._release_date = ''
        self._publisher = ''
        self._size = ''
        self._small_image = ''
        self._studio = ''
        self._title = ''
        self._i_height = 0
        self._i_length = 0
        self._i_width = 0
        self._i_weight = 0
        self._p_height = 0
        self._p_length = 0
        self._p_width = 0
        self._p_weight = 0
        self._i_height_unit = ''
        self._i_length_unit = ''
        self._i_width_unit = ''
        self._i_weight_unit = ''
        self._p_height_unit = ''
        self._p_length_unit = ''
        self._p_width_unit = ''
        self._p_weight_unit = ''
        self._rank_1 = 0
        self._rank_2 = 0
        self._rank_3 = 0
        self._rank_cat_1 = ''
        self._rank_cat_2 = ''
        self._rank_cat_3 = ''

    def spapi_get_participantion(self, region):

        # USから取得する
        #response = Sellers(marketplace=Marketplaces.JP, credentials=self.credentials).get_marketplace_participation()
        if region == 'us':
            response = Sellers(
                marketplace=Marketplaces.US, credentials=self.us_credentials
            ).get_marketplace_participation()
        else :
            # jpでセット
            response = Sellers(
                marketplace=Marketplaces.JP, credentials=self.jp_credentials
            ).get_marketplace_participation()

        self.logger.info('spapi_get_participantion [{}]'.format(response))
        #print(response)
        return

    def spapi_get_catalog_item(self, region, asin):
        """指定されたasinの情報をSP-API経由（JP）で取得する。
            キーワードはブラックリストと突き合わせてNG判定も行う。
            結果は QooAsinDetail に格納

        Args:
            region (_type_): 'jp' を指定する。
            asin (_type_): asin コード

        Return:
            True
            False (エラー発生時)
        """

        # asin = 'B07WXL5YPW'

        # torでAmazonページをスクレイピングして詳細情報を取ってみよう
        self.get_ama_src_with_tor()

        # Catalog から商品の概要を取得
        self._my_res = self.get_catalog_get_item(asin, region)
        # self.logger.info('---> spapi_get_catalog_item response [{}] type[{}]'.format(my_res,type(my_res)))
        # Identifiers　が以下で取れる　{'MarketplaceASIN': {'MarketplaceId': 'A1VC38T7YXB528', 'ASIN': 'B07WXL5YPW'}}
        #self.logger.info('---> response Identifiers [{}]'.format(my_res['Identifiers']))
        self.logger.info('---> response AttributeSets [{}]'.format(self._my_res['AttributeSets']))

        # Products から商品（新品）の出品者情報を取得
        self._my_res_seller = self.get_products_get_item_offers(asin, region)
        self.logger.info('--->> get_products_get_item_offers response [{}] type[{}]'.format(
            self._my_res_seller,type(self._my_res_seller)))

        # CatalogItems から商品の画像情報を取得 →あまり大した情報が取れないからスルー
        # my_res_catalog_item = self.get_catalogitems_get_catalog_item(asin, region)
        # self.logger.info('--->>> get_catalogitems_get_catalog_item response [{}] type[{}]'.format(
        #    my_res_catalog_item,type(my_res_catalog_item)))

        # APIの呼び出し結果をインスタンス変数にセットするだけ。DB登録はまだ
        self.set_params_from_api_result()

        # 出品者の状況から取り扱いの判定
        self._is_seller_ok = self.chk_seller_ok()

        # ブラックリスト判定
        self._is_black_list_ok = self.chk_black_list()

        # DB登録
        self.set_db_product()
        self.logger.info('AmaSPApiQooAsinDetail spapi_get_catalog_item db_set is done.')

        #self.logger.info('spapi_get_catalog_item result_asin [{}]'.format(res["asin"]))
        """
        parsedxml = self.set_asin_data(res)
        if parsedxml:
            # db登録してしまおう
            self.set_db_product(parsedxml)
        """

        return

    def chk_seller_ok(self):
        # 出品者の状況から出品OKかどうかの判定を行う
        self.logger.info('-> chk_seller_ok in.')

        summary = self._my_res_seller.get('Summary', None)
        if summary:
            # まずカート関連情報の保存
            if summary.get('BuyBoxPrices', None):
                self._buybox_listing_price = \
                    summary.get('BuyBoxPrices', None)['ListingPrice']['Amount']
                self._buybox_condition = \
                    summary.get('BuyBoxPrices', None)['condition']
                self._buybox_shipping_price = \
                    summary.get('BuyBoxPrices', None)['Shipping']['Amount']

            # 出品者状況の保存
            for offer in summary.get('BuyBoxEligibleOffers', None):
                if offer.get('fulfillmentChannel', None) == 'Amazon':
                    self._num_offers_amazon = offer.get('OfferCount', 0)
                elif offer.get('fulfillmentChannel', None) == 'Merchant':
                    self._num_offers_merchant = offer.get('OfferCount', 0)

            # 以下でOKかどうかの判定
            for offer in summary.get('Offers', None):
                # SubConditionがnewのみ
                if offer.get('SubCondition', None) == 'new':
                    # CNのcountryのみOKとする
                    if offer.get('ShipsFrom', None)['Country'] == 'CN':
                        # セラーのレートは90% 以上にしておきますか
                        if offer.get('SellerFeedbackRating', None)\
                            ['SellerPositiveFeedbackRating'] >= 90:

                            # FBAのみ
                            # うーんIsFulfilledByAmazonでみるか、isPrimeでみるか。primeにしとくか
                            #if offer.get('IsFulfilledByAmazon', None) == 'True':
                            if offer.get('PrimeInformation', None)['IsPrime'] == 'True':
                                # ここまで条件が揃ってたら出品OKとしよう。
                                # １セラーでも該当したらOK扱いに
                                self._ok_seller_feedback_rate = \
                                    offer.get('SellerFeedbackRating', None)\
                                        ['SellerPositiveFeedbackRating']
                                self._ok_seller_id = offer.get('SellerId', None)
                                self.logger.info('-> chk_seller_ok  this item OK to sell.')
                                return True

        self.logger.info('-> chk_seller_ok  this item NG to sell.')
        return False

    def chk_black_list(self):
        # ブラックリストに含まれるキーワードと
        # 商品タイトル、概要、ブランド、メーカー等との突き合わせ判定を行う
        # 続いてブラックリストASINとのマッチ
        # ret: True (問題なし) False:NG
        self.logger.info('-> chk_black_list in.')

        # 判定結果はそれぞれDBの以下項目にセットする
        # is_blacklist_ok_asin is_blacklist_ok_img is_blacklist_ok_keyword
        # blacklist_keyword_flg (形式は 0000000000 のビット形式)

        # asinとの突き合わせ
        if self._asin == '':
            # asinが未設定はおかしい。処理しない
            self.logger.info('-> chk_black_list asin is blank . something wrong...')
            return

        # asinのチェック
        if AsinBlacklistAsin.objects.filter(asin=self._asin).exists():
            # blacklist のasinに該当
            self.logger.info('-> ### chk_black_list asin blacklisted. ng [{}]'.format(self._asin))
            self._is_blacklist_ok_asin = False

        # ブランドのチェック
        if AsinBlacklistBrand.objects.filter(brand=self._brand).exists():
            # Brand でNG
            self.logger.info('-> ### chk_black_list brand blacklisted. ng [Brand] [{}]'.format(self._brand))
            self._is_blacklist_ok_keyword = False
            self._blacklist_keyword_flg += 100 # BrandでNG : 100の位をON

        if AsinBlacklistBrand.objects.filter(brand=self._publisher).exists():
            # Publisher でNG
            self.logger.info('-> ### chk_black_list brand blacklisted. ng [Publisher] [{}]'.format(self._publisher))
            self._is_blacklist_ok_keyword = False
            self._blacklist_keyword_flg += 1000 # Publisher : 1000の位をON

        if AsinBlacklistBrand.objects.filter(brand=self._manufacturer).exists():
            # Manufacturer でNG
            self.logger.info('-> ### chk_black_list brand blacklisted. ng [Manufacturer] [{}]'.format(self._manufacturer))
            self._is_blacklist_ok_keyword = False
            self._blacklist_keyword_flg += 10000 # Manufacturer : 10000の位をON

        if AsinBlacklistBrand.objects.filter(brand=self._label).exists():
            # Label でNG
            self.logger.info('-> ### chk_black_list brand blacklisted. ng [Label] [{}]'.format(self._label))
            self._is_blacklist_ok_keyword = False
            self._blacklist_keyword_flg += 100000 # Label : 100000の位をON

        if AsinBlacklistBrand.objects.filter(brand=self._title).exists():
            # Title でNG
            self.logger.info('-> ### chk_black_list brand blacklisted. ng [Title] [{}]'.format(self._title))
            self._is_blacklist_ok_keyword = False
            self._blacklist_keyword_flg += 1000000 # Title : 1000000の位をON

        # キーワードのチェック
        for tmpkeyword in AsinBlacklistKeyword.objects.all():
            if tmpkeyword.keyword in self._title:
                # Title でNG
                self.logger.info(
                    '-> ### chk_black_list keyword blacklisted. ng [Title] [{}]'.format(tmpkeyword.keyword))
                self._is_blacklist_ok_keyword = False
                self._blacklist_keyword_flg += 10000000 # Title keyword : 10000000の位をON
                break

        ### →　さらにここで、商品詳細などもチェックしたい・・・・・・・
        #    self._brand = attribute.get('Brand', '')
        #    self._title = attribute.get('Title', '')
        #   AsinBlacklistKeyword,
        #   AsinBlacklistBrand,

        return

    def get_catalog_get_item(self, asin, region):
        # Catalog から商品の概要を取得
        # asin = 'B07WXL5YPW'

        # 2022/08/01
        # conoha-01 の、/usr/lib/python3.6/site-packages/sp_api/api/catalog/catalog.py
        # のget_itemを直接変えて、v0 から2022-04-01　に変えた。
        # marketplace は marketplaceIds に変わってる。
        # includedData で取得対象のカテゴリを選べる。
        # https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-use-case-guide
        includedData = 'attributes,dimensions,identifiers,images,productTypes,salesRanks,summaries,relationships,vendorDetails'
        if region == 'us':
            response = Catalog(
                MarketplaceId=Marketplaces.US,
                credentials=self.us_credentials,
                ).get_item(asin)
        else:
            """
            response = Catalog(
                MarketplaceId=Marketplaces.JP,
                credentials=self.jp_credentials,
                includedData=includedData,).get_item(asin)
            """
            response = Catalog(
                marketplace=Marketplaces.JP,
                credentials=self.jp_credentials,
                ).get_item(asin)
        return response()

    def get_catalogitems_get_catalog_item(self, asin, region):
        # CatalogItems から商品の画像情報を取得
        # asin = 'B07WXL5YPW'
        if region == 'us':
            response = CatalogItems(
                marketplace=Marketplaces.US, credentials=self.us_credentials
                ).get_catalog_item(asin)
        else:
            response = CatalogItems(
                marketplace=Marketplaces.JP, credentials=self.jp_credentials
                ).get_catalog_item(asin)
        return response()

    def get_products_get_item_offers(self, asin, region):
        # Products から商品（新品）の出品者情報を取得
        if region == 'us':
            response = Products(
                marketplace=Marketplaces.US, credentials=self.us_credentials
                ).get_item_offers(asin=asin, item_condition='New')
        else:
            response = Products(
                marketplace=Marketplaces.JP, credentials=self.jp_credentials
                ).get_item_offers(asin=asin, item_condition='New')
        return response()

    def set_asin_data(self, asin_response):

        parsedxml = {}

        key_normal_list = ["ASIN", "MarketplaceId"]
        for key_normal in key_normal_list:
            # 以下は productを引数にとらず一つだけ取ってきていた名残
            #findobj = self.find_list_matched_product(key_normal)
            findobj = self.products.find_list_matched_product_by_obj(asin_response, key_normal)
            if findobj is None:
                return None  # とれなかったらNG
            else:
                parsedxml[key_normal] = findobj.text

        # 初期値はstrのものを対象
        key_default_str_list = [
            "Title",
            "URL",
            "Amount",
            "Binding",
            "Brand",
            "Color",
            "Department",
            "IsAdultProduct",
        ]
        for key_default in key_default_str_list:
            #findobj = self.find_list_matched_product_default(key_default)
            findobj = self.products.find_list_matched_product_default_by_obj(product, key_default)
            if findobj is None:
                parsedxml[key_default] = ''
            else:
                parsedxml[key_default] = findobj.text

        # dimentionに関する値
        key_dimention_str_list = [
            "Height",
            "Length",
            "Width",
            "Weight",
        ]
        # itemdimentionに関する値
        for key_default in key_dimention_str_list:
            #findobj = self.find_list_matched_product_itemdimention(key_default)
            findobj = self.products.find_list_matched_product_itemdimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["i_" + key_default] = ''
            else:
                parsedxml["i_" + key_default] = findobj.text

        # packagedimentionに関する値
        for key_default in key_dimention_str_list: # リストはitemもpackageも同じ
            #findobj = self.find_list_matched_product_packagedimention(key_default)
            findobj = self.products.find_list_matched_product_packagedimention_by_obj(product, key_default)
            if findobj is None:
                parsedxml["p_" + key_default] = ''
            else:
                parsedxml["p_" + key_default] = findobj.text

        # SalesRankに関わるもの
        key_salesrank_list = ["ProductCategoryId", "Rank"]
        i = 0
        #findobj_list = self.find_list_matched_product_all("SalesRank")
        findobj_list = self.products.find_list_matched_product_all_by_obj(product, "SalesRank")
        #self.products.logger.info("AmaMws SalesRank findobj_list text:{0}".format(str(findobj_list)))
        if findobj_list:
            for findobj in findobj_list: # SalesRankは3つ
                i += 1
                #self.products.logger.info("AmaMws SalesRank findobj text:{0}".format(str(findobj)))

                for key_normal in key_salesrank_list:
                    finditem = findobj.find(".//2011-10-01:%s" % key_normal, self.products._products_namespace)

                    if finditem is None:
                        parsedxml[str(i) +  "_" + key_normal] = ''
                    else:
                        parsedxml[str(i) +  "_" + key_normal] = finditem.text
        if i < 3:
            parsedxml['3_Rank'] = 0
            parsedxml['3_ProductCategoryId'] = ''
        if i < 2:
            parsedxml['2_Rank'] = 0
            parsedxml['2_ProductCategoryId'] = ''
        if i < 1:
            parsedxml['1_Rank'] = 0
            parsedxml['1_ProductCategoryId'] = ''

        return parsedxml


    def set_params_from_api_result(self):
        self.logger.info('-> set_params_from_api_result in.')

        # ASIN
        self._asin = self._my_res["Identifiers"]["MarketplaceASIN"]["ASIN"]
        self.logger.info('---> asin [{}]'.format(self._asin))

        # AttributeSets
        for attribute in self._my_res['AttributeSets']:
            self._binding = attribute.get('Binding', '')
            self._color = attribute.get('Color', '')
            self._is_adlt = attribute.get('IsAdultProduct', '')
            self._brand = attribute.get('Brand', '')
            self._label = attribute.get('Label', '')
            if attribute.get('ListPrice', None):
                self._list_price_amount = attribute.get('ListPrice', 0).get('Amount', 0)
                self._list_price_code = attribute.get('ListPrice', '').get('CurrencyCode', '')
            self._manufacturer = attribute.get('Manufacturer', '')
            self._package_quantity = attribute.get('PackageQuantity', 0)
            self._part_number = attribute.get('PartNumber', 0)
            self._platform = attribute.get('Platform', '')
            self._product_group = attribute.get('ProductGroup', '')
            self._product_type_name = attribute.get('ProductTypeName', '')
            self._release_date = attribute.get('ReleaseDate', '')
            self._publisher = attribute.get('Publisher', '')
            self._size = attribute.get('Size', '')
            if attribute.get('SmallImage', None):
                self._small_image_url = attribute.get('SmallImage', '')['URL']
            self._studio = attribute.get('Studio', '')
            self._title = attribute.get('Title', '')

            if attribute.get('ItemDimensions', None):
                self._i_height = float(attribute['ItemDimensions'].get('Height', 0)['value'])
                self._i_length = float(attribute['ItemDimensions'].get("Length", 0)['value'])
                self._i_width = float(attribute['ItemDimensions'].get("Width", 0)['value'])
                self._i_weight = float(attribute['ItemDimensions'].get("Weight", 0)['value'])
                self._i_height_unit = attribute['ItemDimensions'].get('Height', '')['Units']
                self._i_length_unit = attribute['ItemDimensions'].get('Length', '')['Units']
                self._i_width_unit = attribute['ItemDimensions'].get('Width', '')['Units']
                self._i_weight_unit = attribute['ItemDimensions'].get('Weight', '')['Units']
            if attribute.get('PackageDimensions', None):
                self._p_height = float(attribute['PackageDimensions'].get("Height", 0)['value'])
                self._p_length = float(attribute['PackageDimensions'].get("Length", 0)['value'])
                self._p_width = float(attribute['PackageDimensions'].get("Width", 0)['value'])
                self._p_weight = float(attribute['PackageDimensions'].get("Weight", 0)['value'])
                self._p_height_unit = attribute['PackageDimensions'].get('Height', '')['Units']
                self._p_length_unit = attribute['PackageDimensions'].get('Length', '')['Units']
                self._p_width_unit = attribute['PackageDimensions'].get('Width', '')['Units']
                self._p_weight_unit = attribute['PackageDimensions'].get('Weight', '')['Units']
            self.logger.info('---> attribute Binding [{}]'.format(self._binding))

        # ランキング関連は３つまで
        for i, rank in enumerate(self._my_res['SalesRankings']):
            if i == 0:
                self._rank_1 = rank['Rank']
                self._rank_cat_1 = rank['ProductCategoryId']
            elif i == 1:
                self._rank_2 = rank['Rank']
                self._rank_cat_2 = rank['ProductCategoryId']
            elif i == 2:
                self._rank_3 = rank['Rank']
                self._rank_cat_3 = rank['ProductCategoryId']
        self.logger.info('---> rank_1 [{}] rank_cat_1 [{}]'.format(
            self._rank_1, self._rank_cat_1))

        self.logger.info('-> set_params_from_api_result out.')
        return

    def set_db_product(self):

        self.logger.info('-> AmaSPApiAsinDetail set_db_product in.')

        """
        self.logger.info("AmaSPApiAsinDetail set_db_product start update_or_create")
        obj, created = QooAsinDetail.objects.update_or_create(
            asin=self._asin,
            title=self._title,
            url='', # 現状、セットするURLがない。何にするか・・
            amount=0, # ここは販売時のFBA在庫数を入れたい。まだ未定
            binding=self._binding,
            brand=self._brand,
            color=self._color,
            department=self._department,
            is_adlt=True if is_adlt == True else False,
            i_height=self._i_height,
            i_length=self._i_length,
            i_width=self._i_width,
            i_weight=self._i_weight,
            p_height=self._p_height,
            p_length=self._p_length,
            p_width=self._p_width,
            p_weight=self._p_weight,
            rank_cat_1=self._rank_cat_1,
            rank_1=self._rank_1,
            rank_cat_2=self._rank_cat_2,
            rank_2=self._rank_2,
            rank_cat_3=self._rank_cat_3,
            rank_3=self._rank_3,
            buybox_listing_price=self._buybox_listing_price, # カート価格
            buybox_condition=self._buybox_condition, # カート出品状態
            buybox_shipping_price=self._buybox_shipping_price, # カート送料
            shipfrom_country=self._shipfrom_country, # 出品者の所在国
            num_offers_amazon=self._num_offers_amazon, # NumberOfOffersのamazon出品者数
            num_offers_merchant=self._num_offers_merchant, # NumberOfOffersのMerchant出品者数
            ok_seller_feedback_rate=self._ok_seller_feedback_rate, # OKと判断されたセラーのfeedback rate
            ok_seller_id=self._ok_seller_id, # OKと判断されたセラーのid
            is_seller_ok=self._is_seller_ok, # 出品OKかどうかの出品者状態による判定
        )
        obj.save()

        """
        self.logger.info("-> AmaSPApiAsinDetail set_db_product end ")
        return

    def get_ama_src_with_tor(self):
        # torでAmazonページをスクレイピングして詳細情報を取ってみよう
        self.logger.info("--->> get_ama_src_with_tor in ")
        self._common_chrome_driver = CommonChromeDriver(self.logger)

        # self.common_chrome_driver.driverにセット
        #self._common_chrome_driver.init_chrome_with_no_tor(USER_DATA_DIR)
        self._common_chrome_driver.init_chrome_with_tor()

        # asin指定してページ情報取得
        url = 'https://www.amazon.co.jp/dp/' + self._asin + '/ref=nav_logo'

        # これだとうまくいく・・・
        #url = 'https://www.amazon.co.jp/CA4LA-%E3%82%AB%E3%82%B7%E3%83%A9-KTZ02277-HK-BKH/dp/B0B9GRH3PZ/ref=sr_1_1?pf_rd_i=2229202051&pf_rd_m=A3P5ROKL5A1OLE&pf_rd_p=cc33837b-6b21-4d03-8ce5-957c33106d62&pf_rd_r=8TBRNX9MTJ4W04XYC1G6&pf_rd_s=merchandised-search-5&pf_rd_t=101&qid=1662184803&s=fashion&sr=1-1'

        # これでも取れてるかな。 ref=nav_logoをつけただけ
        #url = 'https://www.amazon.co.jp/dp/B084TNP2B4/ref=nav_logo'

        #url = 'https://www.google.com/'
        self.get_ama_src_exec(url)

        self.logger.info("--->> get_ama_src_with_tor page_result [{}]".format(
            self._common_chrome_driver.driver.page_source
        ))

        self.logger.info("--->> get_ama_src_with_tor in ")
        return

    def get_ama_src_exec(self, url):
        try:
            self.logger.info("--->> get_ama_src_exec in ")

            retry_cnt = 3
            for i in range(1, retry_cnt + 1):
                try:
                    self._common_chrome_driver.driver.get(url)
                    # driver.get('https://www.amazon.co.jp/dp/B073QT4NMH/')
                except Exception as e:
                    self.logger.info(traceback.format_exc())
                    self.logger.info('webdriver error occurred start retry..')
                    self._common_chrome_driver.restart_chrome()
                    sleep(3)
                else:
                    break

        except Exception as e:
            #print(traceback.format_exc())
            self.logger.info(traceback.format_exc())
            traceback.print_exc()
            self._common_chrome_driver.quit_chrome_with_tor()

        self.logger.info("--->> get_ama_src_exec out ")
        return


# sp_apiのProductsとかぶったので改名する
class Products_BK20220821(BaseObject):

    # Idlistは最大5　回復レートは5商品/秒　最大20リクエスト　1時間あたり18000
    def GetMatchingProductForId(self, IdList):
        q = {
            'Action': 'GetMatchingProductForId',
            'MarketplaceId': 'A1VC38T7YXB528',
            'Version': '2011-10-01',
            'IdType': 'ASIN',
        }
        [q.update({'IdList.Id.' + str(i + 1): Id}) for i, Id in enumerate(IdList)]

        return q

    # Idlistは最大20　回復レートは10商品/秒　最大20リクエスト　時間最大36000リクエスト
    # 新品のカートボックス価格と中古のカートボックス価格を返す
    def GetCompetitivePricingForASIN(self, IdList):
        q = {
            'Action': 'GetCompetitivePricingForASIN',
            'MarketplaceId': 'A1VC38T7YXB528',
            'Version': '2011-10-01',
        }
        [q.update({'ASINList.ASIN.' + str(i + 1): Id}) for i, Id in enumerate(IdList)]

        return q

    # Idlistは最大20　回復レートは10商品/秒　最大20リクエスト　時間最大36000リクエスト
    # 最低価格
    # ItemCondition値：#New #Used #Collectible #Refurbished #Club #デフォルト：All
    def GetLowestOfferListingsForASIN(self, IdList, ItemCondition='New', ExcludeMe=True):
        q = {
            'Action': 'GetLowestOfferListingsForASIN',
            'MarketplaceId': 'A1VC38T7YXB528',
            'Version': '2011-10-01',
            'ItemCondition': ItemCondition,
            'ExcludeMe': ExcludeMe
        }
        [q.update({'ASINList.ASIN.' + str(i + 1): Id}) for i, Id in enumerate(IdList)]

        return q

    # Idlistは最大20　回復レートは1リクエスト/5秒　最大20リクエスト 時間最大720リクエスト
    def ListMatchingProducts(self, Query, QueryContextId='All'):
        q = {
            'Action': 'ListMatchingProducts',
            'MarketplaceId': 'A1VC38T7YXB528',
            'Version': '2011-10-01',
            'Query': Query,
            'QueryContextId': QueryContextId
        }

        return q

    # 最大20　回復レートは1リクエスト/5秒　最大20リクエスト 時間最大720リクエスト
    def GetProductCategoriesForASIN(self, ASIN):
        q = {
            'Action': 'GetProductCategoriesForASIN',
            'MarketplaceId': 'A1VC38T7YXB528',
            'Version': '2011-10-01',
            'ASIN': ASIN
        }

        return q

    def PostMWS(self, q):
        timestamp = datetime_encode(datetime.datetime.utcnow())
        last_update_after = datetime_encode(
            datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )

        data = {
            'AWSAccessKeyId': AMAZON_CREDENTIAL['ACCESS_KEY_ID'],
            'MarketplaceId': 'A1VC38T7YXB528',
            'SellerId': AMAZON_CREDENTIAL['SELLER_ID'],
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp,
        }

        #self.logger.info('PostMWS q:' + str(q))
        data.update(q)
        query_string = urllib.parse.urlencode(sorted(data.items()))
        #self.logger.info('PostMWS query_string:' + str(query_string))

        # これは例外かも知れないが
        query_string = re.sub('%25', '%', query_string)
        #self.logger.info('PostMWS after qy_str:' + str(query_string))

        canonical = "{}\n{}\n{}\n{}".format(
            'POST', DOMAIN, ENDPOINT, query_string
        )
        h = hmac.new(
            six.b(AMAZON_CREDENTIAL['ACCESS_SECRET']),
            six.b(canonical), hashlib.sha256
        )
        signature = urllib.parse.quote(base64.b64encode(h.digest()), safe='')
        url = 'https://{}{}?{}&Signature={}'.format(
            DOMAIN, ENDPOINT, query_string, signature)

        res = requests.post(url)
        # 文字化け対策
        res.encoding = res.apparent_encoding

        return res.text

    def find_list_matched_product_ns2(self, element):
          #print("find_list_matched_product : resobj:[%s]", str(self._response))
          return self.parse.find(".//ns2:%s" % element, self._products_namespace)


    def find_list_matched_product(self, element):
          #print("find_list_matched_product : resobj:[%s]", str(self._response))
          return self.parse.find(".//2011-10-01:%s" % element, self._products_namespace)

      # https://lets-hack.tech/programming/languages/python/mws/　参考に
      # https://searchcode.com/codesearch/view/81319497/
      # Idlistは最大20　回復レートは1リクエスト/5秒　最大20リクエスト 時間最大720リクエスト
    def request_list_matching_products(self, Query, QueryContextId='All'):
        return self.request(PRODUCTSENDPOINT, **{"Action": "ListMatchingProducts",
                                                'Query': urllib.parse.quote(Query),
                                                'QueryContextId':QueryContextId,
                                                "MarketplaceId.Id.1": MARKETPLACES[self.Region][1]})

    def request_get_matching_product(self, asins):
        data = {
            "Action": "GetMatchingProduct",
            "MarketplaceId.Id.1" : MARKETPLACES[self.Region][1]
        }
        data.update(self.enumerate_param('ASINList.ASIN.', asins))
        return self.request(PRODUCTSENDPOINT, data)
"""
return self.request(PRODUCTSENDPOINT, **{"Action": "GetMatchingProduct",
                                    "MarketplaceId.Id.1": MARKETPLACES[self.Region][1],
                                    self.enumerate_param('ASINList.ASIN.', asins)})
"""

#
class Order(BaseObject):

    # ListOrders
    def request_list_orders(self, days=None):
       if days == None:
           days = 14  # 1
       last_update_after = datetime_encode(
          datetime.datetime.utcnow() - datetime.timedelta(days=days))
    # datetime.datetime.utcnow() - datetime.timedelta(days=14))

       return self.request(ORDERENDPOINT, **{"Action": "ListOrders",
                                             'LastUpdatedAfter': last_update_after,"MarketplaceId.Id.1": MARKETPLACES[self.Region][1]})

#
class Report(BaseObject):

    #
    def request_report(self, ReportType=None):
       return self.request(**{"Action": "RequestReport", "ReportType": ReportType,
                             "MarketplaceIdList.Id.1": MARKETPLACES[self.Region][1]})

    #
    def get_report_request_list(self, RequestId=None):
       return self.request(**{"Action": "GetReportRequestList", "ReportRequestIdList.Id.1": RequestId})

    #
    def get_report_list(self, RequestId=None):
       return self.request(**{"Action": "GetReportList", "ReportRequestIdList.Id.1": RequestId})

    #
    def get_report(self, ReportId=None):
       return self.request(**{"Action": "GetReport", "ReportId": ReportId})


    # Create your views here.
    def index(request):
       return HttpResponse("Hello testscr_1 ! ")


    def getorder(request):
        order = Order()

        #
        #  1
        response = order.request_list_orders(14)
        # print(response.raw)
        # parsed = response.parse
        print('ok parse')
        if (response.find_orders('LatestShipDate')):
            print(response.find_orders('LatestShipDate').text)
        else:
            print('no latest ship date')

        mylastorder = ''
        #  Order/AmazonOrderId
        myorders = response.find_orders_all('Order')

    # f = open('/home/django/sample/amget/tmp/samplesrc.txt', mode='w')
    # f.write(str(response.raw, 'utf-8'))
    # f.close()

        with closing(sqlite3.connect(dbname)) as conn:
            c = conn.cursor()

            for myorder in myorders:
              set_order(c, myorder)
            conn.commit()

# print(find_orders_by_obj(myorder,'AmazonOrderId').text)
# print(myorder.find(".//2013-09-01:%s" % 'AmazonOrderId', _orders_namespace).text)
# mystatus = find_orders_by_obj(myorder,'OrderStatus').text
# if(mystatus is None):
#    print('no orderstatus')
# else:
#    print(mystatus)
# if mystatus == 'Unshipped':
#    myorderobj = find_orders_by_obj(myorder,'BuyerName')
#    if(myorderobj is None):
#        mylastorder += '[none] '
#    else:
#        mylastorder = myorderobj.text
# else:
#    print('no buyer name')

# return HttpResponse(mylastorder)
        return HttpResponse('ok')
# print(myorder.find(".//2013-09-01:%s" % 'BuyerName', _orders_namespace).text)
# parse.find(".//2013-09-01:%s" % element, self._orders_namespace)


#        print('AmazonOrderId:' + myorder.find('./Order', _orders_namespace).text.strip())
# print(response.parse)
# print(response.find_orders("OrderType"))

"""
  #
  response = report.request_report(ReportType="_GET_MERCHANT_LISTINGS_DATA_")
  # ID
  request_id = response.find("ReportRequestId").text

  try:
      # ID
      while True:
          # ID
          response = report.get_report_request_list(RequestId=request_id)
          # status_DONE__DONE_ID
          if "_DONE_" == response.find("ReportProcessingStatus").text:
              report_id = response.find("GeneratedReportId").text
              break
          # 5032
          time.sleep(120)

      # ID
      response = report.get_report(ReportId=report_id)
      print(response.raw)
  except Exception as e:
      print(e)
"""

