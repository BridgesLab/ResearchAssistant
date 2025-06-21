# build_index.py
import os
import numpy as np
import faiss
from pybtex.database import parse_file
from openai import OpenAI
from dotenv import load_dotenv
import pickle
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load model names from .env with fallback defaults
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Paths
BIB_FILE = "library.bib"
INDEX_FILE = "zotero.index"
META_FILE = "zotero_meta.pkl"

def embed(text: str) -> list[float]:
    """Call OpenAI embeddings API to embed a string."""
    response = client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def main():
    # Parse bib file
    print(f"Loading bibliography from {BIB_FILE}")
    bib_data = parse_file(BIB_FILE)
    entries = list(bib_data.entries.values())
    print(f"Loaded {len(entries)} entries from {BIB_FILE}")

    # Embed first entry to get dimension
    first_text = entries[0].fields.get("title", "") or "No title"
    first_emb = embed(first_text)
    dim = len(first_emb)
    print(f"Embedding dimension detected: {dim}")

    # Create new FAISS index
    index = faiss.IndexFlatL2(dim)

    # Metadata storage (e.g. titles, authors, year)
    metadata = []

    # Add first embedding
    index.add(np.array([first_emb], dtype=np.float32))
    metadata.append({
        "title": entries[0].fields.get("title", ""),
        "authors": entries[0].persons.get("author", []),
        "year": entries[0].fields.get("year", ""),
        "id": entries[0].key
    })

    # Embed and add remaining entries
    for entry in tqdm(entries[1:], desc="Embedding entries"):
        text = entry.fields.get("title", "") or "No title"
        emb = embed(text)
        index.add(np.array([emb], dtype=np.float32))
        metadata.append({
            "title": entry.fields.get("title", ""),
            "authors": entry.persons.get("author", []),
            "year": entry.fields.get("year", ""),
            "id": entry.key
        })

    # Save FAISS index and metadata
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print(f"Index and metadata saved: {INDEX_FILE}, {META_FILE}")

if __name__ == "__main__":
    main()
