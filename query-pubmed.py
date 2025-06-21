"""
PubMed Search Agent

This script converts a natural language query into a PubMed-compatible
Boolean search string using GPT-4, queries PubMed via Entrez E-Utilities API,
and returns top abstracts with metadata.
"""

import requests
from xml.etree import ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

# Setup
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def convert_to_pubmed_query(natural_query):
    """
    Uses GPT-4 to convert a natural language query into a PubMed Boolean search string.

    Args:
        natural_query (str): User's natural language question

    Returns:
        str: PubMed-compatible search string
    """
    prompt = f"""You are a biomedical researcher. Convert the following natural language question into a PubMed-compatible search string using Boolean operators and MeSH terms where appropriate.

QUESTION: "{natural_query}"

Search string:"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a PubMed expert."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def query_pubmed(natural_query, max_results=5):
    """
    Queries PubMed using a GPT-generated search string and returns article metadata.

    Args:
        natural_query (str): Natural language query
        max_results (int): Max number of articles to fetch

    Returns:
        list of dict: Articles with title, abstract, authors, year, and raw text
    """
    search_term = convert_to_pubmed_query(natural_query)
    print(f"🔍 PubMed search term: {search_term}")

    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Step 1: Search for article IDs
    search_params = {
        "db": "pubmed",
        "term": search_term,
        "retmode": "xml",
        "retmax": max_results,
    }
    search_resp = requests.get(search_url, params=search_params)
    ids = ET.fromstring(search_resp.content).findall(".//Id")
    id_list = [id.text for id in ids]

    if not id_list:
        return []

    # Step 2: Fetch article metadata
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        "rettype": "abstract",
    }
    fetch_resp = requests.get(fetch_url, params=fetch_params)
    root = ET.fromstring(fetch_resp.content)

    results = []
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", default="No title")
        abstract = article.findtext(".//AbstractText", default="No abstract")
        authors = [
            f"{a.findtext('ForeName', '')} {a.findtext('LastName', '')}".strip()
            for a in article.findall(".//Author")
        ]
        year = article.findtext(".//PubDate/Year", "n.d.")
        results.append({
            "title": title.strip(),
            "abstract": abstract.strip(),
            "authors": ", ".join(authors),
            "year": year,
            "raw": f"Title: {title}\nAuthors: {', '.join(authors)}\nYear: {year}\nAbstract: {abstract}"
        })
    return results

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Does calcium affect cholesterol?"
    papers = query_pubmed(query, max_results=5)
    for p in papers:
        print(f"\n📄 {p['title']} ({p['year']}) — {p['authors']}")
        print(f"{p['abstract']}\n")
