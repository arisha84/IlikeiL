from google.appengine.ext import db

ARTICLES_PER_PAGE = 8
MAX_NUMBER_OF_POSSIBLE_NEXTS = (1000 / ARTICLES_PER_PAGE)
ARTICLES_REFRESH_RATE_IN_MINUTES = 60

DAYS_TO_REMOVE_ARTICLES_FROM_DB = 90

MAX_KEYWORD_WEIGHT = 3
OVER_MAX_ARTICLE_IMPORTANCE = 6

SOURCE_FOR_THRESHOLD = 10 #how many user votes does it take to mark the source as "problematic"
FOR_THRESHOLD = 10 ##how many user votes does it take to mark the source as "confirmed"

ARTICLE_FOR_THRESHOLD = 50
ARTICLE_AGAINST_THRESHOLD = -50

ARTICLE_WEIGHT_THRESHOLD_FOR_REDUCTION = 15 #what is the relevance weight that under it the article importance is reduced to 1

class Feedback(db.Model):
    feed_name = db.StringProperty()
    feed_email = db.StringProperty()
    feed_text = db.StringProperty()


class IlikeUser(db.Model):
    identifier = db.StringProperty()
    name = db.StringProperty()
    username = db.StringProperty()
    email = db.StringProperty()
    token = db.StringProperty()
    user_level = db.IntegerProperty(default = 1) #1=regular user, 2=power user, 3=admin
    voting_weight = db.IntegerProperty(default = 1) #the weight that the user will add/reduce from article
    user_pref_min = db.BooleanProperty(default = False)
    language = db.StringProperty(default = 'english')
    comments_counter = db.IntegerProperty(default = 0) #how many comments have I made?
    
#this class creates enums, for example see activityTypes below
class Enumerate(object):
      def __init__(self, names):
        for number, name in enumerate(names.split()):
          setattr(self, name, number)
          
              
#this class saves data about an article for specific user! 
#when a user makes an activity an instance of this class is created, and this instance
#will save all the activities that the user performed on the article     
class ArticleActivity(db.Model):
    user = db.StringProperty()
    articleID = db.StringProperty()        
    commented = db.BooleanProperty(default = False)
    starred = db.BooleanProperty(default = False)
    irrelevant = db.BooleanProperty(default = False)
    verified = db.BooleanProperty(default = False)
    noComments = db.BooleanProperty(default = False)
    dec = db.BooleanProperty(default = False)
    inc = db.BooleanProperty(default = False)        

class Article(db.Model):
    #raw = db.TextProperty() #used for debugging - too heavy otherwise
    title = db.StringProperty() #article title
    desc = db.TextProperty()    #article description
    source = db.StringProperty()    #article source
    created = db.DateTimeProperty(auto_now_add=True)    #time created
    #attended_users = db.ListProperty(item_type=IlikeUser)   #list of users
    keywords = db.StringListProperty() #list of keywords
    importance = db.IntegerProperty() #Article importance according to it's source and keywords weight
    weight = db.IntegerProperty() #relevance weight of article
    source_weight = db.IntegerProperty() #Weight of the source of the article
    url = db.StringProperty()
    pic_url = db.StringProperty()
    language = db.StringProperty()
    last_modified = db.DateTimeProperty(auto_now_add=True) #time article was last modified
    usersCommented = db.IntegerProperty(default = 0)
    usersViewed = db.IntegerProperty(default = 0)            
    latest_activity = ArticleActivity()
    unverified = db.BooleanProperty(default = True) #true if the article needs verification
    relevance_votes = db.IntegerProperty(default = 0) #Number of votes for/against article

    def pretty_date(self):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """
        from datetime import datetime
        now = datetime.now()
        diff = now - self.created
        second_diff = diff.seconds
        day_diff = diff.days
    
        if day_diff < 0:
            return ''
    
        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return  "a minute ago"
            if second_diff < 3600:
                return str( second_diff / 60 ) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str( second_diff / 3600 ) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff/7) + " weeks ago"
        if day_diff < 365:
            return str(day_diff/30) + " months ago"
        return str(day_diff/365) + " years ago"      

#class FriendlyTimeArticle(db.Model):
#    def __init__(self, realpart, imagpart):
#        self.friendly = 
#        self.i = imagpart

    
    
class Tip(Article):
#    title = db.StringProperty()
#    url = db.StringProperty()
#    keywords = db.StringListProperty()    
    pass

class Keyword(db.Model):
    text = db.StringProperty()
    weight = db.IntegerProperty()

class Sources(db.Model):
    name = db.StringProperty()
    has_tkbks = db.BooleanProperty(default=False)
    weight = db.IntegerProperty(default=1)
    _how_many_against = db.IntegerProperty(default=0)
    _how_many_for = db.IntegerProperty(default=0)
    volatile = db.BooleanProperty(default=False) # is this source consistent with comment/no-comment? (not like nytimes)
    def increment_against(self):
        #Run this when a user votes against the result of this source
        if (not self.volatile):
            self._how_many_against += 1
            #if (self._how_many_against > SOURCE_FOR_THRESHOLD):
            #    self.has_tkbks ^= True #flip the decision
            #    self._how_many_against = 0
        return None
    def increment_for(self):
        #Run this when a user votes for the result of this source
        if (not self.volatile):
            if (self._how_many_for):
                self._how_many_for += 1
            else:
                self._how_many_against -= 1
        return None
    def is_source_problematic(self):
        if self._how_many_for != None:
            if (self._how_many_for < FOR_THRESHOLD) and (self._how_many_against > SOURCE_FOR_THRESHOLD):
                return True
            else:
                return False
        else:
            if (self._how_many_against > SOURCE_FOR_THRESHOLD):
                return True
            else:
                return False

