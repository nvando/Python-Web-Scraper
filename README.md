# Python Web Scraper


This program uses Python and SQLite3 to scrape a pre-defined website and search for specific words within visible text on each page. The HTML is parsed using the Python library Beautiful Soup and the sentences containing the search word are stored in a SQLite database together with the page's URL. This program was build for an organisation that changed their name as part of a rebrand and needed to checQLite database together with the page's URLQLite database together with the page's URL all occurrences of their name within their WordPress website, and manually changed where required.


The Program consists of two python files, which needs to be run seperately:

1. crawler.py
2. wordfinder.py

## 1. Crawler.py

Crawler.py  will crawl through a specific website, indexes all webpages containing html and stores it in the SQLite3 database 'Crawler' in the table "Pages".

This program needs to be run first, and will create the Crawler database. It will then ask the user to enter the url of the website that needs to be searched. The full url needs to be entered, inlcuding the scheme (http:// or https://) part. 

It will also the ask the user for the number of pages that need to be retrieved in one sitting. This allows the user to index the website in batches, as depending on the size of the page, this may take some time. 

If the program is run for the first time, the webpage of the input url is retrieved, and the HTML is parsed using Beautiful Soup. All links to internal webpages are added to the 'Pages' table within the database. External links or links to non-HTML pages suchs as PDF or images are ignored.

It will then fetch a random unretrieved url from the Page's table, retrieve the HTML, parse it with beautiful soup and search and add all internal links to the table. This will repeat itself until the input number of the user has been reached, or all internal links have been retrieved. 

If the user's input number has been reached, he can either enter another number to retrieve more webpages, or quit the program by pressing enter. When Crawler.py is restarted, it will continue with indexing the input url. To start a new crawl of a different website, the 'Crawler.sqlite3' database needs to be deleted before running 'crawler.py'

## 2. Wordfinder.py

Wordfinder.py searched the HTML of the retrieved webpages for specific words, extracts the sentences containing those words and adds those to a table called 'Matches' within the Crawler.sqlite3 database.

Wordfinder.py can only be run after Crawler.py has been run at least once and created the Crawler.sqlite3 database. After starting wordfinder.py, it will ask the user what the word is or words are that the website needs to be searched for. It will then retrieve the HTML from the urls in the Pages table and use Beautiful Soup to find the 'search words' within the webpage. 





