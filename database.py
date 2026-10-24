import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprinter.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                price_usd REAL DEFAULT 0.0,
                category TEXT DEFAULT 'Registration',
                emp_name TEXT DEFAULT '',
                page_found INTEGER DEFAULT 1,
                score INTEGER DEFAULT 50,
                status TEXT DEFAULT 'shortlisted',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT DEFAULT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pages_scanned INTEGER,
                tasks_found INTEGER,
                total_value REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()

def save_task(task_data):
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO tasks (task_id, title, url, price_usd, category, emp_name, page_found, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'shortlisted')
            ON CONFLICT(task_id) DO UPDATE SET
                title = excluded.title,
                price_usd = excluded.price_usd,
                score = excluded.score
        """, (
            str(task_data.get("task_id")),
            task_data.get("title", ""),
            task_data.get("url", ""),
            float(task_data.get("price_usd", 0.0)),
            task_data.get("category", "Registration"),
            task_data.get("emp_name", ""),
            int(task_data.get("page_found", 1)),
            int(task_data.get("score", 50))
        ))
    conn.close()

def get_tasks(status='shortlisted', limit=50):
    conn = get_connection()
    cur = conn.cursor()
    if status == 'all':
        cur.execute("SELECT * FROM tasks ORDER BY score DESC, price_usd DESC LIMIT ?", (limit,))
    else:
        cur.execute("SELECT * FROM tasks WHERE status = ? ORDER BY score DESC, price_usd DESC LIMIT ?", (status, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_task_by_id(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE task_id = ?", (str(task_id),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_task_status(task_id, status):
    conn = get_connection()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if status == "completed" else None
    with conn:
        conn.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE task_id = ?", (status, now, str(task_id)))
    conn.close()

def get_summary(target_goal=100.0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(price_usd), 0.0) as total FROM tasks WHERE status != 'rejected'")
    row = cur.fetchone()
    total_tasks = row["cnt"]
    total_val = row["total"]

    cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(price_usd), 0.0) as total FROM tasks WHERE status = 'completed'")
    comp_row = cur.fetchone()
    completed_cnt = comp_row["cnt"]
    completed_val = comp_row["total"]

    conn.close()
    pct = round((total_val / target_goal) * 100, 1) if target_goal > 0 else 0.0
    return {
        "total_shortlisted_tasks": total_tasks,
        "total_shortlisted_value": round(total_val, 3),
        "target_goal": target_goal,
        "goal_percentage": pct,
        "completed_count": completed_cnt,
        "completed_value": round(completed_val, 3)
    }

def record_scan_log(pages, found, total_val):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO scan_logs (pages_scanned, tasks_found, total_value) VALUES (?, ?, ?)",
                     (pages, found, total_val))
    conn.close()

init_db()
