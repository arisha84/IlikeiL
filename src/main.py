import pipeline
import addarticle
from common import Article
from common import Tip
import cgi
import common
from util import http_request
import os
from google.appengine.ext.webapp import template
import admin
import DbSearchEngine
import util
from operator import itemgetter
import logging
import rpxusers
import urllib
import keywords
import datetime
from article_updater import calculate_article_importance, decrement_article_relevance, increment_article_relevance
import logic
import parser
import traceback

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class MainPage(webapp.RequestHandler):
    template_file = "articleboxes.html"

    def handle_exception(self, exception, debug_mode):
        error_message = traceback.format_exc()  # Get the traceback.
        logging.error(error_message)            # Log the traceback.
        #self._serve_error(500)                  # Serve the error page.
        self.error(500)
        self.response.out.write('<html><body><h2>Sorry! We had problems with our server! Those computers...</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>')
        return ''
        
    def get(self):
        article_offset = 0
        query = ''
        userID = None
        user_preferences = None
        YouTubeFlag = False         

        u = rpxusers.getCurrentUser(self.request, self.response)
        if u:
            utext = rpxusers.create_logout_html(self.request.host, u, self.request.url)
            userID = u.identifier
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        
        if (self.request.get('offset')):
            try:
                article_offset = int(self.request.get('offset'))
            except:
                pass
            
        if article_offset < 0:
            article_offset = 0
        
        #if we should filter articles according to a specific keyword, get that keyword from the url
        #note that get return the string of keywords separated by spaces!
        if (self.request.get('q')):
            query = self.request.get('q')
                
        language = 'english'
        #if we should filter articles according to user preferences, get the preferences from the url                
        if (userID != None):
            user_preferences = DbSearchEngine.user_search_preferences()
            user_preferences.language = u.language
            language = u.language     
            if (self.request.get('starred')=='true'):
                user_preferences.starred = True
            elif (self.request.get('commented')=='true'):
                user_preferences.commented = True
            elif (self.request.get('relevant')=='true'):
                user_preferences.relevant = True
        
            if (self.request.get('language')) and (user_preferences.language != self.request.get('language')):
                user_preferences.language = self.request.get('language')
                language = user_preferences.language
                if (language != 'youtube'):
                    u.language = language                
                    u.put()
        if (self.request.get('YouTube')):                                                                        
            (articles, hasnextpage) = logic.getArticles(query, userID, user_preferences, article_offset,'youtube')
        else:                       
            (articles, hasnextpage) = logic.getArticles(query, userID, user_preferences, article_offset,language)
       
        prev = article_offset - common.ARTICLES_PER_PAGE
        if prev < 0:
            prev =0
        
        next = article_offset + common.ARTICLES_PER_PAGE
        
        last_url = "?"
        for arg in self.request.arguments():
            if (arg!="offset"):
                last_url = last_url + arg + "=" + self.request.get(arg) + "&"
        next_url = last_url + "offset=%d" % next
        
        prev_url = None
        if (article_offset>0):
            prev_url = last_url + "offset=%d" % prev 
        #building a dictionary of user activities
        # key = articleid, value = articleactivity
        
        for article in articles:
            article.latest_activity = None
            
        activities = None   
        helper_user_activities = {}
        if (userID):
            activities = logic.getUserActivities(userID)
                    
                
        if activities:
            for activity in activities:
                helper_user_activities[activity.articleID] = activity
        
        for article in articles:
            if helper_user_activities.has_key(str(article.key())):
                article.latest_activity = helper_user_activities[str(article.key())]
        
        tips = logic.getTipsByDate()

        rank = None
        if userID:
            rank = rpxusers.getCommentsRank(u.comments_counter)
        
        template_values = {
            'rank': rank,
            'tips': tips,
            'articles': articles,
            'prev_url': prev_url,
            'offset': article_offset,
            'next_url': next_url,
            'hasnextpage': hasnextpage,
            'utext': utext,
            'admin': (u and u.user_level==3),
            'query':query,
            'hotkeywords':logic.getHotKeywords(shuffle=True),
            'allkeywords':logic.getAllKeywords(),
            'user': u,
            'user_min': (u and u.user_pref_min),            
            'language': language                 
            }
                
        path = os.path.join(os.path.dirname(__file__), self.template_file)
        html = template.render(path, template_values)      
        self.response.out.write(html)
        
        
class AjaxRelevance(webapp.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        error_message = traceback.format_exc()  # Get the traceback.
        logging.error(error_message)            # Log the traceback.
        #self._serve_error(500)                  # Serve the error page.
        self.error(500)
        self.response.out.write('<html><body><h2>Sorry! We had problems with our server! Those computers...</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>')
        return ''
        
    def get(self):
        reprocess_article = False
        a = self.request.get('article_id')
        logging.debug(a)        
        article = Article.get(a)
        #articleActivity holds all the activities of the current 
        # user on the current article        
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            articleActivity = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user = '%s' AND articleID = '%s' "% (user.identifier, a)).get()
            if (self.request.get('action') == 'dec'):
                reprocess_article = True                       
                if (articleActivity.dec == False):
                    articleActivity.dec = True
                    decrement_article_relevance(article, user.voting_weight) #Change this according to user power
                    if articleActivity.inc == True:
                        articleActivity.inc = False
                        decrement_article_relevance(article, user.voting_weight) #Change this according to user power
                    if(article.weight < 0):
                        article.weight = 0                   
            if (self.request.get('action') == 'inc'):
                reprocess_article = True
                if (articleActivity.inc == False):
                    articleActivity.inc = True
                    increment_article_relevance(article, user.voting_weight)
                    if articleActivity.dec == True:
                        articleActivity.dec = False
                        increment_article_relevance(article, user.voting_weight) #Change this according to user power
            if (self.request.get('action') == 'undec'):
                reprocess_article = True 
                if (articleActivity.dec == True):
                    articleActivity.dec = False
                    increment_article_relevance(article, user.voting_weight) #Change this according to user power
            if (self.request.get('action') == 'uninc'):
                reprocess_article = True 
                if (articleActivity.inc == True):
                    articleActivity.inc = False
                    decrement_article_relevance(article, user.voting_weight)
                    if(article.weight < 0):
                        article.weight = 0
            if (self.request.get('action') == 'starred'):
                articleActivity.starred = True
                
            if (self.request.get('action') == 'unstarred'):
                articleActivity.starred = False
                
            if (self.request.get('action') == 'notrelevant'):
                articleActivity.irrelevant = True
                #If the article was not verified, and the user is a power-user/admin,
                #then remove this article from the results
                if ((article.unverified == True) and (user.user_level > 1)):
                    article.importance = 0
                
            if (self.request.get('action') == 'nocomments'):
                articleActivity.noComments = True
                #Mark for the source that it has no comments
                source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()
                if(source != None):
                    source.increment_against()
                    source.put()
                    
                #If the article was not verified yet, mark it as irrelevant
                if ((article.unverified == True) and (user.user_level > 1)):
                    article.importance = 0                                                       
                
            if (self.request.get('action') == 'commented'):
                if (articleActivity.commented == False):
                    articleActivity.commented = True
                    if (user.comments_counter == None): user.comments_counter = 0
                    user.comments_counter = user.comments_counter + 1
                    user.put()
                    article.usersCommented += 1
                    #Mark for the source that it has comments
                    source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()
                    if(source != None):
                        source.increment_for()
                        source.put()
                        
                    if (article.unverified == True) and (user.user_level > 1):
                        article.unverified = False
            
            if (self.request.get('action') == 'verified'):
                articleActivity.verified = True
                #If the article was not verified, and the user is a power-user/admin,
                #then mark this article as verified
                if ((article.unverified == True) and (user.user_level > 1)):
                    article.unverified = False
                    #Mark for the source that it has comments
                    source = db.GqlQuery("SELECT * FROM Sources WHERE name=:source",source=article.source).get()
                    if(source != None):
                        source.increment_for()
                        source.put()
            
            if reprocess_article:
                calculate_article_importance(article)                          
            article.put()                
            articleActivity.put()
            
        self.response.out.write("<html>Done!</html>")

class ArticlePage(webapp.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        error_message = traceback.format_exc()  # Get the traceback.
        logging.error(error_message)            # Log the traceback.
        #self._serve_error(500)                  # Serve the error page.
        self.error(500)
        self.response.out.write('<html><body><h2>Sorry! We had problems with our server! Those computers...</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>')
        return ''
        
    def get(self):
        #a = db.Key(self.request.get('key'))
        #article = Article.get(a)
        a = self.request.get('key')
        logging.debug(a)        
        article = Article.get(a)

        #add article activity
        user_voting_weight = 0
        is_poweruser_or_admin = False
        did_user_already_comment = False

        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
            userID = user.identifier
            if user.user_level and user.user_level > 1:
                is_poweruser_or_admin = True
            if user.voting_weight:
                user_voting_weight = user.voting_weight
            else:
                user_voting_weight = 1
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)

        if user:
            articleActivity = db.GqlQuery("SELECT * FROM ArticleActivity WHERE user = '%s' AND articleID = '%s' "% (userID, a)).get()
            if (not articleActivity):
                articleActivity = common.ArticleActivity()                
                articleActivity.user = userID
                articleActivity.articleID = a
                articleActivity.put()
                article.usersViewed += 1                
                article.put()
            else:
                if articleActivity.commented or articleActivity.noComments:
                    did_user_already_comment = True
        
        # just for testing (replace with real tips getting):
        tips_dic = {}
        art_keywords2 = list(article.keywords)
        art_keywords = []
        for w in art_keywords2:
            art_keywords.append(w.lower())
            art_keywords.append("%s%s"%(w[0].upper(),w.lower()[1:]))
            
        # Reverse the order of keywords (least appearing first)
        art_keywords.reverse()
        logging.debug("keywords to search: %s"%art_keywords)
        # For each keyword in the article- get tips corresponding to it
        # count it using weights, s.t. the last keyword is the heaviest
        i = 0
        for keyw in art_keywords:
            i += 1
            q = db.GqlQuery("SELECT __key__ FROM Tip WHERE keywords = '%s'"%keyw.lower())
            for k in q:
                if k in tips_dic:
                    tips_dic[k] += i
                else:
                    tips_dic[k] = 1
            
        logging.debug("tips_dic: %s"%tips_dic)
        
        

        # now sort the tip keys using the weights
        tip_keys = [x[0] for x in sorted(tips_dic.items(), key=itemgetter(1), reverse=True)][:15]

        # get the tips to be passed to the template
        tips = db.get(tip_keys)
                
        is_starred = False
        rel_value = 0
        if user:
            is_starred = articleActivity.starred
            if articleActivity.dec:
                rel_value = -1
            if articleActivity.inc:
                rel_value = 1   
        
        template_values = {"utext":utext, 
                           "article": article, 
                           "tips": tips,
                           "user_weight": user_voting_weight,
                           "is_poweruser_or_admin": is_poweruser_or_admin,
                           "rel_value": rel_value, 
                           "is_starred": is_starred,
                           "did_user_already_comment" : did_user_already_comment,
                           "URL": self.request.url}
        if (self.request.get('min')):
            if user:
                user.user_pref_min = True
                user.put()
            path = os.path.join(os.path.dirname(__file__), 'min_article.html')
        else:
            if user:
                user.user_pref_min = False
                user.put()
            path = os.path.join(os.path.dirname(__file__), 'article.html')

        article.title = article.title.replace("'","\\'")
        
        self.response.out.write(template.render(path, template_values))
        return None


class LoginCallback(webapp.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        error_message = traceback.format_exc()  # Get the traceback.
        logging.error(error_message)            # Log the traceback.
        #self._serve_error(500)                  # Serve the error page.
        self.error(500)
        self.response.out.write('<html><body><h2>Sorry! We had problems with our server! Those computers...</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>')
        return ''
    def get(self):
        self.response.headers['Set-Cookie']='token=0'
        redurl = self.request.get('redirect')
        if redurl:
            self.redirect(redurl)
        else:
            self.redirect('/')

    def post(self):
        token = self.request.get('token')
        a = rpxusers.getUserInfo(token, self.response)
        if (a == None):
            self.response.out.write("Failed Login")
            pass #user not logged in

        else:
            # @type a common.IlikeUser
            #self.response.out.write("<html>token: %s<br> ident: %s<br>name: %s<br>email: %s</html>"%(a.token, a.identifier, a.name, a.email))
            #self.response.set_cookie('token', token, max_age=360, path='/', domain='localhost:8080', secure=True)
            pass

        redurl = self.request.get('redirect')
        if redurl:
            self.redirect(self.request.get('redirect'))
        else:
            self.redirect('/')



class Search(webapp.RequestHandler):
    def get(self):
        q = self.request.get('q')
        self.redirect('/?q=%s' % q.strip().replace(' ', '+'))

class Support(webapp.RequestHandler):
    def get(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        username = None
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
            username = user.name
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        path = os.path.join(os.path.dirname(__file__), 'support_template.html')
        self.response.out.write(template.render(path, {"utext": utext, "uname": username}))

    def post(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)

        a = common.Feedback(feed_name=self.request.get("feedback_name"), feed_email=self.request.get("feedback_email"),
                    feed_text=self.request.get("feedback_text"))
        a.put()
        
        path = os.path.join(os.path.dirname(__file__), 'support_template_ty.html')
        self.response.out.write(template.render(path, {"utext": utext}))


class Terms(webapp.RequestHandler):
    def get(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        path = os.path.join(os.path.dirname(__file__), 'terms_template.html')
        self.response.out.write(template.render(path, {"utext": utext}))


class About(webapp.RequestHandler):
    def get(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        path = os.path.join(os.path.dirname(__file__), 'about_template.html')
        self.response.out.write(template.render(path, {"utext": utext}))

class AddArticle(webapp.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        error_message = traceback.format_exc()  # Get the traceback.
        logging.error(error_message)            # Log the traceback.
        #self._serve_error(500)                  # Serve the error page.
        self.error(500)
        self.response.out.write('<html><body><h2>Sorry! We had problems with our server! Those computers...</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>')
        return ''
        
    def get(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        if (self.request.get('min')):
            path = os.path.join(os.path.dirname(__file__), 'min_addarticle_template.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'addarticle_template.html')
        a = self.request.get('url')
        if (a != None):
            u = urllib.unquote(a)
            a = Article()
            addarticle.get_article_details(u, a)
        else:
            a = common.Article()
        self.response.out.write(template.render(path, {"utext": utext, "article": a}))

    def post(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if user:
            utext = rpxusers.create_logout_html(self.request.host, user, self.request.url)
        else:
            utext = rpxusers.create_login_html(self.request.host, self.request.url)
        if (self.request.get('min')):
            path = os.path.join(os.path.dirname(__file__), 'min_addarticle_complete_template.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'addarticle_complete_template.html')

        a = common.Article()
        # fill a
        def sanitize(x): return x.replace('<','&lt;').replace('>','&gt;')
        a.url = sanitize(self.request.get('url'))
        try:
            a.created = sanitize(self.request.get('date'))
        except:
            a.created = ''
        if (a.created == ''): a.created = datetime.datetime.now()
        a.pic_url = sanitize(self.request.get('pic_url'))
        a.desc = sanitize(self.request.get('desc'))
        a.title = sanitize(self.request.get('title'))
        a.source = sanitize(self.request.get('source'))
        logging.debug('User submitted: %s %s %s %s %s'%(a.url,a.created,a.title,a.desc,a.source))
        pipeline.fetch([a])
        self.response.out.write(template.render(path, {"utext": utext}))

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/search', Search),
                                      ('/admin', admin.AdminPage),
                                      ('/tip', admin.TipPage),
                                      ('/article', ArticlePage),
                                      ('/ajax_handler', AjaxRelevance),
                                      ('/keyword', admin.KeywordPage),
                                      ('/keyword_edit', admin.KeywordEditPage),
                                      ('/user_edit', admin.UsersEditPage),
                                      ('/source', admin.SourcePage),                                      
                                      ('/cblogin', LoginCallback),
                                      ('/support', Support),
                                      ('/terms', Terms),
                                      ('/about', About),
                                      ('/addarticle',AddArticle),
                                      ('/.*', MainPage)], #all others are redirected
                                     debug=False)
def main():
    #pipeline.main()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
