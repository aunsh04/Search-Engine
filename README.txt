README

Dependencies / Required Libraries:
- Python3
- BeautifulSoup 4
- nltk
- JDK 1.8
- lucene-core, lucene-queryparser, lucene-analyzers-common for Lucene
- For graph generation: matplotlib, python-tk

###########################################################
Task 1: Non-Lucene Baseline Runs

Relevant Files:

	baseline_indexer.py
	(Index files generated in same directory)
	baseline_search_BM25.py
	baseline_search_JM.py
	baseline_search_TF-IDF.py
	result_tables/


Run baseline indexer (generates index files):

	python3 baseline_indexer.py ./test-collection/cacm/ index_baseline


Configuration:

	Handling punctuation and case folding are enabled by default.
	To disable them, use the -disable_hp and -disable_fc flags respectively.


Run baseline searches (after index generation):

	python3 baseline_search_BM25.py test-collection/cacm.query.txt
	python3 baseline_search_TF-IDF.py test-collection/cacm.query.txt
	python3 baseline_search_JM.py test-collection/cacm.query.txt

(Results written to file in result_tables/)

The Lucene Baseline Run, Query Enrichment and Snippet Generation, Query Highlighting have been implemented in Java. As an initial set up we need to first set up LuceneBaselineModel as a project in an IDE. Once having imported the project into IntelliJ, the IDE will index the project, download/install the dependencies from the pom.xml file. Once completed indexing, compiled you can go ahead and right click on the following classes to run for the tasks - 

###########################################################
Task 1: Lucene Baseline Run

src/main/java/scoring/LuceneScoring.java

Enter the FULL path where the index will be created: (e.g. /Usr/index or c:\temp\index)
./index

Enter the FULL path to add into the index (q=quit): (e.g. /home/mydir/docs or c:\Users\mydir\docs)
./cacm

Enter path of query file
./processed_queries.txt

The results for this run can be seen in the result_tables directory as baseline_Lucene.txt 
###########################################################
Task 2: Query Enrichment on Lucene Run

src/main/java/expansion/KLDQueryExpansion.java

The results for this run can be seen in the result_tables/KLD_query_expansion_Lucene.txt 
###########################################################
Task 3: Stopping and Stemming Runs

Generate stopped index:

	python3 baseline_indexer.py ./test-collection/cacm/ index_stopped -stopped

Generate search results for stopped index:

	python3 search_stopped.py

Generate stemmed index and save query results:
	
	python3 indexer_stemmed.py

###########################################################
Phase 2: Displaying Results

Referring to the above, since this is implemented in Java, we can right click on the class below in the 
imported project from your IDE and Run

src/main/java/snippet/SnippetGeneratorWithLuceneResults.java

The results for this run can be seen in the snippet_results/snippet_Lucene_with_query_highlighting
###########################################################
Phase 3: Evaluation

Notes:
	- Values in precision/recall are truncated to 3 decimal places for readability
	- Because all retrieved documents were included in precision calculations and relevant document sets were small, precision values always became very small towards the lower ranked results
	- MAP and MRR values located at bottom of each evaluation file


Relevant Files:
	
	evaluation/*


Configuration:

	Set path to CAMC relevancy file at top of evaluator.py

	For generating graph:
		pip3 install matplotlib
		apt-get install python-tk


Run Evaluator (Once per run):

	python3 evaluator.py ../result_tables/baseline_BM25.txt eval_baseline_BM25.txt
	python3 evaluator.py ../result_tables/baseline_TF-IDF.txt eval_baseline_TF-IDF.txt
	python3 evaluator.py ../result_tables/baseline_JM.txt eval_baseline_JM.txt
	etc.

Run Grapher:
(Running evaluator on each result table adds required graphing info to evaluation/graph_data/)

	python plot_graph.py


###########################################################
Extra Credit

Generate positional index:
	
	python3 positional_index.py

Search:

	python .\advanced_search.py OBM 'glossary computer 1978' -window 100

Additional help:

	python .\advanced_search.py -h

