from bs4 import BeautifulSoup
import urllib.request


## URL = "http://short.krx.co.kr/contents/SRT/02/02010100/SRT02010100.jsp"
URL = "http://short.krx.co.kr/contents/SRT/02/02010100/SRT02010100.jsp"


html = urllib.request.urlopen(URL)
soup = BeautifulSoup(html, 'html.parser')
#print(soup.prettify())

f_log = open("crawling_test.txt", "w", encoding='utf8')

f_log.write(soup.prettify())

f_log.close()
