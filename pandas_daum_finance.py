import pandas as pd
import urllib.parse


## 외국인 연속 순매매 종목 가져오기 (지분변화율 상위 정렬)
DAUM_FOREIGNER_BUY_URL =   'http://finance.daum.net/quote/signal_foreign.daum?col=foreignrate_change&order=desc&stype=1&type=buy&gubun=F'
foreignerBuy_df = pd.read_html(DAUM_FOREIGNER_BUY_URL, header=0)[0]



#### 코스피 & 코스닥의 종목 코드 받아오기
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
    df = df.rename(columns={'회사명': 'name', '종목코드': 'code'})

    return df

kospi_stocks = download_stock_codes('kospi')
kosdaq_stocks = download_stock_codes('kosdaq')


#### 종목명 --> 종목 코드로 변환
# 종목 이름을 입력하면 종목에 해당하는 코드를 불러와
# 네이버 금융(http://finance.naver.com)에 넣어줌
def get_url(item_name, code_df):
    code = code_df.query("name=='{}'".format(item_name))['code'].to_string(index=False)
    url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)

    print("요청 URL = {}".format(url))
    return url


# 신라젠의 일자데이터 url 가져오기
item_name = 'LG유플러스'
url = get_url(item_name, kospi_stocks)

# 일자 데이터를 담을 df라는 DataFrame 정의
df = pd.DataFrame()

# 1페이지에서 20페이지의 데이터만 가져오기
for page in range(1, 80):
    pg_url = '{url}&page={page}'.format(url=url, page=page)
    df = df.append(pd.read_html(pg_url, header=0)[0], ignore_index=True)

# df.dropna()를 이용해 결측값 있는 행 제거
df = df.dropna()

# 상위 5개 데이터 확인하기
df.head()

print(df.head())





