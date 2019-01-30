import ast
from bs4 import BeautifulSoup
import index_search

# Parse the query file using beautifulsoup
with open('test-collection/cacm.query.txt', 'rb') as query_file:
    raw_html = query_file.read()

queries = {}

soup = BeautifulSoup(raw_html, 'html.parser')
raw_queries = soup.find_all("doc")

querylist = []

# Tokenize each query for use
for raw_q in raw_queries:
    # Extract query number
    heading = raw_q.find('docno')
    query_num = int(heading.get_text().strip())
    heading.decompose()

    # Extract the raw query text
    query_text = raw_q.get_text().strip()

    querylist.append((query_num, query_text))

# iterate over different scoring systems
for mode in ['BM25', 'JM', 'TF-IDF']:

    indexer = index_search.Index('index_stopped', 'result_tables/stopped_{}.txt'.format(mode), mode)

    indexer.new_search_store()

    for query_id, query in querylist:
        indexer.search_store(query_id, query, 100)
