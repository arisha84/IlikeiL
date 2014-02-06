import feedparser
import processarticle
import keywords
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging
import logic
import common
from google.appengine.api.labs import taskqueue

class prepare_fetch(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url='/fetch')
    
def fetch(fetchedArticles=None):
    logging.debug("Fetch articles have been called")
    
    i = 0    
    if (fetchedArticles == None):
        fetchedArticles = feedparser.fetchArticles()

    for fetchedArticle in fetchedArticles:  
        should_add_article = processarticle.process_article(fetchedArticle)
        if (should_add_article):
            processarticle.add_new_article_to_db(fetchedArticle)
            i += 1

    logging.debug("Fetching articles have completed successfully. %s articles were added"%i)
    
    #clean cache if new article was added
    if (i > 0):
        logic.cleanCache(common.Article())
    return i

#main()

class Done(webapp.RequestHandler):
    def get(self):
        i = fetch()
        self.response.out.write('<html><body><h2>%d articles added to the DB</h2><a title="iLike-IL" href="/"><img src="static/logo80.jpg" alt="ilikeil"></a></body></html>'%i)

    def post(self):
        i = fetch()
        self.response.out.write('<html><body><h2>%d articles added to the DB</h2></body></html>'%i)

        
application = webapp.WSGIApplication(
                                     
                                     [('/prepare_fetch', prepare_fetch),
                                     ('/fetch', Done)],
                                     debug=True)

def main():
    #pipeline.main()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
