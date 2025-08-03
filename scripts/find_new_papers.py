#!/usr/bin/env python3
"""
Finds new PubMed papers for previously saved queries in the last N days.
Prints a summary for each query, even if there are no new results.

Usage:
    python scripts/find_new_papers.py --days 60
"""

import os
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from Bio import Entrez

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "queries.db"

# Load .env
load_dotenv(ROOT / ".env")
Entrez.email = os.getenv("EMAIL_USER") or os.getenv("EMAIL_FROM") or "researchassistant@example.com"

def get_saved_queries(db_path="queries.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check which tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    
    query_list = []
    if "queries" in tables:
        # Use queries table
        cur.execute("SELECT DISTINCT query_text FROM query_log ORDER BY timestamp DESC")
        query_list = [row[0] for row in cur.fetchall()]
    elif "query_log" in tables:
        # Fallback to query_log if queries table doesn't exist
        cur.execute("PRAGMA table_info(query_log);")
        cols = [row[1] for row in cur.fetchall()]
        # Try to find a column with 'query' in its name
        query_col = next((c for c in cols if "query" in c.lower()), cols[0])
        cur.execute(f"SELECT DISTINCT {query_col} FROM query_log ORDER BY rowid DESC")
        query_list = [row[0] for row in cur.fetchall()]

    conn.close()
    return query_list


def search_pubmed(query, since_days=30, max_results=10):
    """Search PubMed for new articles on a query since X days ago."""
    since_date = (datetime.today() - timedelta(days=since_days)).strftime("%Y/%m/%d")
    query_str = f"({query}) AND ({since_date}[PDAT] : 3000[PDAT])"

    handle = Entrez.esearch(db="pubmed", term=query_str, retmax=max_results, sort="pub+date")
    results = Entrez.read(handle)
    handle.close()

    ids = results.get("IdList", [])
    return ids

def main(days):
    queries = get_saved_queries()
    if not queries:
        print("⚠️  No saved queries found in the database.")
        return

    print(f"🔎 Checking PubMed for new results in the last {days} days...\n")

    for i, query in enumerate(queries, 1):
        ids = search_pubmed(query, since_days=days, max_results=10)
        if ids:
            print(f"✅ {i}. Topic: {query} — {len(ids)} new papers: {', '.join(ids)}")
        else:
            print(f"ℹ️ {i}. Topic: {query} — 0 new papers")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check PubMed for new papers for saved queries.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back for new papers (default: 30)")
    args = parser.parse_args()

    main(args.days)
