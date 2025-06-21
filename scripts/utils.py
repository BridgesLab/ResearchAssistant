from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"

def load_prompt(name):
    """
    Loads a prompt file from the prompts directory and returns it as a string.
    """
    path = PROMPT_DIR / name
    with open(path, "r") as f:
        return f.read()
    

import os

# Load model choices from .env, with fallbacks
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL_PUBMED = os.getenv("CHAT_MODEL_PUBMED", "gpt-3.5-turbo")
CHAT_MODEL_SYNTHESIS = os.getenv("CHAT_MODEL_SYNTHESIS", "gpt-4o")
