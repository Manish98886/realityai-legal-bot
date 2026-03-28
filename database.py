import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    bar_council_number TEXT,
    specialization TEXT,
    is_admin BOOLEAN DEFAULT 0,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language_preference TEXT DEFAULT 'auto',
    last_active TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    case_type TEXT,
    court TEXT,
    parties TEXT,
    fir_number TEXT,
    sections TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS hearings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    hearing_date DATE NOT NULL,
    hearing_time TEXT,
    court_room TEXT,
    purpose TEXT,
    reminder_sent BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_type TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    user_id INTEGER,
    file_id TEXT NOT NULL,
    file_name TEXT,
    file_type TEXT,
    doc_type TEXT,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db_path():
    global DB_PATH
    if DB_PATH is None:
        from config import DATABASE_PATH
        DB_PATH = DATABASE_PATH
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    return DB_PATH


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# --- User functions ---

def get_or_create_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def update_user(user_id, **kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE users SET {sets}, last_active = ? WHERE user_id = ?", vals + [datetime.now()])
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_registered_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users WHERE name IS NOT NULL ORDER BY registered_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Case functions ---

def create_case(user_id, title, case_type, court, parties, fir_number, sections, description):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO cases (user_id, title, case_type, court, parties, fir_number, sections, description) VALUES (?,?,?,?,?,?,?,?)",
        (user_id, title, case_type, court, parties, fir_number, sections, description)
    )
    conn.commit()
    case_id = cur.lastrowid
    conn.close()
    return case_id


def get_user_cases(user_id, status=None, offset=0, limit=5):
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM cases WHERE user_id = ? AND status = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (user_id, status, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM cases WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_user_cases(user_id, status=None):
    conn = get_connection()
    if status:
        count = conn.execute("SELECT COUNT(*) as c FROM cases WHERE user_id = ? AND status = ?", (user_id, status)).fetchone()["c"]
    else:
        count = conn.execute("SELECT COUNT(*) as c FROM cases WHERE user_id = ?", (user_id,)).fetchone()["c"]
    conn.close()
    return count


def get_case(case_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_case_with_details(case_id):
    conn = get_connection()
    case = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case:
        conn.close()
        return None
    hearings = conn.execute("SELECT * FROM hearings WHERE case_id = ? AND status = 'scheduled' ORDER BY hearing_date", (case_id,)).fetchall()
    evidence = conn.execute("SELECT * FROM evidence WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
    docs = conn.execute("SELECT * FROM documents WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
    conn.close()
    return {
        "case": dict(case),
        "hearings": [dict(h) for h in hearings],
        "evidence": [dict(e) for e in evidence],
        "documents": [dict(d) for d in docs],
    }


def update_case_status(case_id, status):
    conn = get_connection()
    conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?", (status, datetime.now(), case_id))
    conn.commit()
    conn.close()


def delete_case(case_id):
    conn = get_connection()
    conn.execute("DELETE FROM evidence WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM hearings WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM documents WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
    conn.commit()
    conn.close()


def get_all_cases():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Hearing functions ---

def create_hearing(case_id, hearing_date, hearing_time, purpose):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO hearings (case_id, hearing_date, hearing_time, purpose) VALUES (?,?,?,?)",
        (case_id, hearing_date, hearing_time, purpose)
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_upcoming_hearings(days=7):
    conn = get_connection()
    rows = conn.execute(
        "SELECT h.*, c.title, c.user_id FROM hearings h JOIN cases c ON h.case_id = c.case_id WHERE h.hearing_date <= date('now', '+' || ? || ' days') AND h.status = 'scheduled' ORDER BY h.hearing_date",
        (str(days),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hearings_for_reminder(days_before):
    conn = get_connection()
    rows = conn.execute(
        "SELECT h.*, c.title, c.user_id FROM hearings h JOIN cases c ON h.case_id = c.case_id WHERE h.hearing_date = date('now', '+' || ? || ' days') AND h.status = 'scheduled' AND h.reminder_sent = 0",
        (str(days_before),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_hearing_reminder_sent(hearing_id):
    conn = get_connection()
    conn.execute("UPDATE hearings SET reminder_sent = 1 WHERE id = ?", (hearing_id,))
    conn.commit()
    conn.close()


def cancel_hearing(hearing_id):
    conn = get_connection()
    conn.execute("UPDATE hearings SET status = 'cancelled' WHERE id = ?", (hearing_id,))
    conn.commit()
    conn.close()


def get_case_hearings(case_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM hearings WHERE case_id = ? AND status = 'scheduled' ORDER BY hearing_date",
        (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Evidence functions ---

def add_evidence(case_id, item_name, item_type=None, notes=None):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO evidence (case_id, item_name, item_type, status, notes) VALUES (?,?,?,?,?)",
        (case_id, item_name, item_type, "pending", notes)
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_case_evidence(case_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM evidence WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_evidence_status(evidence_id, status):
    conn = get_connection()
    conn.execute("UPDATE evidence SET status = ? WHERE id = ?", (status, evidence_id))
    conn.commit()
    conn.close()


# --- Document functions ---

def save_document(case_id, user_id, file_id, file_name, file_type, doc_type=None, analysis=None):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO documents (case_id, user_id, file_id, file_name, file_type, doc_type, analysis) VALUES (?,?,?,?,?,?,?)",
        (case_id, user_id, file_id, file_name, file_type, doc_type, analysis)
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_document_analysis(doc_id, analysis):
    conn = get_connection()
    conn.execute("UPDATE documents SET analysis = ? WHERE id = ?", (analysis, doc_id))
    conn.commit()
    conn.close()


# --- Conversation history ---

def add_conversation(user_id, role, content):
    conn = get_connection()
    conn.execute("INSERT INTO conversation_history (user_id, role, content) VALUES (?,?,?)", (user_id, role, content))
    conn.commit()
    conn.close()


def get_conversation_history(user_id, limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM conversation_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def trim_conversation_history(user_id, keep=10):
    conn = get_connection()
    conn.execute(
        "DELETE FROM conversation_history WHERE user_id = ? AND id NOT IN (SELECT id FROM conversation_history WHERE user_id = ? ORDER BY id DESC LIMIT ?)",
        (user_id, user_id, keep)
    )
    conn.commit()
    conn.close()


def clear_old_conversations(days=7):
    conn = get_connection()
    conn.execute("DELETE FROM conversation_history WHERE created_at < datetime('now', '-' || ? || ' days')", (str(days),))
    conn.commit()
    conn.close()


# --- Stats functions ---

def log_stat(user_id, action, details=""):
    conn = get_connection()
    conn.execute("INSERT INTO bot_stats (user_id, action, details) VALUES (?,?,?)", (user_id, action, details))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_cases = conn.execute("SELECT COUNT(*) as c FROM cases").fetchone()["c"]
    active_cases = conn.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'active'").fetchone()["c"]
    total_messages = conn.execute("SELECT COUNT(*) as c FROM bot_stats WHERE action = 'message'").fetchone()["c"]
    ai_calls = conn.execute("SELECT COUNT(*) as c FROM bot_stats WHERE action = 'ai_call'").fetchone()["c"]
    conn.close()
    return {
        "total_users": total_users,
        "total_cases": total_cases,
        "active_cases": active_cases,
        "total_messages": total_messages,
        "ai_calls": ai_calls,
    }


# --- Rate limiting ---

_rate_limits = {}

def check_rate_limit(user_id, max_calls=20, window=3600):
    import time
    now = time.time()
    if user_id not in _rate_limits:
        _rate_limits[user_id] = []
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if now - t < window]
    if len(_rate_limits[user_id]) >= max_calls:
        return False
    _rate_limits[user_id].append(now)
    return True
