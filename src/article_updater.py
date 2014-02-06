import datetime
from common import ARTICLES_REFRESH_RATE_IN_MINUTES, DAYS_TO_REMOVE_ARTICLES_FROM_DB, ARTICLE_FOR_THRESHOLD, ARTICLE_AGAINST_THRESHOLD, ARTICLE_WEIGHT_THRESHOLD_FOR_REDUCTION
from common import Article
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging

#time deltas
FIVE_DAYS_DELTA = datetime.timedelta(days = 5)
FOUR_DAYS_DELTA = datetime.timedelta(days = 4)
THREE_DAYS_DELTA = datetime.timedelta(days = 3)
TWO_DAYS_DELTA = datetime.timedelta(days = 2)
ONE_DAY_DELTA = datetime.timedelta(days = 1)

DAYS_TO_ARTICLE_OBSOLETE = 6

def update_article_importance_by_date():
    now = datetime.datetime.now()

    lowerFilterDelta = datetime.timedelta(days = DAYS_TO_ARTICLE_OBSOLETE, seconds = 4*ARTICLES_REFRESH_RATE_IN_MINUTES*60)
    lowerTimeFilter = now - lowerFilterDelta
    
    higherFilterDelta = datetime.timedelta(days = DAYS_TO_ARTICLE_OBSOLETE)
    higherTimeFilter = now - higherFilterDelta
            
    articles = Article.all()

    articles.filter("last_modified > ", lowerTimeFilter)
    articles.filter("last_modified < ", higherTimeFilter)
            
    for article in articles:
        if article.importance > 0:
            article.importance = 0
            article.put()
    

def increment_article_relevance(article, voting_weight):
    if(article.relevance_votes != None):
        article.relevance_votes += voting_weight
    
    article.weight += voting_weight
    
    
 
def decrement_article_relevance(article, voting_weight):
    if(article.relevance_votes != None):
        article.relevance_votes -= voting_weight
    
    article.weight -= voting_weight
    
       

#This function calculates the importance of an article based on its source rating and its weight    
def calculate_article_importance(article):
    
    logging.debug("Calculate importance has been called on article with url = %s"%article.url)
    logging.debug("Calculate importance has been called. Current importance = %d"%article.importance)
    #if article is already not-relevant, do nothing
    if article.importance == 0:
        return 0
    
    current_importance = article.importance
    
    now = datetime.datetime.now()
    
    five_days_old = now - FIVE_DAYS_DELTA
    four_days_old = now - FOUR_DAYS_DELTA
    three_days_old = now - THREE_DAYS_DELTA
    two_days_old = now - TWO_DAYS_DELTA
    one_day_old = now - ONE_DAY_DELTA    
    
    src_weight = article.source_weight
    if src_weight == None:       
        source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()
        src_weight = source.weight
    
    logging.debug("Article is with source weight = %d"%src_weight)
    
    if src_weight == 0:
        article.importance = 0            
    
    if src_weight == 1:
        if (article.created < three_days_old):
            article.importance = 0
        elif (article.created < two_days_old) or (article.weight < ARTICLE_WEIGHT_THRESHOLD_FOR_REDUCTION):
            article.importance = 1
        elif (article.created < one_day_old):
            article.importance = 2
        #Otherwise- the article is for sure from the last day
        else:
            article.importance = 3
                
    if src_weight == 2:
        if (article.created < four_days_old):
            article.importance = 0
        elif (article.created < three_days_old) or (article.weight < ARTICLE_WEIGHT_THRESHOLD_FOR_REDUCTION):
            article.importance = 1
        elif (article.created < two_days_old):
            article.importance = 2
        elif (article.created < one_day_old):
            article.importance = 3
        #Otherwise- the article is for sure from the last day
        else:
            article.importance = 4
                    
    if src_weight == 3:
        if (article.created < five_days_old):
            article.importance = 0
        elif (article.created < four_days_old) or (article.weight < ARTICLE_WEIGHT_THRESHOLD_FOR_REDUCTION):
            article.importance = 1
        elif (article.created < three_days_old):
            article.importance = 2
        elif (article.created < two_days_old):
            article.importance = 3
        elif (article.created < one_day_old):
            article.importance = 4
        #Otherwise- the article is for sure from the last day
        else:
            article.importance = 5
                            

    if (article.relevance_votes != None) and (article.importance > 0):
        if (article.relevance_votes >= ARTICLE_FOR_THRESHOLD) and (article.importance < 5):
            article.importance += 1
        elif (article.relevance_votes <= ARTICLE_AGAINST_THRESHOLD) and (article.importance > 1):
            article.importance -= 1
            
    if (current_importance == article.importance):
        #no need to update the db
        logging.debug("Article importance has not been changed. Not putting article in db")        
        return 0
    else:
        k = article.put()
        logging.debug("Importance of article with key %s have been updated"%k)
        logging.debug("New importance is %d"%article.importance)
        return 1         
    
       
       
def recalculate_all_articles_importance():
    #Mark old articles as not-relevant 
    #update_article_importance_by_date()
        
    articles = db.GqlQuery("SELECT * FROM Article WHERE importance > 0"
                           + "ORDER BY importance DESC")
        
    counter = 0
    total = 0 
    for article in articles:
        counter = counter + calculate_article_importance(article)
        total = total + 1

    logging.debug("%d Articles have been iterated on"%total)
    return counter

def remove_old_entries_from_db():   
    i = 0
    now = datetime.datetime.now()

    timeFilterDelta = datetime.timedelta(days = DAYS_TO_REMOVE_ARTICLES_FROM_DB)
    timeFilter = now - timeFilterDelta
    
    articles = Article.all()
    articles.filter("last_modified < ", timeFilter)
    
    for article in articles:
        key = str(article.key())
        activities = db.GqlQuery("SELECT * FROM ArticleActivity WHERE articleID = '%s'"%key)
        for activity in activities:
            activity.delete()
        
        article.delete()
        i = i + 1
    
    return i       
        
class Clean(webapp.RequestHandler):
    def get(self):
        i = remove_old_entries_from_db()
        logging.debug("%d Articles have been removed from db"%i)
        self.response.out.write('<html><body><h2>%d articles have been removed</h2></body></html>'%i)
        
            
class Done(webapp.RequestHandler):
    def get(self):
        #recalculate articles importance which may have changed according to users activities
        i = recalculate_all_articles_importance()
        logging.debug("%d Articles have been recalculated"%i)
        self.response.out.write('<html><body><h2>%d articles recalculated</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>'%i)

application = webapp.WSGIApplication(                            
                                     [('/recalculate', Done),
                                      ('/cleandb', Clean)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
