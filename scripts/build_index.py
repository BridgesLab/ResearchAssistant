import os
import pickle
import faiss
import bibtexparser
import numpy as np
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAIError, OpenAI
import tiktoken

# Set up paths
ROOT = Path(__file__).resolve().parents[1]
BIB_PATH = ROOT / "library.bib"
INDEX_PATH = ROOT / "zotero.index"
META_PATH = ROOT / "zotero_meta.pkl"
ENV_PATH = ROOT / ".env"

# Load OpenAI key
load_dotenv(dotenv_path=ENV_PATH)
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Tokenizer setup
ENC = tiktoken.encoding_for_model("text-embedding-3-large")

def safe_truncate(text, max_tokens=6000):
    tokens = ENC.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return ENC.decode(tokens[:max_tokens])

def get_embedding(text):
    resp = client.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return resp.data[0].embedding

# Read BibTeX and extract entries
with open(BIB_PATH, "r") as bibfile:
    bib_db = bibtexparser.load(bibfile)

entries = bib_db.entries
print(f"Loaded {len(entries)} entries from library.bib")

# Build FAISS index
dim = 3072  # Dimension for text-embedding-3-large
index = faiss.IndexFlatL2(dim)
metadata = []

for entry in tqdm(entries, desc="Embedding entries"):
    title = entry.get("title", "Unknown Title").strip()
    year = entry.get("year", "Unknown Year")
    authors = entry.get("author", "Unknown Author")
    abstract = entry.get("abstract", "")
    note = entry.get("note", "")

    raw = f"Title: {title}\nAuthors: {authors}\nYear: {year}\nAbstract: {abstract}\nNotes: {note}"
    truncated = safe_truncate(raw)

    try:
        emb = get_embedding(truncated)
    except OpenAIError as e:
        print(f"\n⚠️ Skipping '{title}' due to API error: {e}")
        continue

    index.add(np.array([emb], dtype=np.float32))
    metadata.append({
        "title": title,
        "year": year,
        "authors": authors,
        "raw": truncated
    })

# Save index and metadata
faiss.write_index(index, str(INDEX_PATH))
with open(META_PATH, "wb") as f:
    pickle.dump(metadata, f)

print(f"\n✅ Index built with {len(metadata)} entries.")
print(f"Saved to: {INDEX_PATH} and {META_PATH}")
