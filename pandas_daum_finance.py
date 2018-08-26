import pandas as pd
import urllib.parse

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

    return df

kospi_stocks = download_stock_codes('kospi')
print(kospi_stocks.head())


## print(df.head())

## 외국인 연속 순매매 종목 가져오기 (지분변화율 상위 정렬)
DAUM_FOREIGNER_BUY_URL =   'http://finance.daum.net/quote/signal_foreign.daum?col=foreignrate_change&order=desc&stype=1&type=buy&gubun=F'
code_df = pd.read_html(DAUM_FOREIGNER_BUY_URL, header=0)[0]

## print(code_df.head())


