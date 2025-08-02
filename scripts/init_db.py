import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "queries.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print(f"✅ Database initialized at {DB_PATH}")
