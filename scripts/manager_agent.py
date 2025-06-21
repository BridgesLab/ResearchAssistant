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
from utils import load_prompt

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from utils import CHAT_MODEL_SYNTHESIS

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
    print("🔍 Querying Zotero library...")
    zotero_results = query_zotero_library(query, k=5)

    print("🔎 Querying PubMed...")
    pubmed_results = query_pubmed(query, max_results=5)

    print("🧠 Synthesizing answer with GPT-4...")
    answer = synthesize(query, zotero_results, pubmed_results)

    print("\n=== Synthesized Answer ===\n")
    print(answer)
