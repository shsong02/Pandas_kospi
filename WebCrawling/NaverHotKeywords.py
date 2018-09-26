import requests
from bs4 import BeautifulSoup

req = requests.get("https://naver.com") #connection
#req = requests.get("http://datalab.naver.com/keyword/realtimeList.naver?where=main")
html =  req.text # naver에서 소스를 받아오기

# BeautifulSoup로 html 소스를 python 객체로 변경할 수 있다.
#  첫 인자에는 html 소스코드를 가져온다. 두번째 인자에는 어떤 parser를 이용할지 정해준다.

#---------------------------------------------------------#
#python 내장 함수 html.parser
soup = BeautifulSoup(html, 'html.parser')
sillsigan = soup.select('div.ah_roll.PM_CL_realtimeKeyword_rolling_base > div > ul > li')

#PM_ID_ct > div.header > div.section_navbar > div.area_hotkeyword.PM_CL_realtimeKeyword_base > div.ah_list.PM_CL_realtimeKeyword_list_base

#sillsigan = soup.select('div.ah_roll.PM_CL_realtimeKeyword_rolling_base > div > ul > li')
# 실시간 검색어 부분 copy select
print(sillsigan)
b = []
for sill in sillsigan:
    b.append(sill.text) #tag내 문자열을 b리스트에 추가

k = 1;
list_sillsigan = []
print("="*30 + '\n' + ' '* 7 + "NAVER RANK LIST\n" + '='*30 )

for i in b : #문자열에서 핵심 문자열만 list_sillsigan 리스트에 추가
    if k > 9 :
        list_sillsigan.append(i[5: -2])
    else :
        list_sillsigan.append(i[4: -2])
    k += 1

for s, list in enumerate(list_sillsigan):
#eumerate를 이용하면 s는 갯수를 셀수 있고 list는 목록 요소에 접근이 가능하다.
    print("%d위" %(s+1)+list) # 출력하기