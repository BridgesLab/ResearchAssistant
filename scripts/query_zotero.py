"""
Zotero Search Agent

Loads a local FAISS index of a Zotero library and retrieves the top-k
most relevant papers based on semantic similarity.
"""

import pickle
import faiss
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
import os

from utils import load_prompt

# Setup environment and OpenAI client
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from utils import EMBEDDING_MODEL
ENC = tiktoken.encoding_for_model(EMBEDDING_MODEL)

# Load Zotero search prompt (optional, for explainability or further steps)
# zotero_search_prompt = load_prompt("zotero_search.md")  # currently unused


def get_embedding(text: str) -> list[float]:
    """
    Gets the OpenAI embedding vector for a given text.
    """
    response = client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding


def load_zotero():
    """
    Loads the FAISS index and metadata from disk.

    Returns:
        tuple: (faiss.IndexFlatL2, metadata list)
    """
    index_path = ROOT / "zotero.index"
    meta_path = ROOT / "zotero_meta.pkl"
    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def query_zotero_library(query: str, k: int = 5) -> list[dict]:
    """
    Searches the Zotero FAISS index for the top-k most relevant entries.

    Args:
        query: User input question.
        k: Number of papers to retrieve.

    Returns:
        List of metadata dicts for the most relevant papers.
    """
    index, metadata = load_zotero()
    emb = get_embedding(query)
    D, I = index.search(np.array([emb], dtype=np.float32), k)
    return [metadata[i] for i in I[0]]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the effect of calcium on cholesterol?"
    results = query_zotero_library(query, k=5)
    for r in results:
        print(f"\n📄 {r.get('title', 'Untitled')} ({r.get('year', 'n.d.')}) — {r.get('authors', 'Unknown')}")
        print(f"{r.get('abstract', '[No abstract available]')}\n")
