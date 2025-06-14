import os
import pickle
import faiss
import numpy as np
import openai
from tqdm import tqdm
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load BibTeX entries
def load_bibtex_entries(bib_path):
    with open(bib_path, 'r') as f:
        parser = BibTexParser()
        parser.customization = homogenize_latex_encoding
        bib_database = parser.parse_file(f)
    return bib_database.entries

# Format title/abstract for embedding
def format_entry_for_embedding(entry):
    title = entry.get("title", "")
    abstract = entry.get("abstract", "")
    authors = entry.get("author", "")
    year = entry.get("year", "")
    return f"Title: {title}\nAuthors: {authors}\nYear: {year}\nAbstract: {abstract}"

# Get OpenAI embedding
def get_embedding(text, model="text-embedding-3-large"):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# Build FAISS index
def build_faiss_index(entries):
    dim = 3072  # text-embedding-3-large
    index = faiss.IndexFlatL2(dim)
    metadata = []

    for entry in tqdm(entries):
        text = format_entry_for_embedding(entry)
        embedding = get_embedding(text)
        index.add(np.array([embedding], dtype=np.float32))
        metadata.append({
            "id": entry.get("ID", ""),
            "title": entry.get("title", ""),
            "authors": entry.get("author", ""),
            "year": entry.get("year", ""),
            "raw": text
        })

    return index, metadata

if __name__ == "__main__":
    bib_path = os.path.join(os.path.dirname(__file__), "..", "library.bib")
    index_path = os.path.join(os.path.dirname(__file__), "..", "zotero.index")
    meta_path = os.path.join(os.path.dirname(__file__), "..", "zotero_meta.pkl")

    print("Loading BibTeX entries...")
    entries = load_bibtex_entries(bib_path)

    print("Building index...")
    index, metadata = build_faiss_index(entries)

    print(f"Saving index to {index_path}")
    faiss.write_index(index, index_path)

    print(f"Saving metadata to {meta_path}")
    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    print("Done.")
