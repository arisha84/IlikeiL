from google.appengine.ext import db
from google.appengine.api import urlfetch
from django.utils import simplejson
import urllib
import logging
from common import IlikeUser

def getUserObjectByIdentifier(token, identifier, name, nickname, email):
    a = IlikeUser.gql("WHERE identifier=:1", identifier)
    b = [i for i in a]
    if (len(b) == 0):
        c = IlikeUser(token=token, identifier=identifier, name=name, nickname=nickname, email=email)
        c.put()
    else:
        c = b[0]
        c.token = token
        c.put()
    return c

def getUserObjectByIdentifierDontCreate(identifier):
    a = IlikeUser.gql("WHERE identifier=:1", identifier)
    b = [i for i in a]
    if (len(b) == 0):
        return None
    else:
        return c


def getUserObjectByToken(token):
    a = IlikeUser.gql("WHERE token=:1", token)
    b = a.get()
    return b


def getUserInfo(token, res=None):
    # Try to search user in our datastore using its token
    a = getUserObjectByToken(token)
    if (None != a):
        if (res != None):
            res.out.write("hgh")
            res.headers['Set-Cookie']='token=%s'%token#; Domain=localhost:8080; Max-Age=360; Path=/'%token
        return a
    # Then he doesn't exist, so check if token is valid:

    url = 'https://rpxnow.com/api/v2/auth_info'
    args = {
      'format': 'json',
      'apiKey': '697fc776badd895035c09349cbcb27208a663c4f',
      'token': token
      }

    r = urlfetch.fetch(url=url,
                       payload=urllib.urlencode(args),
                       method=urlfetch.POST,
                       headers={'Content-Type':'application/x-www-form-urlencoded'}
                       )

    json = simplejson.loads(r.content)

    if json['stat'] == 'ok':
      identifier = json['profile']['identifier']
      nickname = json['profile']['preferredUsername']
      try:
          email = json['profile']['email']
      except:
          email = None
      name = json['profile']['displayName']
      a = getUserObjectByIdentifier(token, identifier, name, nickname, email)
      if (res != None):
          #res.headers['Set-Cookie']='token=%s; Domain=localhost; Max-Age=360; Path=/;'%token
          res.headers['Set-Cookie']='token=%s'%token
          #res.set_cookie('token', token, max_age=360, path='/', domain='localhost:8080', secure=True)
      return a
    else:
      return None


def getCurrentUser(req, res=None):
    cookie_token = req.cookies.get('token')
    if (cookie_token == None):
        return None
    return getUserObjectByToken(cookie_token)

def getCommentsRank(rank):
    a = IlikeUser.gql("WHERE comments_counter>:1", rank)
    return a.count()

def create_login_html(host, url):
    return '<a class="rpxnow" onclick="return false;" href="https://ilike-il.rpxnow.com/openid/v2/signin?token_url=http%%3A%%2F%%2F%s%%2Fcblogin%%3Fredirect%%3D%s">Login</a>' % (host, urllib.quote(url, ''))

def create_logout_html(host, user, url):
    return 'Hello, %s <a class="rpxnow" onclick="return false;" href="https://ilike-il.rpxnow.com/openid/v2/signin?token_url=http%%3A%%2F%%2F%s%%2Fcblogin%%3Fredirect%%3D%s"><small>(Not you?)</small></a>&nbsp;&nbsp;<a href="http://%s/cblogin?redirect=%s">Logout</a>' % (user.name, host, urllib.quote(url,''), host, urllib.quote(url,''))