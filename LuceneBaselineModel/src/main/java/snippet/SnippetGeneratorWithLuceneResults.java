package snippet;

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
 * Snippet Generation and Query Term Highlighting on results of Lucene Baseline Model
 */
public class SnippetGeneratorWithLuceneResults {


    // Using Standard Analyzer
    private static Analyzer analyzer = new StandardAnalyzer(Version.LUCENE_47);
//    private static Analyzer sAnalyzer = new SimpleAnalyzer(Version.LUCENE_47);

    private IndexWriter writer;
    private ArrayList<File> queue = new ArrayList<File>();



    /**
     * Read queries from processed queries file
     * @param filePath path of processed queries file
     * @return queryMap map with query id and corresponding query
     */
    public static Map<String,String> getQueries(String filePath) {
        Map<String,String> queryMap = new LinkedHashMap<>();
        File file = new File(filePath);
        BufferedReader b = null;
        try {
            b = new BufferedReader(new FileReader(file));
            String readLine = "";

            System.out.println("Reading file using Buffered Reader");

            while ((readLine = b.readLine()) != null) {
                String[] queryArray  = readLine.split(":");
                System.out.println(queryArray[1].trim().length());
                queryMap.put(queryArray[0],queryArray[1].trim());
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


    public static void main(String[] args) throws IOException {

        System.out
                .println("Enter the FULL path where the index will be created: (e.g. /Usr/index or c:\\temp\\index)");

        String indexLocation = null;
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String s = br.readLine();

        SnippetGeneratorWithLuceneResults indexer = null;
        try {
            indexLocation = s;
            indexer = new SnippetGeneratorWithLuceneResults(s);
        } catch (Exception ex) {
            System.out.println("Cannot create index..." + ex.getMessage());
            System.exit(-1);
        }

        // ===================================================
        // read input from user until he enters q for quit
        // ===================================================
        while (!s.equalsIgnoreCase("q")) {
            try {
                System.out
                        .println("Enter the FULL path to add into the index (q=quit): (e.g. /home/mydir/docs or c:\\Users\\mydir\\docs)");
                System.out
                        .println("[Acceptable file types: .xml, .html, .html, .txt]");
                s = br.readLine();
                if (s.equalsIgnoreCase("q")) {
                    break;
                }

                // try to add file into the index
                indexer.indexFileOrDirectory(s);
            } catch (Exception e) {
                System.out.println("Error indexing " + s + " : "
                        + e.getMessage());
            }
        }

        // ===================================================
        // after adding, we always have to call the
        // closeIndex, otherwise the index is not created
        // ===================================================
        indexer.closeIndex();

//         =========================================================
//         Now search
//         =========================================================
        IndexReader reader = DirectoryReader.open(FSDirectory.open(new File(
                "./index")));
        IndexSearcher searcher = new IndexSearcher(reader);

        // Enter path of query file
        System.out.println("Enter path of query file");
        String queryFilePath  = br.readLine();

        // Populate queries into map
        Map<String,String> queryMap = getQueries(queryFilePath);

        // Result file
        File resultFile=new File("snippet_results/snippet_Lucene_with_query_highlighting.txt");

        // Result string
        String results="";

        // Initialize file writer for writing results to file
        try (FileWriter fw = new FileWriter(resultFile)) {

            // Iterate through map for query id and query
            for (String queryId : queryMap.keySet()) {
                s = queryMap.get(queryId);
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

                        //generate snippet
                        String[] snippet = generateSnippet(String.valueOf(d.get("path")),s);
                        for (String sen:snippet) {
                            System.out.println(sen);
                        }


                        System.out.println((i + 1) + ". " + d.get("path")
                                + " score=" + hits[i].score);
                        results+=" Q"+queryId+" "+(i+1)+" "+d.get("path").substring(7,16)+" "+hits[i].score+" LUCENE\n"+snippet[0]+"\n"+snippet[1]+"\n";

                    }
                    // 5. term stats --> watch out for which "version" of the term
                    // must be checked here instead!
                    Term termInstance = new Term("contents", s);
                    long termFreq = reader.totalTermFreq(termInstance);
                    long docCount = reader.docFreq(termInstance);
                    System.out.println(s + " Term Frequency " + termFreq
                            + " - Document Frequency " + docCount);

                } catch (Exception e) {
                    System.out.println("Error searching " + s + " : "
                            + e.getMessage());
                    break;
                }

            }
            fw.write(results);
            fw.close();
        }

    }


    /**
     * Generate snippet from document
     * @param docPath path of document to generate snippet from
     * @return snippetArray top two sentences as snippet
     */
    public static String[] generateSnippet(String docPath, String query) {
        String[] snippetArray = new String[2];
        Map<String,Double> sentenceScore = new HashMap<>();
        File file = new File(String.valueOf(docPath));
        BufferedReader b = null;
        try {
            b = new BufferedReader(new FileReader(file));
            String readLine = "";

            System.out.println("Reading file using Buffered Reader");

            while ((readLine = b.readLine()) != null) {
                if(readLine.contains("html>")) continue;
                else if(readLine.contains("pre>")) continue;
                else if (readLine.equals("")) continue;
                String pattern = "CA[0-9]+";

                Pattern r = Pattern.compile(pattern);
                Matcher m = r.matcher(readLine);
                if(m.find()) break;

                compute(readLine,query,sentenceScore);
            }

            Map<String,Double> sortedSentenceScoreMap = getSortedScores(sentenceScore);
            int count = 0;
            for (String sentence:sortedSentenceScoreMap.keySet()) {
                if (count==2) {
                    break;
                }
                snippetArray[count] = sentence;
                count++;
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
        return snippetArray;
    }

    /**
     * Return sentences sorted by score in descending order
     * @param scoreMap mapping sentence to its score
     * @return sortedMap map sorted by sentence score
     */
    public static Map<String,Double> getSortedScores(Map<String,Double> scoreMap) {
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

        /*
        //classic iterator example
        for (Iterator<Map.Entry<String, Integer>> it = list.iterator(); it.hasNext(); ) {
            Map.Entry<String, Integer> entry = it.next();
            sortedMap.put(entry.getKey(), entry.getValue());
        }*/


        return sortedMap;

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
     * Compute score for each sentence in document
     * @param sentence sentence in document
     * @param query query for which documents are retrieved
     * @param sentenceScore mapping sentence to its score
     */
    public static void compute(String sentence, String query,Map<String,Double> sentenceScore) {
        String[] queryArray = query.split(" ");
        String[] sentenceArray = sentence.split(" ");
        List<String> stopWords = fetchStopWords("./common_words.txt");
        StringBuilder sb = new StringBuilder();
        Set<String> queryWordsPresent = new HashSet<>();
        for (String q:queryArray) {
            if (stopWords.contains(q)) {
                continue;
            }
            queryWordsPresent.add(q);
        }
        int significantWordCount = 0;
        for (String sentenceWord:sentenceArray) {
            if (queryWordsPresent.contains(sentenceWord)) {
                sb.append("<highlight>"+sentenceWord+"<highlight>"+" ");
                significantWordCount++;
            }
            else {
                sb.append(sentenceWord+" ");
            }
        }
        sb.deleteCharAt(sb.length()-1);
        sentenceScore.put(sb.toString(),(significantWordCount*significantWordCount)*1.0/sentenceArray.length);
    }



    /**
     * Constructor
     *
     * @param indexDir
     *            the name of the folder in which the index should be created
     * @throws java.io.IOException
     *             when exception creating index.
     */
    SnippetGeneratorWithLuceneResults(String indexDir) throws IOException {

        FSDirectory dir = FSDirectory.open(new File(indexDir));

        IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_47,
                analyzer);

        writer = new IndexWriter(dir, config);
    }

    /**
     * Indexes a file or directory
     *
     * @param fileName
     *            the name of a text file or a folder we wish to add to the
     *            index
     * @throws java.io.IOException
     *             when exception
     */
    public void indexFileOrDirectory(String fileName) throws IOException {
        // ===================================================
        // gets the list of files in a folder (if user has submitted
        // the name of a folder) or gets a single file name (is user
        // has submitted only the file name)
        // ===================================================
        addFiles(new File(fileName));

        int originalNumDocs = writer.numDocs();
        for (File f : queue) {
            FileReader fr = null;
            try {
                Document doc = new Document();

                // ===================================================
                // add contents of file
                // ===================================================
                fr = new FileReader(f);
                doc.add(new TextField("contents", fr));
                doc.add(new StringField("path", f.getPath(), Field.Store.YES));
                doc.add(new StringField("filename", f.getName(),
                        Field.Store.YES));

                writer.addDocument(doc);
                System.out.println("Added: " + f);
            } catch (Exception e) {
                System.out.println("Could not add: " + f);
            } finally {
                fr.close();
            }
        }

        int newNumDocs = writer.numDocs();
        System.out.println("");
        System.out.println("************************");
        System.out
                .println((newNumDocs - originalNumDocs) + " documents added.");
        System.out.println("************************");

        queue.clear();
    }

    private void addFiles(File file) {

        if (!file.exists()) {
            System.out.println(file + " does not exist.");
        }
        if (file.isDirectory()) {
            for (File f : file.listFiles()) {
                addFiles(f);
            }
        } else {
            String filename = file.getName().toLowerCase();
            // ===================================================
            // Only index text files
            // ===================================================
            if (filename.endsWith(".htm") || filename.endsWith(".html")
                    || filename.endsWith(".xml") || filename.endsWith(".txt")) {
                queue.add(file);
            } else {
                System.out.println("Skipped " + filename);
            }
        }
    }

    /**
     * Close the index.
     *
     * @throws java.io.IOException
     *             when exception closing
     */
    public void closeIndex() throws IOException {
        writer.close();
    }
}
