import os
import argparse
from bs4 import BeautifulSoup
import nltk

class InvertedIndexer:
    def create_positional_index(self):

        positional_index = {}
        N = 0
        folder_path = self.corpus_path

        # iterate over each document
        for file_name in os.listdir(folder_path):
            # skip if not html document
            if not file_name.endswith(".html"):
                continue

            # current path of doc
            file_path = os.path.join(folder_path, file_name)
            N += 1

            with open(file_path, 'rb') as f:
                html = f.read()
            soup = BeautifulSoup(html, 'html.parser')

            print('Parsing {}'.format(file_name))

            # tokenize words
            all_words = nltk.regexp_tokenize(soup.get_text(), r'(?x)\d[\d.,]*\d|\w[\w-]*\w')
            all_words = [x.lower() for x in all_words]
            
            # remove all numbers towards the end of documents
            for i in range(len(all_words)-1, -1, -1):
                try:
                    int(all_words[i])
                    all_words.pop()
                except:
                    break

            # create positional index for current word
            for i, word in enumerate(all_words):
                if not positional_index.get(word):
                    positional_index[word] = {}
                positional_index[word][file_name] = positional_index[word].get(file_name, []) + [i]
        
        with open('{}/index.txt'.format(self.index_path), 'wb') as f:

            for term, doclist in positional_index.items():

                f.write("{}=>{};".format(term, len(doclist)).encode('utf-8'))
                f.write('{'.encode('utf-8'))

                # iterate over each document for current word
                for docname, idxlist in doclist.items():
                    new_list = []
                    prev = 0
                    # compress this list using delta encoding
                    for x in idxlist:
                        new_list.append(str(x-prev))
                        prev = x
                    cur_txt = "[{};{};({})]".format(docname[:-5], len(new_list), ",".join(new_list))
                    f.write(cur_txt.encode('utf-8'))
                f.write("}\n".encode('utf-8'))

        with open('{}/meta.txt'.format(self.index_path), 'w') as f:
            f.write('N:{}'.format(N))

    def __init__(self, corpus_path, index_path):
        self.corpus_path = corpus_path
        self.index_path = index_path
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
        self.corpus_path_mapping = {}

        for filename in os.listdir(corpus_path):
            if filename.endswith(".html"):
                self.corpus_path_mapping[filename[:-5]] = os.path.join(corpus_path, filename)


def main():
    parser = argparse.ArgumentParser(description='Indexer', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-corpus', default="./test-collection/cacm/", help='Folder for which index is generated. (default: \"%(default)s\")')
    parser.add_argument('-index', default="positional", help='Name of index (default: \"%(default)s\")')
    args = parser.parse_args()
    iidx = InvertedIndexer(args.corpus, args.index)
    iidx.create_positional_index()

if __name__ == '__main__':
    main()