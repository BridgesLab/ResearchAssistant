import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from Bio import Entrez

load_dotenv()

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "queries.db"

ENTREZ_EMAIL = os.getenv("EMAIL_USER")  # Required by NCBI
CACHE_FILE = "pubmed_cache.json"
MAX_RESULTS = 10  # Limit per search term

Entrez.email = ENTREZ_EMAIL

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_recent_queries(db_path=DB_PATH, limit=20):
    """
    Fetch distinct recent queries from the SQLite DB.
    """
    if not os.path.exists(db_path):
        print(f"Warning: {db_path} not found. No queries loaded.")
        return []

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT query_text FROM query_log
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def search_pubmed(term):
    """
    Search PubMed for the given term, returning a list of PMIDs.
    """
    try:
        handle = Entrez.esearch(
            db="pubmed",
            term=term,
            retmax=MAX_RESULTS,
            sort="most+recent"
        )
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"]
    except Exception as e:
        print(f"Error searching PubMed for '{term}': {e}")
        return []

def fetch_details(pmid_list):
    """
    Fetch detailed Medline data for a list of PMIDs.
    """
    if not pmid_list:
        return ""

    try:
        handle = Entrez.efetch(
            db="pubmed",
            id=pmid_list,
            rettype="medline",
            retmode="text"
        )
        result = handle.read()
        handle.close()
        return result
    except Exception as e:
        print(f"Error fetching details from PubMed: {e}")
        return ""

def main():
    print(f"📅 PubMed Watcher started at {datetime.now()}")
    cache = load_cache()
    new_items = []

    search_terms = get_recent_queries()
    if not search_terms:
        print("No recent queries found to search PubMed.")
        return

    for term in search_terms:
        print(f"🔍 Searching PubMed for: {term}")
        ids = search_pubmed(term)
        seen_ids = set(cache.get(term, []))
        new_ids = [pid for pid in ids if pid not in seen_ids]

        if new_ids:
            print(f"🆕 Found {len(new_ids)} new results for: {term}")
            details = fetch_details(new_ids)
            new_items.append((term, new_ids, details))
            cache[term] = list(set(cache.get(term, []) + new_ids))
        else:
            print(f"✅ No new results for: {term}")

    save_cache(cache)

    if new_items:
        print("\n=== New PubMed Articles Found ===\n")
        for term, ids, details in new_items:
            print(f"🔹 Search Term: {term}")
            print(details)
            print("----")
    else:
        print("📭 No new PubMed articles found this time.")

if __name__ == "__main__":
    main()
