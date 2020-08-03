import re

from psycopg2 import connect, sql
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from script.config import *

# Scraping base urls
base_url = 'http://www.tanos.co.uk'
vocab_urls = ['http://www.tanos.co.uk/jlpt/jlpt5/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt4/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt3/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt2/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt1/vocab/']
# Counters
jlpt_level_counter = 5
vocab_id = 1
start = datetime.now()
# Database connection
conn = connect(host=host, port=port, database=database, user=user, password=password)
cur = conn.cursor()

# Create table to store vocabulary entries
cur.execute("CREATE TABLE IF NOT EXISTS vocabulary (id integer NOT NULL PRIMARY KEY, "
            "kanji varchar, hiragana varchar NOT NULL, english varchar NOT NULL, jlpt_level varchar not null);")
# Create table to store example sentences for each entry
cur.execute("CREATE TABLE IF NOT EXISTS example (id SERIAL NOT NULL PRIMARY KEY, "
            "sentence_jp varchar, sentence_en varchar, vocab_id integer REFERENCES vocabulary (id));")
conn.commit()


def get_example_content(item):
    """
    For a list item on the vocab example page, beautify it.
    :param item: li tag
    :return: example sentence string
    """
    if item:
        try:
            result = re.sub('\n', '', item)
            # Split examples into their language category
            result = result.split('\t')
            result_jp = f"{result[0]}"
            result_en = f"{result[1]}"
            return result_jp, result_en
        except IndexError:
            pass


for page_url in vocab_urls:
    print(f"Crawling link {page_url}")
    jlpt_level = f"N{jlpt_level_counter}"
    vocab_page_html = requests.get(page_url).content
    vocab_soup = BeautifulSoup(vocab_page_html, 'html.parser')

    # We get the second table on the page, and remove the table headers
    table = vocab_soup.findAll('table')[1]
    rows = table.findAll('tr')
    rows = rows[1:]

    # Looping over rows to extract data
    for row in rows:
        time_taken = datetime.now() - start
        print(f"Scraping level {jlpt_level} | {vocab_id} entries scraped | Script has been running for {time_taken}")
        cells = row.findAll('td')
        table_items = [cell.get_text() for cell in cells]
        # Add row to vocabulary table
        cur.execute(sql.SQL("insert into vocabulary values (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING "),
                    [vocab_id, table_items[0], table_items[1], table_items[2], jlpt_level])

        # Not all vocab entries have a kanji, so we grab the example from the second column (3rd would work too)
        examples_page = cells[1].find('a')
        examples_page = base_url + examples_page['href'] if examples_page else ""

        # Traverse the examples page
        if examples_page:
            examples_page_html = requests.get(examples_page).content
            examples_soup = BeautifulSoup(examples_page_html, 'html.parser')
            page_divs = examples_soup.find(id='contentright')
            raw_examples = page_divs.find_next('ul')
            if raw_examples:
                for li in raw_examples.find_all('li'):
                    try:
                        example_jp, example_en = get_example_content(li.text)
                        cur.execute(
                            sql.SQL("insert into example (sentence_jp, sentence_en, vocab_id) "
                                    "values (%s, %s, %s) ON CONFLICT DO NOTHING "),
                            [example_jp, example_en, vocab_id])
                    # Some example sentences have a garbled structure, so we skip those
                    except TypeError:
                        pass
        vocab_id += 1
        conn.commit()
    jlpt_level_counter -= 1

cur.close()
conn.close()
