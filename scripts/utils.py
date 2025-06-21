from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"

def load_prompt(name):
    """
    Loads a prompt file from the prompts directory and returns it as a string.
    """
    path = PROMPT_DIR / name
    with open(path, "r") as f:
        return f.read()
