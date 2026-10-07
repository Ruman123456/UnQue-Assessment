import sqlite3
import os
from app.config import settings

def get_db_connection():
    db_path = settings.DATABASE_PATH
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meta_lead_id TEXT UNIQUE NOT NULL,
        form_id TEXT,
        page_id TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        ad_id TEXT,
        adset_id TEXT,
        campaign_id TEXT,
        raw_data TEXT,
        created_time TEXT,
        received_time TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_meta_lead_id ON leads(meta_lead_id)")
    conn.commit()
    conn.close()
