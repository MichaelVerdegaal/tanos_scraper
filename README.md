# Description
This is a script meant to scrape vocabulary from [tanos.co.uk](http://www.tanos.co.uk/jlpt/). 
Furthermore it collects the example sentences together for each vocab word (where possible). 

The reason this was written is because i wanted to experiment with a large set of jlpt training 
data for myself, and i couldn't really find something nice elsewhere.

## Requirements
- The packages installed listed in requirements.txt
- An empty postgres database. Fill in the credentials in `config_example.py`, when you're done, rename 
it to `config.py` 

## How does it work?
This is a fairly simple python script making use of BeautifulSoup4. It extracts each entry from the table,
and then traverses the examples if there are any (there most definitely are examples for most entries, but they get increasingly lacking per JLPT level). Examples are added with a foreign key
to the vocabulary table.

To execute the script run `main_sql.py`.
  
## How long does it take?
A fairly substantial time, except it to take around 4-5 hours in most cases.

## Will this crash the source website?
Very likely it won't. The script takes roughly 1 second per request, which it should handle just fine. 
If you're unsure you can implement a sleep mechanic, or request a database dump by messaging me.
