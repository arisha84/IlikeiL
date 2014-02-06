import logging
import urllib
import re
import sys
from util import http_request
import datetime
import parser

RE_META_TAGS = r'<meta[^>]*name=\"(?:og:)?([^"]*)\"[^>]*content=\"([^"]*)\"[^>]*>'
RE_TITLE_TAG = r'<(title)>([^<]*)</title>'
RE_OG_TAGS = r'<meta[^>]*property=\"(?:og:)?([^"]*)\"[^>]*content=\"([^"]*)\"[^>]*>'
RE_CANONICAL = r'<link[^>]*rel=\"(canonical)\"[^>]*href=\"([^"]*)\"[^>]*>'

## Functions for parsing the HTML data using some heuristics:

def sanitize(x):
    try:
        return x.replace('<','&lt;').replace('>','&gt;').replace('\n','').replace('\r','').decode('utf-8')
    except:
        return x.replace('<','&lt;').replace('>','&gt;').replace('\n','').replace('\r','')

def _get_meta_tags(data):
    return [(x[0].lower(),sanitize(x[1].strip())) for x in re.findall(RE_META_TAGS, data)]

def _get_title_tag(data):
    return [(x[0].lower(),sanitize(x[1].strip())) for x in re.findall(RE_TITLE_TAG, data)]

def _get_ogmeta_tags(data):
    return [(x[0].lower(),sanitize(x[1].strip())) for x in re.findall(RE_OG_TAGS, data)]

def _get_url(data):
    return [(x[0].lower(),sanitize(x[1].strip())) for x in re.findall(RE_CANONICAL, data)]

## This function uses the parser functions to build a large dictionary
def _get_data_dict(data):
    # We do it reverse order so the most important is last (to overwrite old entries)
    ret_dict = {}
    ret_dict.update(dict(_get_title_tag(data)))
    ret_dict.update(dict(_get_meta_tags(data)))
    ret_dict.update(dict(_get_ogmeta_tags(data)))
    ret_dict.update(dict(_get_url(data)))
    return ret_dict

## This function retrieves only the relevant entries from the entire dictionary
def get_info_dict(data):
    ret_dict = {}
    alldata = _get_data_dict(data)
    # title
    if (alldata.has_key('title')):
        ret_dict['title'] = alldata['title']

    # description
    if (alldata.has_key('description')):
        ret_dict['description'] = alldata['description']
    elif (alldata.has_key('desc')):
        ret_dict['description'] = alldata['desc']

    # publish date
    potential_dates = filter(lambda(x): -1 != x.find('date'), alldata.keys())
    if (len(potential_dates) > 0):
        ret_dict['date'] = alldata[potential_dates[0]]

    # thumbnail
    if (alldata.has_key('image')):
        ret_dict['image'] = alldata['image']
    elif (alldata.has_key('img')):
        ret_dict['image'] = alldata['img']
    else:
        potential_images = filter(lambda(x): -1 != x.find('image'), alldata.keys())
        if (len(potential_images) > 0):
            ret_dict['image'] = alldata[potential_images[0]]

    # source name
    if (alldata.has_key('site_name')):
        ret_dict['source'] = alldata['site_name']
    elif (alldata.has_key('source')):
        ret_dict['source'] = alldata['source']
    
    # url
    if (alldata.has_key('canonical')):
        ret_dict['url'] = alldata['canonical']
    elif (alldata.has_key('url')):
        ret_dict['url'] = alldata['url']

    # keywords
    if (alldata.has_key('keywords')):
        ret_dict['keywords'] = alldata['keywords']

    return ret_dict


def get_article_details(url, ret):
        data = http_request(url)
        article_dict = get_info_dict(data)
        logging.debug(article_dict)
        #ret = common.Article()
        def CAG(x):
            if (article_dict.has_key(x)): return article_dict[x]
            else: return None
        #ret.url = CAG('url')
        #if (ret.url == None):
        ret.url = url
        try:
            ret.created = parser.parse(CAG('date'))
        except:
            ret.created = datetime.datetime.now()
        if (ret.created == None): ret.created = datetime.datetime.now()
        ret.pic_url = CAG('image')
        ret.desc = CAG('description')
        ret.title = CAG('title')
        ret.source = CAG('source')
        return ret

#data = urllib.urlopen(sys.argv[1]).read()
#print get_info_dict(data)
