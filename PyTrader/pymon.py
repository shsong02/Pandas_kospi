#-*-coding: utf-8 -*-
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QAxContainer import *
import Kiwoom
import pandas as pd
import datetime
import time
import webreader
import numpy




file_path = "D:\Gdrive\python\PyTrader_note\_results"
MARKET_KOSPI   = 0
MARKET_KOSDAK  = 10

class PyMon:
    def __init__(self) -> object:
        self.kiwoom = Kiwoom.Kiwoom()
        self.kiwoom.CommConnect()
        self.get_code_list()

    def get_code_list(self):
        self.kospi_codes = self.kiwoom.GetCodeListByMarket(MARKET_KOSPI)
        self.kosdak_codes = self.kiwoom.GetCodeListByMarket(MARKET_KOSDAK)

    def get_ohlcv(self, code, start_date):
        # Init data structure
        self.kiwoom.InitOHLCRawData()

        # Request TR and get data
        self.kiwoom.SetInputValue("종목코드", code)
        self.kiwoom.SetInputValue("기준일자", start_date)
        self.kiwoom.SetInputValue("수정주가구분", 1)
        self.kiwoom.CommRqData("opt10081_req", "opt10081", 0, "0101")
        time.sleep(0.5)

        # DataFrame
        df = pd.DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                          index=self.kiwoom.ohlcv['date'])
        return df

    def get_ohlcv_minute(self, code, start_date):
        # Init data structure
        self.kiwoom.InitOHLCRawData_minute()

        # Request TR and get data
        self.kiwoom.SetInputValue("종목코드", code)
        self.kiwoom.SetInputValue("틱범위", 15)
        self.kiwoom.SetInputValue("수정주가구분", 1)
        self.kiwoom.CommRqData("opt10080_req", "opt10080", 0, "0101")
        time.sleep(0.5)

        # DataFrame
        df = pd.DataFrame(self.kiwoom.ohlcv_minute, columns=['open', 'high', 'low', 'close', 'volume'],
                          index=self.kiwoom.ohlcv_minute['time'])
        return df

    def check_speedy_rising_volumn(self, code, test_f, search_box_f):
        today = datetime.datetime.today().strftime("%Y%m%d")
        df = self.get_ohlcv(code, today)
        volumes = df['volume']
        c_values = df['close']
        low_values = df['low']
        high_values = df['high']
        st_values = df['open']
        sum_vol20 = 0
        avg_vol20 = 0

        df_minute = self.get_ohlcv_minute(code, today)
        volumes_minute     = df_minute['volume']
        c_values_minute    = df_minute['close']
        low_values_minute  = df_minute['low']
        high_values_minute = df_minute['high']
        st_values_minute    = df_minute['open']

        # Check small trading days
        if len(volumes) < 21:
            return False


       ####  Algorithm 0 : Search Boxing Period  ###
        # A -- 거래량 비율: 20봉 평균 거래량(어제까지) 대비 동일 주기 0봉 전 250% 이상
        # B -- 주가 비교: [일] 1봉 전 시가 < 0봉 전 종가
        # C -- 주가 범위: 0일 전 종가가 2,000 이상 2,000,000 이하
        # D -- 신고가: [일] 0봉 전 고가가 60봉 신고가에 -5% 이내 근접
        # E -- 신고가: [일] 1봉 전 종가각 60봉 중 신고가 (면 제외)
        # F -- 5일 평균 거래 대금(단위:100만) 5,000 이상, 1,000,000 이하(금일 포함)
        # G -- 외국인 지분율 3% 이상 100.0% 이하
        # H -- 0봉 전 2일 중 1일 외국인 순매수 발생 최소 순매 매수량 1주
        # I -- 0봉 전 2일 중 1일 기관 순매수 발생 최소 순매 매수량 1


        BOX_TIME = 60  ## ( dates > 20 )
        BOX_RATIO = 0.05  ## min/max from avg
        BOX_PREC = 10 ## 0% ~ 20%
        BOX_TAR_VOL = 200 # unit: %

        # Check Volumes
        sum_volX = 0
        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
                check_vol = vol
            elif i >= 1 and i < 21:
                sum_vol20 += vol
            elif i >= 21 and i < BOX_TIME  :
                sum_volX += vol
            elif i >= BOX_TIME:
                break

        avg_vol20 = (sum_vol20) / 20
        avg_volXX = (sum_vol20 + today_vol + sum_volX) / BOX_TIME
        if avg_vol20 * BOX_TAR_VOL/100 < today_vol :
            CheckA = 'O'
        else :
            CheckA = 'X'

        if c_values[0] > st_values[0] :
            CheckB = 'O'
        else :
            CheckB = 'X'
        if 2000 < c_values[0] < 2000000 :
            CheckC = 'O'
        else :
            CheckC = 'X'
        for i, c_value in enumerate(c_values) :
            if i == 0 :
                max_value = 0
            elif i >= 1 and i < 61 :
                if max_value < c_value :
                    max_value_date = i
                    max_value = c_value
            else :
                break
        if (max_value_date != 1) & (c_values[0]> max_value*0.95) :
            CheckDE = 'O'
        else :
            CheckDE = 'X'
        avg5_trade_size = 0
        for i in range(5):
            avg5_trade_size += c_values[i]*volumes[i]
        avg5_trade_size = avg5_trade_size / 5
        if(5000 * 1000000 < avg5_trade_size < 1000000*1000000) :
            CheckF = 'O'
        else:
            CheckF = 'X'

        CheckG = 'X'
        CheckH = 'X'
        self.kiwoom.SetInputValue("종목코드", code)
        self.kiwoom.CommRqData("opt10008_req", "opt10008", 0, "0101")
        time.sleep(0.5)
        cnt = self.kiwoom.GetRepeatCnt("opt10008", "opt10008_req")
        for i in range(cnt):
            bijoong = self.kiwoom.CommGetData("opt10008", "", "opt10008_req", i, "비중")

        CheckI = 5

        if (CheckA =='O')&(CheckB=='O')&(CheckC=='O')&(CheckDE=='O')&(CheckF=='O') :
            buy_st_rslt0 = 'ok_rslt0'
        else :
            buy_st_rslt0 = '........'

        if (buy_st_rslt0=='ok_rslt0')&(CheckG=='O')&(CheckH=='O')&(CheckI > 2):
            buy_st_rslt1 = 'ok_rslt1'
        else :
            buy_st_rslt1 = '........'

        search_box_f.writelines(" code:%s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n"
                                %(code, CheckA, CheckB, CheckC, CheckDE, CheckDE, CheckF, CheckG, CheckH, CheckI, buy_st_rslt0, buy_st_rslt1))


       ####  Algorithm 1 : 눌림목 매매  ###
       # A -- 5일 평균 거래 대금 (단위 100만) 1,000 이상 10,000,000 이하 (금일제외)
       # B -- 주가 이평 추세: [일] 0봉 전(종가20) 이평 상승+보합 추세 유지 1회 이상
       # C -- 주가 비교: [일] 1봉 전 저가 <= 0봉 전 저가
       # D -- 주가 이평 추세: [1분] 0봉 전(종가 20)이평 상승+보합 추세 유지 1회 이상
       # E -- 가격-이동평균비교: [일] 0봉 전(종가 3) 이평 >= 종가
       # F -- 가격-이동평균비고: [일] 0봉 전(종가 5) 이평 >= 종가
       # G -- 주가 이평 추세: [일] 0봉 전(종가 5) 이평 하락 추세 유지 1회 이상
       # H -- 주가 이평 추세: [일] 0봉 전(종가 3) 이평 하락 추세 유지 1회 이상

        A1_CheckA = CheckF
        A1_CheckB = 0
        A1_CheckC = 0
        A1_CheckD = 0
        A1_CheckE = 0
        A1_CheckF = 0
        A1_CheckG = 0
        A1_CheckH = 0

        ma20 = ma60 = ma120 = 0
        ma3 = ma5 =0
        ma20_m5d_0 = 0
        ma20_m5d_1 = 0
        ma3_m1d = ma5_m1d = 0
        for i, c_value in enumerate(c_values) :
            if i == 0 :
                today_c_value = c_value
            if i >= 1 and i < 21 :
                ma20 += c_value
                if 2 <= i < 5 :
                    ma3_m1d += c_value
                if 2<= i < 7 :
                    ma5_m1d += c_value
                if i < 4 :
                    ma3 += c_value
                if i < 6 :
                    ma5 += c_value
                #  if c_value < A1_CheckB_tmp :
                if i>= 5 :
                    ma20_m5d_0 += c_value
            elif i >= 21 and i<61 :
                ma60 += c_value
                if i <25 :
                    ma20_m5d_1 += c_value
            elif i >=60 and i<121 :
                ma120 += c_value
            elif i >= 121 :
                break

        ma3 = int(ma3 / 3); ma3_m1d = int(ma3_m1d/3)
        ma5 = int(ma5 / 5); ma5_m1d = int(ma5_m1d/5)
        ma120   = int((ma120 + ma60 + ma20)/120)
        ma60    = int((ma60+ma20)/60)
        ma20    = int(ma20/20)
        ma20_m5d = int((ma20_m5d_0+ma20_m5d_1)/20)


        if (ma20 - ma20_m5d) > 0 :              A1_CheckB = 'O'
        else :                                  A1_CheckB = 'X'

        if low_values[1] <= low_values[0] :     A1_CheckC = 'O'
        else :                                  A1_CheckC = 'X'

        ma20_minute = ma60_minute = ma120_minute = 0
        ma3_minute = ma5_minute =0
        ma20_m5d_0_minute = 0
        ma20_m5d_1_minute = 0
        for i, c_value in enumerate(c_values_minute) :
            if i == 0 :                         today_c_value_minute = c_value
            if i >= 1 and i < 21 :
                ma20_minute += c_value
                if i < 4 :                      ma3_minute += c_value
                if i < 6 :                      ma5_minute += c_value
                if i>= 5 :                      ma20_m5d_0_minute += c_value
            elif i >= 21 and i<61 :
                ma60_minute += c_value
                if i <25 :                      ma20_m5d_1_minute += c_value
            elif i >=60 and i<121 :            ma120_minute += c_value
            elif i >= 121 :                     break
        ma3_minute = int(ma3_minute / 3)
        ma5_minute = int(ma5_minute / 5)
        ma120_minute   = int((ma120_minute + ma60_minute + ma20_minute)/120)
        ma60_minute    = int((ma60_minute+ma20_minute)/60)
        ma20_minute    = int(ma20_minute/20)
        ma20_m5d_minute = int((ma20_m5d_0_minute+ma20_m5d_1_minute)/20)

        if (ma20_minute - ma20_m5d_minute) > 0 :            A1_CheckD = 'O'
        else :                                              A1_CheckD = 'X'
        if ma3 >= today_c_value :                           A1_CheckE = 'O'
        else:                                               A1_CheckE = 'X'
        if ma5 >= today_c_value :                           A1_CheckF = 'O'
        else:                                               A1_CheckF = 'X'
        if ma3 <= ma3_m1d :                                 A1_CheckG = 'O' # down-direction
        else:                                               A1_CheckG = 'X'
        if ma5 <= ma5_m1d :                                 A1_CheckH = 'O' # down-direction
        else:                                               A1_CheckH = 'X'

        if (A1_CheckA =='O')&(A1_CheckB=='O')&(A1_CheckC=='O')&(A1_CheckE=='O')&(A1_CheckF=='O') &(A1_CheckG=='O')&(A1_CheckH=='O'):
            a1_buy_st_rslt0 = 'ok_rslt0'
        else :
            a1_buy_st_rslt0 = '........'
        if (A1_CheckA =='O')&(A1_CheckB=='O')&(A1_CheckC=='O')&(A1_CheckD=='O')&(A1_CheckE=='O')&(A1_CheckF=='O') &(A1_CheckG=='O')&(A1_CheckH=='O'):
            a1_buy_st_rslt1 = 'ok_rslt1'
        else :
            a1_buy_st_rslt1 = '........'

        #if (a1_buy_st_rslt0=='ok_rslt0')&(A1_CheckG=='O')&(A1_CheckH=='O'):
        #    a1_buy_st_rslt1 = 'ok_rslt1'
        #else :
        #    a1_buy_st_rslt1 = '........'

        test_f.writelines(" code:%s | %s | %s | %s | %s | %s | %s | %s | %s || %s | %s |\n"
                                %(code, A1_CheckA, A1_CheckB, A1_CheckC, A1_CheckD, A1_CheckE, A1_CheckF, A1_CheckG, A1_CheckH, a1_buy_st_rslt0 , a1_buy_st_rslt1))






        c_value_list20 = [0]*BOX_TIME
        for i, c_value in enumerate(c_values) :
            if i >= 0 and i < BOX_TIME:
                c_value_list20[i] = c_value
            else :
                break
        ## Search BOX case
        value_avg = numpy.mean(c_value_list20)
        value_std = numpy.std(c_value_list20)
        value_dev_h = value_avg * (1+BOX_RATIO)
        value_dev_l = value_avg * (1-BOX_RATIO)

        box_error =0
        for i, c_value in enumerate(c_value_list20):
            if value_dev_l > c_value or c_value > value_dev_h :
                box_error += 1



        ##box_vol_chk = value_avg * avg_volXX
        ##if((ma20 - ma20_m5d)>0) & (box_vol_chk > BOX_TAR_VOL) :
        ##    if (box_error <= (BOX_TIME * BOX_PREC / 100) ) :
        ##       search_box_f.writelines("[code: %s] O.K. Boxing period (Avg:%d, min:%d, max:%d, Non-match:%d Day \n"
        ##                               %(code, value_avg,value_dev_l,value_dev_h,box_error))






        c_value_list20 = [0]*BOX_TIME
        for i, c_value in enumerate(c_values) :
            if i >= 0 and i < BOX_TIME:
                c_value_list20[i] = c_value
            else :
                break
        ## Search BOX case
        value_avg = numpy.mean(c_value_list20)
        value_std = numpy.std(c_value_list20)
        value_dev_h = value_avg * (1+BOX_RATIO)
        value_dev_l = value_avg * (1-BOX_RATIO)

        box_error =0
        for i, c_value in enumerate(c_value_list20):
            if value_dev_l > c_value or c_value > value_dev_h :
                box_error += 1



        ##box_vol_chk = value_avg * avg_volXX
        ##if((ma20 - ma20_m5d)>0) & (box_vol_chk > BOX_TAR_VOL) :
        ##    if (box_error <= (BOX_TIME * BOX_PREC / 100) ) :
        ##       search_box_f.writelines("[code: %s] O.K. Boxing period (Avg:%d, min:%d, max:%d, Non-match:%d Day \n"
        ##                               %(code, value_avg,value_dev_l,value_dev_h,box_error))
        ##   else :
        ##       search_box_f.writelines("[code: %s] \n" %(code))



        ####  Algorithm 1 : Search double points of Trading numbers   ###
        for i, c_value in enumerate(c_values) :
            if i == 0 :
                today_c_value = c_value
                date_c_value = i
            elif i >= 1 and i <= 20:
                if (today_c_value < c_value) :
                    date_c_value = i
            elif i >= 21 :
                break


        #if ma60 < ma120 :
        #    test_f.writelines("[code: %s] Not rising_chart(case1) (ma60-ma120=%d)...\n" %(code, date_c_value))
        #    return False
        #else :
        #    if date_c_value != 0 :
        #        test_f.writelines("[code: %s] Not rising_chart(case2) (highest : D-%d)...\n" %(code, date_c_value))
        #        return False
        #    else :
        #        if today_vol > avg_vol20 * 10:
        #            test_f.writelines("[code: %s] volume=%d --> 1000^%% rising\n" %(code, check_vol))
        #            return True
        #        elif today_vol > avg_vol20 * 5 :
        #            test_f.writelines("[code: %s] volume=%d --> 500%% rising\n" %(code, check_vol))
        #            return True
        #        elif today_vol > avg_vol20 * 3 :
        #            test_f.writelines("[code: %s] volume=%d --> 300%% rising\n" %(code, check_vol))
        #            return True
        #        elif today_vol > avg_vol20 * 2 :
        #            test_f.writelines("[code: %s] volume=%d --> 200%% rising\n" %(code, check_vol))
        #            return True
        #        else:
        #            return False

    def update_buy_list(self, buy_list):
        f = open("%s\\buy_list.txt" % (file_path), 'wt')
        for code in buy_list:
            f.writelines("매수;%s;시장가;10;0;매수전\n" % (code))
        f.close()

    def run(self):
        #test_cnt=0
        today = datetime.datetime.today().strftime("%Y%m%d")
        buy_list = []
        test_f = open("%s\check_high_rising_%s.txt" %(file_path, today), "wt")
        search_box_f = open("%s\search_box_code_%s.txt" %(file_path, today), "wt")

        search_box_f.writelines("<검색방법>\n 종목코드 | A | B | C | D | E | F | G | H | I | 결과1 | 결과2 |\n")

        test_f.writelines("Search kospi: \n")
        search_box_f.writelines("Search kospi: \n")

        for code in self.kospi_codes:
            #test_f.writelines("kospi code: %s\n" %(code))
            #search_box_f.writelines("kospi code: %s\n" %(code))

            if self.check_speedy_rising_volumn(code, test_f, search_box_f):
                #print("급등주: ", code)
                buy_list.append(code)

        test_f.writelines("Search kosdak: \n")
        search_box_f.writelines("Search kosdak: \n")
        for code in self.kosdak_codes:
            #test_f.writelines("kosdak code: %s\n" %(code))
            #search_box_f.writelines("kosdak code: %s\n" %(code))

            if self.check_speedy_rising_volumn(code, test_f, search_box_f):
                #print("급등주: ", code)
                buy_list.append(code)

        ### Do not update kosdak codes (16.10.15)
        #self.update_buy_list(buy_list)
        test_f.close()
        search_box_f.close()
    def calculate_estimated_dividend_to_treasury(self, code):
        estimated_dividend_yield = float(webreader.get_estimated_dividend_yield(code))
        current_3year_treasury = float(webreader.get_current_3year_treasury())
        estimated_dividend_to_treasury = estimated_dividend_yield / current_3year_treasury
        return estimated_dividend_to_treasury

    def get_min_max_dividend_to_treasury(self, code):
        previous_dividend_yield = webreader.get_previous_dividend_yield(code)
        three_years_treasury = webreader.get_3year_treasury()

        now = datetime.datetime.now()
        cur_year = now.year
        previous_dividend_to_treasury = {}

        for year in range(cur_year-5, cur_year):
            if year in previous_dividend_yield.keys() and year in three_years_treasury.keys():
                ratio = float(previous_dividend_yield[year]) / float(three_years_treasury[year])
                previous_dividend_to_treasury[year] = ratio

        print(previous_dividend_to_treasury)
        min_ratio = min(previous_dividend_to_treasury.values())
        max_ratio = max(previous_dividend_to_treasury.values())

        return (min_ratio, max_ratio)

    def check_dividend_algorithm(self, code):
        estimated_dividend_to_treasury = self.calculate_estimated_dividend_to_treasury(code)
        (min_ratio, max_ratio) = self.get_min_max_dividend_to_treasury(code)

        if estimated_dividend_to_treasury >= max_ratio:
            return (1, estimated_dividend_to_treasury)
        elif estimated_dividend_to_treasury <= min_ratio:
            return (-1, estimated_dividend_to_treasury)
        else:
            return (0, estimated_dividend_to_treasury)

    def run_dividend(self):
        buy_list = []

        for code in self.kospi_codes:
            ret = self.check_dividend_algorithm(code)
            if ret[0] == 1:
                buy_list.append((code, ret[1]))

        for code in self.kosdak_codes:
            ret = self.check_dividend_algorithm(code)
            if ret[0] == 1:
                buy_list.append((code, ret[1]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pymon = PyMon()
    pymon.run()
    #print(pymon.calculate_estimated_dividend_to_treasury('058470'))
    #print(pymon.get_min_max_dividend_to_treasury('058470'))
