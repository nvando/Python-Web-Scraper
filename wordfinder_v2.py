from urllib.request import urlopen
import re
import ssl
from bs4 import BeautifulSoup
import sqlite3


# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


conn = sqlite3.connect('TheGuild')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS PageMatches(
id INTEGER PRIMARY KEY,
page_id INTEGER,
url VARCHAR,
sentence VARCHAR
)''')

def extract_sentences(text, tags):
# extract sentences which include the target word
# from html body text (text within 'p', 'h1' and 'h2' tags)
# add sentences which match in Pagematches database
# and count the number of sentences with matches
    global sent_count
    for tag in tags:
        print('tag = ', tag)
        for tag in text.findAll(tag):
            tag_text = tag.get_text()
            sentences = re.split('(?:\.\s+|\!|\?)', tag_text)
            for s in sentences:
                # search each sentence for a match with the target word, ignore case
                if "guild" in s.lower():
                    cur.execute('''INSERT INTO PageMatches (page_id, url, sentence) VALUES (?, ?, ?)''', (page_id, url_short, s))
                    conn.commit()
                    print('--------------')
                    print(s)
                    sent_count = sent_count + 1

body_tags = ['h1', 'h2', 'h3', 'h4', 'p', 'li', 'span']

while True:
    # select random unretrieved url from Pagelinks database
    cur.execute('''SELECT id, url FROM Pagelinks WHERE sentences is NULL and html is not NULL and error is NULL ORDER BY RANDOM() LIMIT 1''')
    try:
        row = cur.fetchone()
        page_id = row[0]
        url = row[1]
        print(url)
    except:
        print ('No unretrieved pages found in database')
        quit()

    # retrieve root-relative from absolute url
    if url.endswith('warwidowsnsw.com.au'): url_short = url
    else: url_short = url.split('.au', 1)[1]

    # open url and retrieve html, in a byte string
    # decode to unicode string
    # open with beautiful soup
    resp = urlopen(url, context = ctx)
    html = resp.read().decode()
    soup = BeautifulSoup(html, 'html.parser')
    # extract header tag as menu items will be extracted and stored in the database differenlty.
    # all menu items containing the search word will be added to PageMatches as recurrent

    # extract header and custom footer tag for later use
    #  as the text within these tags are the same on every webpage these only need to be added to Pagematches once
    header = soup.find('header').extract()
    footer = soup.find('div', id="custom_footer").extract()

    # now extract and count number of sentences  containing the target word within one webpage
    sent_count = 0
    body_matches = extract_sentences(soup, body_tags)
    print(sent_count, "sentences with match")
    cur.execute('''UPDATE Pagelinks SET sentences = ? WHERE url = ?''', (sent_count, url))
    conn.commit()



# add all menu items within the header containing the target word to PageMatches as recurrent
header_text = header.get_text(separator="\n")
sentences = re.split('\n', header_text)
head_count = 0
for s in sentences:
    if "guild" in s.lower():
        cur.execute('''INSERT INTO PageMatches (page_id, url, sentence) VALUES ('NA', 'Menu', ?)''', (s,))
        conn.commit()
        print('menu item: ', s, 'added to database as recurrent')
        head_count = head_count + 1
print('sentences in footer containing the search word: ', fcount)
cur.execute('''INSERT INTO Pagelinks (url, sentences, html) VALUES ('Menu',? , 'NA')''', (head_count, ))
conn.commit()


# add text within custom footer containing the target word to PageMatches as recurrent
footer_text = footer.get_text(separator="\n")
sentences = re.split('\n', footer_text)
foot_count = 0
for s in sentences:
    if "guild" in s.lower():
        cur.execute('''INSERT INTO PageMatches (page_id, url, sentence) VALUES ('NA', 'Footer', ?)''', (s,))
        conn.commit()
        print('custom footer: ', s, 'added to database as recurrent')
        foot_count = foot_count + 1
print('sentences in footer containing the search word: ', foot_count)
cur.execute('''INSERT INTO Pagelinks (url, sentences, html) VALUES ('Footer',? , 'NA')''', (foot_count, ))
conn.commit()

cur.close()
