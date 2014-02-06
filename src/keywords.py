from google.appengine.ext import db
import string
import util
import random
from common import Keyword, MAX_KEYWORD_WEIGHT
import logic

class Keyword_count():
    def __init__(self, kw_text, kw_appear, kw_weight):
        self.text = kw_text
        self.appear = kw_appear
        self.weight = kw_weight

#Creates a dictionary of all keywords in db with their appropriate weight
def get_dictonary_of_keywords_from_db():
    dict_of_keywords = {}
    keywords_in_db = db.GqlQuery("SELECT * FROM Keyword")
    for word in keywords_in_db:
        word_text = word.text.lower()
        dict_of_keywords[word_text] = word.weight
    
    return dict_of_keywords

#counts the number of appearances of each keyword in a text
#returns a list of keywords with their weights, sorted by number of appearances
def count_keywords_in_text(text, dict_of_keywords):
    list_keywords = []
    list_keys = []
    for elem in dict_of_keywords.items():
        key = elem[0]
        value = elem[1]
        keyword = Keyword_count(key, 0, value)
        list_keys.append(key)
        list_keywords.append(keyword)
        
    split_text = text.split()
    for word in split_text:
        word = string.strip(word, string.punctuation)
        word = word.lower()
        if(word in dict_of_keywords):
            i = list_keys.index(word)
            list_keywords[i].appear = list_keywords[i].appear + 1
    
    #return list_keywords
    result =  sorted(list_keywords, key = lambda keyword: keyword.appear)
    result.reverse()
    return result

def create_list_of_keywords(sorted_list_of_keywords_count):
    keyword_list = []
    for keyword in sorted_list_of_keywords_count:
        if keyword.appear == 0:
            return keyword_list
        
        keyword_list.append(keyword.text)
        
    return keyword_list   

#return a list of all keywords who appear more then the number of times then defined in the keywords dictonary
def calculate_keywords_weight(sorted_list_of_keywords_count):
    weight = 0
    for keyword in sorted_list_of_keywords_count:
        weight+= keyword.appear*keyword.weight
    
    return weight

def update_keywords_in_article(article, article_data):
    
    if (article_data == None):
        article_data = util.http_request(article.url)
        
    keyword_count_list = count_keywords_in_text(article_data, logic.getKeywordDict())
    article.keywords = create_list_of_keywords(keyword_count_list)
    article.weight = calculate_keywords_weight(keyword_count_list)
    
def add_keyword_to_db(keyword_text, keyword_weight):
    keyw_text = keyword_text.lower()    
    keyw = db.GqlQuery("SELECT * FROM Keyword WHERE text=:text",text=keyw_text).get()
    if(keyword_weight == 0):    #delete keyword from db
        if(keyw!=None):
            keyw.delete()
    else: #keyword weight is not 0. Insert keyword to db        
        if (keyw==None):
            keyw = Keyword()
            keyw.text = keyw_text
            keyw.weight = keyword_weight
            keyw.put()
        else:
            keyw.weight = keyword_weight
            keyw.put()
            
    logic.cleanCache(Keyword())
            
#def get_three_random_hot_keywords():
#    list_of_hot_keywords = []
#    keyword_weight = MAX_KEYWORD_WEIGHT
#    count = 0
#    hot_keywords_query = None
#    
#    while (count == 0) and (keyword_weight > 0):
#        hot_keywords_query = Keyword.all()
#        hot_keywords_query.filter("weight = ", keyword_weight)
#        count = hot_keywords_query.count()
#        keyword_weight -= 1
#        
#    if count == 0:
#        return list_of_hot_keywords
#    
#    elif count <= 3 :
#        results = hot_keywords_query.fetch(limit = count)
#        for word in results:
#            list_of_hot_keywords.append(word.text)
#        
#        return list_of_hot_keywords
#    
#    #Get 3 random keywords from the highest weight, and return them
#    results = hot_keywords_query.fetch(limit = count)
#    index1 = random.randrange(0, count)
#    index2 = index1
#    while index2 == index1 :
#        index2 = random.randrange(0, count)
#    index3 = index1
#    while (index3 == index1) or (index3 == index2) :
#        index3 = random.randrange(0, count)
#        
#    list_of_hot_keywords.append(results[index1].text)
#    list_of_hot_keywords.append(results[index2].text)
#    list_of_hot_keywords.append(results[index3].text)
#    
#    return list_of_hot_keywords

def get_all_hot_keywords():
    list_of_hot_keywords = []
    keyword_weight = MAX_KEYWORD_WEIGHT
    count = 0
    hot_keywords_query = None
    
    while (count == 0) and (keyword_weight > 0):
        hot_keywords_query = Keyword.all()
        hot_keywords_query.filter("weight = ", keyword_weight)
        count = hot_keywords_query.count()
        keyword_weight -= 1
        
    if count == 0:
        return list_of_hot_keywords    
    
    results = hot_keywords_query.fetch(limit = count)
    for word in results:
        list_of_hot_keywords.append(word.text)
        
    return list_of_hot_keywords

def get_list_of_all_keywords():
    list_of_keywords = []
    keywords_query = Keyword.all()
    for word in keywords_query:
        list_of_keywords.append(word.text)
    
    return list_of_keywords
    
    
