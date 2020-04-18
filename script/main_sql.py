import re

from psycopg2 import connect, sql
import requests
from bs4 import BeautifulSoup

from script.config import *

conn = connect(host=host, port=port, database=database, user=user, password=password)
cur = conn.cursor()

# Create table to store vocabulary entries
cur.execute("CREATE TABLE IF NOT EXISTS vocabulary (id integer NOT NULL PRIMARY KEY, "
            "kanji varchar, hiragana varchar NOT NULL, english varchar NOT NULL, jlpt_level varchar not null);")
# Create table to store example sentences for each entry
cur.execute("CREATE TABLE IF NOT EXISTS example (id SERIAL NOT NULL PRIMARY KEY, "
            "sentence varchar, vocab_id integer REFERENCES vocabulary (id));")
conn.commit()

# TODO
base_url = 'http://www.tanos.co.uk'
# vocab_urls = ['http://www.tanos.co.uk/jlpt/jlpt5/vocab/',
#               'http://www.tanos.co.uk/jlpt/jlpt4/vocab/',
#               'http://www.tanos.co.uk/jlpt/jlpt3/vocab/',
#               'http://www.tanos.co.uk/jlpt/jlpt2/vocab/',
#               'http://www.tanos.co.uk/jlpt/jlpt1/vocab/']
vocab_urls = ['http://www.tanos.co.uk/jlpt/jlpt5/vocab/']
jlpt_level_counter = 5


def get_example_content(item):
    """
    For a list item on the vocab example page, beautify it.
    :param item: li tag
    :return: example sentence string
    """
    if item:
        try:
            result = re.sub('\n', '', item)
            result = result.split('\t')
            result = f"JP: {result[0]}\n EN {result[1]}"
            return result
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
    vocab_id = 1
    for row in rows:
        print(f"Scraping for level {jlpt_level} - {vocab_id}/{len(rows)}")
        cells = row.findAll('td')
        table_items = [cell.get_text() for cell in cells]
        # Not all vocab entries have a kanji, so we grab this page from the second column (3rd would work too)
        # examples_page = cells[1].find('a')
        # examples_page = base_url + examples_page['href'] if examples_page else ""


        # Add row to vocabulary table
        cur.execute(sql.SQL("insert into vocabulary values (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING "),
                    [vocab_id, table_items[0], table_items[1], table_items[2], jlpt_level])
        conn.commit()
        vocab_id += 1

jlpt_level_counter -= 1


# Traverse the examples page
# print(f"Crawling example page for kanji {table_items[1]}")
# example_sentence_list = []
# if examples_page:
#     examples_page_html = requests.get(examples_page).content
#     examples_soup = BeautifulSoup(examples_page_html, 'html.parser')
#     page_divs = examples_soup.find(id='contentright')
#     raw_examples = page_divs.find_next('ul')
#
#     if raw_examples:
#         for li in raw_examples.find_all('li'):
#             example = get_example_content(li.text)
#             example_sentence_list.append(example)
#
# # Add everything to a list to append as an excel row
# to_insert.append(str(example_sentence_list))


cur.close()
conn.close()
