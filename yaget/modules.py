from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
#from google import spreadsheet
import gspread
import subprocess
import traceback
from oauth2client.service_account import ServiceAccountCredentials

# Create your views here.
from .models import Friend, Message, YaItemList, YaItemDetail
from .forms import FriendForm, MessageForm, YaItemListForm, YaSetListToSheet, KickYagetForm
from .forms import FindForm

from django.db.models import Q
from django.db.models import Count, Sum, Avg, Min, Max
from .forms import CheckForm

from django.core.paginator import Paginator
from wowma_access import WowmaAccess
from qoo10_access import Qoo10Access
from buyers_info import BuyersInfo, BuyersBrandInfo
import error_goods_log


class CommonModules(object):

    def __init__(self, logger):
        self._logger = logger
        self.driver = None

        # google trans関連
        self._trans_cnt = 0  # get_translated_word の呼び出し先アカウントを覚えておく
        self._trans_target_url = [
            'https://script.google.com/macros/s/AKfycbx3uANmPUC0wDdEWMdZmf-aB1cf8Oga_sR_M0_fejD1fGQw04U/exec',
            'https://script.google.com/macros/s/AKfycbxyOWjdZrrlC8mQf_IH_ao44mamXiazuXv0aS6DuYFsSY4hitzK/exec',
            'https://script.google.com/macros/s/AKfycbydWkMZ5FUb7S9EkZK2_F0bSo6rQjoimB2f0vzyG5j_Iys6UQaX/exec',
            'https://script.google.com/macros/s/AKfycbzrhK-yu12yhYEz8fmgi540Lf1l9VRa3Zh7iIIOz7v7RTojce4H/exec',
            'https://script.google.com/macros/s/AKfycbwaC0JST3uGRQd2BjUgwilpUeVbPtZYIgnL4owal3y9C0MuQTY/exec',
            'https://script.google.com/macros/s/AKfycbwDw64__CqgdV4zmchfJmfQm3VO0aI_-AjDdE-pOG_5faNOHis/exec',
            'https://script.google.com/macros/s/AKfycbyHScoCJbSeEdKtGvX4iGri9uy5hj-xlsLMOzsd5MlwJtNGQw/exec',
            'https://script.google.com/macros/s/AKfycbzQcbGoKhb0m8lOtvuVZ1dPRniP-kZqjk1v0UWtTjRpmmg5ftQ/exec',
            'https://script.google.com/macros/s/AKfycbwqYTSsPVZJ5OrZY8vom1kavrWMFJngd6BC0T7pY4a8K79lp0yx/exec',
            'https://script.google.com/macros/s/AKfycbzvjRTzDH4x3F3ydMrTqPTz9xl6EYTJ7YzNbOR0qUNMahyk1mU/exec',
            'https://script.google.com/macros/s/AKfycby3O42O8cPZFedG3TZa0H6zpgeX7HG2RLlpt_YpRSZKhZqAced0/exec',
            'https://script.google.com/macros/s/AKfycbyg0xubxYhP-4bvKs1zL6wIYS3g9UD3K2MCnfV7dT04VWyGsi-V/exec',
            'https://script.google.com/macros/s/AKfycbwflOQjC-raqshfcDk-VFU921xVB34NzohS1gaWpiOSpBLWmQ0/exec',
        ]


    def force_timeout(self):
        os.system('systemctl restart httpd')
        return

    # torリスタート
    def restart_tor(self):
        try:
            # tor をリスタートしてIP切り替える
            args = ['sudo', 'service', 'tor', 'restart']
            subprocess.call(args)
            sleep(2)
            proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()
        return

    # headless chromeをtorセットして初期化する
    def init_chrome_with_tor(self):
        try:
            # tor をリスタートしてIP切り替える
            args = ['sudo', 'service', 'tor', 'restart']
            subprocess.call(args)
            sleep(2)
            proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,1024')
            options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

            self.driver = webdriver.Chrome(chrome_options=options)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()

        return

    # headless chromeをtorなしで初期化する
    def init_chrome_with_no_tor(self):
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,1024')

            self.driver = webdriver.Chrome(chrome_options=options)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()

        return

    # headless chromeをcloseする
    def quit_chrome_with_tor(self):
        try:
            # self.driver.close() # closeはフォーカスがあたってるブラウザを閉じるらしい
            self.driver.quit()  # quitは全ウィンドウを閉じてwebdriverセッションを終了する
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()

        return

    def restart_chrome(self):
        try:
            if self.driver:
                self.driver.quit()  # quitは全ウィンドウを閉じてwebdriverセッションを終了する

            # httpd restart
            self._logger.info('eb_restart_chrome restart httpd')
            self.force_timeout()
            sleep(3)

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,1024')
            options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

            self.driver = webdriver.Chrome(chrome_options=options)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()

        self._logger.info('eb_restart_chrome end')
        return

    def restart_chrome_no_tor(self):
        try:
            if self.driver:
                self.driver.quit()  # quitは全ウィンドウを閉じてwebdriverセッションを終了する

            # httpd restart
            self._logger.info('eb_restart_chrome restart httpd')
            self.force_timeout()
            sleep(3)

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,1024')

            self.driver = webdriver.Chrome(chrome_options=options)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self._logger.info(traceback.format_exc())
            traceback.print_exc()

        self._logger.info('eb_restart_chrome end')
        return

    # 自作のgoogle transAPIを呼び出して翻訳した文字列を得る
    def get_translated_word(self, word, from_lang, to_lang):
        # 翻訳する文章
        """
        以下が呼び出し用API
        kuurie7のアカウントに紐づけて作った
        場所はここ。kuurie7@gmail.comのgoogle driveにて
        https://script.google.com/d/1G7-CJLUtHXDsawkjAiGXYY-Uh08rrq5b9yF9HQU9E8JSAUxpABUmpTwZ/edit?usp=drive_web

        function doGet(e) {
          var p = e.parameter;
          var translatedText = LanguageApp.translate(p.text, p.source, p.target);
          return ContentService.createTextOutput(translatedText);
        }

        """
        #myurl = 'https://script.google.com/macros/s/AKfycbx3uANmPUC0wDdEWMdZmf-aB1cf8Oga_sR_M0_fejD1fGQw04U/exec'
        #from_lang = 'ja'
        #to_lang = 'en'

        # カウント中の配列から、リクエストするgoogle transのスクリプトを呼び出す。
        # 翻訳がエラーになったら次のURLに切り替えないといけない
        payload = {'text': word, 'source': from_lang, 'target': to_lang}
        r = ''
        for i in range(len(self._trans_target_url)):
            myurl = self._trans_target_url[self._trans_cnt]
            r = requests.get(myurl, params=payload)
            # エラーになったら「errorMessage」が含まれてくる
            if 'errorMessage' in r.text:
                self._trans_cnt += 1
                if self._trans_cnt >= len(self._trans_target_url):
                    self._trans_cnt = 0  # 配列一周してたら0に
            else:
                break
        return r.text

    # 半角スペースで区切られた文字列から重複文字と不要文字を削除する
    @staticmethod
    def get_ddjasted_keyword(moto_key):
        tmp_list_moto = moto_key.split(" ")
        tmp_list_unique = list(set(tmp_list_moto))
        ret_str = ' '.join(tmp_list_unique)

        # 不要文字は削除
        ret_str = ret_str.replace('\'s ',' ')
        ret_str = ret_str.replace('\'s','')
        return ret_str


class TestMsgModule(object):
    def get_message(self):
        return ('test get_message ok')


class GSpreadModule(object):
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


# バッチコマンドなどから共通で呼び出されるqoo10関連実行クラス
class ExecQoo10(object):

    def __init__(self, logger):
        self._logger = logger
        self._qoo10_access = Qoo10Access(self._logger)
        self._qoo10_access.qoo10_create_cert_key()

    def exec_qoo10_goods_update(self, myobj):
        """ qoo10の商品を更新する
        params: myobj YaBuyersItemDetail 商品情報
        return: true, msg 正常終了
                false, error_msg 異常終了
        """
        try:
            # qoo10 更新 ###################################################################################################
            #     qoo_upd_status = ((1, '取引待機'), (2, '取引可能'), (3, '取引廃止'))
            #     qoo_on_flg = ((0, '確認待ち'), (1, 'OK'), (2, 'NG'), (3, '在庫切れ'))
            # qooについて画面から1(出品OK)もしくは3（在庫切れ）になっている対象は、以下で掲載状況を確認して更新してゆく
            if myobj.qoo_on_flg == 1 or myobj.qoo_on_flg == 3:

                # 出品OKなのに在庫０なら、そのまま未掲載にしておく
                if int(myobj.stock) == 0:
                    if myobj.qoo_upd_status == 1 or myobj.qoo_upd_status == 3:  # qoo未掲載
                        # 未掲載 qoo_upd_status = 1（取引待機）もしくは3（登録済みだが取引廃止）
                        # 出品OKなのに在庫０、かつ未掲載なら、そのまま未掲載にしておく
                        self._logger.info('--> exec_qoo10_goods_update 出品OKなのに在庫０　未掲載のまま')
                        myobj.qoo_on_flg = 3
                    else:
                        # 掲載中 qoo_upd_status = 2 取引可能
                        # ★★出品OKなのに在庫０、掲載済みなら、在庫を0で更新しないといけない、かつ登録済みだが未掲載に切り替える
                        myobj.qoo_on_flg = 3  # 更新成功したら 在庫切れにする。出品OK状態はそのまま、qoo掲載状況は取引待機になってる
                        myobj.qoo_upd_status = 1  # 取引待機に
                        # 商品更新のセットを投げる
                        try:
                            self._qoo10_access.qoo10_my_set_update_goods(myobj)
                            self._logger.info('--> exec_qoo10_goods_update 在庫切れにした。')
                        except Exception as e:
                            self._logger.info(traceback.format_exc())
                            self._logger.info('--> exec_qoo10_goods_update 掲載中に更新中にエラーになったがそのまま続行する。後で要確認')
                            my_err_list = {
                                'batch_name': 'ExecQoo10 exec_qoo10_goods_update',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': '',
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            return False, traceback.format_exc()  # DB更新せずに戻す

                # 　在庫がある
                elif int(myobj.stock) > 0:
                    # ☆☆　出品もしくは在庫更新しないといけない ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
                    if myobj.qoo_upd_status == 1:  # 取引待機（1）は未登録か、登録済みだが在庫0で更新された場合も。
                        if myobj.qoo_gdno:  # 商品登録済み
                            # 商品更新のセットを投げる
                            myobj.qoo_on_flg = 1  # OKに。
                            myobj.qoo_upd_status = 2  # 掲載中に更新
                            try:
                                self._qoo10_access.qoo10_my_set_update_goods(myobj)
                                self._logger.info('--> exec_qoo10_goods_update 出品OKで在庫あるので掲載中に更新！ 1')
                            except Exception as e:
                                self._logger.info(traceback.format_exc())
                                self._logger.info('--> exec_qoo10_goods_update 掲載中に更新中にエラーになったがそのまま続行する。後で要確認')
                                my_err_list = {
                                    'batch_name': 'ExecQoo10 exec_qoo10_goods_update',
                                    'gid': myobj.gid,
                                    'status': 1,
                                    'code': '',
                                    'message': traceback.format_exc(),
                                }
                                error_goods_log.exe_error_log(my_err_list)
                                return False, traceback.format_exc()  # DB更新せずに戻す
                        else:
                            self._logger.info('--> exec_qoo10_goods_update 未登録だが出品OKで在庫あるので登録開始')
                            # 未掲載 qoo_upd_status = 0 なら新規登録する
                            myobj.qoo_on_flg = 1  # OKに。
                            myobj.qoo_upd_status = 2  # 掲載中に更新

                            # 商品登録のセットを投げる
                            try:
                                self._qoo10_access.qoo10_my_set_new_goods(myobj)
                                self._logger.info('--> exec_qoo10_goods_update 在庫あり、未登録だったので新規登録OK！')
                            except Exception as e:
                                self._logger.info(traceback.format_exc())
                                self._logger.info('--> exec_qoo10_goods_update 新規登録中にエラーになったがそのまま続行する。後で要確認')
                                my_err_list = {
                                    'batch_name': 'ExecQoo10 exec_qoo10_goods_update',
                                    'gid': myobj.gid,
                                    'status': 1,
                                    'code': '',
                                    'message': traceback.format_exc(),
                                }
                                error_goods_log.exe_error_log(my_err_list)
                                return False, traceback.format_exc()  # DB更新せずに戻す
                    else:
                        # 掲載中 qoo_upd_status = 2　か、登録済みだが未掲載 3 （これまで在庫０だった）
                        # 現在の在庫数で更新する、未掲載だったら復活させる
                        myobj.qoo_on_flg = 1  # 更新成功した。
                        myobj.qoo_upd_status = 2  # 掲載中に更新

                        # 商品更新のセットを投げる
                        try:
                            self._qoo10_access.qoo10_my_set_update_goods(myobj)
                            self._logger.info('--> exec_qoo10_goods_update 出品OKで在庫あるので掲載中に更新！')
                        except Exception as e:
                            self._logger.info(traceback.format_exc())
                            self._logger.info('--> exec_qoo10_goods_update 掲載中に更新中にエラーになったがそのまま続行する。後で要確認')
                            my_err_list = {
                                'batch_name': 'ExecQoo10 exec_qoo10_goods_update',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': '',
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            return False, traceback.format_exc()  # DB更新せずに戻す

                    """
                    if myobj.qoo_upd_status != 0:
                        # 登録済みだったら、在庫状況によらず商品内容をupdateする
                        myobj.qoo_on_flg = 1  # OKのまま
                        myobj.qoo_upd_status = 1  # 掲載中に
                        # 商品更新のセットを投げる
                        self._qoo10_access.qoo10_my_set_update_goods(myobj)
                    """
                else:  # 在庫数の取得エラー？
                    # raise Exception("在庫数の取得に失敗？stock:[{}] gid:[{}]".format(myobj.stock, myobj.gid))
                    return False, "在庫数の取得に失敗？stock:[{}] gid:[{}]".format(myobj.stock, myobj.gid)  # DB更新せずに戻す

            else:
                # ここにきたら、qoo_on_flg は 0（確認中）か2（NG）のはず。
                if myobj.qoo_on_flg == 2:
                    self._logger.info('--> exec_qoo10_goods_update qoo 未出品に更新しないと flg=2 （NG）')
                    if myobj.qoo_upd_status != 1:  # 登録済みのものは未掲載に倒さないと
                        myobj.qoo_on_flg = 2  # NGのまま。
                        myobj.qoo_upd_status = 1  # 取引待機に

                        # 商品更新のセットを投げる
                        try:
                            self._qoo10_access.qoo10_my_set_update_goods(myobj)
                            self._logger.info('--> exec_qoo10_goods_update qoo 出品OKで在庫あるので掲載中に更新！')
                        except Exception as e:
                            self._logger.info(traceback.format_exc())
                            self._logger.info('--> exec_qoo10_goods_update 掲載中に更新中にエラーになったがそのまま続行する。後で要確認')
                            my_err_list = {
                                'batch_name': 'ExecQoo10 exec_qoo10_goods_update',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': '',
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            return False, traceback.format_exc()  # DB更新せずに戻す

                    else:
                        # 更新時にエラー？
                        self._logger.info(
                            '--> exec_qoo10_goods_update qoo 未出品に更新しないと flg=2 （NG）qoo_upd_status:[{}]'.format(
                                myobj.qoo_upd_status))
                        """
                        raise Exception("qoo 出品NGで在庫あったのでNGにする更新中に失敗？ gid:[{0}] stock:[{1}]".format(
                            myobj.gid, myobj.stock))
                        """
                        # 2021/11/16 ひとまず初期登録中なのでエラーになってもそのまま進んでしまう。後で直すこと！
                        return False, "qoo 未出品に更新しないと flg=2 （NG）qoo_upd_status:[{}]".format(
                                myobj.qoo_upd_status)  # DB更新せずに戻す
                else:
                    self._logger.info('--> exec_qoo10_goods_update qoo 在庫あるがNGフラグたってて未出品なので処理せず flg=0 ')

            # ここまで到達したら商品の状態は更新してしまう
            myobj.save()
        except:
            return False, traceback.format_exc()  # DB更新せずに戻す

        return True, "qoo10 更新 正常終了"


# バッチコマンドなどから共通で呼び出されるwowma関連実行クラス
class ExecWowma(object):

    def __init__(self, logger):
        self._logger = logger
        self._wowma_access = WowmaAccess(self._logger)
        self._buinfo_obj = BuyersInfo(self._logger)

    def exec_wowma_goods_update(self, myobj, taglist_upd_flg):
        """ wowmaの商品を更新する
        params: myobj YaBuyersItemDetail 商品情報
                taglist_upd_flg: 0 タグは最新化せず、dbに登録されてるままを
                                 1 タグは指定のカテゴリにマッチしたリストで最新化する
        return: true, msg 正常終了
                false, error_msg 異常終了
        """
        try:
            self._logger.debug('--> exec_wowma_goods_update 処理開始 tag_flg:[{}]'.format(taglist_upd_flg))
            # 既存DBのフラグによってどうステータスを更新するか
            # 出品はまだNG。（画面から編集してない）が、DBの在庫などは更新していい
            if myobj.wow_on_flg == 0:
                self._logger.debug('--> exec_wowma_goods_update 出品まだNG そのまま')
                return True, "wow_on_flg[0] のためwowmaの更新はしません"

            # 画面から出品OKになっている。以下で掲載状況を確認して更新してゆく
            elif myobj.wow_on_flg == 1:

                if taglist_upd_flg == '1':
                    # wowmaのtagidは、このタイミングで最新化しておく
                    # wowma は検索タグIDを設定。
                    myobj.wow_tagid = self._buinfo_obj.get_wow_tagid_list(
                        myobj.bu_ctid, myobj.wow_gname, myobj.wow_ctid)
                    myobj.save()

                # 画像情報を作らないといけない。
                images = [{'imageUrl': myobj.g_img_src_1, 'imageName': 'image_1', 'imageSeq': 1},
                          {'imageUrl': myobj.g_img_src_2, 'imageName': 'image_2', 'imageSeq': 2},
                          {'imageUrl': myobj.g_img_src_3, 'imageName': 'image_3', 'imageSeq': 3},
                          {'imageUrl': myobj.g_img_src_4, 'imageName': 'image_4', 'imageSeq': 4},
                          {'imageUrl': myobj.g_img_src_5, 'imageName': 'image_5', 'imageSeq': 5},
                          {'imageUrl': myobj.g_img_src_6, 'imageName': 'image_6', 'imageSeq': 6},
                          {'imageUrl': myobj.g_img_src_7, 'imageName': 'image_7', 'imageSeq': 7},
                          {'imageUrl': myobj.g_img_src_8, 'imageName': 'image_8', 'imageSeq': 8},
                          {'imageUrl': myobj.g_img_src_9, 'imageName': 'image_9', 'imageSeq': 9},
                          {'imageUrl': myobj.g_img_src_10, 'imageName': 'image_10', 'imageSeq': 10},
                          {'imageUrl': myobj.g_img_src_11, 'imageName': 'image_11', 'imageSeq': 11},
                          {'imageUrl': myobj.g_img_src_12, 'imageName': 'image_12', 'imageSeq': 12},
                          {'imageUrl': myobj.g_img_src_13, 'imageName': 'image_13', 'imageSeq': 13},
                          {'imageUrl': myobj.g_img_src_14, 'imageName': 'image_14', 'imageSeq': 14},
                          {'imageUrl': myobj.g_img_src_15, 'imageName': 'image_15', 'imageSeq': 15},
                          {'imageUrl': myobj.g_img_src_16, 'imageName': 'image_16', 'imageSeq': 16},
                          {'imageUrl': myobj.g_img_src_17, 'imageName': 'image_17', 'imageSeq': 17},
                          {'imageUrl': myobj.g_img_src_18, 'imageName': 'image_18', 'imageSeq': 18},
                          {'imageUrl': myobj.g_img_src_19, 'imageName': 'image_19', 'imageSeq': 19},
                          {'imageUrl': myobj.g_img_src_20, 'imageName': 'image_20', 'imageSeq': 20}]

                # 出品OKなのに在庫０なら、そのまま未掲載にしておく
                if int(myobj.stock) == 0:
                    if myobj.wow_upd_status == 0:
                        # 未掲載 wow_upd_status = 0
                        # 出品OKなのに在庫０、かつ未掲載なら、そのまま未掲載にしておく
                        self._logger.debug('--> exec_wowma_goods_update 出品OKなのに在庫０　未掲載のまま')
                        myobj.wow_on_flg = 1
                    else:
                        # 掲載中 wow_upd_status = 1
                        # ★★出品OKなのに在庫０、掲載済みなら、在庫を0で更新しないといけない
                        try:
                            ret_obj_list = self._wowma_access.wowma_update_item_info(
                                    myobj.wow_gname,
                                    myobj.gid,
                                    myobj.gcode,
                                    myobj.wow_price,
                                    myobj.wow_fixed_price,
                                    myobj.wow_postage_segment,
                                    myobj.wow_postage,
                                    myobj.wow_delivery_method_id,
                                    myobj.wow_gdetail,
                                    myobj.wow_ctid,
                                    myobj.wow_keyword,
                                    myobj.wow_tagid,
                                    myobj.wow_upd_status,  # 1は販売中。2は販売終了。
                                    int(myobj.stock),  # ★要確認、DBの在庫数をそのまま更新すること。在庫数
                                    images,  # 画像情報。リストで images[imageUrl,imageName,imageSeq]
                            )
                            for ret_obj in ret_obj_list:
                                if ret_obj['res_rtn'] == "0":  # 正常に更新されていた場合
                                    # lotnumberを更新しておく
                                    myobj.wow_lotnum = ret_obj['res_code']
                                    self._logger.debug(
                                        '--> exec_wowma_goods_update wowma側更新OK。lotnum[{}]'.format(
                                            myobj.wow_lotnum))
                        except:
                            # 更新時にエラー？
                            my_err_list = {
                                'batch_name': 'exec_wowma_goods_update wowma_update_stock point 0_1',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': myobj.gcode,
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            raise Exception("wowma更新時に失敗？{}".format(myobj.gcode))

                # 　在庫がある
                elif int(myobj.stock) > 0:
                    # ☆☆　出品もしくは在庫更新しないといけない ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
                    if myobj.wow_upd_status == 0:
                        self._logger.debug('--> exec_wowma_goods_update 未登録だが出品OKで在庫あるので登録開始')
                        # 未掲載 wow_upd_status = 0
                        try:
                            ret_obj_list = self._wowma_access.wowma_register_item_info(
                                                               myobj.wow_gname,
                                                               myobj.gid,
                                                               myobj.gcode,
                                                               myobj.wow_price,
                                                               myobj.wow_fixed_price,
                                                               myobj.wow_postage_segment,
                                                               myobj.wow_postage,
                                                               myobj.wow_delivery_method_id,
                                                               myobj.wow_gdetail,
                                                               myobj.wow_ctid,
                                                               myobj.wow_keyword,
                                                               myobj.wow_tagid,
                                                               1,  # 出品OKなので1は販売中。
                                                               int(myobj.stock),  # 在庫数
                                                               images,  # 画像情報。リストで images[imageUrl,imageName,imageSeq]
                                                               )

                            chk_flg = 0
                            for ret_obj in ret_obj_list:
                                # PME0106:入力された商品コードは、既に登録されています。
                                if ret_obj['res_rtn'] == '1' and ret_obj['res_code'] == 'PME0106':
                                    # 出品していいはずなので、更新をかけ直す
                                    try:
                                        ret_obj_list = self._wowma_access.wowma_update_item_info(
                                            myobj.wow_gname,
                                            myobj.gid,
                                            myobj.gcode,
                                            myobj.wow_price,
                                            myobj.wow_fixed_price,
                                            myobj.wow_postage_segment,
                                            myobj.wow_postage,
                                            myobj.wow_delivery_method_id,
                                            myobj.wow_gdetail,
                                            myobj.wow_ctid,
                                            myobj.wow_keyword,
                                            myobj.wow_tagid,
                                            1,  # 1は販売中。2は販売終了。出品OKなので販売中 ( 1 ) にしておく
                                            int(myobj.stock),  # 在庫数
                                            images,  # 画像情報。リストで images[imageUrl,imageName,imageSeq]
                                        )
                                        for ret_obj in ret_obj_list:
                                            if ret_obj['res_rtn'] == "0":  # 正常に更新されていた場合
                                                # lotnumberを更新しておく
                                                myobj.wow_lotnum = ret_obj['res_code']
                                                self._logger.debug(
                                                    '--> exec_wowma_goods_update wowma側更新OK_1。lotnum[{}]'.format(
                                                        myobj.wow_lotnum))
                                                myobj.wow_upd_status = 1  # 掲載中に更新

                                    except:
                                        # 更新時にエラー？
                                        my_err_list = {
                                            'batch_name': 'wowma_stock_chk exec_wowma_goods_update point 1_1',
                                            'gid': myobj.gid,
                                            'status': 1,
                                            'code': myobj.gcode,
                                            'message': traceback.format_exc(),
                                        }
                                        error_goods_log.exe_error_log(my_err_list)
                                        #continue  # DB更新せずに戻す
                                        raise Exception(
                                            "出品OKで在庫あるので更新中に失敗？ gid:[{0}] stock:[{1}]".format(
                                                myobj.gid, myobj.stock))

                                elif ret_obj['res_rtn'] != "0":
                                    self._logger.debug(
                                        "exec_wowma_goods_update wowma 商品登録でエラー [{}][{}]".format(
                                            ret_obj['res_code'], ret_obj['res_msg']))
                                    chk_flg = 1  # なにかエラーになってた

                                elif ret_obj['res_rtn'] == "0":  # 正常に更新されていた場合
                                    self._logger.debug(
                                        "exec_wowma_goods_update wowma 商品登録できた [{}][{}]".format(
                                            ret_obj['res_code'], ret_obj['res_msg']))
                                    # lotnumberを更新しておく
                                    myobj.wow_lotnum = ret_obj['res_code']

                            if chk_flg == 0:
                                # 0が返ってきて 出品OKだったら、フラグを出品済みに
                                # 出品失敗なら 1 が返される。この場合は未出品のまま
                                self._logger.debug('--> exec_wowma_goods_update 登録OK！ 1_2')
                                myobj.wow_on_flg = 1  # OK
                                myobj.wow_upd_status = 1  # 掲載中に更新
                            else:
                                # 更新時にエラー？
                                my_err_list = {
                                    'batch_name': 'wowma_stock_chk exec_wowma_goods_update point 2_1',
                                    'gid': myobj.gid,
                                    'status': 1,
                                    'code': myobj.gcode,
                                    'message': traceback.format_exc(),
                                }
                                error_goods_log.exe_error_log(my_err_list)
                                raise Exception("wowma更新時に失敗？ _1 {}".format(myobj.gcode))

                        except:
                            # 更新時にエラー？
                            my_err_list = {
                                'batch_name': 'exec_wowma_goods_update wowma_update_stock point 2_2',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': myobj.gcode,
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            raise Exception(
                                "出品OKで在庫あるので登録中に失敗？_2 gid:[{0}] stock:[{1}]".format(
                                    myobj.gid, myobj.stock))

                    else:
                        # 掲載中 wow_upd_status = 1
                        # 現在の在庫数で更新する
                        self._logger.debug('--> exec_wowma_goods_update 掲載中。現時点の在庫数で更新')
                        try:
                            ret_obj_list = self._wowma_access.wowma_update_item_info(
                                    myobj.wow_gname,
                                    myobj.gid,
                                    myobj.gcode,
                                    myobj.wow_price,
                                    myobj.wow_fixed_price,
                                    myobj.wow_postage_segment,
                                    myobj.wow_postage,
                                    myobj.wow_delivery_method_id,
                                    myobj.wow_gdetail,
                                    myobj.wow_ctid,
                                    myobj.wow_keyword,
                                    myobj.wow_tagid,
                                    myobj.wow_upd_status,  # 1は販売中。2は販売終了。
                                    int(myobj.stock),  # 在庫数
                                    images,  # 画像情報。リストで images[imageUrl,imageName,imageSeq]
                            )
                            for ret_obj in ret_obj_list:
                                if ret_obj['res_rtn'] == "0":  # 正常に更新されていた場合
                                    # lotnumberを更新しておく
                                    myobj.wow_lotnum = ret_obj['res_code']
                                    myobj.wow_on_flg = 1  # 更新成功した。
                                    self._logger.debug(
                                        '--> exec_wowma_goods_update 在庫数更新 gid:[{0}] stock:[{1}]'.format(
                                            myobj.gid, myobj.stock))
                        except:
                            # 更新時にエラー？
                            #raise Exception("在庫を0更新時に失敗？ gid:[{0}] stock:[{1}]".format(gid, tmpgretail))
                            my_err_list = {
                                'batch_name': 'exec_wowma_goods_update wowma_update_stock point 1_1',
                                'gid': myobj.gid,
                                'status': 1,
                                'code': myobj.gcode,
                                'message': traceback.format_exc(),
                            }
                            error_goods_log.exe_error_log(my_err_list)
                            raise Exception(
                                "出品OKで在庫あるのに更新中に失敗？_3 gid:[{0}] stock:[{1}]".format(
                                    myobj.gid, myobj.stock))


                else:  # 在庫数の取得エラー？
                    raise Exception("在庫数の取得に失敗？{}".format(myobj.stock))

            else:
                # ここにきたら、wow_on_flg は 2（NG）のはず。そのままにしておく
                # ただし本メソッド呼び出し時の条件で 2は除外してあるのでここには来ないはず
                self._logger.debug('--> exec_wowma_goods_update 処理せず flg=2 （NG）')
                return True, "wowma 商品情報更新 flg=2 （NG）なので更新せずに終了"

            # DBを更新
            myobj.save()

        except:
            return False, traceback.format_exc()  # DB更新せずに戻す

        return True, "wowma 商品情報更新 正常終了"

