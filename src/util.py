import urllib2
from BeautifulSoup import BeautifulSoup

if __name__ == '__main__':
    pass

ID='ilikeil'

def http_request(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', ID)]
    try:
        return opener.open(url).read()
    except:
        return ''

def extract_text(html):
    soup = BeautifulSoup(html)
    desc = u''
    textList = soup.findAll(text=True)   
    for text in textList:
        desc += text + ' '
    return desc

html_escape_table = {
"&": "&amp;",
'"': "&quot;",
"'": "&#39;", # IE sucks!
">": "&gt;",
"<": "&lt;",
}
def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)
                   