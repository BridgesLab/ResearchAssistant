# ResearchAssistant

![Built with GPT-4](https://img.shields.io/badge/Built%20with-GPT--4-blueviolet)

An AI-powered assistant for querying your personal Zotero library and synthesizing literature across sources like PubMed using GPT-4.

This tool lets you interrogate your own research collection using natural language, and combines it with up-to-date PubMed searches to generate integrated answers, identify gaps, and recommend papers to add.

---

## Features

- ✅ Query your Zotero library using natural language  
- 🔍 Automatically search PubMed for new or related findings  
- 🧠 Synthesizes both sources with GPT-4 (or GPT-4o)  
- 🗃️ Local vector search with FAISS for your own library  
- 🧾 Logs and stores queries and results in a local SQLite database  
- 📬 Watch PubMed for new papers on past queries and send email alerts  
- 📄 Prompts factored into editable Markdown files in `/prompts`  

---

## Requirements

- Python 3.10+  
- A Zotero library (`.bib` file)  
- Conda (Miniconda or Anaconda)  
- An OpenAI API key with access to:  
  - `text-embedding-3-large`  
  - `gpt-4` or `gpt-4o`  

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/BridgesLab/ResearchAssistant.git
cd ResearchAssistant
```

### 2. Export your Zotero library
You can either:

Export manually from Zotero:
File → Export Library → Format: BibTeX
Save the file as library.bib in the project root.

Or create a symbolic link to your .bib file:

```bash
ln -s /path/to/your/library.bib ./library.bib
```

### 3. Set up the Environment

```bash
ln -s /path/to/your/library.bib ./library.bib
```

### 4. Add your OpenAI API key and email settings

Create a .env file in the root folder containing at minimum:

```
OPENAI_API_KEY=your-api-key-here

# For email alerts (adjust according to your SMTP provider)
EMAIL_USER=your.email@example.com
EMAIL_PASS=your-email-password-or-app-token
EMAIL_SMTP=smtp.example.com
EMAIL_PORT=587
EMAIL_TO=your.email@example.com
```

### 5. Build the Zotero index
Run this once after setup, or whenever your library.bib is updated:

```bash
python scripts/build_index.py
```

This creates:

zotero.index — FAISS vector index of embedded papers
zotero_meta.pkl — metadata used for retrieval and synthesis

## Running a Query (Multi-Agent Mode)
Use the manager agent to query both Zotero and PubMed, and get a synthesized answer:

```bash
python scripts/manager_agent.py "What is the relationship between calcium and cholesterol?"
```

* Log your query to a local SQLite database
* Search your Zotero library using semantic similarity
* Use GPT-4 to create a PubMed search string and query PubMed
* Synthesize results and highlight any gaps or missing references
* Store results and synthesis in the database for future reference

## ⏰ Keeping Updated with PubMed Watcher
Periodically run the watcher script to search PubMed for new results related to your past queries and receive email alerts:

```bash
python scripts/watch_pubmed.py
```

Automate this with cron or task scheduler to run weekly or biweekly.

## 🌐 Optional: Streamlit UI
Launch a simple browser interface for querying your Zotero library:

```bash
streamlit run scripts/app.py
```

Open the provided local address in your browser.

## 🧾 Prompt Customization
All GPT prompts are stored in Markdown format under /prompts. These are easy to edit and version, and follow a structured format with role, task, input, output, and guardrails. Current prompts include:

* pubmed_search.md — converts questions to PubMed Boolean searches
* synthesis.md — integrates and summarizes findings
* zotero_search.md — (optional/future) for explainable Zotero querying

## Coming Soon / Possible Extensions

* 🔁 Auto-add recommended PubMed papers to Zotero
* 📄 Export summaries or citations to BibTeX, Markdown, or Notion
* 📊 Interactive filters for Zotero results
* 🧪 Jupyter or VS Code extension for integrated research