import main
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import os
from google.appengine.ext.webapp import template
import secretshandler

FACEBOOK_APP_ID = "125870884100192"
FACEBOOK_APP_SECRET = secretshandler.getSecret("FB_APP_SECRET").secret

import base64
import cgi
import Cookie
import email.utils
import hashlib
import os.path
import time
import urllib
import wsgiref.handlers
import main

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import rpxusers


class OnceHandler(webapp.RequestHandler):
    def get(self):
        secretshandler.setSecret("FB_APP_SECRET", "CHANGE THIS BEFORE YOU RUN ONCEHANDLER")
        self.response.out.write(secretshandler.getSecret("FB_APP_SECRET").secret)
        pass

class LoginHandler(webapp.RequestHandler):
    def get(self):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=self.request.path_url)
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")
            b=urllib.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read()
            response = cgi.parse_qs(b)

            if (response.has_key("access_token")):
                access_token = response["access_token"][-1]
            else:
                self.response.out.write(b)
                return
            # Download the user profile and cache a local instance of the
            # basic profile info
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))

            ident = "http://www.facebook.com/profile.php?id=%s"%str(profile["id"])

            user = rpxusers.getUserObjectByIdentifier(token=access_token, identifier=ident,
            name=str(profile["name"]), nickname=None, email=None)

#            user = User(key_name=str(profile["id"]), id=str(profile["id"]),
#                        name=profile["name"], access_token=access_token,
#                        profile_url=profile["link"])

                        
#            user.put()
            self.response.headers['Set-Cookie']='token=%s'%access_token
            self.redirect("/fbmain")
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" +
                urllib.urlencode(args))

    def post(self):
        path = os.path.join(os.path.dirname(__file__), 'fbpromo.html')
        self.response.out.write(template.render(path, dict()))



class FBMain(main.MainPage):
    template_file = "fb_articleboxes.html"



application = webapp.WSGIApplication([  ('/fblogin', LoginHandler),
                                        ('/fbonce', OnceHandler),
                                        ('/fbmain', FBMain)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
