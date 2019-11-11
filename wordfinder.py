from urllib.request import urlopen
import re
import ssl
from bs4 import BeautifulSoup
import sqlite3

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# count the frequency of the word "KBCS"
url = "https://sydneybats.org.au/"
resp = urlopen(url, context=ctx)
html_raw = resp.read().decode()
html = html_raw.replace("&nbsp;", " ")


def tag_visible(element):
    if element.parent.name in ["style", "script", "head", "title", "meta", "[document]"]:
        return False
    return True


def text_from_html(body):
    count = 0
    soup = BeautifulSoup(body, "html.parser")
    # return all tags which hold text between opening and closing tag
    invalid_tags = ["b", "strong", "em", "i"]
    for tag in invalid_tags:
        for match in soup.find_all(tag):
            match.unwrap()
    texts = soup.find_all(text=True)
    # filer out all tags which are not visible on the webpage, returns filer object which is iterable
    visible_texts = filter(tag_visible, texts)
    for t in visible_texts:
        sentences = t.split(". ")
        for s in sentences:
            if "KBCS" in s:
                print("---------------------------------")
                print(s)
                count = count + 1
    print(count, "sentences")
    # return u"\n".join(t.strip()


text = text_from_html(html)

# b/strong/i/em tags
# save tag name in colum as well. to find out if within menu bar
