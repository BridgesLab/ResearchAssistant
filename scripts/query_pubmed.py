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

from utils import CHAT_MODEL_PUBMED

def convert_to_pubmed_query(natural_query: str) -> str:
    """
    Converts a natural language question to a PubMed-compatible search string
    using a prompt loaded from /prompts/pubmed_search.md.
    """
    template = load_prompt("pubmed_search.md")
    prompt = template.format(natural_query=natural_query)

    response = client.chat.completions.create(
        model=CHAT_MODEL_PUBMED,
        messages=[
            {"role": "system", "content": "You are a PubMed expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


# Replace your line 69 and surrounding code with this:

def query_pubmed(natural_query: str, max_results: int = 5) -> list[dict]:
    """
    Queries PubMed with a GPT-generated search string and returns metadata of articles.
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
    
    try:
        search_resp = requests.get(search_url, params=search_params, timeout=30)
        search_resp.raise_for_status()  # Raises HTTPError for bad status codes
        
        # Check if response looks like HTML (server error)
        content = search_resp.content.decode('utf-8', errors='ignore')
        if content.strip().lower().startswith('<html'):
            raise Exception("PubMed server returned HTML error page - servers may be down")
        
        # Try to parse XML
        try:
            search_root = ET.fromstring(search_resp.content)
        except ET.ParseError as e:
            # Print the problematic content for debugging
            print(f"❌ XML Parse Error: {e}")
            print(f"Response content preview: {content[:500]}...")
            raise Exception(f"PubMed returned malformed XML - servers may be experiencing issues: {e}")
        
        ids = search_root.findall(".//Id")
        id_list = [id.text for id in ids]
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error accessing PubMed: {e}")
    except Exception as e:
        if "server" in str(e).lower() or "html" in str(e).lower():
            raise Exception(f"PubMed server error: {e}")
        else:
            raise Exception(f"PubMed query error: {e}")

    if not id_list:
        return []

    # Step 2: Fetch article metadata - add similar error handling
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        "rettype": "abstract",
    }
    
    try:
        fetch_resp = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_resp.raise_for_status()
        
        # Check for HTML response
        content = fetch_resp.content.decode('utf-8', errors='ignore')
        if content.strip().lower().startswith('<html'):
            raise Exception("PubMed server returned HTML error page during fetch - servers may be down")
        
        try:
            root = ET.fromstring(fetch_resp.content)
        except ET.ParseError as e:
            print(f"❌ XML Parse Error during fetch: {e}")
            print(f"Response content preview: {content[:500]}...")
            raise Exception(f"PubMed returned malformed XML during fetch: {e}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error fetching from PubMed: {e}")
    except Exception as e:
        if "server" in str(e).lower() or "html" in str(e).lower():
            raise Exception(f"PubMed server error during fetch: {e}")
        else:
            raise Exception(f"PubMed fetch error: {e}")

    # Rest of your existing code for processing results...
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
