"""
Zotero Search Agent

This script loads a local FAISS index of your Zotero library and uses
OpenAI embeddings to retrieve top-k relevant papers for a given query.
"""

import pickle
import faiss
import numpy as np
from pathlib import Path
from openai import OpenAI
import tiktoken
from dotenv import load_dotenv
import os

# Path setup
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
META_PATH = ROOT / "zotero_meta.pkl"
INDEX_PATH = ROOT / "zotero.index"

load_dotenv(ENV_PATH)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ENC = tiktoken.encoding_for_model("text-embedding-3-large")

def get_embedding(text):
    """
    Returns the OpenAI embedding vector for a given text.
    """
    return client.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    ).data[0].embedding

def load_zotero():
    """
    Loads the FAISS index and metadata from disk.
    
    Returns:
        tuple: (faiss.IndexFlatL2, metadata list)
    """
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

def query_zotero_library(query, k=5):
    """
    Searches the Zotero FAISS index for the top-k most relevant entries.

    Args:
        query (str): User input question
        k (int): Number of papers to retrieve

    Returns:
        list of dict: Retrieved metadata entries
    """
    index, metadata = load_zotero()
    emb = get_embedding(query)
    D, I = index.search(np.array([emb], dtype=np.float32), k)
    return [metadata[i] for i in I[0]]
