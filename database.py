"""
Database helper module.
Uses Python's built-in sqlite3 module - no external ORM required.
"""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "certificate_portal.db")


def get_connection():
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    cert_type TEXT NOT NULL,
    applicant_name TEXT NOT NULL,
    father_name TEXT,
    dob TEXT,
    gender TEXT,
    caste TEXT,
    religion TEXT,
    annual_income TEXT,
    address TEXT,
    district TEXT,
    taluk TEXT,
    village TEXT,
    purpose TEXT,
    status TEXT DEFAULT 'Pending',
    remarks TEXT,
    officer_id INTEGER,
    certificate_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (officer_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    doc_type TEXT,
    original_name TEXT,
    stored_name TEXT,
    uploaded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE
);
"""


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def dict_from_row(row):
    return dict(row) if row else None
