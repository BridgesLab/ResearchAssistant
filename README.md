# ResearchAssistant
Research assistant for querying a local library and pubmed and returning research questions

This an AI-powered literature assistant that lets you interrogate your own Zotero library using GPT-4.  
It uses OpenAI’s `text-embedding-3-large` to index your `.bib` file and enables natural language queries with GPT-based summarization and synthesis.

---

## Features

- Uses your existing `library.bib` exported from Zotero
- Builds a local vector database (FAISS) of your papers
- Queries via natural language, returns GPT-4 answers with citations
- No internet calls to external data sources — runs on your own references

---

## Requirements

- Python 3.10+
- A zotero library
- Conda (Miniconda or Anaconda)
- An OpenAI API key with access to:
  - `text-embedding-3-large`
  - `gpt-4` or `gpt-4o`

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/BridgesLab/ResearchAssistant.git
cd zotero-rag
```

### 2. Export your Zotero library
From Zotero there are two options:

1. Within Zotero `File → Export Library → Format: BibTeX`.  Save as library.bib in the project root
2. Create a symbolic link if you manage the file elsewhere:

```bash
ln -s /path/to/your/library.bib ./library.bib
```

### 3. Set up the environment

```bash
conda env create -f environment.yml
conda activate research-assistant
```

### 4. Add your OpenAI API key
To get an API key, visit https://platform.openai.com/account/api-keys
Create a .env file in the root folder with these contents (will not be shared):

```
OPENAI_API_KEY=<ENTER IT HERE>
```

### 5. Build the Index
Run once after setting up or whenever your library.bib changes:

```bash
python scripts/build_index.py
```

This generates two files: 

* zotero.index — FAISS vector index
* zotero_meta.pkl — metadata for retrieval

---

## To Run a Query
Ask a question using your library:

```bash
python scripts/query.py "What evidence supports calcium's role in cholesterol metabolism?"
```