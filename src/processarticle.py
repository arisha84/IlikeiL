import string
import re
import urllib
from util import http_request
from google.appengine.ext import db
from common import Sources, OVER_MAX_ARTICLE_IMPORTANCE
from article_updater import calculate_article_importance
import logging
import keywords

AGAINST_THRESHOLD = 10 #how many users does it take to turn the algorithm's decision
RE_BETWEEN_TAGS = r'<a[^>]*>(.*?)</a>'
RE_INSIDE_TAG = r'<([^>]*)>'


def get_link_texts(data):
    """
    Fetches the texts inside <a href> tags.
    Returns a list of strings.
    """
    return re.findall(RE_BETWEEN_TAGS, data.lower())

def search_comment_forms(data):
    """
    Searches the comment keywords inside tags (for id,class attributes etc.)
    """
    a = re.findall(RE_INSIDE_TAG, data.lower())
    for i in a:
        for x in ["comments","trackback","talkback","comentarios"]:
            if (-1 != i.find(x)):
                logging.debug("Found an attribute: %s"%i)
                return True
    return False


def _has_talkback_reuters(url, data):
    if (data == None):
        data = http_request(url)
    logging.debug("Reuters returning %s"%(-1 != data.find('/articles/comments/')))
    return (-1 != data.find('/article/comments/'))


def _has_talkback_guardian(url, data):
    if (data == None):
        data = http_request(url)
    return (-1 != data.find('Comments in chronological order'))


def _has_talkback(url, data=None):
    if (data == None):
        data = http_request(url)
    # one method for determining talkback is by looking at the text of the <a> tags
    links = get_link_texts(data)
    for link in links:
        con = "".join(link)
        con = con.lower()
        for x in ["comments","talkback","trackback","talk-back","track-back","comentarios"]:
            if ((-1 != con.find(x)) and (-1 == con.find("commentary")) and (-1 == con.find("commented"))):
                logging.debug("TalkBack: Found '%s' in '%s'. Has talkbacks."%(x,con))
                return True
    # second method is looking for a <form> with ID "comment" or "something-back"
    if (search_comment_forms(data)):
        return True
    return False


def has_talkback(article):
    """
    Gets an instance of Article and returns a boolean whether it has talkback feature
    or not.
    """
    volatile = False
    # @type article Article
    
    source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()

    # we check if the source exists and whether it's volatile (should check talkbacks for every article seperately)
    if ((source != None) and (source.volatile == False)):
        logging.debug("known source, returning %s"%source.has_tkbks)
        article.source_weight = source.weight         
        return source.has_tkbks
    elif ((source != None) and (source.volatile)):
        volatile = True
        logging.debug("volatile source (%s)"%source.name)
    else:
        logging.debug("new source (%s)"%article.source)
        
    source = Sources(name=article.source)
    source.has_tkbks = _has_talkback(article.url)
    if (not volatile):
        source.put()

    logging.debug("returning %s"%source.has_tkbks)
    article.source_weight = source.weight
    #At the beginning, give each article max importance- until we recalculate the importance
    return source.has_tkbks

def add_new_article_to_db(article):
    article.importance = OVER_MAX_ARTICLE_IMPORTANCE
    calculate_article_importance(article) #This call calculates the article importance and adds it to the db                   

def remove_article_by_key(key):
    article = db.get(key)
    article.importance = 0
    article.put()   

#This function process the article source and keywords, and return True if the article should be added to db
def process_article(article):
    logging.debug("Got article: %s (%s)"%(article.source,article.url))
    
    has_talkbacks = False
    volatile = False
    create_new_source = True
    article_data = None
    
    #Check if article has a known source
    source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()

    # if this is a known source
    if (source != None):
        # Reuters and guardian is big enough sources so we give them a delicate handling
        if (source.name.lower() == 'reuters'):
            logging.debug("A reuters article")
            article_data = http_request(article.url)
            has_talkbacks = _has_talkback_reuters(article.url, article_data)
            create_new_source = False
        elif (source.name.lower().find('guardian') != -1):
            logging.debug("A guardian article")
            article_data = http_request(article.url)
            has_talkbacks = _has_talkback_guardian(article.url, article_data)
            create_new_source = False
        else:
            if (source.volatile == False):
                logging.debug("known source, has talkbacks = %s"%source.has_tkbks)
                article.source_weight = source.weight
                has_talkbacks = source.has_tkbks
                create_new_source = False
            else:
                logging.debug("volatile source (%s)"%source.name)
                volatile = True

    if (create_new_source):
        source = Sources(name=article.source)
        article_data = http_request(article.url) 
        has_talkbacks = _has_talkback(url = article.url, data = article_data)
        logging.debug("A new source = %s, has talkbacks = %s"%(article.source,source.has_tkbks))
        #If this is not a volatile source, we should add it to the db
        if (not volatile):
            source.has_tkbks = has_talkbacks
            source.put()
    
    #If the source has no talkbacks, we shouldn't process the article
    if (has_talkbacks == False):
        logging.debug("Article has no talkbacks")
        return False
    
    article.source_weight = source.weight
    #Process the keywords in the article
    keywords.update_keywords_in_article(article, article_data)
    
    logging.debug("Article with src_weight = %d and keywords_weight = %d"%(article.source_weight, article.weight))
    
    if (article.weight > 0):
        logging.debug("Article was added")
        return True
    else:
        logging.debug("No keywords. Article was not added")
        return False   
    
