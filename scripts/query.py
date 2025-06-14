import os
import pickle
import faiss
import numpy as np
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load index and metadata
def load_index_and_metadata():
    index_path = os.path.join(os.path.dirname(__file__), "..", "zotero.index")
    meta_path = os.path.join(os.path.dirname(__file__), "..", "zotero_meta.pkl")

    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata

# Get OpenAI embedding
def get_embedding(text, model="text-embedding-3-large"):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# Search the index
def search_index(query, index, metadata, k=5):
    embedding = get_embedding(query)
    D, I = index.search(np.array([embedding], dtype=np.float32), k)
    return [metadata[i] for i in I[0]]

# Ask GPT based on retrieved results
def ask_gpt_with_context(query, results):
    context = "\n\n".join([r["raw"] for r in results])
    prompt = f"""You are a research assistant. Based on the following papers, answer the user's question with evidence-based reasoning.

PAPERS:
{context}

QUESTION:
{query}
"""
    response = openai.ChatCompletion.create(
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
        print("Usage: python scripts/query.py \"Your research question here\"")
        exit(1)

    query = sys.argv[1]
    print(f"Running query: {query}")

    index, metadata = load_index_and_metadata()
    results = search_index(query, index, metadata)

    print("\n🧠 GPT-4 Answer:")
    answer = ask_gpt_with_context(query, results)
    print(answer)

    print("\n📚 Cited Papers:")
    for r in results:
        print(f"- {r['title']} ({r['year']})")
