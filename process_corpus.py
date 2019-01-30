# Corpus Processor for use with Lucene runs
# Adapted from Indexer
# by Will Enright

from os import listdir
from bs4 import BeautifulSoup
import sys
import nltk

# Configuration values
corpus_output_dir = "./processed_corpus/"

case_folding = True			# Default: True
handle_punctuation = True	# Default: True


# Check command line arguments
if len(sys.argv) != 2:
    print('To use this program:')
    print('\tpython3 process_corpus.py [HTML_dir]')
    exit(1)

# Parse html_dir from command line
html_dir = str(sys.argv[1])


# Process the raw HTML and generate processed files
def main():
	# Pull all the file names (docID) from the HTML directory into a list
	doc_ids = [f.split('.')[0] for f in listdir(html_dir)]

	# Initialize index objects
	index = {}

	# Track the following stats for retrieval models
	# N : Total number of documents
	# dl : Length (# tokens) of each document
	# avdl : Average document length
	# |C| : Total corpus length (# tokens)
	stats = {'num_docs': len(doc_ids), 
			'avdl': 0, 
			'corpus_len': 0, 
			'doc_lengths': {}}

	# Parse each file and update index
	print("Parsing raw HTML files:")
	for id in doc_ids:
		sys.stdout.write('.')
		sys.stdout.flush()

		# Process the HTML file
		with open(html_dir + id + '.html', 'rb') as file:
			raw_html = file.read()

			# Extract main content using BeautifulSoup
			# (No extra content filtering needed for CACM files)
			soup = BeautifulSoup(raw_html, 'html.parser')
			content = soup.pre

			# Extract the raw text from the filtered content
			page_text = content.get_text()

			# Normalize case, if required
			if case_folding:
				page_text = page_text.lower()

			# Tokenize with punctuation filtering or not
			if handle_punctuation:
				# Hyphenated words:		\w[\w-]*\w
				# Punctuation in nums:	\d[\d.,]*\d
				punc_regex = r'(?x)\d[\d.,]*\d|\w[\w-]*\w'
				tokens = nltk.regexp_tokenize(page_text, punc_regex)
			else:
				# Simple word tokenization
				tokens = nltk.word_tokenize(page_text)

			# Filter out the numbers at the end of the file
			word_occured = False
			final_tokens = []
			for t in reversed(tokens):
				try: 
					int(t)
				except ValueError:
					word_occured = True

				if not word_occured:
					continue

				final_tokens.append(t)

			tokens = reversed(final_tokens)


		# Write the processed corpus document to file
		with open(corpus_output_dir + id + ".txt", 'w') as output_file:
			output_file.write(' '.join(tokens))

	print("Done!")


if __name__ == "__main__":
	main()
