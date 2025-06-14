import os
import pickle
import faiss
import numpy as np
import streamlit as st
from time import sleep
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

# ------------------------
# Set up project paths
# ------------------------
ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "zotero.index"
META_PATH = ROOT / "zotero_meta.pkl"
ENV_PATH = ROOT / ".env"

# ------------------------
# Streamlit page config
# ------------------------
st.set_page_config(page_title="Zotero‑RAG Search")

# ------------------------
# Load API key from .env
# ------------------------
load_dotenv(dotenv_path=ENV_PATH)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
ENC = tiktoken.encoding_for_model("text-embedding-3-large")

def get_embedding(text):
    embedding = client.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return embedding.data[0].embedding

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
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a biomedical research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ------------------------
# UI: Branding and styles
# ------------------------
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
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title">Research Assistant</div>', unsafe_allow_html=True)

# ------------------------
# Main interaction
# ------------------------
query = st.text_input("Enter your research question", "")

if st.button("Search"):
    with st.spinner("🔍 Searching your Zotero library..."):
        papers = search(query)
        sleep(0.5)
    with st.spinner("🤖 Querying GPT-4 for an answer..."):
        answer = ask_gpt(query, papers)
        sleep(0.5)

    st.markdown("### 🧠 GPT-4 Answer")
    st.write(answer)

    st.markdown("### 📚 Retrieved Papers")
    for p in papers:
        title = p["title"]
        year = p["year"]
        authors = p["authors"]
        st.markdown(
            f"- <span class='paper-title'><a href='https://scholar.google.com/scholar?q={title}' target='_blank'>{title}</a></span> ({year}) – {authors}",
            unsafe_allow_html=True
        )
