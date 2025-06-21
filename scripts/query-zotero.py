import os
import pickle
import faiss
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import tiktoken

# ------------------------
# Configuration
# ------------------------

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
INDEX_PATH = ROOT / "zotero.index"
META_PATH = ROOT / "zotero_meta.pkl"

# Load environment variables (API key)
load_dotenv(dotenv_path=ENV_PATH)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------
# Tokenizer for truncation
# ------------------------

ENC = tiktoken.encoding_for_model("text-embedding-3-large")

def safe_truncate(text, max_tokens=6000):
    tokens = ENC.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return ENC.decode(tokens[:max_tokens])

# ------------------------
# Embedding + retrieval
# ------------------------

def get_embedding(text):
    embedding = client.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return embedding.data[0].embedding

def load_index_and_meta():
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

def search(query, k=5):
    index, metadata = load_index_and_meta()
    emb = get_embedding(query)
    D, I = index.search(np.array([emb], dtype=np.float32), k)
    return [metadata[i] for i in I[0]]

# ------------------------
# GPT-4 response
# ------------------------

def ask_gpt(query, papers):
    context = "\n\n".join([p["raw"] for p in papers])
    prompt = f"""You are a biomedical research assistant. Based on the following papers, answer the user's question with scientific evidence and clarity.

PAPERS:
{context}

QUESTION:
{query}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a biomedical research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ------------------------
# CLI entry point (optional)
# ------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/query.py 'your question here'")
    else:
        query = " ".join(sys.argv[1:])
        papers = search(query)
        answer = ask_gpt(query, papers)
        print("\n=== GPT-4 Answer ===\n")
        print(answer)
        print("\n=== Top Papers ===")
        for p in papers:
            print(f"- {p['title']} ({p['year']}) — {p['authors']}")
