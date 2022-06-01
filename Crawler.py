from urllib.request import urlopen
from urllib.parse import urljoin
from urllib.parse import urlparse
import ssl
from bs4 import BeautifulSoup
import sqlite3

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# create table which includes all pagelinks with html
conn = sqlite3.connect("Crawler.sqlite3")
cur = conn.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS Pages(
id INTEGER PRIMARY KEY,
url TEXT UNIQUE,
sentences INTEGER,
html TEXT,
error INTEGER
)"""
)


# check to see if crawler.py has been run before and retrieved pages or if we need to start a new crawl
cur.execute("""SELECT url FROM Pages WHERE id = 1""")
row = cur.fetchone()
if row is not None:
    starturl = row[0]
    print(
        f"Restarting existing crawl of {starturl}. If you want to start a fresh crawl, quit program and delete Pages database."
    )

# starting new crawl
# ask for url and check if it is valid
else:
    starturl = None
    while starturl is None:
        input_url = input("Enter the full website's url: ")
        parsed_url = urlparse(input_url)
        if not bool(parsed_url.scheme):
            print(
                "Not a valid url, enter the complete url including the 'http://' or 'https://' component: "
            )
            continue
        elif input_url.endswith("/"):
            starturl = input_url[:-1]
        elif input_url.endswith("htm") or input_url.endswith("html"):
            pos = input_url.find("/")
            starturl = input_url[:pos]
        else:
            starturl = input_url

    # insert the website's url in database
    cur.execute(
        """INSERT OR IGNORE INTO Pages (url, html, error) VALUES (?, NULL, NULL)""",
        (starturl,),
    )
    conn.commit()


# loop through a predefined number of urls on the website
number_urls = 0
while True:
    if number_urls < 1:
        sval = input("Enter number of pages to retrieve, or press enter to quit: ")
        # break out of the loop with enter
        if len(sval) < 1 or int(sval) == 0:
            break
        number_urls = int(sval)
    number_urls = number_urls - 1

    cur.execute(
        """SELECT id, url FROM Pages WHERE html is NULL and error is NULL ORDER BY RANDOM() LIMIT 1"""
    )
    try:
        row = cur.fetchone()
        id = row[0]
        url = row[1]
        print(url, " ")

    except:
        print("No unretrieved HTML pages found")
        number_urls = 0
        break

    # returns html document in a single big string (incl. new lines), BS decodes from bytes (likely UTF-8)
    try:
        resp = urlopen(url, context=ctx)
        html = resp.read()

        if resp.getcode() != 200:
            print("Error on page: ", html.getcode())
            cur.execute("""UPDATE Pages SET error = ? WHERE url = ?""", (html.getcode(), url))

        # delete url from Pages if it links to non text/html page
        if "text/html" != resp.info().get_content_type():
            print("non text/html page - ignored")
            cur.execute("""DELETE FROM Pages WHERE url = ?""", (url,))
            conn.commit()
            continue

        # parse html with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

    except KeyboardInterrupt:
        print("\n Program interupted by user")
        break
    except:
        print("Unable to retrieve or parse page")
        cur.execute("""UPDATE Pages SET error = -1 WHERE url = ?""", (url,))
        conn.commit()
        continue

    cur.execute("""UPDATE Pages SET html = ? WHERE url = ?""", (html, url))
    # conn.commit()

    # Retrieve all of the anchor tags (objects) within the html and
    # add each internal link to the Pages database, if it is not already in there
    count = 0
    tags = soup("a")
    for tag in tags:
        href = tag.get("href", None)
        if href is None:
            continue
        if len(href) < 1:
            continue
        if href.endswith("/"):
            href = href[:-1]
        # ignore links to images or pdfs
        if (
            href.endswith(".png")
            or href.endswith(".jpeg")
            or href.endswith(".gif")
            or href.endswith(".jpg")
            or href.endswith(".pdf")
        ):
            continue
        # resolve relative links like href="/contact"
        if href.startswith("/"):
            parsed = urlparse(href)
            if len(parsed.scheme) < 1:
                href = urljoin(url, href)
        # ignore external links
        if not href.startswith(starturl):
            continue

        cur.execute(
            """INSERT OR IGNORE INTO Pages (url, html, error) VALUES (?, NULL, NULL)""", (href,)
        )
        count = count + 1
        conn.commit()

    print(count, "links")
cur.close()
