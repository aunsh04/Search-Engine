import math
import ast
import sys
import nltk
import os
import argparse
from bs4 import BeautifulSoup

# used to parse (query_id:query) pair 
def querypair(q):
    tmp = q.split(':')
    if len(tmp) == 2:
        return tmp
    else:
        raise argparse.ArgumentTypeError('[Query ID]:[Query] pair expected')

# Calculate the BM25 score of a doc for a single query term
def BM25_Score(qf, f, n, N, dl, avdl, k1 = 1.2, k2 = 100, b = 0.75):
	# (Sum over query terms)
	# log(1 / ((n + 0.5) / (N - n + 0.5)))
	# * (k1 + 1)f / (K + f)
	# * (k2 + 1)qf / (k2 + qf)

	# Where:
	# qf : query term frequency 	(in query)
	# n : document frequency 		(in corpus)
	# f : term frequency 			(in document)
	# N : number of documents in corpus
	# dl : document length (# tokens)
	# avdl : average document length in corpus

    K = k1 * ((1 - b) + (b * dl / avdl))

    score = math.log(1 / ((n + 0.5) / (N - n + 0.5)))
    score *= (k1 + 1) * f / (K + f)
    score *= (k2 + 1) * qf / (k2 + qf)

    return score

# Calculate the JM score of a doc for a single query term
def JM_Score(fqd, cq, D, C, A = 0.35):

	# (Add across query terms when logged)
	# log( [(1-A) * fqd / |D|] + [A * cq / |C|] )

	score = math.log(((1-A) * fqd / D) + (A * cq / C))
	return score

# Calculate the TF-IDF score of a doc for a single query term
def TFIDF_Score(f, df, N):
	# (Sum over query terms)
	# tf * log(N / df)

	# Where:
	# f : term frequency (in document)
	# df : document frequency (in corpus)
	# N : total number of documents
    try:
	    score = f * math.log(N / df)
    except Exception as e:
        print(e)
        sys.exit(1)

    return score


class Index:
    # precompute required metrics for scoring
    def __init__(self, index_name, output_file, mode):
        # Load stats from file
        with open("{}_stats.txt".format(index_name), 'r') as stats_file:
            stats = ast.literal_eval(stats_file.read())
        
        # Extract statistics 
        self.N = stats['num_docs']
        self.avdl = stats['avdl']
        self.C = stats['corpus_len']
        self.doc_lens = stats['doc_lengths']

        self.output_file = output_file

        # extract index metadata (to allow mirroring text transformations)

        # default case handling returns the text as is
        self.case_handler = lambda x: x
        # if case_folding is enabled, the handler is set to get lowercase text
        if stats.get('case_folding'):
            self.case_handler = lambda x: x.lower()
        
        # default token handling returns tokens as is
        self.get_tokens = lambda text: nltk.word_tokenize(text)
		# if punctuation handling is enabled, the tokenizer is set to extract tokens that follow required regex
        if stats.get('handle_punctuation'):
            self.get_tokens = lambda text: nltk.regexp_tokenize(text, r'(?x)\d[\d.,]*\d|\w[\w-]*\w')

        self.stopwords = []
		# If stopping is enabled, store stopwords in-memory
        if stats.get('stopped'):
            with open('test-collection/common_words') as f:
                self.stopwords = set(list(f.read().split('\n')))

        # Initialize index
        index = {}
        term_doc_ids = {}

        # Parse the index file and store relevant entries
        with open("{}.txt".format(index_name), 'r') as index_file:

            # For each line in index file, process inverted lists
            for l in index_file:

                # Skip blank lines
                if not l.strip():
                    continue

                # EX: mollin: 2, {'carbon_tetrachloride': 1, 'eu': 1}
                # Parse values from the line
                [term, freqs] = l.split(":", 1)
                freqs = ast.literal_eval(freqs.split(",", 1)[1].strip())

                index[term] = freqs

                # store relevant documents for each term
                tmp = term_doc_ids.get(term, set())
                tmp.update(freqs.keys())
                term_doc_ids[term] = tmp
        
        self.index = index
        self.term_doc_ids = term_doc_ids
        self.mode = mode

    # search for a query and return top results
    def search(self, query_num, query, limit):
        # mirror the transformations done on corpus to the query
        query = self.case_handler(query)
        query_tokens = self.get_tokens(query)
        # remove stopwords from query
        query_tokens = [x for x in query_tokens if not x.lower() in self.stopwords]

        search_docs = set()

        scores = {}
        # create a list of documents to be processed
        for q in query_tokens:
            search_docs.update(self.term_doc_ids.get(q, set()))

        # generate scores term at a time
        for q in query_tokens:

            # skip if not in index
            if not q in self.index:
                continue

            for doc_id in search_docs:

                # frequency of term 
                f = self.index[q].get(doc_id, 0)

                # gather scorer specific metrics and calculate score
                if self.mode == 'BM25':
                    n = len(self.index[q])
                    N = self.N
                    dl = self.doc_lens[doc_id]
                    avdl = self.avdl
                    score = BM25_Score(1,f,n,N,dl,avdl)

                if self.mode == 'JM':
                    C = self.C
                    D = self.doc_lens[doc_id]
                    cq = sum(self.index[q].values())
                    score = JM_Score(f, cq, D, C)

                if self.mode == 'TF-IDF':
                    df = len(self.index[q])
                    N = self.N
                    score = TFIDF_Score(f, df, N)
                
                scores[doc_id] = scores.get(doc_id, 0) + score

        # sort by descending order of scores
        results = sorted([(doc_id, score) for doc_id, score in scores.items()], key = lambda x: -x[1])[:limit]
        return results

    # clean file at beginning
    def new_search_store(self):
        with open(self.output_file, 'w'):
            pass

    # get search results and store to output file
    def search_store(self, query_num, query, limit):
        scores = self.search(query_num, query, limit)
            
        # write scores to file
        with open(self.output_file, 'a+') as f:
            for rank, (doc_id, score) in enumerate(scores):
                f.write('Q{} {} {} {}\n'.format(query_num, rank+1, doc_id, score))

def main():
    parser = argparse.ArgumentParser(description='Search', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('index_name', help='Name of the index')
    parser.add_argument('output_file', help='Output index file.')
    parser.add_argument('-q', type=querypair ,action='append', help='[Query ID]:[Query] pair (e.g. 25:"cow horse moon")')
    parser.add_argument("-mode", default='TF-IDF', help="Scoring mode (BM25, TF-IDF, JM) (default: \"%(default)s\")")
    parser.add_argument("-limit", type=int, default=100, help="Limit. (default: \"%(default)s\")")
    parser.add_argument('-new', action='store_true', help="Creates a new output file (otherwise appends to existing file).")
    args = parser.parse_args()
    print("args:", args)

    index = Index(args.index_name, args.output_file, args.mode)

    if args.new:
        index.new_search_store()

    for q_id, q in args.q:
        index.search_store(q_id, q, args.limit)

if __name__ == '__main__':
    main()








        
        


