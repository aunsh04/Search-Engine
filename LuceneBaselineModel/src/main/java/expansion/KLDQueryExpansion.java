package expansion;

import java.io.*;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

/**
 * Implementing Kullback Leibler Divergence technique (Pseudo Relevance Feedback)
 * for query expansion/refinement
 */
public class KLDQueryExpansion {

    // Using Standard Analyzer
    private static Analyzer analyzer = new StandardAnalyzer(Version.LUCENE_47);
    private static int totalCorpusCount;
    private static Map<String,String> expandedQueries;

    public KLDQueryExpansion() {
        totalCorpusCount = 0;
        expandedQueries = new LinkedHashMap<>();
    }


    /**
     * Fetch stop words from file
     * @param filePath path of stopwords file
     * @return stopWords list of stopwords
     */
    public static List<String> fetchStopWords(String filePath) {
        List<String> stopWords = new ArrayList<>();
        File file = new File(filePath);
        BufferedReader b = null;
        try {
            b = new BufferedReader(new FileReader(file));
            String readLine = "";

            System.out.println("Reading common words file using Buffered Reader");

            while ((readLine = b.readLine()) != null) {
                stopWords.add(readLine.trim());
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                b.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        return stopWords;
    }





    /**
     * Read queries from processed queries file
     *
     * @param filePath path of processed queries file
     * @return queryMap map with query id and corresponding query
     */
    public static Map<String, String> getQueries(String filePath) {
        Map<String, String> queryMap = new LinkedHashMap<>();
        File file = new File(filePath);
        BufferedReader b = null;
        try {
            b = new BufferedReader(new FileReader(file));
            String readLine = "";

            System.out.println("Reading file using Buffered Reader");

            while ((readLine = b.readLine()) != null) {
                String[] queryArray = readLine.split(":");
                System.out.println(queryArray[1].trim().length());
                queryMap.put(queryArray[0], queryArray[1].trim());
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                b.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return queryMap;
    }

    /**
     * Precompute required values for pseudo relevance feedback algorithm
     * such as total corpus terms, raw frequency of terms in corpus
     * and relevant set
     */
    public static Map<String,Map<String,Integer>> precompute(String path) {
        Map<String,Map<String,Integer>> fileCountMap = new HashMap<>();
        File dir = new File(path);
        for (File file:dir.listFiles()) {
            Map<String,Integer> countMap = new HashMap<>();
            BufferedReader b = null;
            try {
                b = new BufferedReader(new FileReader(file));
                String readLine = "";
                while ((readLine = b.readLine()) != null) {
                    String[] terms = readLine.split(" ");
                    totalCorpusCount+= terms.length;
                    for (String term:terms) {
                        String pattern = "ca[0-9]+";

                        Pattern r = Pattern.compile(pattern);
                        Matcher m = r.matcher(term);
                        if(m.find()) {
                            continue;
                        }
                        if (countMap.containsKey(term)) {
                            int f = countMap.get(term);
                            countMap.put(term,f+1);
                        }
                        else {
                            countMap.put(term,1);
                        }
                    }
                }
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            } finally {
                try {
                    b.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }

            fileCountMap.put(file.getName(),countMap);
        }
        return fileCountMap;

    }



    public static void main(String[] args) throws IOException {

        KLDQueryExpansion e = new KLDQueryExpansion();
        Map<String,Map<String,Integer>> termFrequency = precompute("./processed_corpus");
        List<String> stopWords = fetchStopWords("./common_words.txt");

        for (String docName:termFrequency.keySet()) {
            System.out.println("Frequency Map for "+docName);
            for (String term:termFrequency.get(docName).keySet()) {
                System.out.println(term + " "+termFrequency.get(docName).get(term));
            }
        }
        System.out.println("Total corpus count is "+totalCorpusCount);
        System.out.println("Total number of documents are "+termFrequency.size());


        // =========================================================
        // Now search
        // =========================================================

        // Populate queries into map
        Map<String, String> queryMap = getQueries("./processed_queries.txt");
        for (String queryId:queryMap.keySet()) {
            System.out.println(queryId + " "+queryMap.get(queryId));
        }


//
//        // Result file
        File resultFile = new File("result_tables/baseline_Lucene.txt");

        try (FileWriter fw = new FileWriter(resultFile)) {
            for (String queryId : queryMap.keySet()) {
                String s = queryMap.get(queryId);
                Map<String, Float> relevantDocumentScores = computeScore(s, queryId, fw);
                Map<String, Float> sortedDocumentScores = getSortedScores(relevantDocumentScores);
                System.out.println("Top Ranked Documents for query id "+queryId);
                for (String doc:sortedDocumentScores.keySet()) {
                    System.out.println(doc+ " "+sortedDocumentScores.get(doc));
                }

                System.out.println("Top 10 ranked documents for queryId "+queryId);

                List<String> relevantDocuments = fetchRelevantDocuments(sortedDocumentScores,10);
                for (String doc:relevantDocuments) {
                    System.out.println(doc);
                }

                Set<String> candidateTerms = fetchCandidateTerms(termFrequency,relevantDocuments,stopWords);
                System.out.println("Number of candidate terms for queryId "+queryId+" are "+candidateTerms.size());

                //
                Map<String, Double> candidateTermScores = calculateCandidateScores(queryId,candidateTerms,termFrequency,relevantDocuments,candidateTerms.size());
                Map<String,Double> sortedCandidateTermScores = getTermSortedScores(candidateTermScores);
                System.out.println("Expanded query terms for queryId "+queryId+" are");

                int expandedQueryCount = 0;
                String expandedQuery  = s;
                for (String t:sortedCandidateTermScores.keySet()) {
                    if (expandedQueryCount==40) {
                        break;
                    }
                    expandedQuery+=" "+t;
                    expandedQueryCount++;
                }
                System.out.println("Hi!!!! "+expandedQuery);
                expandedQueries.put(queryId,expandedQuery);


            }
            fw.close();
            File expandedResultFile = new File("result_tables/KLD_query_expansion_Lucene.txt");
            try (FileWriter fw1 = new FileWriter(expandedResultFile)) {
                for (String newQueryId:expandedQueries.keySet()) {
                    String newQuery = expandedQueries.get(newQueryId);
                    computeScore(newQuery, newQueryId, fw1);
                }
                fw1.close();
            }
        }


    }

    /**
     * Compute total score for each candidate term from relevant documents
     * on basis of divergence score
     */
    public static Map<String,Double> calculateCandidateScores(String queryId, Set<String> terms, Map<String,Map<String,Integer>> frequencies,
                                                              List<String> relevantDocuments,int relevantTermsSize) {
        System.out.println("query id is "+queryId);
        System.out.println(relevantDocuments.size());
        Map<String,Double> scores = new HashMap<>();
        for (String term:terms) {

            double relevantTermScore = fetchRelevantScore(term,frequencies,relevantDocuments,relevantTermsSize);
            System.out.println(relevantTermScore);

            double corpusTermScore = fetchCorpusScore(term,frequencies);
            System.out.println(corpusTermScore);

            double finalScore = relevantTermScore*Math.log10(relevantTermScore/corpusTermScore);
            System.out.println("finalScore for term "+term+" is "+finalScore);

            scores.put(term,finalScore);
        }
      return scores;
    }


    /**
     * Fetch unigram probability distribution of term from entire corpus
     */
    public static double fetchCorpusScore(String term,Map<String,Map<String,Integer>> frequencies) {
        int f = 0;
        for (String docName:frequencies.keySet()) {
            Map<String,Integer> termMap = frequencies.get(docName);
            if (termMap.containsKey(term)) {
                f+=termMap.get(term);
            }
        }
        return f*1.0/totalCorpusCount;
    }


    /**
     * Fetch unigram probability distribution of term from relevant set of documents
     */
    public static double fetchRelevantScore(String term, Map<String,Map<String,Integer>> frequencies, List<String> relevantDocuments,
                                            int relevantTermsSize) {
        int f = 0;
        int count = 0;
        for (String t:frequencies.keySet()) {
            if (relevantDocuments.contains(t)) {
                count++;
                Map<String,Integer> m = frequencies.get(t);
                if (m.containsKey(term)) {
                    f += m.get(term);
                }
            }
        }
        System.out.println("Number of relevant documents :" +count);
        return f*1.0/relevantTermsSize;
    }


    /**
     * Fetch all candidate terms - all terms from the relevant documents retrieved from Lucene
     */
    public static Set<String> fetchCandidateTerms(Map<String,Map<String,Integer>> frequencyMap, List<String> relevantDocuments,
                                                  List<String> stopWordsList) {
        int count = 0;
        Set<String> candidates = new HashSet<>();
        for (String docName:frequencyMap.keySet()) {
            if (relevantDocuments.contains(docName)) {
                count++;
                System.out.println(docName);
                Map<String,Integer> frequency = frequencyMap.get(docName);
                for (String term:frequency.keySet()) {
                    if (!stopWordsList.contains(term)) {
                        candidates.add(term);
                    }
                }
            }
        }
        System.out.println("Number of matched documents "+count);
        return candidates;
    }





    /**
     * Fetch the top k relevant documents from result documents obtained
     * @param sortedDocumentScores
     * @param k
     */
    public static List<String> fetchRelevantDocuments(Map<String,Float> sortedDocumentScores, int k) {
        int count = 0;
        List<String> relevantDocuments = new ArrayList<>();
        for (String doc:sortedDocumentScores.keySet()) {
            count++;
            relevantDocuments.add(doc+".txt");
            if (count==k) {
                break;
            }
        }
        return relevantDocuments;
    }



    /**
     * Return sentences sorted by score in descending order
     *
     * @param scoreMap mapping sentence to its score
     * @return sortedMap map sorted by sentence score
     */
    public static Map<String, Float> getSortedScores(Map<String, Float> scoreMap) {
        // 1. Convert Map to List of Map
        List<Map.Entry<String, Float>> list =
                new LinkedList<Map.Entry<String, Float>>(scoreMap.entrySet());

        // 2. Sort list with Collections.sort(), provide a custom Comparator
        //    Try switch the o1 o2 position for a different order
        Collections.sort(list, new Comparator<Map.Entry<String, Float>>() {
            public int compare(Map.Entry<String, Float> o1,
                               Map.Entry<String, Float> o2) {
                return (o2.getValue()).compareTo(o1.getValue());
            }
        });

        // 3. Loop the sorted list and put it into a new insertion order Map LinkedHashMap
        Map<String, Float> sortedMap = new LinkedHashMap<String, Float>();
        for (Map.Entry<String, Float> entry : list) {
            sortedMap.put(entry.getKey(), entry.getValue());
        }
        return sortedMap;
    }


    /**
     * Constructor
     *
     * @param indexDir the name of the folder in which the index should be created
     * @throws java.io.IOException when exception creating index.
     */
    KLDQueryExpansion(String indexDir) throws IOException {

//        FSDirectory dir = FSDirectory.open(new File(indexDir));

//        IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_47,
//                analyzer);
//
//        writer = new IndexWriter(dir, config);
    }


    public static Map<String, Float> computeScore(String s, String queryId, FileWriter fw) {

        System.out.println(s);

        // Result string
        String results = "";
        Map<String, Float> relevantDocumentScores = new HashMap<>();
        try {
            IndexReader reader = DirectoryReader.open(FSDirectory.open(new File(
                    "./index")));
            IndexSearcher searcher = new IndexSearcher(reader);
            try {
                TopScoreDocCollector collector = TopScoreDocCollector.create(100, true);
                Query q = new QueryParser(Version.LUCENE_47, "contents",
                        analyzer).parse(s);
                searcher.search(q, collector);
                ScoreDoc[] hits = collector.topDocs().scoreDocs;

                // 4. display results
                System.out.println("Found " + hits.length + " hits.");
                for (int i = 0; i < hits.length; ++i) {
                    int docId = hits[i].doc;
                    Document d = searcher.doc(docId);

                    results += " Q" + queryId + " " + (i + 1) + " " + d.get("path").substring(38, 47) + " " + hits[i].score + " LUCENE\n";

                    relevantDocumentScores.put(d.get("path").substring(38, 47), hits[i].score);
                }

            } catch (Exception e) {
                System.out.println("Error searching " + s + " : "
                        + e.getMessage());
            }


        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            fw.write(results);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return relevantDocumentScores;

    }

    /**
     * Get sorted scores in descending order
     */
    public static Map<String, Double> getTermSortedScores(Map<String, Double> scoreMap) {
        // 1. Convert Map to List of Map
        List<Map.Entry<String, Double>> list =
                new LinkedList<Map.Entry<String, Double>>(scoreMap.entrySet());

        // 2. Sort list with Collections.sort(), provide a custom Comparator
        //    Try switch the o1 o2 position for a different order
        Collections.sort(list, new Comparator<Map.Entry<String, Double>>() {
            public int compare(Map.Entry<String, Double> o1,
                               Map.Entry<String, Double> o2) {
                return (o2.getValue()).compareTo(o1.getValue());
            }
        });

        // 3. Loop the sorted list and put it into a new insertion order Map LinkedHashMap
        Map<String, Double> sortedMap = new LinkedHashMap<String, Double>();
        for (Map.Entry<String, Double> entry : list) {
            sortedMap.put(entry.getKey(), entry.getValue());
        }
        return sortedMap;
    }



}

