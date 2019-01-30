import baseline_indexer
import index_search
import re
import os


try:
    os.makedirs('tmp')
except:
    pass

# Instead of parsing the stemmed contents seperately, the contents
# are transformed into HTML files (such that it is usable by the baseline indexer)
with open('test-collection/cacm_stem.txt', 'r') as f:
    for match in re.findall(r'\# (\d+)([^\#]+)', f.read()):
        with open('tmp/CACM-{}-STEMMED.html'.format(match[0]), 'wb') as cacm:
            cur = '<html><pre>{}</pre></html>'.format(match[1])
            cacm.write(cur.encode('utf-8'))

# extract queries
with open('test-collection/cacm_stem.query.txt') as f:
    querylist = [x.strip() for x in f.read().split('\n') if x.strip()]

idxr = baseline_indexer.Indexer('tmp', True, True, False)
idxr.create_index('index_stemmed')

# iterate over different scoring systems
for mode in ['BM25', 'JM', 'TF-IDF']:

    indexer = index_search.Index('index_stemmed', 'result_tables/stemmed_{}.txt'.format(mode), mode)

    indexer.new_search_store()

    # iterate over queries and generate score results
    for query_id, query in enumerate(querylist):
        indexer.search_store(query_id+1, query, 100)