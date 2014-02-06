from common import Article
from google.appengine.ext import db
from common import ARTICLES_PER_PAGE

class user_search_preferences:
    def __init__(self):
        self.starred = False
        self.commented = False
        self.relevant = False
        

#Creates and returns a GQL query object of the articles sorted by their importance
def create_query_of_articles():   
    articles = Article.all()
    articles.filter("importance >", 0)
    articles.order("-importance")
    #articles.order("-created")
    #articles.order("-source_weight")
    articles.order("-weight") 
    
    return articles

def create_query_of_articles_filtered_by_list_of_articleIDs(list_of_ids, filter_old_articles):   
    articles = Article.all()
    articles.filter("__key__ IN", list_of_ids)
    if filter_old_articles:
        articles.filter("importance >", 0)
    articles.order("-importance")
    #articles.order("-created")
    #articles.order("-source_weight")
    articles.order("-weight")    
    
    return articles

def create_query_of_articles_based_on_keyword(keywords_string):
    #split the multiple keywords string into separate keywords
    keywords_string = keywords_string.replace(',',' ')
    keyword_list = keywords_string.split()
    
    #1st OPTION- filter based on any of the keywords
    #for keyword in keyword_list:        
    #    keyw = db.GqlQuery("SELECT * FROM Keyword WHERE text='%s'"%keyword).get()
    #    if keyw == None:
    #        keyword_list.remove(keyword)
    #End of 1st option
            
    articles = Article.all()
    #1st OPTION- filter based on any of the keywords
    #articles.filter("keywords IN", keyword_list)
    #End of 1st option
    
    #2nd OPTION- filter based on all of the keywords
    for keyword in keyword_list: 
        keyword = keyword.lower()       
        articles.filter("keywords =", keyword)
    #End of 2nd option
    
    articles.filter("importance >", 0)
    articles.order("-importance")
    #articles.order("-created")
    #articles.order("-source_weight")
    articles.order("-weight")
    
    return articles


def getActivitiesQuery(userID, user_preferences):
    activities = None
    filter_old_articles = True
    if (user_preferences.starred):
        activities = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user='%s' AND starred = True"%userID)
        filter_old_articles = False
    elif (user_preferences.commented):
        activities = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user='%s' AND commented = True"%userID)
        filter_old_articles = False
    elif (user_preferences.relevant):
        activities = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user='%s' AND inc = True"%userID)
        
    return (activities,filter_old_articles)  
        
def create_query_of_articles_based_on_user_prefernces(userID, user_preferences):
    
    (activities, filter_old_articles)= getActivitiesQuery(userID, user_preferences)
    
    if activities == None:
        return create_query_of_articles()
            
    articleIDsList = []
    for activity in activities:
        articleIDsList.append(db.Key(activity.articleID))
    
    return create_query_of_articles_filtered_by_list_of_articleIDs(articleIDsList, filter_old_articles)
    
def create_general_query_of_articles(keyword, userID, user_preferences, language):
    query = None
    if keyword != '':
        query = create_query_of_articles_based_on_keyword(keyword)        
    
    elif userID != None:
        query = create_query_of_articles_based_on_user_prefernces(userID, user_preferences)
        
    else:
        query = create_query_of_articles()
        
    query.filter("language =", language )
    return query        
    
def get_chosen_query_of_articles(articles_offset, articles_general_query):
    
    total_number_of_articles = articles_general_query.count()    
    if (articles_offset < 0) or (articles_offset >= total_number_of_articles):
        return []
    
    result = articles_general_query.fetch(ARTICLES_PER_PAGE, offset = articles_offset)
    
    return result

def does_query_have_next(articles_offset, total_number_of_articles):
    if total_number_of_articles > (articles_offset + ARTICLES_PER_PAGE):
        return True
    else:
        return False
    
    
    