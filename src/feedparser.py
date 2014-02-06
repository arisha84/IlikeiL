import common
import util
import logging
import datetime
import re

from xml.dom import minidom
from google.appengine.ext import db
from BeautifulSoup import BeautifulSoup
from util import html_escape

def isURLInDB(url):
    q = db.GqlQuery("SELECT __key__ FROM Article WHERE url = :url ", url=url)
    if (q.count() == 0):
        return False
    else:
        return True
    
def fetchByUrl(NEWS_URL, language):
    articles = []
    dom = minidom.parseString(util.http_request(NEWS_URL))
    for node in dom.getElementsByTagName('item'):
        # the source is the last part and the rest is the title
        arr = node.getElementsByTagName('title')[0].firstChild.data.rsplit('-',1) 
        newArticle = common.Article()
        newArticle.title = arr[0].strip()
        logging.debug("Parsing article: '%s'"%newArticle.title)
        #replace the ' mark to its html encoding and save in source
        newArticle.source = arr[1].strip()
        url = node.getElementsByTagName('link')[0].firstChild.data
        newArticle.url = url 

        # Here we test if this article is already in the DB, and if so we continue:
        if (isURLInDB(url)):
            logging.debug("Article already in the DB, skipping")
            continue

        #extract text
        rawDescription = node.getElementsByTagName('description')[0].firstChild.data
        #newArticle.raw = rawDescription # used for debugging
        description = util.extract_text(rawDescription).split("...")[0].strip() # get all the text before the ...
        if (description.find(newArticle.source) > -1):
            newArticle.desc = description.split(newArticle.source)[1]
        else:
            newArticle.desc = description
        datestring = node.getElementsByTagName('pubDate')[0].firstChild.data
        if datestring != '':
            newArticle.created = datetime.datetime.strptime(datestring, '%a, %d %b %Y %H:%M:%S GMT+00:00' )
        
        soup = BeautifulSoup(rawDescription)
        thumbnail = soup.find('img')
        if thumbnail:
            try:
                newArticle.pic_url = thumbnail['src']
            except:
                pass 
        #@@ari
        newArticle.language = language
        articles.append(newArticle)
    
    return articles

def fetchByUrlYT(NEWS_URL, language):
    articles = []
    dom = minidom.parseString(util.http_request(NEWS_URL))
    for node in dom.getElementsByTagName('entry'):
        # the source is the last part and the rest is the title
        newArticle = common.Article()
        newArticle.title = node.getElementsByTagName('title')[0].firstChild.data
        logging.debug("Parsing article: '[YouTube] %s'"%newArticle.title)
        #replace the ' mark to its html encoding and save in source
        newArticle.source = "YouTube"
        url = node.getElementsByTagName('link')[0].getAttribute('href')
        newArticle.url = url

        # Here we test if this article is already in the DB, and if so we continue:
        if (isURLInDB(url)):
            logging.debug("Article already in the DB, skipping")
            continue

        #extract text
        rawDescription = node.getElementsByTagName('content')[0].firstChild.data
        #newArticle.raw = rawDescription # used for debugging
        #description = rawDescription.split('tyle="font-size: 12px; margin: 3px 0px;"&gt;&lt;span&gt;')[1].split('&lt;/span&gt;&lt;/div&gt;&lt;/td&gt;')[0].strip() # get all the text before the ...
        description = util.extract_text(rawDescription).strip()[len(newArticle.title):]
        newArticle.desc = description
        datestring = node.getElementsByTagName('updated')[0].firstChild.data
        if datestring != '':
            newArticle.created = datetime.datetime.strptime(datestring, '%Y-%m-%dT%H:%M:%S.000Z' )

        thumbnail = re.findall(r'img alt="" src="(http://i.ytimg.com/[^"]+)"',rawDescription)
        if len(thumbnail) > 0:
            newArticle.pic_url = thumbnail[0]

        #@@ari
        newArticle.language = language
        articles.append(newArticle)

    return articles


def appendArticles (Articles, Articles_lang):
    for a in Articles_lang:
        Articles.append(a)
    return Articles
    
    
def fetchArticles():
    query = 'israel' # no need  further keywords at the moment
    NEWS_URL = 'http://news.google.com/news/search?cf=all&ned=us&hl=en&q=%s&cf=all&as_qdr=h&as_drrb=q&output=rss' % query
    NEWS_URL_SP = 'http://news.google.es/news/search?aq=f&pz=1&cf=all&ned=es&hl=es&q=%s&output=rss' %query
    NEWS_URL_YT = 'http://gdata.youtube.com/feeds/base/videos?q=%s&orderby=published&max-results=10&prettyprint=true' % query
    
    articles = []    
    articles_eng = fetchByUrl(NEWS_URL, 'english')
    articles = appendArticles(articles, articles_eng)
    articles_sp = fetchByUrl(NEWS_URL_SP, 'spanish')
    articles = appendArticles(articles, articles_sp)
    articles_yt = fetchByUrlYT(NEWS_URL_YT, 'youtube')
    articles = appendArticles(articles, articles_yt)
    return articles
    
def extract_key_from_querystring(fullurl, key):
    from urlparse import urlparse
    url = urlparse(fullurl)
    params = dict([part.split('=') for part in url[4].split('&')])
    if key in params:
        return params[key]
    else:
        return ''
        
if __name__ == '__main__':
    main()
   