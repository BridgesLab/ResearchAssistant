import os
import faiss
import pickle
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pybtex.database import parse_file
from tqdm import tqdm

# Load env vars and OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# File paths
BIB_FILE = "library.bib"
INDEX_FILE = "zotero.index"
META_FILE = "zotero_meta.pkl"

def embed(text: str) -> list[float]:
    """Generate an OpenAI embedding for a string of text."""
    response = client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def load_existing_keys(meta_file):
    if not os.path.exists(meta_file):
        return set(), []
    with open(meta_file, "rb") as f:
        metadata = pickle.load(f)
    keys = set(m["id"] for m in metadata)
    return keys, metadata

def main():
    print("🔍 Loading existing metadata...")
    existing_keys, metadata = load_existing_keys(META_FILE)

    print("📚 Loading current Zotero library...")
    bib_data = parse_file(BIB_FILE)
    entries = list(bib_data.entries.values())
    print(f"Parsed {len(entries)} total entries from library.bib")
    print(f"First 5 keys: {[e.key for e in entries[:5]]}")

    new_entries = [e for e in entries if e.key not in existing_keys]
    print(f"➕ {len(new_entries)} new entries found.")

    if not new_entries:
        print("✅ No updates needed.")
        return

    print("🔧 Loading existing FAISS index...")
    index = faiss.read_index(INDEX_FILE)

    for entry in tqdm(new_entries, desc="📈 Indexing new entries"):
        title = entry.fields.get("title", "")
        emb = embed(title)
        index.add(np.array([emb], dtype=np.float32))
        metadata.append({
            "title": title,
            "authors": entry.persons.get("author", []),
            "year": entry.fields.get("year", ""),
            "id": entry.key
        })

    # Save updated index and metadata
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ Updated index and metadata with {len(new_entries)} new entries.")

if __name__ == "__main__":
    main()
