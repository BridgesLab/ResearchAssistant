#!/usr/bin/env python3
"""
watch_pubmed.py

Runs a biweekly PubMed check for saved queries in queries.db.
Sends an email summary with any new results or a status note.
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

from query_pubmed import query_pubmed  # uses your PubMed agent

# ------------------------
# Setup paths and logging
# ------------------------
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "queries.db"
ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info(f"Starting PubMed watcher at {datetime.now()}")
logging.info(f"Using database at {DB_PATH}")


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
print("DEBUG: Loading .env from:", ROOT / ".env")
print("DEBUG: EMAIL_FROM =", os.getenv("EMAIL_FROM"))
print("DEBUG: EMAIL_TO =", os.getenv("EMAIL_TO"))
print("DEBUG: EMAIL_APP_PASSWORD =", os.getenv("EMAIL_APP_PASSWORD"))

# ------------------------
# Email configuration (from .env)
# ------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("EMAIL_APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL", SMTP_USER)

if not SMTP_USER or not SMTP_PASS:
    logging.error("❌ Email credentials are missing in .env")
    exit(1)


# ------------------------
# Email function
# ------------------------
def send_email_summary(results, note=None):
    """
    Send an email with PubMed results or a status update.
    """
    if results:
        body = "Here are the new PubMed results:\n\n"
        for r in results:
            title = r.get("title", "Untitled")
            link = r.get("link", "")
            body += f"- {title}\n  {link}\n\n"
    else:
        body = note or "No new results this cycle."

    msg = MIMEText(body)
    msg["Subject"] = "PubMed Watcher Update"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    logging.info(f"📧 Email sent to {TO_EMAIL}")


# ------------------------
# Database access
# ------------------------
def get_saved_queries():
    """Retrieve distinct saved queries from queries.db."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT query FROM query_log")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


# ------------------------
# Main watcher logic
# ------------------------
def run_biweekly_pubmed_check():
    queries = get_saved_queries()
    logging.info(f"Found {len(queries)} saved queries")

    all_new_results = []
    for q in queries:
        logging.info(f"🔎 Checking PubMed for: {q}")
        results = query_pubmed(q, max_results=5)
        # In production, filter only "new" results if desired
        all_new_results.extend(results)

    if all_new_results:
        logging.info(f"Found {len(all_new_results)} total results")
        send_email_summary(all_new_results)
    else:
        logging.info("No new PubMed results found. Sending status email...")
        send_email_summary([], note="No new results this cycle.")


# ------------------------
# Entrypoint
# ------------------------
if __name__ == "__main__":
    try:
        run_biweekly_pubmed_check()
    except Exception as e:
        logging.exception("❌ Watcher run failed")
