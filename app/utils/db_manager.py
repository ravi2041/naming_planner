# app/utils/db_manager.py
import mysql.connector
from mysql.connector import Error
from app.utils.config_loader import MYSQL_CONFIG


def get_connection():
    """Establish a MySQL connection using config."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        print(f"❌ MySQL Connection Error: {e}")
        raise


def init_db():
    """Initialize MySQL table if it doesn't exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_names (
        id INT AUTO_INCREMENT PRIMARY KEY,
        planner_type VARCHAR(50) NOT NULL,
        plan_number VARCHAR(50),
        name VARCHAR(255) UNIQUE,
        advertiser VARCHAR(100),
        product VARCHAR(100),
        objective VARCHAR(50),
        campaign VARCHAR(255),
        month VARCHAR(20),
        year VARCHAR(10),
        strategy_tactic VARCHAR(100),
        publisher VARCHAR(100),
        site VARCHAR(100),
        media_type VARCHAR(50),
        targeting VARCHAR(255),
        size_format VARCHAR(100),
        creative_message TEXT,
        free_form TEXT,
        source VARCHAR(50),
        validation_status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def insert_name(record: dict):
    """Insert new name record into MySQL database."""
    conn = get_connection()
    cur = conn.cursor()

    query = """
    INSERT INTO marketing_names (
        planner_type, plan_number, name, advertiser, product, objective, campaign,
        month, year, strategy_tactic, publisher, site, media_type, targeting,
        size_format, creative_message, free_form, source, validation_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
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
        record.get("source"),
        record.get("validation_status")
    )

    try:
        cur.execute(query, values)
        conn.commit()
        print(f"✅ Saved '{record.get('name')}' successfully.")
    except mysql.connector.Error as e:
        print(f"⚠️ Error inserting record: {e}")
    finally:
        conn.close()


def fetch_all_names(planner_type: str = None):
    """Fetch all campaign names (optionally filtered by planner type)."""
    conn = get_connection()
    cur = conn.cursor()

    if planner_type:
        cur.execute("SELECT name FROM marketing_names WHERE planner_type = %s", (planner_type,))
    else:
        cur.execute("SELECT name FROM marketing_names")

    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
