# app/utils/db_manager.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "naming_panner.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS names (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        planner_type TEXT NOT NULL,
        plan_number TEXT,
        name TEXT UNIQUE,
        advertiser TEXT,
        product TEXT,
        objective TEXT,
        campaign TEXT,
        month TEXT,
        year TEXT,
        strategy_tactic TEXT,
        publisher TEXT,
        site TEXT,
        media_type TEXT,
        targeting TEXT,
        size_format TEXT,
        creative_message TEXT,
        free_form TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()


def insert_name(record: dict):
    """Generic insert for any planner type."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO names (
            planner_type, plan_number, name, advertiser, product, objective, campaign,
            month, year, strategy_tactic, publisher, site, media_type, targeting,
            size_format, creative_message, free_form
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("planner_type"),
        record.get("plan_number"),
        record.get("name"),
        record.get("advertiser"),
        record.get("product"),
        record.get("objective"),
        record.get("campaign"),
        record.get("month"),
        record.get("year"),
        record.get("strategy_tactic"),
        record.get("publisher"),
        record.get("site"),
        record.get("media_type"),
        record.get("targeting"),
        record.get("size_format"),
        record.get("creative_message"),
        record.get("free_form"),
    ))
    conn.commit()
    conn.close()


def fetch_all_names(planner_type: str = None):
    conn = get_connection()
    cur = conn.cursor()
    if planner_type:
        cur.execute("SELECT name FROM names WHERE planner_type=?", (planner_type,))
    else:
        cur.execute("SELECT name FROM names")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
