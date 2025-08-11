"""
Manager Agent

Coordinates responses from:
- Local Zotero RAG agent
- External PubMed agent

Then synthesizes the results using GPT-4 and identifies missing papers
not in the user's Zotero library.
"""

from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import sqlite3
from datetime import datetime

from query_zotero import query_zotero_library
from query_pubmed import query_pubmed, iterative_pubmed_search

from utils import load_prompt

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from utils import CHAT_MODEL_SYNTHESIS

DB_PATH = ROOT / "queries.db"


def log_query(query: str, db_path=DB_PATH):
    """
    Logs the user query into the SQLite database and returns the inserted query's ID.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("INSERT INTO query_log (query_text, timestamp) VALUES (?, ?)", (query, datetime.now()))
    query_id = c.lastrowid
    conn.commit()
    conn.close()
    return query_id

def save_results(query_id: int, source: str, content: str, db_path=DB_PATH):
    """
    Saves the results content for a given query and source into the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS query_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(query_id) REFERENCES query_log(id)
        )
    """)
    c.execute(
        "INSERT INTO query_results (query_id, source, content) VALUES (?, ?, ?)",
        (query_id, source, content)
    )
    conn.commit()
    conn.close()


def synthesize(query, zotero_results, pubmed_results):
    """
    Synthesizes results using a prompt from /prompts/synthesis.md
    """
    def format_docs(docs):
        return "\n\n".join([
            f"Title: {d.get('title', 'Untitled')}\n"
            f"Authors: {d.get('authors', 'Unknown')}\n"
            f"Year: {d.get('year', 'n.d.')}\n"
            f"Abstract: {d.get('abstract', '[No abstract available]')}"
            for d in docs
        ])

    template = load_prompt("synthesis.md")
    prompt = template.format(
        query=query,
        zotero_docs=format_docs(zotero_results),
        pubmed_docs=format_docs(pubmed_results)
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL_SYNTHESIS,
        messages=[
            {"role": "system", "content": "You are a biomedical research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scripts/manager_agent.py 'your research question'")
        exit()

    query = " ".join(sys.argv[1:])

    # Log the query and get its unique ID
    query_id = log_query(query)

    print("🔍 Querying Zotero library...")
    zotero_results = query_zotero_library(query, k=5)
    zotero_text = "\n\n".join([
        f"Title: {d.get('title', 'Untitled')}\n"
        f"Authors: {d.get('authors', 'Unknown')}\n"
        f"Year: {d.get('year', 'n.d.')}\n"
        f"Abstract: {d.get('abstract', '[No abstract available]')}"
        for d in zotero_results
    ])
    save_results(query_id, "zotero", zotero_text)

    print("🔎 Querying PubMed...")
    pubmed_results = iterative_pubmed_search(query, max_results=5)
    pubmed_text = "\n\n".join([
        f"Title: {d.get('title', 'Untitled')}\n"
        f"Authors: {d.get('authors', 'Unknown')}\n"
        f"Year: {d.get('year', 'n.d.')}\n"
        f"Abstract: {d.get('abstract', '[No abstract available]')}"
        for d in pubmed_results
    ])
    save_results(query_id, "pubmed", pubmed_text)

    print("🧠 Synthesizing answer with GPT-4...")
    answer = synthesize(query, zotero_results, pubmed_results)
    save_results(query_id, "synthesis", answer)

    print("\n=== Synthesized Answer ===\n")
    print(answer)
