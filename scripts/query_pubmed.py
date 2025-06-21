"""
PubMed Search Agent

Uses GPT-4 to convert a natural language query into a PubMed-compatible search string
and retrieves top article metadata from PubMed via E-utilities.
"""

import requests
from xml.etree import ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

from utils import load_prompt

# Setup environment and OpenAI client
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def convert_to_pubmed_query(natural_query: str) -> str:
    """
    Converts a natural language question to a PubMed-compatible search string
    using a prompt loaded from /prompts/pubmed_search.md.
    """
    template = load_prompt("pubmed_search.md")
    prompt = template.format(natural_query=natural_query)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a PubMed expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def query_pubmed(natural_query: str, max_results: int = 5) -> list[dict]:
    """
    Queries PubMed with a GPT-generated search string and returns metadata of articles.

    Args:
        natural_query: User’s question in natural language.
        max_results: Number of articles to fetch.

    Returns:
        List of article metadata dicts with keys: title, abstract, authors, year, raw.
    """
    search_term = convert_to_pubmed_query(natural_query)
    print(f"🔍 PubMed search term: {search_term}")

    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Step 1: Search article IDs
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
        abstract = article.findtext(".//AbstractText", default="[No abstract available]")
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
