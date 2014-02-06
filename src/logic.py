from google.appengine.api import memcache
import DbSearchEngine
import keywords
from google.appengine.ext import db #TODO: remove import
import random

######################################################################################
#
# Logic layer between the GUI and the DAL
# Simplifies the usage for the GUI and integrates memcache so not every call
# require an DB query
#
######################################################################################
def getArticles(query, userID, user_preferences, article_offset, language):
    
    if (userID):
        (activities,filter) = DbSearchEngine.getActivitiesQuery(userID, user_preferences)
    else:
        activities = None

    if (query=='' and activities==None):        
        data = memcache.get('articles.%s.%s'%(language,article_offset))
        if (data):
            return data
        else:
            data = getArticlesFromDB(query, userID, user_preferences, article_offset, language)
            memcache.set('articles.%s.%s'%(language,article_offset),data,3600)
            return data
    else:
        return getArticlesFromDB(query, userID, user_preferences, article_offset, language)       

def getArticlesFromDB(query, userID, user_preferences, article_offset, language):
    general_query = DbSearchEngine.create_general_query_of_articles(query, userID, user_preferences, language)                
    articles = DbSearchEngine.get_chosen_query_of_articles(article_offset, general_query)               
    hasnextpage = DbSearchEngine.does_query_have_next(article_offset, general_query.count())
    return (articles, hasnextpage)

def getKeywordDict():
    data = memcache.get('keywords.dict')
    if (data==None):
        data = keywords.get_dictonary_of_keywords_from_db()
        memcache.set('keywords.dict', data)
    
    return data

def getHotKeywords(shuffle=False):
    words = memcache.get('keywords.hot')
    if (words==None):
        words = keywords.get_all_hot_keywords()
        memcache.set('keywords.hot', words)
    
    if (shuffle):
        random.shuffle(words)
    return words

def getAllKeywords(shuffle=False):
    words = memcache.get('keywords.all')
    if (words==None):
        words = keywords.get_list_of_all_keywords()
        memcache.set('keywords.all', words)
    
    if (shuffle):
        random.shuffle(words)
    return words

def getTipsByDate(count=7):
    data = memcache.get('tips.bydate.%s'%count)
    if (data==None):
        data= db.GqlQuery("SELECT * FROM Tip order by created desc").fetch(count)
        memcache.set('tips.bydate.%s'%count, data)
    
    return data

def getUserActivities(userID, count=2000):
    #data = memcache.get('activities.%s'%userID)
    #if (data==None):
    data = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user = '%s'"% (userID)).fetch(count)
    #    memcache.set('activities.%s'%userID,data,3600)
    return data
def cleanCache(type):
    memcache.flush_all()
    
    