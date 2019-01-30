# Baseline Search - BM25
# by Will Enright

import math
import ast
import sys
import operator
import nltk
import os
from bs4 import BeautifulSoup

# Configuration options
index_file_loc = "index_baseline.txt"
stats_file_loc = "index_baseline_stats.txt"
query_file_loc = "test-collection/cacm.query.txt"
result_file_loc = "result_tables/baseline_BM25.txt"
case_folding = True
handle_punctuation = True

# Retrieval algorithm configuration
k1 = 1.2
k2 = 100
b = 0.75

# Check number of arguments
if len(sys.argv) != 2:
    print('To use this program:')
    print('\tpython3 baseline_search_BM25.py [query_file]')
    exit(1)

# Parse query string from command line
query_file_loc = str(sys.argv[1])


# Calculate the BM25 score of a doc for a single query term
def BM25_Score(qf, f, n, N, dl, avdl):
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


# Process the query and retrieve files
def search_query(query_num, query_terms):

	# Load stats from file
	with open(stats_file_loc, 'r') as stats_file:
		stats = ast.literal_eval(stats_file.read())

	# Initialize score dictionary and partial index
	scores = {}
	index = {}
	doc_ids = set()

	# Parse the index file and store relevant entries
	with open(index_file_loc, 'r') as index_file:

		# For each line in index file, process inverted lists
		for l in index_file:

			# Skip blank lines
			if not l.strip():
				continue

			# EX: mollin: 2, {'carbon_tetrachloride': 1, 'eu': 1}
			# Parse values from the line
			[term, freqs] = l.split(":", 1)
			freqs = ast.literal_eval(freqs.split(",", 1)[1].strip())

			# Store index record for terms in query
			if term in query_terms:
				index[term] = freqs

				# Record any doc_id that contains a query term
				# (These are the only docs we want to score)
				doc_ids.update(freqs.keys())


	# Parse the query and compute score for documents
	# Compute score term-at-a-time
	for q in query_terms:

		# If term is not in corpus, do not calculate scores for it
		if q in index:
			q_freqs = index[q]
		else:
			continue

		# Loop over documents to be scored
		for d in doc_ids:
			
			# Term frequency
			if d in q_freqs:
				f = q_freqs[d]
			else:
				f = 0

			# Other params
			n = len(q_freqs)
			N = stats['num_docs']
			dl = stats['doc_lengths'][d]
			avdl = stats['avdl']

			# Compute the score for the current query term and doc
			score = BM25_Score(1,f,n,N,dl,avdl)

			# Accumulate doc score or initialize
			if d in scores:
				scores[d] += score
			else:
				scores[d] = score

	# Report Results
	with open(result_file_loc, "a+") as output_file:
		rank = 1
		for doc_id, score in sorted(scores.items(), 
							reverse=True, key=operator.itemgetter(1))[:100]:

			output_file.write("Q"+str(query_num)+" "+str(rank)+" "+doc_id+" "+str(score)+"\n")
			rank += 1


# Read, tokenize, and search each query in the query file
def main():
	# Delete result file if it exists
	if os.path.exists(result_file_loc):
		os.remove(result_file_loc)

	# Parse the query file using beautifulsoup
	with open(query_file_loc, 'rb') as query_file:
		raw_html = query_file.read()

		queries = {}

		soup = BeautifulSoup(raw_html, 'html.parser')
		raw_queries = soup.find_all("doc")
		
		# Tokenize each query for use
		for raw_q in raw_queries:
			# Extract query number
			heading = raw_q.find('docno')
			query_num = int(heading.get_text().strip())
			heading.decompose()

			# Extract the raw query text
			query_text = raw_q.get_text().strip()

			# Perform case folding
			if case_folding:
				query_text = query_text.lower()
			# Cleanup punctuation and tokenize
			if handle_punctuation:
				# Hyphenated words:		\w[\w-]*\w
				# Punctuation in nums:	\d[\d.,]*\d
				punc_regex = r'(?x)\d[\d.,]*\d|\w[\w-]*\w'
				query_tokens = nltk.regexp_tokenize(query_text, punc_regex)
			else:
				query_tokens = nltk.word_tokenize(query_text)

			# Store the recovered query
			queries[query_num] = query_tokens

	# Perform each of the queries sequentially
	for i in sorted(queries.keys()):
		print("Performing Query: " + str(i))
		search_query(i, queries[i])


if __name__ == "__main__":
	main()