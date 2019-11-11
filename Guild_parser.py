from urllib.request import urlopen
import urllib.error
from urllib.parse import urljoin
from urllib.parse import urlparse
import re
import ssl
from bs4 import BeautifulSoup
import sqlite3

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# create table which includes all page links with html
conn = sqlite3.connect("KBCS")
cur = conn.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS Pagelinks(
id INTEGER PRIMARY KEY,
url TEXT UNIQUE,
html TEXT,
error INTEGER
)"""
)


# check to see if spider.py has been run before and retrieved pages or if we need to start a new crawl
cur.execute(
    """SELECT url FROM Pagelinks WHERE html is NULL and error is NULL ORDER BY RANDOM() limit 1"""
)
row = cur.fetchone()
if row is not None:
    print("Restarting existing crawl. Delete TheGuild.sqlite if you want to start a fresh crawl")
else:
    # starting new crawl
    starturl = input("Enter URL: ")
    if len(starturl) < 1:
        starturl = "https://sydneybats.org.au/"
    if starturl.endswith("/"):
        starturl = starturl[:-1]
    web = starturl
    if starturl.endswith("htm") or starturl.endswith("html"):
        pos = starturl.find("/")
        web = starturl[:pos]
    if len(starturl) > 1:
        # insert the website's url in database
        cur.execute(
            """INSERT OR IGNORE INTO Pagelinks (url, html, error) VALUES (?, NULL, NULL)""",
            (starturl,),
        )
    conn.commit()


# loop through a predefined number of urls on the website
number_urls = 0
while True:
    if number_urls < 1:
        sval = input("Enter number of pages to retrieve, or press enter to quit: ")
        # break out of the loop with enter
        if len(sval) < 1:
            break
        number_urls = int(sval)
    number_urls = number_urls - 1

    cur.execute(
        """SELECT id, url FROM Pagelinks WHERE html is NULL and ERROR IS NULL ORDER BY RANDOM() LIMIT 1"""
    )
    try:
        row = cur.fetchone()
        id = row[0]
        url = row[1]
        print(url, " ")
    except:
        # why not use "if row is None: break"? what does cur.fetchone return?
        print("No unretrieved HTML pages found")
        number_urls = 0
        break

    # returns html document in a single big string (incl. new lines), BS decodes from bytes (likely UTF-8)
    try:
        resp = urlopen(url, context=ctx)
        html = resp.read()

        if resp.getcode() != 200:
            print("Error on page: ", html.getcode())
            cur.execute("""UPDATE Pagelinks SET error = ? WHERE url = ?""", (html.getcode(), url))

        if "text/html" != resp.info().get_content_type():
            print("non text/html page - ignored")
            cur.execute(
                """UPDATE Pagelinks SET error = ? WHERE url = ?""", ("non text/html page", url)
            )
            conn.commit()
            continue

        # parse html with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

    except KeyboardInterrupt:
        print("\n Program interupted by user")
        break
    except:
        print("Unable to retrieve or parse page")
        cur.execute("""UPDATE Pagelinks SET error = -1 WHERE url = ?""", (url,))
        conn.commit()
        continue

    cur.execute("""UPDATE Pagelinks SET html = ? WHERE url = ?""", (html, url))
    # Retrieve all of the anchor tags (objects)
    count = 0
    tags = soup("a")
    for tag in tags:
        href = tag.get("href", None)
        if href is None:
            continue
        if len(href) < 1:
            continue
        if href.endswith(".png") or href.endswith("jpeg") or href.endswith("gif"):
            continue
        if href.endswith("/"):
            href = href[:-1]
        # Resolve relative references like href="/contact"
        if href.startswith("/"):
            parsed = urlparse(href)
            if len(parsed.scheme) < 1:
                href = urljoin(url, href)
        if not href.startswith(starturl):
            continue

        cur.execute(
            """INSERT OR IGNORE INTO Pagelinks (url, html, error) VALUES (?, NULL, NULL)""", (href,)
        )
        count = count + 1
        conn.commit()

    print(count, "links")
cur.close()
