#-*- coding: utf-8 -*-


import pandas as pd
import urllib.parse
import plotly.offline as offline
import plotly.graph_objs as go
import plotly.plotly as py
from plotly import __version__
import matplotlib.pyplot as plt
import numpy as np

import pymysql
from sqlalchemy import create_engine

##########
## ./mysql -u root -p systrading
## show tables
## dtop table _tablename_
## desc _tablename_
## drop index unique_name on tablename
## alter table _name_ add unique key (cdate, mcode);
## select * from companyList limit 10;
## select * from companyList limit 10,20;

### Init
f = open("foreigner_buy_list.txt", "w", encoding='utf8')
f_log = open("systransing_log.txt", "w", encoding='utf8')



###  1) DB 생성
###  2) CompanyList Table 생성
###  3) KOSPI, KOSDAK 모든 종목을 table 에 삽입
###  4) 종목별, 날짜별 거래 내용 Table 생성
###  5) 날짜, 종가, 전일비, 시가, 저가, 거래량을 4) Table 에 삽입 하기
###  6) 공매도 관련 주가 정 4) Table 에 삽입 하기
###  7) 거래원별(외국인, 기관) 4) Table 에 삽입 하기
###  8) 거래원별(개인) 4) Table 에 삽입 하기 -- Kiwoom API
###  9) 5분봉 거래내역 Table 생성
### 10) 주요? 종목들의 5분봉 거래내역을 9) Table 에 삽입 하기 -- Kiwoom API
### 11) news & notification Table 생성
### 12) news & notification  11) Table 에 삽입 하기








### MySQL 접속
try:
    conn = pymysql.connect(host='localhost',
                    user = 'root',
                    password = 'songsong',
                    db='systrading',
                    charset = 'utf8mb4')
except:
    print("Can't connect to MySQL server. !! \n")




cur = conn.cursor()
## Database 생성
cur.execute("CREATE DATABASE IF NOT EXISTS systrading")
## 사용할 DB 지정
cur.execute("USE systrading")

## Table 생성
try:
    sql = '''CREATE TABLE IF NOT EXISTS companyList(
        id      INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, 
        mgroup  VARCHAR(20) NOT NULL, 
        mcode   INT(11) NOT NULL,  
        mname   VARCHAR(200) NOT NULL)
        '''
    cur.execute(sql)
except:
    print("transactionSummary Table 이 이미 DB 에 존재합니다.\n")



###  3) KOSPI, KOSDAK 모든 종목을 table 에 삽입
###  3-1) KOSPI & KOSDAK 종목 코드 받아오기
MARKET_CODE_DICT = {
    'kospi': 'stockMkt',
    'kosdaq': 'kosdaqMkt',
    'konex': 'konexMkt'
}

CODE_DOWNLOAD_URL = 'kind.krx.co.kr/corpgeneral/corpList.do'

def download_stock_codes(market=None, delisted=False):
    params = {'method': 'download'}

    if market.lower() in MARKET_CODE_DICT:
        params['marketType'] = MARKET_CODE_DICT[market]

    if not delisted:
        params['searchType'] = 13

    params_string = urllib.parse.urlencode(params)
    request_url = urllib.parse.urlunsplit(['http', CODE_DOWNLOAD_URL, '', params_string, ''])

    df = pd.read_html(request_url, header=0)[0]
    df.종목코드 = df.종목코드.map('{:06d}'.format)

    df = df[['회사명', '종목코드']]
    df['mgroup']=market
    df = df.rename(columns={'회사명': 'mname', '종목코드': 'mcode'})


    return df

kospi_stocks = download_stock_codes('kospi')
kosdaq_stocks = download_stock_codes('kosdaq')

print(kospi_stocks['mname'].head(5))
kospi_stocks['mname'] = kospi_stocks['mname'].str.replace(" ", "")
print(kospi_stocks['mname'].head(5))

###  3-2) KOSPI & KOSDAK 를 Database 에 저장하기

#engine = create_engine("mysql+pymysql://아이디:"+"암호"+"@mysql주소:포트/데이터베이스이름?charset=utf8", encoding='utf-8')
engine = create_engine("mysql+pymysql://root:"+"songsong"+"@localhost/systrading?charset=utf8", encoding='utf-8')

#if_exists='fail' 옵션이 있으면, 기존 테이블이 있을 경우, 아무일도 하지 않음
try:
    kospi_stocks.to_sql (name='companyList', con=engine, if_exists='append', index=False)
except:
    print("이미 companyList Table 에 kospi 종목을 추가하였습니다. \n ")

try:
    kosdaq_stocks.to_sql(name='companyList', con=engine, if_exists='append', index=False)
except:
    print("이미 companyList Table 에 kosdaq 종목을 추가하였습니다. \n ")



#####################################
###  4) 종목별, 날짜별 거래 내용 Table 생성
#####################################
## 4-1) Table 생성
try:
    sql = '''CREATE TABLE IF NOT EXISTS transactionSummary(
        id      INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, 
        mcode   INT(11) NOT NULL,  
        cdate    DATE NOT NULL, 
        ctime    TIME NOT NULL, 
        cdiff    INT(20),
        copen    INT(20),
        chigh    INT(20),
        clow     INT(20),
        cend     INT(20),
        cvolume  INT(20), 
        foreign_buy INT(20),
        foreign_shareholding FLOAT(20),
        instit_buy INT(20),
        instit_shareholding FLOAT(20),
        retail_buy INT(20),
        shrtselling_volume INT(20),
        shrtselling_volcount INT(20),
        shrtselling_buy INT(20),
        shrtselling_count INT(20))
        '''
    cur.execute(sql)
except:
    print("transactionSummary Table 이 이미 DB 에 존재합니다.\n")

### 4-2) 종목별 거래내용 크롤링

#### 종목명 --> 종목 코드로 변환
# 종목 이름을 입력하면 종목에 해당하는 코드를 불러와
# 네이버 금융(http://finance.naver.com)에 넣어줌
def save_db(item_code, code_df):
    ##code = code_df.query("mname=='{}'".format(item_name))['mcode'].to_string(index=False)
    url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=item_code)
    ##url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
    ##url = 'http://finance.daum.net/item/news.daum?code={code}'.format(code=code)

    #print("요청 URL = {}".format(url))
    # 일자 데이터를 담을 df라는 DataFrame 정의
    df = pd.DataFrame()

    # 1페이지에서 20페이지의 데이터만 가져오기
    for page in range(1, 43):
        pg_url = '{url}&page={page}'.format(url=url, page=page)
        df = df.append(pd.read_html(pg_url, header=0)[0], ignore_index=True)

    # df.dropna()를 이용해 결측값 있는 행 제거
    df = df.dropna()
    # 휴장일 날을 제거
    df = df[df['거래량'] != 0]

    # 한글로 된 컬럼명을 영어로 바꿔줌
    df = df.rename(columns= {'날짜': 'cdate', '종가': 'cclose',
                             '전일비': 'cdiff', '시가': 'copen', '고가': 'chigh', '저가': 'clow', '거래량': 'cvolume'})
    # 데이터의 타입을 int형으로 바꿔줌
    df[['cclose', 'cdiff', 'copen', 'chigh', 'clow', 'cvolume']] \
        = df[['cclose', 'cdiff', 'copen', 'chigh', 'clow', 'cvolume']].astype(int)

    # 컬럼명 'date'의 타입을 date로 바꿔줌
    df['cdate'] = pd.to_datetime(df['cdate'])

    # 일자(date)를 기준으로 오름차순 정렬
    df = df.sort_values(by=['cdate'], ascending=True)

    # code 삽입
    df['mcode']=item_code

    try:
        df.to_sql(name='transactionSummary', con=engine, if_exists='append', index=False)
    except :
        print ("%s 의 주가 정보는 이미 존재합니다. \n" %(item_code))
        f_log.write("%s 의 주가 정보는 이미 존재합니다. \n" %(item_code))

    return url, item_code
    #return url, code

## 종목코드를 전부 읽어서 주가 거래 내용을 DB 에 저장
sql = '''SELECT mcode FROM companyList WHERE mgroup='kospi' '''
## sql = '''SELECT mname FROM companyList WHERE mgroup='kospi' '''
cur.execute(sql)
rslt = cur.fetchall()

f_log.write("kospi 주가 정보를 DB에 저장합니다.\n")
for item_code in rslt:
    sql = 'SELECT * from companyList where mcode=%s'
    item_name = cur.execute(sql, 'item_code')
    f_log.write("%s 의 DB 입력을 시작합니다.\n" %item_name)
    url, mcode = save_db(item_code, kospi_stocks)



# 신라젠의 일자데이터 url 가져오기
#item_name = 'LG유플러스'   ### SSH (temp 18.09.27)


## sql = 'INSERT INTO transsactionSummary (cdate, cclose, cdiff, copen, chigh, clow, cvolume)
##         VALUES (%s, %s, %s, %s, %s, %s, %s) '
## cur.execute(sql, (item_name, ))


### 4-3) 거래내용을 DB에 저장


######################################
conn.close()
f.close()
f_log.close()
exit()


######################################################


## PART1
## 외국인 연속 순매매 종목 가져오기 (지분변화율 상위 정렬)
DAUM_FOREIGNER_BUY_URL =  [
    'http://finance.daum.net/quote/signal_foreign.daum?col=foreignrate_change&order=desc&stype=1&type=buy&gubun=F',
    'http://finance.daum.net/quote/signal_foreign.daum?stype=1&type=buy&col=foreignrate_change&order=desc&gubun=F&page=2',
    'http://finance.daum.net/quote/signal_foreign.daum?stype=1&type=buy&col=foreignrate_change&order=desc&gubun=F&page=3',
    'http://finance.daum.net/quote/signal_foreign.daum?stype=1&type=buy&col=foreignrate_change&order=desc&gubun=F&page=4',
    'http://finance.daum.net/quote/signal_foreign.daum?stype=1&type=buy&col=foreignrate_change&order=desc&gubun=F&page=5',
    'http://finance.daum.net/quote/signal_foreign.daum?stype=1&type=buy&col=foreignrate_change&order=desc&gubun=F&page=6'
]

df1 = pd.read_html(DAUM_FOREIGNER_BUY_URL[0], header=0)[0]
df2 = pd.read_html(DAUM_FOREIGNER_BUY_URL[1], header=0)[0]
df3 = pd.read_html(DAUM_FOREIGNER_BUY_URL[2], header=0)[0]
df4 = pd.read_html(DAUM_FOREIGNER_BUY_URL[3], header=0)[0]
df5 = pd.read_html(DAUM_FOREIGNER_BUY_URL[4], header=0)[0]
df6 = pd.read_html(DAUM_FOREIGNER_BUY_URL[5], header=0)[0]

df = pd.concat([df1,df2,df3,df4,df5,df6], ignore_index=True)


#foreignerBuy_df.to_csv(f, sep='|')
#np.savetxt(f, foreignerBuy_df.종목명,fmt='%s')


# print(df.head())  ### 처음 5줄
print(df)
# print(df.index) ### Table size
exit()





## PART 증가 추세인지 확인

##ma5 = df['종가'].rolling(window=5).mean()
##print(ma5.head(10))

##print(df.head(100))



# jupyter notebook 에서 출력
#offline.init_notebook_mode()
#offline.init_notebook_mode(connected=True)

trace = go.Scatter(x=df.date, y=df.close, name=item_name)
data = [trace]

# data = [celltrion]
layout = dict( title='{}의 종가(close) Time Series'.format(item_name),
               xaxis=dict(
                   rangeselector=dict(
                       buttons=list([
                           dict(count=1,
                                label='1m',
                                step='month',
                                stepmode='backward'),
                           dict(count=3,
                                label='3m',
                                step='month',
                                stepmode='backward'),
                           dict(count=6,
                                label='6m',
                                step='month',
                                stepmode='backward'),
                           dict(step='all')
                       ])
                   ),
                   rangeslider=dict(),
                   type='date'
               )
               )


fig =go.Figure(data=data, layout=layout)
plt.plot(df['close'])
plt.show()

##offline.iplot(fig)

fig = py.get_figure('https://plot.ly/~jackp/8715', raw=True)
offline.iplot(fig)


