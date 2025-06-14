import os
import pickle
import faiss
import numpy as np
import openai
import streamlit as st
from time import sleep
from pathlib import Path
from dotenv import load_dotenv

# ------------------------
# Set project root and paths
# ------------------------
ROOT = Path(__file__).resolve().parents[1]  # project root
INDEX_PATH = ROOT / "zotero.index"
META_PATH = ROOT / "zotero_meta.pkl"
ENV_PATH = ROOT / ".env"

# ------------------------
# Load API key from .env
# ------------------------
load_dotenv(dotenv_path=ENV_PATH)
openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------------
# Load FAISS index and metadata
# ------------------------
@st.cache_resource
def load_index_meta():
    idx = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    return idx, meta

idx, metadata = load_index_meta()

# ------------------------
# Embedding function
# ------------------------
def get_embedding(text):
    resp = openai.embeddings.create(input=[text], model="text-embedding-3-large")
    return resp.data[0].embedding

# ------------------------
# Search function
# ------------------------
def search(query, k=5):
    emb = get_embedding(query)
    D, I = idx.search(np.array([emb], dtype=np.float32), k)
    return [metadata[i] for i in I[0]]

# ------------------------
# Query GPT-4 with paper context
# ------------------------
def ask_gpt(query, papers):
    context = "\n\n".join([p["raw"] for p in papers])
    prompt = f"""You are a research assistant. Based on the following papers, answer the user's question with evidence-based reasoning.

PAPERS:
{context}

QUESTION:
{query}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"system","content":"You are a biomedical research assistant."},
                  {"role":"user","content":prompt}],
    )
    return resp.choices[0].message.content

# ------------------------
# Streamlit UI setup
# ------------------------
st.set_page_config(page_title="Zotero‑RAG Search")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');

    html, body, [class*="css"]  {
      background-color: #FFFFFF;
      color: #00274C;
      font-family: 'Nunito Sans', sans-serif;
    }
    .title { color: #FFCB05; font-weight:700; font-size:2.5rem; }
    .paper-title { font-weight:700; font-size:1.1rem; }
    .sidebar .stButton > button {
      background-color: #00274C; color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">Zotero‑RAG</div>', unsafe_allow_html=True)

# ------------------------
# Query Input and Run
# ------------------------
query = st.text_input("Enter your research question", "")

if st.button("Search"):
    with st.spinner("Searching your library…"):
        papers = search(query)
        sleep(0.5)
    with st.spinner("Querying GPT-4…"):
        answer = ask_gpt(query, papers)
        sleep(0.5)

    st.markdown("### 🧠 GPT-4 Answer")
    st.write(answer)

    st.markdown("### 📚 Retrieved Papers")
    for p in papers:
        st.markdown(
            f"- <span class='paper-title'><a href='https://scholar.google.com/scholar?q={p['title']}' target='_blank'>{p['title']}</a></span> ({p['year']}) – {p['authors']}",
            unsafe_allow_html=True
        )
