#-*-coding: utf-8 -*-
import sys
import inspect
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2
frame = inspect.currentframe()

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

        # self.connect(self, SIGNAL("OnEventConnect(int)"), self.OnEventConnect)
        # self.connect(self, SIGNAL("OnReceiveTrData(QString, QString, QString, QString, QString, int, QString, \
        #                            QString, QString)"), self.OnReceiveTrData)
        # self.connect(self, SIGNAL("OnReceiveChejanData(QString, int, QString)"), self.OnReceiveChejanData)

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0 :
            print("connected")
        else :
            print("disconnected")
        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        # print(frame.f_lineno)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    ## 매수 주문은 3단계로 구성
    ##  1) APP->Server : SenoOrder
    ##  2) Server->APP : OnReceiveChejanData (Event)  --  발생할 때 까지 대기
    ##  3) APP->Server : GetChejanData (FID)
    ## 참고 (FID)
    ##    9203   :     주문번호
    ##     302   :     종목명
    ##     900   :     주문수량
    ##     901   :     주문가격
    ##     902   :     미체결수량
    ##     904   :     원주문번호
    ##     905   :     주문구분
    ##     908   :     주문 / 체결시간
    ##     909   :     체결번호
    ##     910   :     체결가
    ##     911   :     체결량
    ##      10   :     현재가, 체결가, 실시간종가

    ## 매수 주문 용 메서드 (매수 주문 (과정 1))
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    ## 채결 잔고 이벤트 확인 ( 매수 주문 (과정 2))
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))

    ## 채결 잔고 데이터를 가져오는 메서드 (매수 주문 (과정 3))
    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    ## 계좌 정보 및 로그인 정보를 얻어오는 메서드
    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret


    ######################################################################
    #### Transaction 구현
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        print(frame.f_lineno)
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        ## ??
        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        ## 예수금 확인 용
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        ## 보유 종목 확인
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    ## 종목 확인
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    ## 예수금 확인
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    ## 보유 종목 확인용
    def _opw00018(self, rqname, trcode):

        # single data
        # frame = inspect.currentframe()
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        ## 실투는 총수익률 표시 방법이 다름
        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))


        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price,
                                                  eval_profit_loss_price, earning_rate])

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    #########################  그밖에 .. #########################

    ## 실투인지, 모의토자 인지 구분하기 위해..
    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'

        format_data = format(int(strip_data), ',d')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.reset_opw00018_output()
    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]
    print(account_number)

    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")




'''
    def CommTerminate(self):
        self.dynamicCall("CommTerminate()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def init_opw00018_data(self):
        self.data_opw00018 = {'single': [], 'multi': [] }


    def OnEventConnect(self, errCode):
        if errCode == 0:
            print("connected")
        else:
            print("disconnected")
        self.login_event_loop.exit()

    def SetInputValue(self, sID, sValue):
        self.dynamicCall("SetInputValue(QString, QString)", sID, sValue)

    def CommRqData(self, sRQName, sTRCode, nPrevNext, sScreenNo):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", sRQName, sTRCode, nPrevNext, sScreenNo)

        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def CommGetData(self, sJongmokCode, sRealType, sFieldName, nIndex, sInnerFiledName):
        data = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", sJongmokCode, sRealType,
                                sFieldName, nIndex, sInnerFiledName)
        return data.strip()

    def OnReceiveTrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        self.prev_next = PrevNext

        #if RQName == "opt10008_req":
        #    cnt = self.GetRepeatCnt(TrCode, RQName)
        #    for i in range(cnt):
        #        foreign_rt = self.CommGetData(TrCode, "", RQName, i, "비중" )

        #    self.foreign_ratio = foreign_rt

        if RQName == "opt10080_req":
            cnt = self.GetRepeatCnt(TrCode, RQName)

            for i in range(cnt):
                date = self.CommGetData(TrCode, "", RQName, i, "체결시간")
                open = self.CommGetData(TrCode, "", RQName, i, "시가")
                high = self.CommGetData(TrCode, "", RQName, i, "고가")
                low  = self.CommGetData(TrCode, "", RQName, i, "저가")
                close  = self.CommGetData(TrCode, "", RQName, i, "현재가")
                volume  = self.CommGetData(TrCode, "", RQName, i, "거래량")

                self.ohlcv_minute['time'].append(date)
                self.ohlcv_minute['open'].append(int(open))
                self.ohlcv_minute['high'].append(int(high))
                self.ohlcv_minute['low'].append(int(low))
                self.ohlcv_minute['close'].append(int(close))
                self.ohlcv_minute['volume'].append(int(volume))

        if RQName == "opt10081_req":
            cnt = self.GetRepeatCnt(TrCode, RQName)

            for i in range(cnt):
                date = self.CommGetData(TrCode, "", RQName, i, "일자")
                open = self.CommGetData(TrCode, "", RQName, i, "시가")
                high = self.CommGetData(TrCode, "", RQName, i, "고가")
                low  = self.CommGetData(TrCode, "", RQName, i, "저가")
                close  = self.CommGetData(TrCode, "", RQName, i, "현재가")
                volume  = self.CommGetData(TrCode, "", RQName, i, "거래량")

                self.ohlcv['date'].append(date)
                self.ohlcv['open'].append(int(open))
                self.ohlcv['high'].append(int(high))
                self.ohlcv['low'].append(int(low))
                self.ohlcv['close'].append(int(close))
                self.ohlcv['volume'].append(int(volume))

        if RQName == "opw00001_req":
            estimated_day2_deposit = self.CommGetData(TrCode, "", RQName, 0, "d+2추정예수금")
            estimated_day2_deposit = self.change_format(estimated_day2_deposit)
            self.data_opw00001 = estimated_day2_deposit

        if RQName == "opw00018_req":
            # Single Data
            single = []

            total_purchase_price = self.CommGetData(TrCode, "", RQName, 0, "총매입금액")
            total_purchase_price = self.change_format(total_purchase_price)
            single.append(total_purchase_price)

            total_eval_price = self.CommGetData(TrCode, "", RQName, 0, "총평가금액")
            total_eval_price = self.change_format(total_eval_price)
            single.append(total_eval_price)

            total_eval_profit_loss_price = self.CommGetData(TrCode, "", RQName, 0, "총평가손익금액")
            total_eval_profit_loss_price = self.change_format(total_eval_profit_loss_price)
            single.append(total_eval_profit_loss_price)

            total_earning_rate = self.CommGetData(TrCode, "", RQName, 0, "총수익률(%)")
            total_earning_rate = self.change_format(total_earning_rate, 1)
            single.append(total_earning_rate)

            estimated_deposit = self.CommGetData(TrCode, "", RQName, 0, "추정예탁자산")
            estimated_deposit = self.change_format(estimated_deposit)
            single.append(estimated_deposit)

            self.data_opw00018['single'] = single

            # Multi Data
            cnt = self.GetRepeatCnt(TrCode, RQName)
            for i in range(cnt):
                data = []

                item_name = self.CommGetData(TrCode, "", RQName, i, "종목명")
                data.append(item_name)

                quantity = self.CommGetData(TrCode, "", RQName, i, "보유수량")
                quantity = self.change_format(quantity)
                data.append(quantity)

                purchase_price = self.CommGetData(TrCode, "", RQName, i, "매입가")
                purchase_price = self.change_format(purchase_price)
                data.append(purchase_price)

                current_price = self.CommGetData(TrCode, "", RQName, i, "현재가")
                current_price = self.change_format(current_price)
                data.append(current_price)

                eval_profit_loss_price = self.CommGetData(TrCode, "", RQName, i, "평가손익")
                eval_profit_loss_price = self.change_format(eval_profit_loss_price)
                data.append(eval_profit_loss_price)

                earning_rate = self.CommGetData(TrCode, "", RQName, i, "수익률(%)")
                earning_rate = self.change_format(earning_rate, 2)
                data.append(earning_rate)

                self.data_opw00018['multi'].append(data)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFidList):
        print("sGubun: ", sGubun)
        print(self.GetChejanData(9203))
        print(self.GetChejanData(302))
        print(self.GetChejanData(900))
        print(self.GetChejanData(901))

    def GetRepeatCnt(self, sTrCode, sRecordName):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRecordName)
        return ret

    def GetCodeListByMarket(self, sMarket):
        cmd = 'GetCodeListByMarket("%s")' % sMarket
        ret = self.dynamicCall(cmd)
        item_codes = ret.split(';')
        return item_codes

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFidList):
        print(self.GetChejanData(9203))
        print(self.GetChejanData(302))
        print(self.GetChejanData(900))
        print(self.GetChejanData(901))

    def GetRepeatCnt(self, sTrCode, sRecordName):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRecordName)
        return ret

    def GetCodeListByMarket(self, sMarket):
        cmd = 'GetCodeListByMarket("%s")' % sMarket
        ret = self.dynamicCall(cmd)
        item_codes = ret.split(';')
        return item_codes[:-1]

    def GetMasterCodeName(self, strCode):
        cmd = 'GetMasterCodeName("%s")' % strCode
        ret = self.dynamicCall(cmd)
        return ret

    def GetConnectState(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def GetLoginInfo(self, sTag):
        cmd = 'GetLoginInfo("%s")' % sTag
        ret = self.dynamicCall(cmd)
        return ret


    def GetChejanData(self, nFid):
        cmd = 'GetChejanData("%s")' % nFid
        ret = self.dynamicCall(cmd)
        return ret

    def SendOrder(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        err_check = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo])
        return err_check

    def InitOHLCRawData(self):
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def InitOHLCRawData_minute(self):
        self.ohlcv_minute = {'time': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def change_format(self, data, percent=0):
        is_minus = False

        if data.startswith('-'):
            is_minus = True

        strip_str = data.lstrip('-0')

        if strip_str == '':
            if percent == 1:
                return '0.00'
            else:
                return '0'
        ## average ma20 ~ ma120
        if percent == 1:
            strip_data = int(strip_str)
            strip_data = strip_data / 100
            form = format(strip_data, ',.2f')
        elif percent == 2:
            strip_data = float(strip_str)
            form = format(strip_data, ',.2f')
        else:
            strip_data = int(strip_str)
            form = format(strip_data, ',d')

        if form.startswith('.'):
            form = '0' + form
        if is_minus:
            form = '-' + form

        return form

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Login
    kiwoom = Kiwoom()
    kiwoom.CommConnect()

    # opw00018
    kiwoom.init_opw00018_data()

    kiwoom.SetInputValue("계좌번호", "8080996211")
    kiwoom.SetInputValue("비밀번호", "0000")
    kiwoom.CommRqData("opw00018_req", "opw00018", 0, "2000")

    while kiwoom.prev_next == '2':
        time.sleep(0.5)
        kiwoom.SetInputValue("계좌번호", "8080996211")
        kiwoom.SetInputValue("비밀번호", "0000")
        kiwoom.CommRqData("opw00018_req", "opw00018", 2, "2000")

    print(kiwoom.data_opw00018['single'])
    print(kiwoom.data_opw00018['multi'])

'''

