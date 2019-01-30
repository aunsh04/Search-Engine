import os
import argparse
import re
import nltk
import heapq
import math

# Calculate the TF-IDF score of a doc for a single query term
def TFIDF_Score(f, df, N):
	# (Sum over query terms)
	# tf * log(N / df)

	# Where:
	# f : term frequency (in document)
	# df : document frequency (in corpus)
	# N : total number of documents
    score = f * math.log(N / df)

    return score


class Search:
    # set index name
    def __init__(self, index_name):
        self.index_name = index_name

    # fetch documents that are relevant to the query
    def fetch_relevant(self, query):
        term_docs = {}
        tf = {}
        df = {}
        with open('./{}/meta.txt'.format(self.index_name), 'r') as f:
            self.N = int(f.read().split(':')[-1])

        with open('./{}/index.txt'.format(self.index_name), 'rb') as f:
            # iterate over all words
            for line in f.readlines():
                line = line.decode('utf-8')
                term, rest = line.split('=>')

                if not term in query:
                    continue

                tf[term] = {}
                term_docs[term] = {}
                df[term] = 0

                # extract corresponding fields using regex
                r = re.compile(r'\[([\w\,\-\.]+);(\d+);\(([\d\,]*)\)\]')

                # store index
                for (doc_id, count, indices) in re.findall(r, rest):
                    compressed = [int(i) for i in indices.split(',')]
                    # expand to normal positional indices
                    for i in range(1, len(compressed)):
                        compressed[i] += compressed[i-1]

                    term_docs[term][doc_id] = compressed
                    tf[term][doc_id] = int(count)
                    df[term] += 1

                # if all relevant indexing have been fetched, break
                if len(term_docs) == len(query):
                    break

        self.term_docs = term_docs
        self.tf = tf
        self.df = df

    # This algorithm does not account for repeating words in the query

    # The algorithm aims at efficiency. It finds the smallest size window that
    # contains the exact order match in O(n log n) time, where n is the length of
    # the merged positional index array. 
    def ordered_best_match(self, query, window_size = -1):

        # fetch all relevant documents
        term_docs = self.term_docs
        
        docs = [set(t.keys()) for t in term_docs.values()]

        try:
            doc_set = docs[0].intersection(*docs[1:])
        except IndexError:
            doc_set = set()
        
        if not doc_set:
            print('No documents contain \"{}\"'.format(query))

        # Object to be returned
        result = []

        # Consider the query "a likes b"
        # "b" should be preceded by "likes"
        # "likes" should be preceded by "a"
        # We first generate this mapping
        query_map = {}

        for i in range(1, len(query)):
            query_map[query[i]] = query[i-1]

        # iterate over valid documents
        for doc_id in doc_set:
            
            # Smallest window in which all words exist (with order preserved)
            min_window = float('inf')

            # This stores the most recent start index for a term
            mr_start_idx = {}
            cur_doc = []

            # Merge the word lists
            for k in query:
                cur_doc.extend([(k, pos_index) for pos_index in term_docs[k][doc_id]])
            
            # O(n log(n)) to sort the words to as it would in the document
            cur_doc.sort(key = lambda x: x[1])

            # Backbone of the algorithm. O(n) loop
            for term, idx in cur_doc:

                # Fetch the previous required word
                previous_query_term = query_map.get(term)

                # Only the first word has no mapping
                if previous_query_term == None:
                    mr_start_idx[term] = idx
                else:
                    mr_start_idx[term] = mr_start_idx.get(previous_query_term, -1)

                # Check if the last word of the query was read, and it was assigned a value
                # besides -1. Then a new sequence has been found.
                if term == query[-1] and mr_start_idx[term] != -1:
                    min_window = min(min_window, idx - mr_start_idx[term])
            
            # If no limit was given, just add document to result
            # Otherwise add only if min_window <= window_size
            if window_size == -1:
                result.append({'doc_id': doc_id})
            else:
                if min_window <= window_size:
                    result.append({'doc_id': doc_id, 'window': min_window})

        return result

    # Return all documents that contain even one of the words
    def best_match(self, query):
        # fetch all relevant documents
        term_docs = self.term_docs
        
        docs = [set(t.keys()) for t in term_docs.values()]

        try:
            doc_set = docs[0].union(*docs[1:])
        except IndexError:
            doc_set = set()

        return [{'doc_id': d} for d in doc_set]

    def match(self, query_full, matching_mode, window = -1, max_docs = 100):
        # Tokenize the query
        query = nltk.regexp_tokenize(query_full, r'(?x)\d[\d.,]*\d|\w[\w-]*\w')
        query = [x.lower() for x in query]
        
        self.fetch_relevant(query)

        if matching_mode == 'EM':
            docs = self.ordered_best_match(query)
        if matching_mode == 'BM':
            docs = self.best_match(query)
        if matching_mode == 'OBM':
            docs = self.ordered_best_match(query, window)

        prio_q = []
        # Now that all the documents have been retrieved, rank according to tf-idf
        # The documents are sorted by best scores. Documents with equal scores are sorted by minimum window length.
        for cur in docs:
            d = cur['doc_id']
            score = 0
            for q in query:
                cur_df = self.df.get(q, 0)
                if cur_df == 0:
                    continue
                score += TFIDF_Score(self.tf.get(q, {}).get(d, 0), cur_df, self.N)

            # heapq implements min-heap by default
            heapq.heappush(prio_q, (-score, cur.get('window', -1), d))
        
        resultant = []
        for _ in range(max_docs):
            if not prio_q:
                break
            resultant.append(heapq.heappop(prio_q))
        resultant = [(d, -score) if w == -1 else (d, -score, w) for score, w, d in resultant]

        return resultant

def main():
    parser = argparse.ArgumentParser(description='Advanced search', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('mode', help='Search mode (\'EM\', \'BM\', \'OBM\')')
    parser.add_argument('query', help='Query')
    parser.add_argument('-index', default='positional', help='Name of index (default: \"%(default)s\")')
    parser.add_argument('-window', default=-1, type=int, help='Window size (for ordered best match)')
    parser.add_argument('-limit', default=100, type=int, help='Number of results')
    args = parser.parse_args()
    s = Search(args.index)
    resultant = s.match(args.query, args.mode, args.window, args.limit)
    for r in resultant:
        print(" ".join([str(x) for x in r]))


    
if __name__ == '__main__':
    main()