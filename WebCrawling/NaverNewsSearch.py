#-*- coding:utf-8 -*-


from bs4 import BeautifulSoup
import urllib.request

# File name
OUTPUT_FILE_NAME = 'output.txt'
#  URL
##URL = 'http://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=103&oid=055&aid=0000445667'
URL = 'https://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20'

## Crawling
def get_text(URL):
    source_code_from_URL = urllib.request.urlopen(URL)
    soup = BeautifulSoup(source_code_from_URL, 'lxml', from_encoding='utf-8')
    text = ''
    for item in soup.find_all('div', id='articleBodyContents'):
        text = text + str(item.find_all(text=True))
    return text


# Main
def main():
    f = open(OUTPUT_FILE_NAME, 'w')
    result_text = get_text(URL)
    f.write(result_text)
    f.close()


if __name__ == '__main__':
    main()

