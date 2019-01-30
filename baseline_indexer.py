# Baseline Indexer (Task 1)
# Adapted from Assignment 3 submissions 
# by Will Enright

from os import listdir
from bs4 import BeautifulSoup
import sys
import nltk
import argparse

class Indexer:
	def create_index(self, output_file_name):

		self.stats['num_docs'] = len(self.doc_ids)

		# iterate over doc_ids
		for doc_id in self.doc_ids:
			sys.stdout.write('.')
			sys.stdout.flush()
			# Process the HTML file
			with open('{}/{}.html'.format(self.html_dir, doc_id), 'rb') as file:
				raw_html = file.read()

			# Extract main content using BeautifulSoup
			# (No extra content filtering needed for CACM files)
			soup = BeautifulSoup(raw_html, 'html.parser')
			content = soup.pre

			# Extract the raw text from the filtered content
			page_text = content.get_text()

			# Transform text and get tokens based on settings
			page_text = self.case_handler(page_text)

			tokens = self.get_tokens(page_text)


			# Parse tokens to create index
			# (For unigram implementation, each token is a term)
			# The tokens are read from the end to facilitate ignoring numers towards the end
			word_occured = False

			for term in reversed(tokens):
				# Make sure all tokens are represented as strings
				term = str(term)

				# Check if a word has been reached while traversing from the end of the document
				# continue if not
				try:
					int(term)
				except ValueError:
					word_occured = True

				if not word_occured:
					continue

				# skip processing the token if it exists in the stopword list
				if term in self.stopwords:
					continue


				# Increment counters (this ensures discounting of stopwords in statistics)
				self.stats['corpus_len'] += 1
				self.stats['doc_lengths'][doc_id] = self.stats['doc_lengths'].get(doc_id, 0) + 1

				
				# Update the index as necessary
				if not term in self.index:
					self.index[term] = {}

				posting_list = self.index[term]
				posting_list[doc_id] = posting_list.get(doc_id, 0) + 1

			C = self.stats['corpus_len']
			N = self.stats['num_docs']

			self.stats['avdl'] = C/N

		with open('{}.txt'.format(output_file_name), 'w') as index_file:
			for t, d in self.index.items():
				index_file.write(t + ': ' + str(len(d)) + ', ')
				index_file.write(str(d) + '\n')
		
		# Write the additional stats file to be used by retrieval algorithms
		with open("{}_stats.txt".format(output_file_name), 'w') as stats_file:
			stats_file.write(str(self.stats))

	def __init__(self, html_dir, case_folding, handle_punctuation, stopped):

		self.html_dir = html_dir

		# Pull all the file names (docID) from the HTML directory into a list
		self.doc_ids = [f.split('.')[0] for f in listdir(html_dir) if f]

		# default case handling returns the text as is
		self.case_handler = lambda page_text: page_text 
		# if case_folding is enabled, the handler is set to get lowercase text
		if case_folding:
			self.case_handler = lambda page_text: page_text.lower()


		# default token handling returns tokens as is
		self.get_tokens = lambda page_text: nltk.word_tokenize(page_text)
		# if punctuation handling is enabled, the tokenizer is set to extract tokens that follow required regex
		if handle_punctuation:
			self.get_tokens = lambda page_text: nltk.regexp_tokenize(page_text, r'(?x)\d[\d.,]*\d|\w[\w-]*\w')


		self.stopwords = []
		# If stopping is enabled, store stopwords in-memory
		if stopped:
			with open('test-collection/common_words') as f:
				self.stopwords = set(list(f.read().split('\n')))

		# Initialize index objects
		self.index = {}

		# Track the following stats for retrieval models
		# N : Total number of documents
		# dl : Length (# tokens) of each document
		# avdl : Average document length
		# |C| : Total corpus length (# tokens)
		self.stats = {
			'num_docs': 0, 
			'avdl': 0, 
			'corpus_len': 0, 
			'doc_lengths': {},
			'case_folding': case_folding,
			'handle_punctuation': handle_punctuation,
			'stopped': stopped
			}


# Process the raw HTML and generate index files
def main():
	parser = argparse.ArgumentParser(description='Indexer', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('input_folder', help='Folder for which index is generated.')
	parser.add_argument('output_name', help='Name for output index file.')
	parser.add_argument("-disable_fc", action='store_true', help="Disable fold cases.")
	parser.add_argument("-disable_hp", action='store_true', help="Disable handle punctuations.")
	parser.add_argument("-stopped", action='store_true', help="Stopping.")
	args = parser.parse_args()
	print("args:", args)

	idxr = Indexer(args.input_folder, not args.disable_fc, not args.disable_hp, args.stopped)
	idxr.create_index(args.output_name)


if __name__ == "__main__":
	main()
