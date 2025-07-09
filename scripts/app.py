import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Add scripts folder to path so we can import manager_agent
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from manager_agent import query_zotero_library, query_pubmed, synthesize

# Load environment variables for OpenAI key
load_dotenv(ROOT / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit page config
st.set_page_config(page_title="Research Assistant — Multi-Agent Mode")

# Custom styling (University of Michigan colors + fonts)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');
    html, body, [class*="css"] {
      background-color: #FFFFFF;
      color: #00274C;
      font-family: 'Nunito Sans', sans-serif;
    }
    .title { color: #FFCB05; font-weight:700; font-size:2.5rem; margin-bottom:1rem; }
    .paper-title { font-weight:700; font-size:1.1rem; }
    a { color: #00274C; text-decoration: none; }
    a:hover { text-decoration: underline; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Research Assistant — Multi-Agent Mode</div>', unsafe_allow_html=True)

query = st.text_input("Enter your research question", "")

if st.button("Run Multi-Agent Query") and query.strip():
    with st.spinner("🔍 Querying Zotero library..."):
        zotero_results = query_zotero_library(query, k=5)

    with st.spinner("🔎 Querying PubMed..."):
        pubmed_results = query_pubmed(query, max_results=5)

    with st.spinner("🧠 Synthesizing results with GPT-4..."):
        answer = synthesize(query, zotero_results, pubmed_results)

    st.markdown("### 🧠 Synthesized Answer")
    st.write(answer)

    st.markdown("### 📚 Zotero Results")
    for doc in zotero_results:
        url = doc.get("url", "#")
        title = doc.get("title", "Untitled")
        year = doc.get("year", "n.d.")
        authors = doc.get("authors", "Unknown")
        st.markdown(
            f"- <a href='{url}' target='_blank' class='paper-title'>{title}</a> ({year}) – {authors}",
            unsafe_allow_html=True,
        )

    st.markdown("### 🔬 PubMed Results")
    for doc in pubmed_results:
        url = doc.get("url", "#")
        title = doc.get("title", "Untitled")
        year = doc.get("year", "n.d.")
        authors = doc.get("authors", "Unknown")
        st.markdown(
            f"- <a href='{url}' target='_blank' class='paper-title'>{title}</a> ({year}) – {authors}",
            unsafe_allow_html=True,
        )
