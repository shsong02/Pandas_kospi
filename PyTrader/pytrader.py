#-*-coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *

import datetime
import time


##  트 기 ㅣ기보트스
file_path = "G:\gdrive\python\PyTrader"
form_class = uic.loadUiType("pytrader.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.trade_stocks_done = False


        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        self.timer = QTimer(self)
        self.timer.start(1000) ## 1000 ms 마다 시작
        self.timer.timeout.connect(self.timeout)  ## timer 가 timeout 되면 -> 이를 처리할 슬롯 : timeout func

        ## code 를 보고 종목명 표시
        self.lineEdit.textChanged.connect(self.code_changed)

        ## 계좌번호 표시 (여러개는 ; 로 구분)
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        ## [현금주문] 버튼을 클릭하면 매수 실행
        self.pushButton.clicked.connect(self.send_order)

        ## 보유 종목 table  에 값 입력
        self.pushButton_2.clicked.connect(self.check_balance)

        # Timer2
        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)

        ##buy(sell)_list.txt 에서 종목 리스트 불러옴
        ## 자동 선정 종목 리스트 (테이블) 에 리스트 표시
        self.load_buy_sell_list()

        # bus(sell)_list.txt 에서 종목을 읽어서 실제 거래 진행







    ##########################################################

    # bus(sell)_list.txt 에서 종목을 읽어서 실제 거래 진행
    def trade_stocks(self):
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        # account
        account = self.comboBox.currentText()

        # buy list
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price,
                                       hoga_lookup[hoga], "")

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price,
                                       hoga_lookup[hoga], "")

        # buy list
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # file update
        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = open("sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    ##buy(sell)_list.txt 에서 종목 리스트 불러옴
    def load_buy_sell_list(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_4.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(len(buy_list) + j, i, item)

        self.tableWidget_4.resizeRowsToContents()

    ## 실제 조회 체크박슬 표시 시,
    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    ## 보요 종목을 확인하기 위한 "조회" 버튼 클릭 시..
    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()




    def timeout(self):
        market_start_time = QTime(9,10,0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True


        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusBar().showMessage(state_msg + " | " + time_msg)

    ## 종목(텍스트 박스) 에 입력한 code  를 보고 종목명 표시
    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    ## Kiwoom 의 send_order (매수 과정 3 단계 진행) 를 실행 시키기 위한 준비 작업
    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga], "")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()


'''
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()

        # Timer
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        # Timer2
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        # Get Account Number
        accouns_num = int(self.kiwoom.GetLoginInfo("ACCOUNT_CNT"))
        accounts = self.kiwoom.GetLoginInfo("ACCNO") ## .rstrip(";")
        ## kiwoom.SetInputValue("계좌번호", accounts)
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        self.lineEdit.textChanged.connect(self.code_changed)
        self.pushButton.clicked.connect(self.send_order)
        self.pushButton_2.clicked.connect(self.check_balance)


        today = datetime.datetime.today().strftime("%Y%m%d")
        now = time.localtime()
        now_s = "%04d%02d%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        f_trace = open("%s\pytrader_exec_trace_%s.txt" %(file_path, today), "wt")
        self.conduct_buy_sell(f_trace, now_s)
        self.load_buy_sell_list()

    def conduct_buy_sell(self,f_trace, now_s):
        hoga_lookup = {'지정가': "00", '시장가': "03"}
        error_lookup = {
          0  : 'OP_ERR_NONE'                  ## "정상처리"
        ,100 :'OP_ERR_LOGIN'                ## "사용자정보교환에 실패하였습니다. 잠시후 다시 시작하여 주십시오."
        ,101 :'OP_ERR_CONNECT'              ## "서버 접속 실패"
        ,102 :'OP_ERR_VERSION'              ## "버전처리가 실패하였습니다.
        ,200 : 'OP_ERR_SISE_OVERFLOW'       ##”시세조회과부하”
        ,201 : 'OP_ERR_RQ_STRUCT_FAIL'      ##”REQUEST_INPUT_st Failed”
        ,202 : 'OP_ERR_RQ_STRING_FAIL'      ##”요청전문작성실패”
        ,300 : 'OP_ERR_ORD_WRONG_INPUT'     ##”주문입력값 오류”
        ,301 : 'OP_ERR_ORD_WRONG_ACCNO'     ##”계좌비밀번호를 입력하십시오.”
        ,302 : 'OP_ERR_OTHER_ACC_USE'       ##”타인계좌는 사용할 수 없습니다.
        ,303 : 'OP_ERR_MIS_2BILL_EXC'       ##”주문가격이 20 억원을 초과합니다.”
        ,304 : 'OP_ERR_MIS_5BILL_EXC'       ##”주문가격은 50 억원을 초과할 수 없습니다.”
        ,305 : 'OP_ERR_MIS_1PER_EXC'        ##”주문수량이 총발행주수의 1 % 를 초과합니다.”
        ,306 : 'OP_ERR_MID_3PER_EXC'        ##”주문수량은 총발행주수의 3 % 를 초과할 수 없습니다.”

        }




        f = open("%s\\buy_list.txt" %(file_path), 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("%s\sell_list.txt" %(file_path), 'rt')
        sell_list = f.readlines()
        f.close()

        account = self.comboBox.currentText()

        # buy list
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga    = split_row_data[2]
            code    = split_row_data[1]
            num     = split_row_data[3]
            price   = split_row_data[4]

            f_trace.writelines("[%s] Start Buy....\n" %(now_s))
            if split_row_data[-1].rstrip() == '매수전':
                f_trace.writelines("[%s]\t(buy) account=%s, code=%s, num=%s, price=%s, hoga=%s\n" %(now_s, account, code, num, price, hoga))

                err_chk = self.kiwoom.SendOrder("SendOrder_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")
                f_trace.writelines("[%s]\t(buy) account=%s, code=%s, num=%s, price=%s, hoga=%s\n" %(now_s, account, code, num, price, hoga))
                #f_trace.writelines("Sendorder result : err_value -> %s\n" %(err_chk))
                if (err_chk in error_lookup) :
                    f_trace.writelines("Sendorder result : err_value -> %s,\t\t err_type -> %s\n" %(err_chk, error_lookup[err_chk]))
                else :
                    f_trace.writelines("Sendorder result : err_value -> %s, \"no_error_type\" \n" %(err_chk))

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga    = split_row_data[2]
            code    = split_row_data[1]
            num     = split_row_data[3]
            price   = split_row_data[4]
            f_trace.writelines("[%s] Start Sell....\n" %(now_s))
            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.SendOrder("SendOrder_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")
                f_trace.writelines("[%s]\t (sell) account=%s, code=%s, num=%s, price=%s, hoga=%s\n" %(now_s, account, code, num, price, hoga))
        # buy list
        for i, row_data in enumerate(buy_list):
             buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # file update
        f = open("%s\\buy_list.txt" %(file_path), 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
             sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = open("%s\sell_list.txt" %(file_path), 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    def load_buy_sell_list(self):
        f = open("%s\\buy_list.txt" %(file_path), 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("%s\sell_list.txt" %(file_path), 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_4.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            for i in range(len(split_row_data)):
                if i == 1:
                    name = self.kiwoom.GetMasterCodeName(split_row_data[i].rstrip())
                    item = QTableWidgetItem(name)
                else:
                    item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            for i in range(len(split_row_data)):
                if i == 1:
                    name = self.kiwoom.GetMasterCodeName(split_row_data[i].rstrip())
                    item = QTableWidgetItem(name)
                else:
                    item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(len(buy_list) + j, i, item)

        self.tableWidget_4.resizeRowsToContents()

    def timeout2(self):
        if self.checkBox.isChecked() == True:
            self.check_balance()

    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def code_changed(self):
        code = self.lineEdit.text()
        code_name = self.kiwoom.GetMasterCodeName(code)
        self.lineEdit_2.setText(code_name)

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.SendOrder("SendOrder_req", "0101", account, order_type_lookup[order_type], code, num, price, hoga_lookup[hoga], "")

    def check_balance(self):
        self.kiwoom.init_opw00018_data()

        # Request opw00018
        self.kiwoom.SetInputValue("계좌번호", "8082978711")
        self.kiwoom.SetInputValue("비밀번호", "5054")
        self.kiwoom.CommRqData("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.prev_next == '2':
            time.sleep(0.2)
            self.kiwoom.SetInputValue("계좌번호", "8082978711")
            self.kiwoom.SetInputValue("비밀번호", "5054")
            self.kiwoom.CommRqData("opw00018_req", "opw00018", 2, "2000")

        # Request opw00001
        self.kiwoom.SetInputValue("계좌번호", "8082978711")
        self.kiwoom.SetInputValue("비밀번호", "5054")
        self.kiwoom.CommRqData("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.data_opw00001)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.data_opw00018['single'][i-1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.data_opw00018['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.data_opw00018['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
'''