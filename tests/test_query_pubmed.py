import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import unittest
from unittest.mock import patch, MagicMock

from query_pubmed import query_pubmed, iterative_pubmed_search


class TestPubMedSearch(unittest.TestCase):

    @patch("query_pubmed.requests.get")
    @patch("query_pubmed.client.chat.completions.create")
    def test_query_pubmed_returns_results(self, mock_openai, mock_requests):
        # Mock the OpenAI call to convert natural query to Boolean
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="cholesterol AND calcium"))]
        )
        
        # Mock the PubMed ESearch XML response
        esearch_xml = """
        <eSearchResult>
            <IdList>
                <Id>12345</Id>
                <Id>67890</Id>
            </IdList>
        </eSearchResult>
        """
        # Mock the PubMed EFetch XML response
        efetch_xml = """
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <Article>
                        <ArticleTitle>Test Paper 1</ArticleTitle>
                        <Abstract>
                            <AbstractText>Abstract 1</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author><ForeName>John</ForeName><LastName>Doe</LastName></Author>
                        </AuthorList>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
            <PubmedArticle>
                <MedlineCitation>
                    <Article>
                        <ArticleTitle>Test Paper 2</ArticleTitle>
                        <Abstract>
                            <AbstractText>Abstract 2</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author><ForeName>Jane</ForeName><LastName>Smith</LastName></Author>
                        </AuthorList>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2022</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>
        """
        
        # Setup mock responses
        mock_requests.side_effect = [
            MagicMock(content=esearch_xml.encode("utf-8")),  # First call: esearch
            MagicMock(content=efetch_xml.encode("utf-8")),   # Second call: efetch
        ]

        results = query_pubmed("cholesterol and calcium", max_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], "Test Paper 1")
        self.assertEqual(results[1]['authors'], "Jane Smith")

    @patch("query_pubmed.query_pubmed")
    @patch("query_pubmed.client.chat.completions.create")
    def test_iterative_pubmed_search_expands_queries(self, mock_openai, mock_query_pubmed):
        # Mock initial query results
        initial_results = [
            {"title": "Paper A", "abstract": "Abstract A", "authors": "A Author", "year": "2020", "raw": ""},
            {"title": "Paper B", "abstract": "Abstract B", "authors": "B Author", "year": "2021", "raw": ""},
        ]
        # Mock subsequent results for refined queries
        refined_results_1 = [
            {"title": "Paper C", "abstract": "Abstract C", "authors": "C Author", "year": "2022", "raw": ""},
        ]
        refined_results_2 = [
            {"title": "Paper D", "abstract": "Abstract D", "authors": "D Author", "year": "2023", "raw": ""},
        ]

        # query_pubmed called for initial + two refined queries = 3 calls total
        mock_query_pubmed.side_effect = [
            initial_results,      # initial query
            refined_results_1,    # first refined query
            refined_results_2,    # second refined query
        ]

        # Mock OpenAI refinement to return two queries
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="cholesterol OR lipids\ncalcium metabolism"))]
        )

        results = iterative_pubmed_search("cholesterol and calcium", max_results=2)
        # Should include initial + both refined results, deduplicated
        self.assertEqual(len(results), 4)
        titles = {r['title'] for r in results}
        self.assertTrue("Paper A" in titles and "Paper C" in titles and "Paper D" in titles)


if __name__ == "__main__":
    unittest.main()
