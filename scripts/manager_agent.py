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

from query_zotero import query_zotero_library
from query_pubmed import query_pubmed

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def synthesize(query, zotero_results, pubmed_results):
    """
    Synthesizes answers from Zotero and PubMed search agents.

    Args:
        query (str): User research question
        zotero_results (list): Local results from Zotero index
        pubmed_results (list): External results from PubMed

    Returns:
        str: GPT-4 synthesized response with analysis and gaps
    """
    def format_docs(docs):
        return "\n\n".join([
            f"Title: {d['title']}\nAuthors: {d['authors']}\nYear: {d['year']}\nAbstract: {d['abstract']}"
            for d in docs
        ])

    prompt = f"""You are a biomedical research assistant. I asked two agents to find papers on the same topic.

Agent 1 searched my personal Zotero library.
Agent 2 searched PubMed.

Your tasks:
1. Answer the question using evidence from both sources.
2. Identify important PubMed papers not present in Zotero.
3. Recommend whether to add them to Zotero.

QUESTION:
{query}

ZOTERO RESULTS:
{format_docs(zotero_results)}

PUBMED RESULTS:
{format_docs(pubmed_results)}
"""

    response = client.chat.completions.create(
        model="gpt-4",
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
    print("🔍 Querying Zotero library...")
    zotero_results = query_zotero_library(query, k=5)

    print("🔎 Querying PubMed...")
    pubmed_results = query_pubmed(query, max_results=5)

    print("🧠 Synthesizing answer with GPT-4...")
    answer = synthesize(query, zotero_results, pubmed_results)

    print("\n=== Synthesized Answer ===\n")
    print(answer)
