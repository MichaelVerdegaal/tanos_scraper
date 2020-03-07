import re

import requests
from bs4 import BeautifulSoup

from fileutil import return_workbook, filename


base_url = 'http://www.tanos.co.uk'
vocab_urls = ['http://www.tanos.co.uk/jlpt/jlpt5/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt4/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt3/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt2/vocab/',
              'http://www.tanos.co.uk/jlpt/jlpt1/vocab/']

workbook = return_workbook()
sheet = workbook.active
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
    vocab_page_html = requests.get(page_url).content
    vocab_soup = BeautifulSoup(vocab_page_html, 'html.parser')

    # We get the second table on the page, and remove the table headers
    table = vocab_soup.findAll('table')[1]
    rows = table.findAll('tr')
    rows = rows[1:]

    # Add kanji, hiragana, english meaning, example page and jlpt level per row
    for row in rows:
        cells = row.findAll('td')
        table_items = [cell.get_text() for cell in cells]
        # Not all vocab entries have a kanji, so we grab this page from the second column (3rd would work too)
        examples_page = cells[1].find('a')
        examples_page = base_url + examples_page['href'] if examples_page else ""
        jlpt_level = f"N{jlpt_level_counter}"

        # Traverse the examples page
        print(f"Crawling example page for kanji {table_items[1]}")
        example_sentence_list = []
        if examples_page:
            examples_page_html = requests.get(examples_page).content
            examples_soup = BeautifulSoup(examples_page_html, 'html.parser')
            page_divs = examples_soup.find(id='contentright')
            raw_examples = page_divs.find_next('ul')

            if raw_examples:
                for li in raw_examples.find_all('li'):
                    example = get_example_content(li.text)
                    example_sentence_list.append(example)

        # Add everything to a list to append as an excel row
        to_insert = []
        to_insert.extend(table_items)
        to_insert.append(jlpt_level)
        to_insert.append(str(example_sentence_list))
        sheet.append(to_insert)

    jlpt_level_counter -= 1

workbook.save(filename)
