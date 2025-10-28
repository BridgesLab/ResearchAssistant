import os
import re
import faiss
import pickle
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pybtex.database.input import bibtex
from pybtex.scanner import PybtexSyntaxError
from tqdm import tqdm

# Load env vars and OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# File paths
BIB_FILE = "library.bib"
CLEAN_FILE = "library_cleaned.bib"
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

def balance_braces(text: str) -> str:
    """Trims unmatched closing braces and balances braces crudely but safely."""
    stack = 0
    cleaned = []
    for ch in text:
        if ch == '{':
            stack += 1
            cleaned.append(ch)
        elif ch == '}':
            if stack > 0:
                stack -= 1
                cleaned.append(ch)
            else:
                # skip stray closing brace
                continue
        else:
            cleaned.append(ch)
    # add closing braces if still open
    cleaned.extend('}' * stack)
    return ''.join(cleaned)

def safe_parse_bib(file_path):
    """
    Parse a .bib file safely by removing duplicates and cleaning brace errors.
    Writes a cleaned .bib file for inspection.
    """
    with open(file_path, encoding="utf-8") as f:
        bib_content = f.read()

    # Split file into entries
    entries_raw = re.split(r'(?=@)', bib_content)
    seen_keys = set()
    deduped_entries = []

    for block in entries_raw:
        if not block.strip().startswith("@"):
            continue
        match = re.match(r'@(\w+)\{([^,]+),', block)
        if not match:
            continue
        key = match.group(2).strip()
        if key in seen_keys:
            print(f"⚠️  Skipping duplicate entry: {key}")
            continue
        seen_keys.add(key)

        # sanitize braces to prevent syntax errors
        cleaned_block = balance_braces(block)
        deduped_entries.append(cleaned_block)

    deduped_text = "\n".join(deduped_entries)

    # Write out cleaned bib for manual inspection
    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        f.write(deduped_text)

    # Now parse safely
    parser = bibtex.Parser()
    try:
        parser.parse_string(deduped_text)
    except PybtexSyntaxError as e:
        print(f"⚠️  BibTeX syntax error detected: {e}. Some entries may still be malformed.")
        print(f"💾 A cleaned version has been written to {CLEAN_FILE}")
    entries = parser.data.entries
    print(f"✅ Loaded {len(entries)} unique entries (duplicates removed).")
    return entries

def main():
    print("🔍 Loading existing metadata...")
    existing_keys, metadata = load_existing_keys(META_FILE)

    print("📚 Loading current Zotero library...")
    entries = safe_parse_bib(BIB_FILE)
    print(f"Parsed {len(entries)} unique entries from {BIB_FILE}")

    new_entries = [e for k, e in entries.items() if k not in existing_keys]
    print(f"➕ {len(new_entries)} new entries found.")

    if not new_entries:
        print("✅ No updates needed.")
        return

    print("🔧 Loading existing FAISS index...")
    index = faiss.read_index(INDEX_FILE)

    for entry in tqdm(new_entries, desc="📈 Indexing new entries"):
        title = entry.fields.get("title", "")
        if not title.strip():
            print(f"⚠️  Skipping entry with no title: {entry.key}")
            continue
        emb = embed(title)
        index.add(np.array([emb], dtype=np.float32))
        metadata.append({
            "title": title,
            "authors": [str(p) for p in entry.persons.get("author", [])],
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
