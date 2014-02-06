import addarticle
import cgi
import common
import os
import keywords
import rpxusers
import logging
from google.appengine.ext.webapp import template

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import logic

class AlreadyExistsException(Exception):
    pass

class AdminPage (webapp.RequestHandler):
    def get(self):
        user = rpxusers.getCurrentUser(self.request, self.response)
        if not user:
            self.redirect('/')
        elif user.user_level != 3:
            ##self.response.out.write('<input type="button" onclick="history.back()" value="unauthorized" /></body></html>')
            self.redirect('/')
        else:
            if (None != self.request.get('tipurl')):
                tp = common.Tip()
                addarticle.get_article_details(self.request.get('tipurl'), tp)
            else:
                tp = None
            disp(self, None, None, tp)
            
            
def disp(self, errMsgKeywords,errMsgTip, tp=None):
    sources = db.GqlQuery("SELECT * FROM Sources")
    keywords = db.GqlQuery("SELECT * FROM Keyword")
    users = db.GqlQuery("SELECT * FROM IlikeUser")
    template_values = {
        'sources'  : sources,
        'keywords' : keywords,
        'users'    : users,
        'err'      : errMsgKeywords,
        'errTip'   : errMsgTip,
        'tip'      : tp
        }                        
    path = os.path.join(os.path.dirname(__file__), 'admin.html')
    self.response.out.write(template.render(path, template_values))       
        
        
class TipPage(webapp.RequestHandler):
    changed = False
    def post(self):
        errMsg = None
        try:            
            newTip = common.Tip()
            newTip.title = cgi.escape(self.request.get('title'))
            newTip.url = cgi.escape(self.request.get('url'))          
            keywords_text = cgi.escape(self.request.get('keywords'))
            keywords_text = keywords_text.replace(',',' ')
            keywords_list = keywords_text.split()
            processed_keywords_list = []
            for keyword in keywords_list:
                processed_keyword = keyword.strip().lower()
                if (db.GqlQuery("SELECT * FROM Keyword WHERE text = :text ", text=processed_keyword).get() != None):
                    processed_keywords_list.append(processed_keyword)                      
            newTip.keywords = processed_keywords_list       
            newTip.desc = cgi.escape(self.request.get('description'))
            newTip.pic_url = cgi.escape(self.request.get('thumb'))
            newTip.language = cgi.escape(self.request.get('language'))
            if (db.GqlQuery("SELECT * FROM Tip WHERE url ='"+newTip.url.replace("'","''")+"'").get() != None):
                db.GqlQuery("SELECT * FROM Tip WHERE url ='"+newTip.url.replace("'","''")+"'").get().delete()
                newTip.put()
                changed = True
                raise AlreadyExistsException()
            newTip.put()
            changed = True
        except AlreadyExistsException:
            errMsg = 'Tip Already exists. Tip info has been updated'
        except:
            errMsg = 'error occurred, did you fill all the fields?'
        if (changed):
            logic.cleanCache(common.Tip())
            logging.debug('tip changed/added')  
        disp(self, None, errMsg)
        
class KeywordPage(webapp.RequestHandler):
    def post(self):                                
        text = cgi.escape(self.request.get('text'))
        err_msg = None
        if text == '':
          err_msg = 'keyword cannot be empty'
        else:
            try:
                weight = int(cgi.escape(self.request.get('weight')))                
                if weight < 0:
                    err_msg ='keyword must be positive!'
                else:                                                                                                 
                    keywords.add_keyword_to_db(text, weight)                
            except:
                err_msg = 'keyword weight must be a number'            
        disp(self, err_msg, None)       
            
class SourcePage(webapp.RequestHandler):
    def post(self):  
        counter = 0    
        for k, v in self.request.POST.iteritems():
            try:
                key = db.Key(k.split('_')[1])
                source = common.Sources.get(key)
                if (k.split('_')[0] == 'source'):
                    if (source.weight != int(v)):
                        source.weight = int(v)
                        source.put()
                        counter += 1
                else:
                    if ((v == 'True') and (source.volatile == False)):
                        source.volatile = True
                        source.put()
                        counter += 1
                    elif ((v == 'False') and (source.volatile == True)):
                        source.volatile = False
                        source.put()
                        counter += 1
            except:
                pass
        
        if (counter > 0):
            logic.cleanCache(common.Sources())
        logging.debug('%d sources were changed'%counter)
        self.redirect('/admin')            
        ##self.response.out.write('changes applied!')
        ##self.response.out.write('<input type="button" onclick="history.back()" value="ok" /></body></html>')
    
class KeywordEditPage(webapp.RequestHandler):
    def post(self):      
        for k, v in self.request.POST.iteritems():
            try:
                key = db.Key(k.split('_')[1])
                keyword = common.Keyword.get(key)
                if (keyword.weight != int(v)):
                    keyword.weight = int(v)
                    if keyword.weight == 0:
                        keyword.delete()
                    else:
                        keyword.put();
            except:
                pass
        self.redirect('/admin')
        ##self.response.out.write('keywords changed!')
        ##self.response.out.write('<input type="button" onclick="history.back()" value="ok" /></body></html>')            
                     
class UsersEditPage(webapp.RequestHandler):
    def post(self):      
        for k, v in self.request.POST.iteritems():
            try:
                key = db.Key(k.split('_')[1])
                user = common.IlikeUser.get(key)
                if (user.user_level != int(v)):    
                    user.user_level = int(v)
                    if user.user_level == 1:
                        user.voting_weight = 1                    
                    elif user.user_level == 2:
                        user.voting_weight = 5   ##give more weight to power users and admins
                    elif user.user_level == 3:
                        user.voting_weight = 10
                    if user.user_level == 0:
                        user.delete()
                    else: 
                        user.put();
            except:
                pass
        self.redirect('/admin')
        ##self.response.out.write('user changed!')
        ##self.response.out.write('<input type="button" onclick="history.back()" value="ok" /></body></html>')            
#from django import template
#from django.template.defaultfilters import stringfilter
#@register.filter 
#def multiply(value, arg): 
#    return int(value) * int(arg)         
#            
#            
                    
                       
