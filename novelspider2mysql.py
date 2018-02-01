# encoding:utf-8
from bs4 import BeautifulSoup
import requests
import re
import pymysql
from multiprocessing import Pool

class Sql():

    def addnovel(self, sort, name, imageurl, author, description):
        db = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             database="novelspider",
                             port=3306,
                             charset='utf8')
        cur = db.cursor()
        try:
            cur.execute("insert into novel(sort, name, imageurl,author, description) "
                        "values('%s','%s','%s','%s','%s')"
                        % (sort, name, imageurl, author, description))  # 执行sql语句
            db.commit()
        except:
            db.rollback()
        cur.close()
        db.close()

    def addchapter(self, novelname, title, content, url):
        db = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             database="novelspider",
                             port=3306,
                             charset='utf8')
        cur = db.cursor()
        try:
            cur.execute("insert into chapter(novelname, title, content,url)"
                        "values('%s', '%s', '%s','%s')"
                        % (novelname, title, content, url))
            db.commit()
        except:
            db.rollback()
        cur.close()
        db.close()


mysql = Sql()

sort_dict = {
    'xuanhuan': '玄幻奇幻',
    'yanqing': '都市言情',
    'xianxia': '武侠仙侠',
    'lishi': '军事历史',
    'wangyou': '网游竞技',
    'lingyi': '科幻灵异',
    'tongren': '女生同人',
    'erciyuan': '二次元'
}

path = '/users/alex/downloads/'

main_url = 'https://www.uukanshu.com/user/shujia.aspx'

cookie = 'Cookie:fcip=111; ASP.NET_SessionId=oqn2uxx2ucjasulzlgotltcc; _ga=GA1.2.2072163454.1517104726; _gid=GA1.2.2039201761.1517104726; __atuvc=2%7C4; __atuvs=5a6d2e56d56fcd4a001; uc=true; au=1; UID=110928; UNN=dGtubm4%3d'
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    'Connection': 'keep-alive',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cookie': cookie}


def get_novel_urls(url, sort):
    wbdata = requests.get(url).text
    soup = BeautifulSoup(wbdata, 'lxml')

    titles = soup.find_all('a', 'title-link')
    urls = soup.find_all('a', 'title-link')
    for title, url in zip(titles, urls):
        title = title.get_text()
        url = 'https://www.uukanshu.com' + url.get('href')
        sort = sort
        get_novel_info(url, title, sort)


# def get_novel_info(url,title,sort): #for 我的书架
#     wbdata = requests.get(url, headers=header).text
#     soup = BeautifulSoup(wbdata, 'lxml')
#     for i in range(2, 32):
#
#         cates = soup.select(('tr:nth-of-type(%s) > td:nth-of-type(1)') %i)
#         names = soup.select(('tr:nth-of-type(%s) > td:nth-of-type(2) > a > font') %i)
#         shorturls = soup.select(('tr:nth-of-type(%s) > td:nth-of-type(2) > a') %i)
#         authors = soup.select(('tr:nth-of-type(%s) > td:nth-of-type(6)') %i)
#         for cate, name, author, shorturl in zip(cates, names, authors, shorturls):
#             cate = cate.get_text().replace('[', '')
#             cate = cate.replace(']', '')
#             name = name.get_text()
#             author = author.get_text()
#             url = 'https://www.uukanshu.com' + shorturl.get('href')
#
#             novel_data = {
#                 'cate': cate,
#                 'name': name,
#                 'author': author,
#                 'url': url
#             }
#             print(novel_data)
def get_novel_info(url, title, sort):
    wbdata = requests.get(url, headers=header).text
    soup = BeautifulSoup(wbdata, 'lxml')

    authors = soup.select('body > div.xiaoshuo_content.clear > dl > dd > h2 > a')
    imageurls = soup.select('body > div.xiaoshuo_content.clear > dl > dt > a > img')
    descriptions = soup.select('body > div.xiaoshuo_content.clear > dl > dd > h3')
    for author, imageurl, description in zip(authors, imageurls, descriptions):
        title = title
        sort = sort
        author = author.get_text()
        imageurl = 'http:' + imageurl.get('src')
        description = description.get_text()
        mysql.addnovel(sort, title, imageurl, author, description)
        print(('正在爬: %s') % title)
        get_chapterUrls(url, title)


def get_chapterUrls(url, novelname):  # 由前一章获取下一章的网址
    wb_data = requests.get(url)
    soup = BeautifulSoup(wb_data.text, 'lxml')

    urls = soup.select('body > div.xiaoshuo_content.clear > div.zhangjie.clear > ul > li > a')
    for url in urls:
        url = 'https://www.uukanshu.com' + url.get('href')
        get_chapterInfo(url, novelname)


def get_chapterInfo(url, novelname):  # 获取章节的标题和内容
    wb_data = requests.get(url)
    soup = BeautifulSoup(wb_data.text, 'lxml')

    titles = soup.select('h1#timu')
    contents = soup.select('div#contentbox')

    for title, content in zip(titles, contents):
        title = title.get_text()
        content = content.get_text().replace('\xa0', '')
        content = content.replace('(adsbygoogle = window.adsbygoogle || []).push({});', '')

        print('正在爬：' + novelname +' '+ title+': '+title+content)
        mysql.addchapter(novelname, title, content, url)


# for sort in sort_dict:
#     for j in range(20):
#         p = ('https://www.uukanshu.com/list/%s-%s.html') %(sort, j)
#         get_novel_urls(p, sort)


if __name__ == '__main__':
    pool = Pool(processes=6)
    tasks = []
    for sort in sort_dict:
        for j in range(20):
            p = ('https://www.uukanshu.com/list/%s-%s.html') %(sort, j)
            tasks.append((p,sort))
    pool.starmap(get_novel_urls, tasks)