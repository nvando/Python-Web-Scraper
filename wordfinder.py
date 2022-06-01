from urllib.request import urlopen
from urllib.parse import urlparse
import re
import ssl
from bs4 import BeautifulSoup
import sqlite3


body_tags = ["h1", "h2", "h3", "h4", "p", "li", "lu", "span"]


def extract_sentences_body(soup, tags, target_word):
    #  extract sentences which include the target word
    #  from html body text (text within 'p', 'h1' to 'h4', 'li', and 'span' tags)
    #  add the matched sentences into the Matches table
    #  count the number of sentences with matches
    global sent_count
    for tag in tags:
        for t in soup.findAll(tag):
            tag_text = t.get_text()
            # split sentences based after a dot followed
            # by one or multipe white spaces,
            # or after an exlemation or question mark.
            # '?:' means a non-capturing group , 's+' matches a string of whitespace characters
            sentences = re.split("(?:\.\s+|\!|\?)", tag_text)

            for s in sentences:
                # search each sentence for a match with the target word, ignore case
                if target_word in s.lower():  # CHANGE TO TARGET WORD, ASK FOR WITH INPUT
                    cur.execute(
                        """INSERT INTO Matches (page_id, path, sentence) VALUES (?, ?, ?)""",
                        (page_id, url_path, s),
                    )
                    conn.commit()
                    print(f"Matched within {tag} tag: {s}")
                    print("--------------")
                    sent_count = sent_count + 1


def extract_sentences_repeated_blocks(block, target_word, id=None):
    #  extract sentences containing target word
    #  from the footer or menu items within the header
    #  these blocks are repeated on every page
    #  but the matched sentences are added into the database only once
    #  with url = 'header' or 'footer' and page_id = 'NA'

    # first make sure header/footer has been searched already
    cur.execute("SELECT * FROM pages WHERE url = ?", (block,))
    if cur.fetchone() is None:
        # select a row from pages which contains html. Header/footer is repeated on
        # every page, so it doesn't matter which page is chosen
        cur.execute("""SELECT html FROM Pages WHERE html is not NULL ORDER BY RANDOM() LIMIT 1""")
        row = cur.fetchone()
        html = row[0]

        # parse html with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # extract header/footer from parsed html
        searched_soup = soup.find(block, id)
        if not searched_soup is None:
            extracted_block = searched_soup.extract()
            text = extracted_block.get_text(separator="\n")
            sentences = re.split("\n", text)
            count = 0
            print(f"searching {block} ")
            for s in sentences:
                if target_word in s.lower():
                    cur.execute(
                        """INSERT INTO Matches (page_id, path, sentence) VALUES ('NA', ?, ?)""",
                        (block, s),
                    )
                    conn.commit()
                    print(f"""Found match in {block}. '{s}' added to database.""")
                    count = count + 1
            print(f"sentences in {block} containing the search word: {count}")
            cur.execute(
                """INSERT INTO Pages (url, sentences, html) VALUES (?,? , 'NA')""",
                (
                    block,
                    count,
                ),
            )
            conn.commit()
        else:
            print(f"could not extract {block}")

    else:
        print(f"The {block} has already been checked for matches")


#########################################################################################################


# Connect to Crawler database and create 'Matches' table
conn = sqlite3.connect("Crawler.sqlite3")
cur = conn.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS Matches(
id INTEGER PRIMARY KEY,
page_id INTEGER,
path VARCHAR,
sentence VARCHAR
)"""
)

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

target_word = input("Enter the word(s) you want to search the site for: ").lower()
print(f"""The website will be searched for sentences which include the word(s) '{target_word}'.""")


# find target word within menu items of header and add to Matches
extract_sentences_repeated_blocks("header", target_word)
# check if menu items within the footer contain the target word
extract_sentences_repeated_blocks("footer", target_word)


# check if menu items within the footer contain the target word
while True:
    # select random unretrieved url from the Pages database
    # check for macthes in the html of the body
    # add matched senteces to Pages
    cur.execute(
        """SELECT id, url, html FROM Pages WHERE sentences is NULL and html is not NULL and error is NULL ORDER BY RANDOM() LIMIT 1"""
    )
    try:
        row = cur.fetchone()
        page_id = row[0]
        url = row[1]
        html = row[2]
        print("searching url: ", url)
    except:
        print("No unretrieved pages found in database")
        break

    # retrieve url path from absolute url

    url_path = urlparse(url).path

    # parse html with beautiful soup
    soup = BeautifulSoup(html, "html.parser")

    # extract and count number of sentences containing the target word within one webpage
    sent_count = 0
    body_matches = extract_sentences_body(soup, body_tags, target_word)
    print(f"Finished searching this page. Found {sent_count} sentences with match")
    cur.execute("""UPDATE Pages SET sentences = ? WHERE url = ?""", (sent_count, url))
    conn.commit()


cur.close()
